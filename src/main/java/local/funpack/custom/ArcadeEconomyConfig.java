package local.funpack.custom;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.util.RandomSource;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.Items;
import net.neoforged.neoforge.common.ModConfigSpec;

/** Server-owned, synchronized prices and reward profiles; no client-supplied money values. */
public final class ArcadeEconomyConfig {
    public static final ModConfigSpec SPEC;
    private static final ModConfigSpec.IntValue IRON, GOLD, EMERALD, DIAMOND, PLAY_COST, COOLDOWN;
    private static final ModConfigSpec.ConfigValue<List<? extends String>> RANKS, MACHINES;
    private static final Map<String, ModConfigSpec.IntValue> PRICES = new LinkedHashMap<>();
    public record Exchange(Item material, int credits) {}
    public record Rank(String label, int weight, int points) {}
    public record PlayProfile(int credits, String name, List<Rank> ranks) {
        public int maximumPoints() { return ranks.stream().mapToInt(Rank::points).max().orElse(0); }
    }
    static {
        ModConfigSpec.Builder builder = new ModConfigSpec.Builder();
        builder.comment("Credits received for ONE material. Values are server authoritative.").push("exchange");
        IRON = builder.defineInRange("iron", 20, 1, 1_000_000);
        GOLD = builder.defineInRange("gold", 60, 1, 1_000_000);
        EMERALD = builder.defineInRange("emerald", 120, 1, 1_000_000);
        DIAMOND = builder.defineInRange("diamond", 240, 1, 1_000_000);
        builder.pop().push("play");
        PLAY_COST = builder.defineInRange("defaultCreditCost", 10, 1, 1_000_000);
        COOLDOWN = builder.comment("Minimum ticks between paid plays by one player, across all machines.")
            .defineInRange("cooldownTicks", 60, 10, 1200);
        RANKS = builder.comment("Rows: profile|rank label|weight|prize points. Add new profiles and assign them below.",
                "Each weight is relative to other rows in that profile. The standard profile must exist.")
            .defineListAllowEmpty("rankProfiles", List.of("standard|C|45|10", "standard|B|30|20", "standard|A|18|40",
                "standard|S|6|80", "standard|SS / Perfect|1|150"), ArcadeEconomyConfig::validRank);
        MACHINES = builder.comment("Optional overrides: namespace:machine|credit cost|profile. Empty uses default cost and standard ranks.",
                "Example: funpackcustom:initial_d|15|standard",
                "BeatStream uses its own machine ID: funpackcustom:beatstream|10|standard")
            .defineListAllowEmpty("machineOverrides", List.of(), ArcadeEconomyConfig::validMachine);
        builder.pop().comment("Prize Point costs; ordinary material recipes are intentionally absent.").push("prizes");
        PRICES.put("hatsune_miku_figure", builder.defineInRange("hatsune_miku_figure", 2500, 1, 1_000_000));
        PRICES.put("kasane_teto_figure", builder.defineInRange("kasane_teto_figure", 2500, 1, 1_000_000));
        PRICES.put("wacca_poster", builder.defineInRange("wacca_poster", 750, 1, 1_000_000));
        builder.pop();
        SPEC = builder.build();
    }
    private ArcadeEconomyConfig() {}
    private static boolean integer(String text, int minimum, int maximum) {
        try { int value = Integer.parseInt(text); return value >= minimum && value <= maximum; }
        catch (NumberFormatException ignored) { return false; }
    }
    private static boolean validRank(Object object) {
        if (!(object instanceof String text)) { return false; }
        String[] fields = text.split("\\|", -1);
        return fields.length == 4 && fields[0].matches("[a-z0-9_-]{1,32}") && !fields[1].isBlank()
            && fields[1].length() <= 24 && integer(fields[2], 1, 10000) && integer(fields[3], 1, 1_000_000);
    }
    private static boolean validMachine(Object object) {
        if (!(object instanceof String text)) { return false; }
        String[] fields = text.split("\\|", -1);
        return fields.length == 3 && ResourceLocation.tryParse(fields[0]) != null && integer(fields[1], 1, 1_000_000)
            && fields[2].matches("[a-z0-9_-]{1,32}");
    }
    public static List<Exchange> exchangeRates() { return List.of(new Exchange(Items.IRON_INGOT, IRON.get()),
        new Exchange(Items.GOLD_INGOT, GOLD.get()), new Exchange(Items.EMERALD, EMERALD.get()), new Exchange(Items.DIAMOND, DIAMOND.get())); }
    public static int prizePrice(ResourceLocation id) {
        ModConfigSpec.IntValue price = id.getNamespace().equals(FunPackCustom.MOD_ID) ? PRICES.get(id.getPath()) : null;
        return price == null ? -1 : price.get();
    }
    public static int cooldownTicks() { return COOLDOWN.get(); }
    public static PlayProfile profile(ResourceLocation machine) {
        String selected = "standard";
        int cost = PLAY_COST.get();
        for (String line : MACHINES.get()) {
            if (!validMachine(line)) { continue; }
            String[] fields = line.split("\\|");
            if (fields[0].equals(machine.toString())) { cost = Integer.parseInt(fields[1]); selected = fields[2]; break; }
        }
        List<Rank> ranks = ranks(selected);
        if (ranks.isEmpty()) { selected = "standard"; ranks = ranks(selected); }
        // A malformed/empty profile disables plays instead of silently creating a free economy.
        return new PlayProfile(cost, selected, ranks);
    }
    private static List<Rank> ranks(String profile) {
        List<Rank> ranks = new ArrayList<>();
        for (String line : RANKS.get()) {
            if (!validRank(line) || ranks.size() >= 64) { continue; }
            String[] fields = line.split("\\|");
            if (fields[0].equals(profile)) { ranks.add(new Rank(fields[1], Integer.parseInt(fields[2]), Integer.parseInt(fields[3]))); }
        }
        return List.copyOf(ranks);
    }
    public static Rank roll(PlayProfile profile, RandomSource random) {
        int total = profile.ranks.stream().mapToInt(Rank::weight).sum();
        if (total <= 0) { throw new IllegalArgumentException("No available arcade rank profile"); }
        int draw = random.nextInt(total);
        for (Rank rank : profile.ranks) { draw -= rank.weight; if (draw < 0) { return rank; } }
        throw new IllegalStateException("Invalid arcade rank weights");
    }
}
