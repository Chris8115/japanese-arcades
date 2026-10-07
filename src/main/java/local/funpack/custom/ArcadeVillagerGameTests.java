package local.funpack.custom;

import static local.funpack.custom.GachaponTransactionGameTests.createPlayer;

import java.util.List;
import java.util.concurrent.atomic.AtomicReference;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.GlobalPos;
import net.minecraft.gametest.framework.GameTest;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.tags.PoiTypeTags;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.ai.memory.MemoryModuleType;
import net.minecraft.world.entity.ai.village.poi.PoiManager;
import net.minecraft.world.entity.npc.Villager;
import net.minecraft.world.entity.npc.VillagerProfession;
import net.minecraft.world.inventory.MerchantMenu;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.item.trading.MerchantOffer;
import net.minecraft.world.level.GameType;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.properties.DoubleBlockHalf;
import net.neoforged.neoforge.gametest.GameTestHolder;
import net.neoforged.neoforge.gametest.PrefixGameTestTemplate;

/** Exercises real POI indexing, vanilla villager brains, merchant slots, and saved trade data. */
@GameTestHolder(FunPackCustom.MOD_ID)
@PrefixGameTestTemplate(false)
public final class ArcadeVillagerGameTests {
    private static final BlockPos KIOSK = new BlockPos(3, 1, 3);

    private static void kiosk(GameTestHelper helper, Direction facing) {
        var state = FunPackCustom.ARCADE_KIOSK.get().defaultBlockState().setValue(ArcadeKioskBlock.FACING, facing);
        helper.getLevel().setBlock(helper.absolutePos(KIOSK), state, Block.UPDATE_CLIENTS | Block.UPDATE_KNOWN_SHAPE);
        helper.getLevel().setBlock(helper.absolutePos(KIOSK.above()),
            state.setValue(ArcadeKioskBlock.HALF, DoubleBlockHalf.UPPER), Block.UPDATE_ALL);
    }

    private static void assertPoi(GameTestHelper helper) {
        var manager = helper.getLevel().getPoiManager();
        var pos = helper.absolutePos(KIOSK);
        helper.assertTrue(manager.getType(pos).filter(poi -> poi.is(ArcadeVillagers.ARCADE_KIOSK.getKey())
            && poi.is(PoiTypeTags.ACQUIRABLE_JOB_SITE)).isPresent(), "Lower kiosk was not indexed as an acquirable job site");
        helper.assertTrue(manager.getType(pos.above()).isEmpty(), "Upper kiosk created a second job site");
        helper.assertTrue(manager.getCountInRange(poi -> poi.is(ArcadeVillagers.ARCADE_KIOSK.getKey()),
            pos, 1, PoiManager.Occupancy.ANY) == 1, "One kiosk must create exactly one workstation");
    }

    @GameTest(template = "nostalgia_test", batch = "arcade_operator", timeoutTicks = 1800)
    public static void kioskNaturallyEmploysOneOperatorAndRestocksItsTrades(GameTestHelper helper) {
        // Keep this AI test in its own batch so nearby test kiosks cannot attract either villager.
        helper.setDayTime(2500);
        for (int x = 0; x <= 6; x++) {
            for (int z = 0; z <= 6; z++) {
                helper.setBlock(new BlockPos(x, 0, z), Blocks.STONE);
                if (x == 0 || x == 6 || z == 0 || z == 6) {
                    helper.setBlock(new BlockPos(x, 1, z), Blocks.GLASS);
                    helper.setBlock(new BlockPos(x, 2, z), Blocks.GLASS);
                }
            }
        }
        var sequence = helper.startSequence();
        for (Direction facing : Direction.Plane.HORIZONTAL) {
            sequence.thenExecute(() -> kiosk(helper, facing)).thenIdle(3).thenExecute(() -> assertPoi(helper));
        }
        AtomicReference<List<Villager>> villagers = new AtomicReference<>();
        AtomicReference<Villager> worker = new AtomicReference<>();
        AtomicReference<MerchantOffer> depleted = new AtomicReference<>();
        sequence.thenExecute(() -> {
            villagers.set(List.of(helper.spawn(EntityType.VILLAGER, 2, 1, 3), helper.spawn(EntityType.VILLAGER, 4, 1, 3)));
            for (Villager villager : villagers.get()) { villager.setAge(0); }
        }).thenWaitUntil(() -> {
            var employed = villagers.get().stream()
                .filter(villager -> villager.getVillagerData().getProfession() == ArcadeVillagers.ARCADE_OPERATOR.get()).toList();
            helper.assertTrue(employed.size() == 1, "A nearby unemployed adult did not naturally become an arcade operator");
            worker.set(employed.getFirst());
        }).thenIdle(100).thenExecute(() -> {
            helper.assertTrue(villagers.get().stream().filter(villager ->
                villager.getVillagerData().getProfession() == ArcadeVillagers.ARCADE_OPERATOR.get()).count() == 1,
                "Two villagers claimed one kiosk");
            helper.assertTrue(worker.get().getBrain().getMemory(MemoryModuleType.JOB_SITE)
                .filter(GlobalPos.of(helper.getLevel().dimension(), helper.absolutePos(KIOSK))::equals).isPresent(),
                "Operator did not remember the lower kiosk as its actual job site");
            helper.assertTrue(helper.getLevel().getPoiManager().getFreeTickets(helper.absolutePos(KIOSK)) == 0,
                "Claimed kiosk still has a free worker ticket");
            helper.assertTrue(worker.get().getOffers().size() == 2, "Naturally employed operator has no novice trades");
            var offer = worker.get().getOffers().getFirst();
            offer.setToOutOfStock();
            depleted.set(offer);
        }).thenWaitUntil(() -> {
            helper.assertTrue(!depleted.get().isOutOfStock()
                && worker.get().getBrain().hasMemoryValue(MemoryModuleType.LAST_WORKED_AT_POI),
                "Operator did not use its kiosk to restock during work hours");
        }).thenExecute(() -> helper.getLevel().destroyBlock(helper.absolutePos(KIOSK.above()), false))
            .thenIdle(3).thenExecute(() -> {
                helper.assertTrue(helper.getLevel().getPoiManager().getType(helper.absolutePos(KIOSK)).isEmpty(),
                    "Breaking the upper half left an employable kiosk POI behind");
            }).thenSucceed();
    }

    @GameTest(template = "nostalgia_test")
    public static void operatorTradesUseRealMerchantPaymentStockAndSaveData(GameTestHelper helper) {
        ServerPlayer player = createPlayer(helper, "ArcadeTrader", GameType.SURVIVAL);
        for (int level = 1; level <= 5; level++) {
            Villager villager = new Villager(EntityType.VILLAGER, helper.getLevel());
            villager.setNoAi(true);
            villager.setVillagerData(villager.getVillagerData().setProfession(ArcadeVillagers.ARCADE_OPERATOR.get()).setLevel(level));
            villager.setTradingPlayer(player);
            helper.assertTrue(villager.getOffers().size() == 2, "Each career level must expose two usable offers: " + level);
            MerchantMenu menu = new MerchantMenu(80 + level, player.getInventory(), villager);
            for (int index = 0; index < villager.getOffers().size(); index++) {
                MerchantOffer offer = villager.getOffers().get(index);
                menu.setSelectionHint(index);
                menu.getSlot(0).set(ItemStack.EMPTY);
                menu.getSlot(1).set(ItemStack.EMPTY);
                helper.assertTrue(!menu.getSlot(2).hasItem(), "Merchant offered goods without payment");
                ItemStack price = offer.getCostA().copy();
                if (price.getCount() > 1) {
                    menu.getSlot(0).set(price.copyWithCount(price.getCount() - 1));
                    helper.assertTrue(!menu.getSlot(2).hasItem(), "Merchant accepted an incomplete payment");
                }
                menu.getSlot(0).set(price);
                helper.assertTrue(ItemStack.matches(menu.getSlot(2).getItem(), offer.getResult()), "Payment did not produce the advertised result");
                int xp = villager.getVillagerXp();
                ItemStack bought = menu.getSlot(2).remove(offer.getResult().getCount());
                menu.getSlot(2).onTake(player, bought);
                helper.assertTrue(menu.getSlot(0).getItem().isEmpty() && offer.getUses() == 1
                    && villager.getVillagerXp() > xp, "Completed merchant trade did not consume payment, stock, and award profession XP");
                if (bought.is(FunPackCustom.ARCADE_PASS.get())) {
                    var pass = bought.getOrDefault(FunPackCustom.PASS_DATA.get(), ArcadePassData.empty());
                    helper.assertTrue(pass.credits() == 0 && pass.prizePoints() == 0, "Operator minted funded passes");
                }
                if (bought.is(FunPackCustom.CUSTOM_DISPLAY_BOX_ITEM.get())) {
                    helper.assertTrue(CustomDisplayBoxData.from(bought).containedItem().isEmpty(), "Operator's empty packaging contained a free item");
                }
                offer.setToOutOfStock();
                menu.getSlot(0).set(offer.getCostA().copy());
                helper.assertTrue(!menu.getSlot(2).hasItem(), "Depleted offer sold beyond its stock limit");
                menu.getSlot(0).set(ItemStack.EMPTY);
            }
            villager.setTradingPlayer(null);
            CompoundTag saved = new CompoundTag();
            villager.saveWithoutId(saved);
            Villager restored = new Villager(EntityType.VILLAGER, helper.getLevel());
            restored.load(saved);
            helper.assertTrue(restored.getVillagerData().getProfession() == ArcadeVillagers.ARCADE_OPERATOR.get()
                && restored.getVillagerData().getLevel() == level && restored.getVillagerXp() == villager.getVillagerXp(),
                "Saved operator lost its profession, rank, or XP");
            helper.assertTrue(restored.getOffers().size() == 2 && restored.getOffers().stream().allMatch(MerchantOffer::isOutOfStock),
                "Reloading operator replenished its used stock or changed its offers");
            for (int index = 0; index < restored.getOffers().size(); index++) {
                helper.assertTrue(ItemStack.matches(restored.getOffers().get(index).getResult(), villager.getOffers().get(index).getResult()),
                    "Saved operator rerolled a trade result");
            }
        }
        helper.succeed();
    }
}
