package local.funpack.custom;

import java.util.List;
import java.util.Optional;
import java.util.function.Supplier;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;

/** Stable prize identities. Point prices are supplied by the arcade economy config. */
public final class ArcadePrizeCatalog {
    public record Entry(ResourceLocation id, Supplier<? extends Item> item) {
        public ItemStack output() { return new ItemStack(item.get()); }
        public Component title() { return output().getHoverName(); }
    }

    private static final List<Entry> ENTRIES = List.of(
        new Entry(id("hatsune_miku_figure"), FunPackCustom.HATSUNE_MIKU_FIGURE_ITEM),
        new Entry(id("kasane_teto_figure"), FunPackCustom.KASANE_TETO_FIGURE_ITEM),
        new Entry(id("wacca_poster"), FunPackCustom.WACCA_POSTER));

    private ArcadePrizeCatalog() {}
    private static ResourceLocation id(String path) { return ResourceLocation.fromNamespaceAndPath(FunPackCustom.MOD_ID, path); }
    public static List<Entry> entries() { return ENTRIES; }
    public static Optional<Entry> find(ResourceLocation id) { return ENTRIES.stream().filter(entry -> entry.id().equals(id)).findFirst(); }
}
