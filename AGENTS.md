# Fun pack custom mods

This workspace targets Minecraft 1.21.1, NeoForge 21.1.252, and Java 21.
Use `./dev.cmd Build` to build with the configured JDK; the machine default Java is a different version.
Local Java and source-pack paths are in the ignored `dev.local.json`.

Source starts at `src/main/java/local/funpack/custom/FunPackCustom.java`.
Mod id: `funpackcustom`. Keep it consistent with `gradle.properties` and mod metadata.
Common code must work on dedicated servers; keep client classes in client-only entry points.
Do not change Minecraft or loader versions without an explicit pack-upgrade request.

Test runs and copied third-party mods live under ignored `runs/`.
Use the small client for quick iteration and the copied pack client for compatibility checks.
Do not automatically install builds in the original pack or modify its saves.
Do not commit downloaded mods, credentials, instance metadata, logs, worlds, or machine-local settings.
Keep copied third-party jars out of the release artifact.

After functional code changes, run `./dev.cmd Build` and use appropriate runtime verification.
Cabinet placement, disc playback, persistence, and removal integration tests run with `./dev.cmd GameTest`.
Do not add placeholder tests that only mirror declarations.
