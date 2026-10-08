package local.japanesearcades;

import java.util.List;
import java.util.Optional;
import java.util.function.Supplier;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;

/** Shared display catalog. The server resolves every order against this list. */
public final class ArcadeOrderCatalog {
    public record Category(ResourceLocation id, Component title) {}

    public record Cost(Item item, int count) {
        public Cost {
            if (count < 1 || count > 64) { throw new IllegalArgumentException("Invalid material count"); }
        }
        public ItemStack stack() { return new ItemStack(item, count); }
    }

    public record Entry(ResourceLocation id, ResourceLocation categoryId,
            Supplier<? extends Item> result, List<Cost> costs) {
        public Entry {
            costs = List.copyOf(costs);
            if (costs.isEmpty() || costs.stream().map(Cost::item).distinct().count() != costs.size()) {
                throw new IllegalArgumentException("Each order needs a nonempty, unique list of material costs");
            }
        }
        public ItemStack output() { return new ItemStack(result.get()); }
        public Component title() { return output().getHoverName(); }
    }

    public static final ResourceLocation MACHINES = id("machines");
    public static final ResourceLocation PRIZES = id("prizes");
    public static final ResourceLocation PASSES = id("passes");
    private static final List<Category> CATEGORIES = List.of(
        new Category(MACHINES, Component.translatable("kiosk.category.machines")),
        new Category(PRIZES, Component.translatable("kiosk.category.prizes")),
        new Category(PASSES, Component.translatable("kiosk.category.passes")));
    private static final List<Entry> ENTRIES = List.of(
        machine("nostalgia_op3", JapaneseArcades.NOSTALGIA_OP3_ITEM, 16, 4, 1, 6, 6),
        machine("beatstream", JapaneseArcades.BEATSTREAM_ITEM, 16, 4, 1, 6, 6),
        machine("sound_voltex_valkyrie", JapaneseArcades.SOUND_VOLTEX_VALKYRIE_ITEM, 18, 4, 1, 6, 8),
        machine("sound_voltex_nemsys", JapaneseArcades.SOUND_VOLTEX_NEMSYS_ITEM, 16, 4, 1, 6, 6),
        machine("wacca", JapaneseArcades.WACCA_ITEM, 16, 4, 1, 8, 6),
        machine("chunithm", JapaneseArcades.CHUNITHM_ITEM, 16, 4, 1, 6, 6),
        machine("ongeki", JapaneseArcades.ONGEKI_ITEM, 16, 4, 1, 6, 6),
        machine("groove_coaster", JapaneseArcades.GROOVE_COASTER_ITEM, 16, 4, 1, 6, 6),
        machine("museca", JapaneseArcades.MUSECA_ITEM, 16, 4, 1, 6, 6),
        machine("project_diva", JapaneseArcades.PROJECT_DIVA_ITEM, 16, 4, 1, 6, 6),
        machine("chrono_circle", JapaneseArcades.CHRONO_CIRCLE_ITEM, 18, 4, 1, 8, 8),
        machine("music_diver", JapaneseArcades.MUSIC_DIVER_ITEM, 18, 4, 1, 8, 8),
        machine("popn_music", JapaneseArcades.POPN_MUSIC_ITEM, 16, 4, 1, 6, 6),
        machine("maimai", JapaneseArcades.MAIMAI_ITEM, 24, 6, 2, 8, 8),
        machine("ddr_supernova", JapaneseArcades.DDR_SUPERNOVA_ITEM, 24, 6, 2, 8, 8),
        machine("beatmania_iidx_lightning", JapaneseArcades.BEATMANIA_IIDX_LIGHTNING_ITEM, 24, 6, 2, 8, 8),
        machine("taiko", JapaneseArcades.TAIKO_ITEM, 20, 4, 1, 6, 6),
        machine("initial_d", JapaneseArcades.INITIAL_D_ITEM, 20, 4, 1, 6, 6),
        machine("jubeat", JapaneseArcades.JUBEAT_ITEM, 12, 2, 1, 4, 4),
        machine("claw_machine", JapaneseArcades.CLAW_MACHINE_ITEM, 24, 4, 1, 12, 8),
        new Entry(id("gachapon"), MACHINES, JapaneseArcades.GACHAPON_ITEM, List.of(
            new Cost(Items.IRON_INGOT, 8), new Cost(Items.GOLD_INGOT, 2),
            new Cost(Items.GLASS, 4), new Cost(Items.REDSTONE, 2))));

    private ArcadeOrderCatalog() {}

    private static Entry machine(String name, Supplier<? extends Item> item,
            int iron, int gold, int diamond, int glass, int redstone) {
        return new Entry(id(name), MACHINES, item, List.of(new Cost(Items.IRON_INGOT, iron),
            new Cost(Items.GOLD_INGOT, gold), new Cost(Items.DIAMOND, diamond),
            new Cost(Items.GLASS, glass), new Cost(Items.REDSTONE, redstone)));
    }

    private static ResourceLocation id(String path) { return ResourceLocation.fromNamespaceAndPath(JapaneseArcades.MOD_ID, path); }

    public static List<Category> categories() { return CATEGORIES; }
    public static List<Entry> entries(ResourceLocation categoryId) {
        return ENTRIES.stream().filter(entry -> entry.categoryId.equals(categoryId)).toList();
    }
    public static Optional<Entry> find(ResourceLocation id) {
        return ENTRIES.stream().filter(entry -> entry.id.equals(id)).findFirst();
    }

    /** Ordinary crafting ingredients match item identity; names do not make iron a different material. */
    public static int count(Player player, Item item) {
        int total = 0;
        for (ItemStack stack : player.getInventory().items) { if (stack.is(item)) { total += stack.getCount(); } }
        for (ItemStack stack : player.getInventory().offhand) { if (stack.is(item)) { total += stack.getCount(); } }
        return total;
    }

    public static boolean canAfford(Player player, Entry entry) {
        return entry.costs.stream().allMatch(cost -> count(player, cost.item) >= cost.count);
    }
}
