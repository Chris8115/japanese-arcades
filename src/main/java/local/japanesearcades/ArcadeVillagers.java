package local.japanesearcades;

import com.google.common.collect.ImmutableSet;
import java.util.stream.Collectors;
import net.minecraft.core.registries.Registries;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.world.entity.ai.village.poi.PoiType;
import net.minecraft.world.entity.npc.VillagerProfession;
import net.minecraft.world.entity.npc.VillagerTrades;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.item.trading.ItemCost;
import net.minecraft.world.item.trading.MerchantOffer;
import net.minecraft.world.level.block.state.properties.DoubleBlockHalf;
import net.neoforged.bus.api.IEventBus;
import net.neoforged.neoforge.common.NeoForge;
import net.neoforged.neoforge.event.village.VillagerTradesEvent;
import net.neoforged.neoforge.registries.DeferredHolder;
import net.neoforged.neoforge.registries.DeferredRegister;

/** Ordinary village employment and emerald trades; pass balances remain owned by the kiosk. */
public final class ArcadeVillagers {
    private static final DeferredRegister<PoiType> POIS =
        DeferredRegister.create(Registries.POINT_OF_INTEREST_TYPE, JapaneseArcades.MOD_ID);
    private static final DeferredRegister<VillagerProfession> PROFESSIONS =
        DeferredRegister.create(Registries.VILLAGER_PROFESSION, JapaneseArcades.MOD_ID);

    public static final DeferredHolder<PoiType, PoiType> ARCADE_KIOSK = POIS.register("arcade_kiosk",
        () -> new PoiType(JapaneseArcades.ARCADE_KIOSK.get().getStateDefinition().getPossibleStates().stream()
            .filter(state -> state.getValue(ArcadeKioskBlock.HALF) == DoubleBlockHalf.LOWER)
            .collect(Collectors.toSet()), 1, 1));
    public static final DeferredHolder<VillagerProfession, VillagerProfession> ARCADE_OPERATOR =
        PROFESSIONS.register("arcade_operator", () -> new VillagerProfession("japanesearcades.arcade_operator",
            poi -> poi.is(ARCADE_KIOSK.getKey()), poi -> poi.is(ARCADE_KIOSK.getKey()),
            ImmutableSet.of(), ImmutableSet.of(), SoundEvents.VILLAGER_WORK_CARTOGRAPHER));

    private ArcadeVillagers() {}

    public static void register(IEventBus modEventBus) {
        POIS.register(modEventBus);
        PROFESSIONS.register(modEventBus);
        NeoForge.EVENT_BUS.addListener(ArcadeVillagers::addTrades);
    }

    private static void addTrades(VillagerTradesEvent event) {
        if (event.getType() != ARCADE_OPERATOR.get()) { return; }
        var trades = event.getTrades();
        trades.get(1).add(buy(Items.PAPER, 24, 16, 2));
        trades.get(1).add(sell(JapaneseArcades.ARCADE_PASS.get(), 1, 2, 12, 1));
        trades.get(2).add(buy(Items.GLASS_PANE, 16, 16, 10));
        trades.get(2).add(sell(JapaneseArcades.CUSTOM_DISPLAY_BOX_ITEM.get(), 4, 1, 12, 5));
        trades.get(3).add(buy(Items.COPPER_INGOT, 12, 12, 20));
        trades.get(3).add(sell(JapaneseArcades.WACCA_POSTER.get(), 1, 8, 4, 10));
        trades.get(4).add(sell(JapaneseArcades.HATSUNE_MIKU_CUTOUT_ITEM.get(), 1, 16, 2, 15));
        trades.get(4).add(sell(JapaneseArcades.KASANE_TETO_CUTOUT_ITEM.get(), 1, 16, 2, 15));
        trades.get(5).add(sell(JapaneseArcades.HATSUNE_MIKU_FIGURE_ITEM.get(), 1, 24, 2, 30));
        trades.get(5).add(sell(JapaneseArcades.KASANE_TETO_FIGURE_ITEM.get(), 1, 24, 2, 30));
    }

    private static VillagerTrades.ItemListing buy(Item item, int count, int stock, int xp) {
        return (villager, random) -> new MerchantOffer(new ItemCost(item, count), new ItemStack(Items.EMERALD), stock, xp, .05F);
    }

    private static VillagerTrades.ItemListing sell(Item item, int count, int emeralds, int stock, int xp) {
        return (villager, random) -> new MerchantOffer(new ItemCost(Items.EMERALD, emeralds), new ItemStack(item, count), stock, xp, .05F);
    }
}
