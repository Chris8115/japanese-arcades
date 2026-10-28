package local.japanesearcades;

import java.text.Normalizer;
import java.util.Comparator;
import java.util.List;
import java.util.Locale;
import java.util.Optional;
import java.util.function.Supplier;
import java.util.regex.Pattern;
import java.util.stream.Stream;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;

/** Stable prize identities. Point prices are supplied by the arcade economy config. */
public final class ArcadePrizeCatalog {
    public enum Category {
        ALL, MOB_FIGURES, CHARACTER_FIGURES, POSTERS, CUTOUTS, GLOW_STICKS, SPECIAL;

        public String id() { return name().toLowerCase(Locale.ROOT); }
        public Component title() { return Component.translatable("kiosk.prize.category." + id()); }
    }

    public enum Sort {
        NAME, PRICE_ASCENDING, PRICE_DESCENDING;

        public String id() { return name().toLowerCase(Locale.ROOT); }
        public Component title() { return Component.translatable("kiosk.prize.sort." + id()); }
    }

    public record Entry(ResourceLocation id, Supplier<? extends Item> item, Category category) {
        public ItemStack output() { return new ItemStack(item.get()); }
        public Component title() { return output().getHoverName(); }
    }

    /** One cached UI offer, rebuilt after a price or language change rather than each rendered frame. */
    public record Offer(Entry entry, Component title, ItemStack output, int price) {}

    private record SearchableOffer(Offer offer, String name, String searchText) {
        private SearchableOffer(Offer offer) {
            this(offer, normalize(offer.title().getString()),
                normalize(offer.title().getString() + " " + offer.entry().id().getPath()));
        }
    }

    private static final Pattern ACCENTS = Pattern.compile("\\p{M}+");
    private static final Pattern SEPARATORS = Pattern.compile("[\\s_-]+");
    private static final List<Entry> ENTRIES = Stream.of(Stream.of(
        new Entry(id("hatsune_miku_figure"), JapaneseArcades.HATSUNE_MIKU_FIGURE_ITEM, Category.CHARACTER_FIGURES),
        new Entry(id("kasane_teto_figure"), JapaneseArcades.KASANE_TETO_FIGURE_ITEM, Category.CHARACTER_FIGURES),
        new Entry(id("hatsune_miku_cutout"), JapaneseArcades.HATSUNE_MIKU_CUTOUT_ITEM, Category.CUTOUTS),
        new Entry(id("kasane_teto_cutout"), JapaneseArcades.KASANE_TETO_CUTOUT_ITEM, Category.CUTOUTS),
        new Entry(id("kagamine_rin_cutout"), JapaneseArcades.KAGAMINE_RIN_CUTOUT_ITEM, Category.CUTOUTS),
        new Entry(id("kagamine_len_cutout"), JapaneseArcades.KAGAMINE_LEN_CUTOUT_ITEM, Category.CUTOUTS),
        new Entry(id("wacca_poster"), JapaneseArcades.WACCA_POSTER, Category.POSTERS),
        new Entry(id("sleeping_fox_plush"), JapaneseArcades.SLEEPING_FOX_PLUSH_ITEM, Category.SPECIAL),
        new Entry(id("mech_suit"), JapaneseArcades.MECH_SUIT_ITEM, Category.SPECIAL)),
        JapaneseArcades.ARCADE_POSTERS.stream().map(poster -> new Entry(id(poster.path()), poster.item(), Category.POSTERS)),
        JapaneseArcades.MOB_FIGURES.stream().map(figures -> new Entry(
            id(MobFigureBlock.path(figures.mob(), MobFigureBlock.Form.BOXED)), figures.boxedFigureItem(), Category.MOB_FIGURES)),
        JapaneseArcades.GLOW_STICKS.stream().map(stick -> new Entry(id(stick.path()), stick.item(), Category.GLOW_STICKS)))
        .flatMap(entries -> entries).toList();

    private ArcadePrizeCatalog() {}
    private static ResourceLocation id(String path) { return ResourceLocation.fromNamespaceAndPath(JapaneseArcades.MOD_ID, path); }
    public static List<Entry> entries() { return ENTRIES; }
    public static Optional<Entry> find(ResourceLocation id) { return ENTRIES.stream().filter(entry -> entry.id().equals(id)).findFirst(); }

    public static List<Offer> snapshot() {
        return ENTRIES.stream().map(entry -> {
            ItemStack output = entry.output();
            return new Offer(entry, output.getHoverName(), output, ArcadeEconomyConfig.prizePrice(entry.id()));
        }).toList();
    }

    public static boolean pricesChanged(List<Offer> offers) {
        return offers.size() != ENTRIES.size()
            || offers.stream().anyMatch(offer -> offer.price() != ArcadeEconomyConfig.prizePrice(offer.entry().id()));
    }

    /** Pure browsing over a snapshot. This never approves a purchase or changes the server catalogue. */
    public static List<Offer> browse(List<Offer> offers, Category category, String query, Sort sort,
            long points, boolean affordableOnly) {
        String normalized = normalize(query);
        String[] terms = normalized.isEmpty() ? new String[0] : normalized.split(" ");
        Comparator<SearchableOffer> byName = Comparator.comparing(SearchableOffer::name)
            .thenComparing(row -> row.offer().entry().id().toString());
        Comparator<SearchableOffer> order = switch (sort) {
            case NAME -> byName;
            // Disabled/unpriced rewards are never affordable and sort after valid prices in both directions.
            case PRICE_ASCENDING -> Comparator.<SearchableOffer>comparingInt(row -> row.offer().price() > 0 ? row.offer().price() : Integer.MAX_VALUE)
                .thenComparing(byName);
            case PRICE_DESCENDING -> Comparator.<SearchableOffer>comparingInt(row -> row.offer().price() > 0 ? -row.offer().price() : Integer.MAX_VALUE)
                .thenComparing(byName);
        };
        return offers.stream()
            .filter(offer -> category == Category.ALL || offer.entry().category() == category)
            .filter(offer -> !affordableOnly || offer.price() > 0 && offer.price() <= points)
            .map(SearchableOffer::new)
            .filter(row -> {
                for (String term : terms) {
                    if (!row.searchText().contains(term)) return false;
                }
                return true;
            })
            .sorted(order).map(SearchableOffer::offer).toList();
    }

    private static String normalize(String text) {
        String unaccented = ACCENTS.matcher(Normalizer.normalize(text, Normalizer.Form.NFKD)).replaceAll("");
        return SEPARATORS.matcher(unaccented.toLowerCase(Locale.ROOT)).replaceAll(" ").strip();
    }
}
