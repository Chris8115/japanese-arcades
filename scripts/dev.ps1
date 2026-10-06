[CmdletBinding(SupportsShouldProcess = $true)]
param(
    [ValidateSet('Build', 'Prepare', 'Client', 'PackClient', 'DebugClient', 'DebugPackClient', 'Server', 'Data', 'SyncPack', 'GameTest')]
    [string]$Task = 'Build'
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
$workspace = Split-Path -Parent $PSScriptRoot
$settingsPath = Join-Path $workspace 'dev.local.json'
if (-not (Test-Path -LiteralPath $settingsPath)) {
    throw 'Copy dev.local.example.json to dev.local.json and set javaHome and packPath.'
}
$settings = Get-Content -LiteralPath $settingsPath -Raw | ConvertFrom-Json

function Get-WorkspacePath([string]$RelativePath) {
    $path = [IO.Path]::GetFullPath((Join-Path $workspace $RelativePath))
    $prefix = [IO.Path]::GetFullPath($workspace).TrimEnd('\') + '\'
    if (-not $path.StartsWith($prefix, [StringComparison]::OrdinalIgnoreCase)) {
        throw "Path is outside the development workspace: $path"
    }
    # Refuse junctions/symlinks that could redirect writes into the live pack.
    $ancestor = $path
    while ($ancestor.Length -ge $prefix.Length) {
        if (Test-Path -LiteralPath $ancestor) {
            if ((Get-Item -LiteralPath $ancestor -Force).Attributes -band [IO.FileAttributes]::ReparsePoint) {
                throw "Development paths must not be links: $ancestor"
            }
        }
        $ancestor = Split-Path -Parent $ancestor
    }
    return $path
}

function Sync-Pack {
    $pack = (Resolve-Path -LiteralPath $settings.packPath).Path
    $metadata = Get-Content -LiteralPath (Join-Path $pack 'minecraftinstance.json') -Raw | ConvertFrom-Json
    if ($metadata.gameVersion -ne '1.21.1' -or $metadata.baseModLoader.name -ne 'neoforge-21.1.252') {
        throw 'The source pack must use Minecraft 1.21.1 / NeoForge 21.1.252. Update the project deliberately before syncing an upgraded pack.'
    }
    $destination = Get-WorkspacePath 'runs/pack-client'
    if ($destination.StartsWith($pack.TrimEnd('\') + '\', [StringComparison]::OrdinalIgnoreCase) -or
        $pack.StartsWith($destination.TrimEnd('\') + '\', [StringComparison]::OrdinalIgnoreCase) -or
        $destination -eq $pack) {
        throw 'The development copy and source pack must be separate directories.'
    }
    if (-not $PSCmdlet.ShouldProcess($destination, 'Refresh development mods and configuration from the source pack')) {
        return
    }
    $modsPath = Get-WorkspacePath 'runs/pack-client/mods'
    New-Item -ItemType Directory -Path $modsPath -Force | Out-Null
    $manifestPath = Get-WorkspacePath 'runs/pack-client/pack-snapshot.json'
    $sourceMods = @(Get-ChildItem -LiteralPath (Join-Path $pack 'mods') -File -Filter '*.jar' |
        Where-Object { $_.Name -notlike 'funpackcustom-*' })
    $currentNames = @($sourceMods | ForEach-Object { $_.Name })
    if (Test-Path -LiteralPath $manifestPath) {
        $previous = Get-Content -LiteralPath $manifestPath -Raw | ConvertFrom-Json
        foreach ($oldMod in $previous.mods) {
            if ([IO.Path]::GetFileName($oldMod.name) -ne $oldMod.name) {
                throw 'Invalid filename in the previous pack snapshot.'
            }
            if ($oldMod.name -notin $currentNames) {
                $stale = Get-WorkspacePath ('runs/pack-client/mods/' + $oldMod.name)
                if (Test-Path -LiteralPath $stale) { Remove-Item -LiteralPath $stale }
            }
        }
    }
    $snapshotMods = foreach ($mod in $sourceMods) {
        $target = Get-WorkspacePath ('runs/pack-client/mods/' + $mod.Name)
        Copy-Item -LiteralPath $mod.FullName -Destination $target -Force
        $sha = [Security.Cryptography.SHA256]::Create()
        $stream = [IO.File]::OpenRead($target)
        try { $hash = [BitConverter]::ToString($sha.ComputeHash($stream)).Replace('-', '') }
        finally { $stream.Dispose(); $sha.Dispose() }
        [ordered]@{ name = $mod.Name; sha256 = $hash }
    }
    # Copy only pack content. Worlds, server addresses, account metadata, and logs stay in the source instance.
    foreach ($folder in @('config', 'defaultconfigs', 'kubejs', 'scripts', 'resourcepacks',
            'shaderpacks', 'moonlight-global-datapacks', 'global_packs', 'datapacks', 'patchouli_books')) {
        $sourceFolder = Join-Path $pack $folder
        if (Test-Path -LiteralPath $sourceFolder) {
            $targetFolder = Get-WorkspacePath ('runs/pack-client/' + $folder)
            New-Item -ItemType Directory -Path $targetFolder -Force | Out-Null
            foreach ($item in Get-ChildItem -LiteralPath $sourceFolder -Force) {
                Copy-Item -LiteralPath $item.FullName -Destination $targetFolder -Recurse -Force
            }
        }
    }
    [ordered]@{
        source = $pack
        copiedAtUtc = [DateTime]::UtcNow.ToString('o')
        minecraft = $metadata.gameVersion
        neoforge = '21.1.252'
        mods = @($snapshotMods)
    } | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $manifestPath -Encoding UTF8
    Write-Host "Copied $($sourceMods.Count) pack mods to $destination"
}

function Invoke-DevGradle([string[]]$GradleTasks) {
    $javaHome = (Resolve-Path -LiteralPath $settings.javaHome).Path
    $javaExe = Join-Path $javaHome 'bin/java.exe'
    $javacExe = Join-Path $javaHome 'bin/javac.exe'
    if (-not (Test-Path -LiteralPath $javacExe)) { throw 'javaHome must point to a JDK, not a JRE.' }
    $release = Get-Content -LiteralPath (Join-Path $javaHome 'release') -Raw
    if ($release -notmatch '(?m)^JAVA_VERSION="21\.') { throw 'This project needs a Java 21 JDK.' }
    $oldJavaHome = $env:JAVA_HOME
    $oldPath = $env:PATH
    try {
        $env:JAVA_HOME = $javaHome
        $env:PATH = (Join-Path $javaHome 'bin') + ';' + $oldPath
        Push-Location -LiteralPath $workspace
        try {
            & (Join-Path $workspace 'gradlew.bat') "-Dorg.gradle.java.home=$javaHome" @GradleTasks --console=plain
            if ($LASTEXITCODE -ne 0) { throw "Gradle failed with exit code $LASTEXITCODE." }
        } finally { Pop-Location }
    } finally {
        $env:JAVA_HOME = $oldJavaHome
        $env:PATH = $oldPath
    }
}

function Initialize-DevServer {
    $serverPath = Get-WorkspacePath 'runs/server'
    New-Item -ItemType Directory -Path $serverPath -Force | Out-Null
    $propertiesPath = Get-WorkspacePath 'runs/server/server.properties'
    $lines = @()
    if (Test-Path -LiteralPath $propertiesPath) {
        $lines = @(Get-Content -LiteralPath $propertiesPath |
            Where-Object { $_ -notmatch '^(server-ip|server-port|online-mode)=' })
    }
    $lines += @('server-ip=127.0.0.1', 'server-port=25575', 'online-mode=false')
    [IO.File]::WriteAllLines($propertiesPath, [string[]]$lines, [Text.Encoding]::ASCII)
}

switch ($Task) {
    'Build' { if (-not $WhatIfPreference) { Invoke-DevGradle @('build') } }
    'GameTest' {
        if (-not $WhatIfPreference) {
            $gameTestPath = Get-WorkspacePath 'runs/gametest'
            New-Item -ItemType Directory -Path $gameTestPath -Force | Out-Null
            $gameTestProperties = Get-WorkspacePath 'runs/gametest/server.properties'
            if (-not (Test-Path -LiteralPath $gameTestProperties)) {
                [IO.File]::WriteAllLines($gameTestProperties,
                    [string[]]@('server-ip=127.0.0.1', 'server-port=25576', 'online-mode=false'), [Text.Encoding]::ASCII)
            }
            Invoke-DevGradle @('runGameTestServer')
        }
    }
    'Prepare' { if (-not $WhatIfPreference) { Invoke-DevGradle @('prepareClientRun', 'preparePackClientRun', 'prepareServerRun') } }
    'Client' { if (-not $WhatIfPreference) { Invoke-DevGradle @('runClient') } }
    { $_ -in 'PackClient', 'DebugPackClient' } {
        $snapshot = Get-WorkspacePath 'runs/pack-client/pack-snapshot.json'
        if (-not (Test-Path -LiteralPath $snapshot)) { Sync-Pack }
        if (-not $WhatIfPreference) {
            if ($Task -eq 'DebugPackClient') { Invoke-DevGradle @('runPackClient', '--debug-jvm') }
            else { Invoke-DevGradle @('runPackClient') }
        }
    }
    'DebugClient' { if (-not $WhatIfPreference) { Invoke-DevGradle @('runClient', '--debug-jvm') } }
    'Server' {
        if (-not $WhatIfPreference) {
            Initialize-DevServer
            Invoke-DevGradle @('runServer')
        }
    }
    'Data' { if (-not $WhatIfPreference) { Invoke-DevGradle @('runData') } }
    'SyncPack' { Sync-Pack }
}
