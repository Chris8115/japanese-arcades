package local.japanesearcades;

import net.neoforged.neoforge.common.ModConfigSpec;

/** Loaded before datapack registries, so village injection also works during world creation. */
public final class ArcadeWorldgenConfig {
    public static final ModConfigSpec SPEC;
    private static final ModConfigSpec.BooleanValue VILLAGES;
    private static final ModConfigSpec.BooleanValue STANDALONE;
    private static final ModConfigSpec.IntValue VILLAGE_WEIGHT;

    static {
        ModConfigSpec.Builder builder = new ModConfigSpec.Builder();
        builder.comment("Arcade generation in new chunks. Restart the world/server after changes.",
            "Standalone spacing, biome eligibility and terrain tolerance are also editable by datapack.");
        VILLAGES = builder.comment("Add the arcade to vanilla and supported Integrated Villages house pools, preserving existing entries.")
            .worldRestart().define("villageArcades", true);
        STANDALONE = builder.comment("Generate independent arcades, including with village overhaul mods.")
            .worldRestart().define("standaloneArcades", true);
        VILLAGE_WEIGHT = builder.comment("Relative weight multiplier for arcade entries in vanilla and supported village-overhaul pools.")
            .worldRestart().defineInRange("villageWeight", 2, 1, 10);
        SPEC = builder.build();
    }

    private ArcadeWorldgenConfig() {}

    public static boolean standaloneEnabled() { return STANDALONE.get(); }
    public static int villageWeight() { return VILLAGES.get() ? VILLAGE_WEIGHT.get() : 0; }
}
