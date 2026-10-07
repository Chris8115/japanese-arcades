# Japanese Arcades

This workspace targets Minecraft 1.21.1, NeoForge 21.1.252, and Java 21.
Use `./dev.cmd Build` to build with the configured JDK; the machine default Java is a different version.
Local Java and source-pack paths are in the ignored `dev.local.json`.

Source starts at `src/main/java/local/japanesearcades/JapaneseArcades.java`.
Mod id: `japanesearcades`. Keep it consistent with `gradle.properties` and mod metadata.
Common code must work on dedicated servers; keep client classes in client-only entry points.
Do not change Minecraft or loader versions without an explicit pack-upgrade request.

Test runs and copied third-party mods live under ignored `runs/`.
Use the small client for quick iteration and the copied pack client for compatibility checks.
Do not automatically install builds in the original pack or modify its saves.
Do not commit downloaded mods, credentials, instance metadata, logs, worlds, or machine-local settings.
Keep copied third-party jars out of the release artifact.

For new models and substantial model rebuilds, target fewer than roughly 10,000 faces.
Count the complete placed object, including every multiblock section and fixed moving hardware,
not each section separately. Check the inventory model's face count separately as well.
Exceeding this budget needs a strong, specific visual or functional justification; explain
that reason and the measured face count to the user. Prefer efficient curved meshes,
hidden-face removal, and texture detail before adding subdivisions. Audit the final exported
models rather than relying on authoring counts or treating face count as an FPS measurement.

After functional code changes, run `./dev.cmd Build` and use appropriate runtime verification.
Cabinet placement, disc playback, persistence, and removal integration tests run with `./dev.cmd GameTest`.
Do not add placeholder tests that only mirror declarations.
