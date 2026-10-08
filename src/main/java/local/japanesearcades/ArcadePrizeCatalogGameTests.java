package local.japanesearcades;

import java.util.List;
import net.minecraft.gametest.framework.GameTest;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.ResourceLocation;
import net.neoforged.neoforge.common.ModConfigSpec;
import net.neoforged.neoforge.gametest.GameTestHolder;
import net.neoforged.neoforge.gametest.PrefixGameTestTemplate;

/** Runs the same search, sort and affordability pipeline used by the reward screen on a dedicated server. */
@GameTestHolder(JapaneseArcades.MOD_ID)
@PrefixGameTestTemplate(false)
public final class ArcadePrizeCatalogGameTests {
    private static ResourceLocation id(String path) {
        return ResourceLocation.fromNamespaceAndPath(JapaneseArcades.MOD_ID, path);
    }

    private static List<ResourceLocation> ids(List<ArcadePrizeCatalog.Offer> offers) {
        return offers.stream().map(offer -> offer.entry().id()).toList();
    }

    private static ArcadePrizeCatalog.Offer namedOffer(String path, String title, int price) {
        var entry = ArcadePrizeCatalog.find(id(path)).orElseThrow();
        return new ArcadePrizeCatalog.Offer(entry, Component.literal(title), entry.output(), price);
    }

    @GameTest(template = "nostalgia_test")
    public static void rewardSearchCombinesCategoryNamesIdsAndAllTerms(GameTestHelper helper) {
        var offers = ArcadePrizeCatalog.snapshot();
        var sort = ArcadePrizeCatalog.Sort.NAME;
        var mobs = ArcadePrizeCatalog.browse(offers, ArcadePrizeCatalog.Category.MOB_FIGURES,
            "  SKELETON   WITHÉR  ", sort, -1, false);
        helper.assertTrue(ids(mobs).equals(List.of(id("boxed_wither_skeleton_figure"))),
            "Multi-term, case-insensitive and accent-insensitive mob search did not find the boxed reward");
        helper.assertTrue(ArcadePrizeCatalog.browse(offers, ArcadePrizeCatalog.Category.POSTERS,
            "wither skeleton", sort, Long.MAX_VALUE, false).isEmpty(),
            "Category filtering leaked a mob figure into the posters list");
        helper.assertTrue(ids(ArcadePrizeCatalog.browse(offers, ArcadePrizeCatalog.Category.CHARACTER_FIGURES,
            "miku", sort, -1, false)).equals(List.of(id("hatsune_miku_figure")))
            && ids(ArcadePrizeCatalog.browse(offers, ArcadePrizeCatalog.Category.CUTOUTS,
            "miku", sort, -1, false)).equals(List.of(id("hatsune_miku_cutout"))),
            "The figure and cutout categories did not narrow the same character search independently");
        var named = List.of(namedOffer("wacca_poster", "Limited Lunar Collectible", 750));
        helper.assertTrue(ArcadePrizeCatalog.browse(named, ArcadePrizeCatalog.Category.ALL,
            "LUNAR", sort, -1, false).size() == 1,
            "Search must match the displayed localized name as well as the stable item ID");
        helper.assertTrue(ArcadePrizeCatalog.browse(offers, ArcadePrizeCatalog.Category.ALL,
            "no_such_reward_xyz", sort, -1, false).isEmpty(), "An unmatched search must produce an empty result");
        helper.assertTrue(ArcadePrizeCatalog.browse(offers, ArcadePrizeCatalog.Category.ALL,
            "   ", sort, -1, false).size() == offers.size(), "Clearing search must restore every reward");
        helper.succeed();
    }

    @GameTest(template = "nostalgia_test")
    public static void rewardSortIsStableAndDoesNotMutateItsSnapshot(GameTestHelper helper) {
        var poster = namedOffer("wacca_poster", "Zebra", 750);
        var teto = namedOffer("kasane_teto_figure", "Éclair", 2500);
        var miku = namedOffer("hatsune_miku_figure", "Eclair", 2500);
        var disabled = namedOffer("mech_suit", "A disabled reward", -1);
        var offers = List.of(poster, teto, miku, disabled);
        var category = ArcadePrizeCatalog.Category.ALL;
        var alphabetical = ArcadePrizeCatalog.browse(offers, category, "", ArcadePrizeCatalog.Sort.NAME, 0, false);
        helper.assertTrue(ids(alphabetical).equals(List.of(disabled.entry().id(), miku.entry().id(), teto.entry().id(), poster.entry().id())),
            "Name sorting must ignore accents/case and resolve equal names by stable prize ID");
        var cheapest = ArcadePrizeCatalog.browse(offers, category, "", ArcadePrizeCatalog.Sort.PRICE_ASCENDING, 0, false);
        var expensive = ArcadePrizeCatalog.browse(offers, category, "", ArcadePrizeCatalog.Sort.PRICE_DESCENDING, 0, false);
        helper.assertTrue(ids(cheapest).equals(List.of(poster.entry().id(), miku.entry().id(), teto.entry().id(), disabled.entry().id()))
            && ids(expensive).equals(List.of(miku.entry().id(), teto.entry().id(), poster.entry().id(), disabled.entry().id())),
            "Price sorting must order valid prices in both directions, retain stable ties and put unavailable prices last");
        helper.assertTrue(ids(offers).equals(List.of(poster.entry().id(), teto.entry().id(), miku.entry().id(), disabled.entry().id())),
            "Browsing mutated the original snapshot and can invalidate the selected reward");
        helper.assertTrue(ArcadePrizeCatalog.browse(offers, category, "", ArcadePrizeCatalog.Sort.NAME, -1, true).isEmpty(),
            "A missing pass must not expose affordable rewards or treat an invalid negative price as free");
        helper.assertTrue(ids(ArcadePrizeCatalog.browse(offers, category, "", ArcadePrizeCatalog.Sort.NAME, 750, true))
            .equals(List.of(poster.entry().id())), "Affordable-only must include the exact balance boundary and reject larger prices");
        helper.succeed();
    }

    @GameTest(template = "nostalgia_test")
    public static void rewardPriceRefreshUpdatesAffordabilityWithoutChangingCachedRows(GameTestHelper helper) {
        ModConfigSpec.IntValue price = ArcadeEconomyConfig.SPEC.getValues().get("prizes.hatsune_miku_figure");
        int originalPrice = price.get();
        try {
            price.set(120);
            var before = ArcadePrizeCatalog.snapshot();
            helper.assertFalse(ArcadePrizeCatalog.pricesChanged(before), "A fresh offer snapshot was marked stale");
            helper.assertTrue(ArcadePrizeCatalog.browse(before, ArcadePrizeCatalog.Category.CHARACTER_FIGURES,
                "miku", ArcadePrizeCatalog.Sort.NAME, 120, true).size() == 1, "An exactly affordable reward was omitted");
            price.set(121);
            helper.assertTrue(ArcadePrizeCatalog.pricesChanged(before), "Live synchronized price changes must invalidate the UI snapshot");
            var after = ArcadePrizeCatalog.snapshot();
            helper.assertTrue(ArcadePrizeCatalog.browse(after, ArcadePrizeCatalog.Category.CHARACTER_FIGURES,
                "miku", ArcadePrizeCatalog.Sort.NAME, 120, true).isEmpty(),
                "Refreshing prices failed to remove a newly unaffordable reward");
            helper.assertTrue(ArcadePrizeCatalog.browse(before, ArcadePrizeCatalog.Category.CHARACTER_FIGURES,
                "miku", ArcadePrizeCatalog.Sort.NAME, 120, true).size() == 1,
                "A price change mutated old offer data behind an existing UI selection");
            helper.assertTrue(ArcadePrizeCatalog.browse(after, ArcadePrizeCatalog.Category.CHARACTER_FIGURES,
                "miku", ArcadePrizeCatalog.Sort.NAME, 121, true).size() == 1,
                "Changing the selected pass balance must allow the reward to reappear");
        } finally {
            price.set(originalPrice);
        }
        helper.succeed();
    }
}
