package local.funpack.custom;

import static local.funpack.custom.GachaponTransactionGameTests.aimAt;
import static local.funpack.custom.GachaponTransactionGameTests.createPlayer;

import io.netty.buffer.Unpooled;
import java.util.List;
import java.util.UUID;
import java.util.function.Consumer;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.component.DataComponents;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.gametest.framework.GameTest;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.nbt.NbtOps;
import net.minecraft.network.RegistryFriendlyByteBuf;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.util.RandomSource;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.item.ItemEntity;
import net.minecraft.world.item.BlockItem;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.item.context.BlockPlaceContext;
import net.minecraft.world.level.GameType;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.phys.BlockHitResult;
import net.minecraft.world.phys.Vec3;
import net.neoforged.neoforge.common.NeoForge;
import net.neoforged.neoforge.common.ModConfigSpec;
import net.neoforged.neoforge.event.entity.EntityJoinLevelEvent;
import net.neoforged.neoforge.gametest.GameTestHolder;
import net.neoforged.neoforge.gametest.PrefixGameTestTemplate;

/** Real menu dispatch, saved bearer cards, and atomic inventory/ground deliveries. */
@GameTestHolder(FunPackCustom.MOD_ID)
@PrefixGameTestTemplate(false)
public final class ArcadeEconomyTransactionGameTests {
    private static final BlockPos BASE = new BlockPos(3, 1, 3);
    private static ResourceLocation id(String path) { return ResourceLocation.fromNamespaceAndPath(FunPackCustom.MOD_ID, path); }
    private static ArcadeKioskMenu setup(GameTestHelper helper, ServerPlayer player) {
        helper.setBlock(BASE.below(), Blocks.STONE);
        player.setYRot(180);
        player.setItemInHand(InteractionHand.MAIN_HAND, new ItemStack(FunPackCustom.ARCADE_KIOSK_ITEM.get()));
        BlockPos floor = helper.absolutePos(BASE.below());
        var hit = new BlockHitResult(Vec3.atCenterOf(floor).add(0, .5, 0), Direction.UP, floor, false);
        helper.assertTrue(((BlockItem)player.getMainHandItem().getItem()).place(
            new BlockPlaceContext(player, InteractionHand.MAIN_HAND, player.getMainHandItem(), hit)).consumesAction(), "Kiosk placement failed");
        player.getInventory().clearContent();
        return open(helper, player);
    }
    private static ArcadeKioskMenu open(GameTestHelper helper, ServerPlayer player) {
        aimAt(player, helper.absolutePos(BASE));
        helper.useBlock(BASE, player);
        helper.assertTrue(player.containerMenu instanceof ArcadeKioskMenu, "Kiosk did not open");
        return (ArcadeKioskMenu)player.containerMenu;
    }
    private static ItemStack pass(long credits, long points) {
        ItemStack result = ArcadePassItem.createPass();
        ArcadePassItem.setData(result, new ArcadePassData(1, ArcadePassItem.data(result).id(), id("custom_festival_design"), credits, points, 7));
        result.set(DataComponents.CUSTOM_NAME, Component.literal("Festival pass"));
        return result;
    }
    private static ArcadePassData data(ServerPlayer player, int slot) { return ArcadePassItem.data(player.getInventory().getItem(slot)); }
    private static ArcadeKioskNetwork.ExchangePayload exchange(ArcadeKioskMenu menu, ServerPlayer player, int slot, ResourceLocation material) {
        ArcadePassData pass = data(player, slot);
        return new ArcadeKioskNetwork.ExchangePayload(menu.containerId, slot, pass.id(), pass.revision(), material);
    }
    private static ArcadeKioskNetwork.TransferPayload transfer(ArcadeKioskMenu menu, ServerPlayer player, int source, int target) {
        ArcadePassData from = data(player, source), to = data(player, target);
        return new ArcadeKioskNetwork.TransferPayload(menu.containerId, source, from.id(), from.revision(), target, to.id(), to.revision());
    }
    private static ArcadeKioskNetwork.PrizePayload prize(ArcadeKioskMenu menu, ServerPlayer player, ResourceLocation prize) {
        ArcadePassData pass = data(player, 0);
        return new ArcadeKioskNetwork.PrizePayload(menu.containerId, prize, 0, pass.id(), pass.revision());
    }
    private static void full(ServerPlayer player) {
        for (int slot = 1; slot < 36; slot++) { player.getInventory().setItem(slot, new ItemStack(Items.COBBLESTONE, 64)); }
    }
    private static void noDrops(GameTestHelper helper, int expected) {
        helper.assertTrue(helper.getEntities(EntityType.ITEM, BASE, 5).size() == expected, "Unexpected ground delivery count");
    }

    @GameTest(template = "nostalgia_test")
    public static void arcadePassIssueIsBlankAndDetectsInventoryOffhandAndCursor(GameTestHelper helper) {
        ServerPlayer player = createPlayer(helper, "PassIssue", GameType.SURVIVAL);
        ArcadeKioskMenu menu = setup(helper, player);
        var request = new ArcadeKioskNetwork.IssuePassPayload(menu.containerId);
        ArcadeKioskNetwork.handleIssuePass(player, request);
        ItemStack issued = player.getInventory().getItem(0);
        ArcadePassData first = data(player, 0);
        helper.assertTrue(first != null && first.credits() == 0 && first.prizePoints() == 0
            && !first.id().equals(ArcadePassData.UNASSIGNED) && issued.getMaxStackSize() == 1, "Issued pass must be a unique nonstackable empty wallet");
        for (int location = 0; location < 3; location++) {
            player.getInventory().clearContent(); menu.setCarried(ItemStack.EMPTY);
            if (location == 0) { player.getInventory().setItem(5, issued.copy()); }
            if (location == 1) { player.getInventory().setItem(40, issued.copy()); }
            if (location == 2) { menu.setCarried(issued.copy()); }
            int revision = menu.getStatusRevision();
            ArcadeKioskNetwork.handleIssuePass(player, request);
            helper.assertTrue(menu.getStatus() == ArcadeKioskMenu.STATUS_PASS_EXISTS && menu.getStatusRevision() != revision,
                "A pass already held in inventory, offhand or cursor allowed repeated issuance");
            helper.assertTrue(player.getInventory().getItem(0).isEmpty(), "Repeated issuance generated another wallet");
        }
        menu.setCarried(ItemStack.EMPTY);
        player.getInventory().clearContent();
        player.getInventory().setItem(0, new ItemStack(Items.COBBLESTONE, 64)); full(player);
        Consumer<EntityJoinLevelEvent> veto = event -> {
            if (event.getEntity() instanceof ItemEntity item && item.distanceToSqr(player) < 4
                    && item.getItem().is(FunPackCustom.ARCADE_PASS.get())) { event.setCanceled(true); }
        };
        NeoForge.EVENT_BUS.addListener(veto);
        try {
            ArcadeKioskNetwork.handleIssuePass(player, request);
            helper.assertTrue(menu.getStatus() == ArcadeKioskMenu.STATUS_UNAVAILABLE, "Canceled pass delivery reported success");
            noDrops(helper, 0);
        } finally { NeoForge.EVENT_BUS.unregister(veto); }
        helper.succeed();
    }

    @GameTest(template = "nostalgia_test")
    public static void arcadePassPersistsComponentsAndRoundTripsItsVersionedCodec(GameTestHelper helper) {
        ItemStack original = pass(987654, 123456);
        ItemStack reloaded = ItemStack.parse(helper.getLevel().registryAccess(), original.save(helper.getLevel().registryAccess())).orElseThrow();
        helper.assertTrue(ItemStack.matches(original, reloaded), "Saving a pass lost its name, design, identity or balances");
        ArcadePassData value = ArcadePassItem.data(original);
        RegistryFriendlyByteBuf buffer = new RegistryFriendlyByteBuf(Unpooled.buffer(), helper.getLevel().registryAccess());
        try {
            ArcadePassData.STREAM_CODEC.encode(buffer, value);
            helper.assertTrue(ArcadePassData.STREAM_CODEC.decode(buffer).equals(value), "Network pass codec changed wallet data");
        } finally { buffer.release(); }
        ArcadePassData defaults = ArcadePassData.CODEC.parse(NbtOps.INSTANCE, new CompoundTag()).getOrThrow();
        helper.assertTrue(defaults.equals(ArcadePassData.empty()), "Missing future-compatible optional fields did not default to a blank pass");
        CompoundTag malformed = new CompoundTag(); malformed.putLong("credits", -1);
        helper.assertTrue(ArcadePassData.CODEC.parse(NbtOps.INSTANCE, malformed).error().isPresent(), "Negative pass balance was accepted from saved data");
        ItemStack raw = new ItemStack(FunPackCustom.ARCADE_PASS.get());
        helper.assertTrue(ArcadePassItem.data(raw) != null && ArcadePassItem.data(raw).credits() == 0, "A raw creative pass cannot start empty");
        helper.succeed();
    }

    @GameTest(template = "nostalgia_test")
    public static void arcadeMaterialExchangeUsesEveryConfiguredRateOnceAndNeverArmor(GameTestHelper helper) {
        ServerPlayer player = createPlayer(helper, "PassRates", GameType.SURVIVAL);
        ArcadeKioskMenu menu = setup(helper, player);
        player.getInventory().setItem(0, pass(0, 55));
        long expected = 0;
        for (var rate : ArcadeEconomyConfig.exchangeRates()) {
            player.getInventory().setItem(40, new ItemStack(rate.material(), 2));
            var request = exchange(menu, player, 0, BuiltInRegistries.ITEM.getKey(rate.material()));
            ArcadeKioskNetwork.handleExchange(player, request);
            expected += rate.credits();
            helper.assertTrue(data(player, 0).credits() == expected && data(player, 0).prizePoints() == 55
                && player.getInventory().getItem(40).getCount() == 1, "Exchange charged more than one material or ignored the server rate");
            ArcadeKioskNetwork.handleExchange(player, request);
            helper.assertTrue(data(player, 0).credits() == expected && player.getInventory().getItem(40).getCount() == 1,
                "Repeated exchange packet credited or charged twice");
        }
        player.getInventory().setItem(40, ItemStack.EMPTY);
        player.getInventory().setItem(36, new ItemStack(Items.IRON_INGOT, 64));
        ArcadeKioskNetwork.handleExchange(player, exchange(menu, player, 0, BuiltInRegistries.ITEM.getKey(Items.IRON_INGOT)));
        helper.assertTrue(data(player, 0).credits() == expected && player.getInventory().getItem(36).getCount() == 64,
            "Exchange consumed an armor slot or generated credits without material");
        helper.succeed();
    }

    @GameTest(template = "nostalgia_test")
    public static void arcadePassTransferConservesBothBalancesAndPreservesBothCards(GameTestHelper helper) {
        ServerPlayer player = createPlayer(helper, "PassTransfer", GameType.SURVIVAL);
        ArcadeKioskMenu menu = setup(helper, player);
        player.getInventory().setItem(0, pass(11, 17)); player.getInventory().setItem(1, pass(31, 47));
        ItemStack beforeA = player.getInventory().getItem(0).copy(), beforeB = player.getInventory().getItem(1).copy();
        var request = transfer(menu, player, 1, 0);
        ArcadeKioskNetwork.handleTransfer(player, request);
        helper.assertTrue(data(player, 0).credits() == 42 && data(player, 0).prizePoints() == 64
            && data(player, 1).credits() == 0 && data(player, 1).prizePoints() == 0, "B to A transfer lost or duplicated either balance");
        ArcadePassItem.setData(beforeA, ArcadePassItem.data(beforeA).withBalances(42, 64));
        ArcadePassItem.setData(beforeB, ArcadePassItem.data(beforeB).withBalances(0, 0));
        helper.assertTrue(ItemStack.matches(beforeA, player.getInventory().getItem(0)) && ItemStack.matches(beforeB, player.getInventory().getItem(1)),
            "Transfer changed a skin, name, identity or destroyed the emptied card");
        ArcadeKioskNetwork.handleTransfer(player, request);
        helper.assertTrue(ItemStack.matches(beforeA, player.getInventory().getItem(0)) && ItemStack.matches(beforeB, player.getInventory().getItem(1)),
            "Stale transfer replay changed either pass");
        ArcadeKioskNetwork.handleTransfer(player, transfer(menu, player, 0, 0));
        helper.assertTrue(ItemStack.matches(beforeA, player.getInventory().getItem(0)), "Transfer to the same slot destroyed its balance");
        player.getInventory().setItem(1, beforeA.copy());
        ArcadeKioskNetwork.handleTransfer(player, transfer(menu, player, 1, 0));
        helper.assertTrue(ItemStack.matches(beforeA, player.getInventory().getItem(0)) && ItemStack.matches(beforeA, player.getInventory().getItem(1)),
            "Two copies of one assigned pass identity were allowed to transfer");
        player.getInventory().setItem(0, pass(ArcadePassData.MAX_BALANCE, ArcadePassData.MAX_BALANCE));
        player.getInventory().setItem(1, pass(1, 1));
        ArcadeKioskNetwork.handleTransfer(player, transfer(menu, player, 1, 0));
        helper.assertTrue(menu.getStatus() == ArcadeKioskMenu.STATUS_BALANCE_LIMIT && data(player, 1).credits() == 1 && data(player, 1).prizePoints() == 1,
            "Overflowing transfer partially drained its source");
        player.getInventory().setItem(0, new ItemStack(FunPackCustom.ARCADE_PASS.get()));
        ItemStack rawSource = new ItemStack(FunPackCustom.ARCADE_PASS.get());
        ArcadePassItem.setData(rawSource, new ArcadePassData(1, ArcadePassData.UNASSIGNED, id("custom_festival_design"), 7, 12, 0));
        player.getInventory().setItem(1, rawSource);
        ArcadeKioskNetwork.handleTransfer(player, transfer(menu, player, 1, 0));
        helper.assertTrue(data(player, 0).credits() == 7 && data(player, 0).prizePoints() == 12 && data(player, 1).credits() == 0
            && !data(player, 0).id().equals(ArcadePassData.UNASSIGNED) && !data(player, 1).id().equals(ArcadePassData.UNASSIGNED)
            && !data(player, 0).id().equals(data(player, 1).id()), "Valid unassigned cards failed to initialize independent identities during transfer");
        helper.succeed();
    }

    @GameTest(template = "nostalgia_test")
    public static void arcadePassRejectsStaleSlotsIdentitiesSessionsAndBalanceOverflow(GameTestHelper helper) {
        ServerPlayer player = createPlayer(helper, "PassStale", GameType.SURVIVAL);
        ArcadeKioskMenu menu = setup(helper, player);
        player.getInventory().setItem(0, pass(4, 9)); player.getInventory().setItem(1, new ItemStack(Items.IRON_INGOT, 20));
        var original = exchange(menu, player, 0, BuiltInRegistries.ITEM.getKey(Items.IRON_INGOT));
        player.getInventory().setItem(2, player.getInventory().getItem(0)); player.getInventory().setItem(0, ItemStack.EMPTY);
        ArcadeKioskNetwork.handleExchange(player, original);
        player.getInventory().setItem(0, pass(4, 9));
        ArcadeKioskNetwork.handleExchange(player, original);
        helper.assertTrue(data(player, 0).credits() == 4 && data(player, 2).credits() == 4 && player.getInventory().getItem(1).getCount() == 20,
            "A stale slot or changed card identity spent materials");
        var valid = exchange(menu, player, 0, original.materialId());
        ServerPlayer visitor = createPlayer(helper, "PassVisitor", GameType.SURVIVAL);
        visitor.getInventory().setItem(0, pass(91, 13)); visitor.getInventory().setItem(1, new ItemStack(Items.IRON_INGOT, 3));
        var visitorMenu = visitor.containerMenu;
        visitor.containerMenu = menu;
        try {
            ArcadeKioskNetwork.handleExchange(visitor, exchange(menu, visitor, 0, original.materialId()));
            helper.assertTrue(data(visitor, 0).credits() == 91 && visitor.getInventory().getItem(1).getCount() == 3
                && data(player, 0).credits() == 4 && player.getInventory().getItem(1).getCount() == 20,
                "A different player reused another viewer's kiosk session");
        } finally { visitor.containerMenu = visitorMenu; }
        ArcadeKioskNetwork.handleExchange(player, new ArcadeKioskNetwork.ExchangePayload(menu.containerId+1, 0, valid.passId(), valid.revision(), valid.materialId()));
        ArcadeKioskNetwork.handleExchange(player, new ArcadeKioskNetwork.ExchangePayload(menu.containerId, 40, valid.passId(), valid.revision(), valid.materialId()));
        ArcadeKioskNetwork.handleExchange(player, new ArcadeKioskNetwork.ExchangePayload(menu.containerId, 0, valid.passId(), valid.revision(), id("forged_material")));
        player.closeContainer(); ArcadeKioskNetwork.handleExchange(player, valid); menu.exchange(player, 0, valid.passId(), valid.revision(), valid.materialId());
        menu = open(helper, player);
        valid = exchange(menu, player, 0, original.materialId());
        player.setPos(player.getX()+20, player.getY(), player.getZ()); ArcadeKioskNetwork.handleExchange(player, valid);
        aimAt(player, helper.absolutePos(BASE));
        helper.assertTrue(data(player, 0).credits() == 4 && player.getInventory().getItem(1).getCount() == 20, "An invalid or stale menu request was accepted");
        player.getInventory().setItem(0, pass(ArcadePassData.MAX_BALANCE, 9));
        ArcadeKioskNetwork.handleExchange(player, exchange(menu, player, 0, original.materialId()));
        helper.assertTrue(menu.getStatus() == ArcadeKioskMenu.STATUS_BALANCE_LIMIT && player.getInventory().getItem(1).getCount() == 20, "Balance overflow consumed material");
        player.getInventory().setItem(0, pass(0, 0));
        helper.getLevel().destroyBlock(helper.absolutePos(BASE.above()), false);
        ArcadeKioskNetwork.handleExchange(player, exchange(menu, player, 0, original.materialId()));
        helper.assertTrue(data(player, 0).credits() == 0 && player.getInventory().getItem(1).getCount() == 20, "Destroyed kiosk changed a wallet");
        helper.succeed();
    }

    @GameTest(template = "nostalgia_test")
    public static void arcadeEveryConfiguredPrizeChargesOnlyItsPointPrice(GameTestHelper helper) {
        ServerPlayer player = createPlayer(helper, "PassPrizes", GameType.SURVIVAL);
        ArcadeKioskMenu menu = setup(helper, player);
        for (var entry : ArcadePrizeCatalog.entries()) {
            player.getInventory().clearContent();
            int price = ArcadeEconomyConfig.prizePrice(entry.id());
            player.getInventory().setItem(0, pass(1234, price-1));
            ArcadeKioskNetwork.handlePrize(player, prize(menu, player, entry.id()));
            helper.assertTrue(menu.getStatus() == ArcadeKioskMenu.STATUS_MISSING_POINTS && data(player, 0).prizePoints() == price-1,
                "Unaffordable prize charged points");
            player.getInventory().setItem(0, pass(1234, price));
            var request = prize(menu, player, entry.id());
            ArcadeKioskNetwork.handlePrize(player, request);
            helper.assertTrue(data(player, 0).credits() == 1234 && data(player, 0).prizePoints() == 0
                && ArcadeOrderCatalog.count(player, entry.item().get()) == 1, "Prize order used credits, mispriced points or lost its prize");
            ArcadeKioskNetwork.handlePrize(player, request);
            helper.assertTrue(ArcadeOrderCatalog.count(player, entry.item().get()) == 1, "Prize packet replay dispensed twice");
        }
        player.getInventory().setItem(0, pass(1000, 1000));
        ArcadeKioskNetwork.handlePrize(player, prize(menu, player, id("initial_d")));
        helper.assertTrue(data(player, 0).prizePoints() == 1000, "A machine forged as a prize charged points");
        helper.succeed();
    }

    @GameTest(template = "nostalgia_test")
    public static void arcadePrizeOverflowVetoMutationAndReentryNeverDuplicateOrCharge(GameTestHelper helper) {
        ServerPlayer player = createPlayer(helper, "PassOverflow", GameType.SURVIVAL);
        ArcadeKioskMenu menu = setup(helper, player);
        var entry = ArcadePrizeCatalog.entries().getFirst();
        int price = ArcadeEconomyConfig.prizePrice(entry.id());
        for (int mode = 0; mode < 3; mode++) {
            player.getInventory().setItem(0, pass(99, price*2L)); full(player);
            ItemStack before = player.getInventory().getItem(0).copy();
            var request = prize(menu, player, entry.id());
            int action = mode;
            Consumer<EntityJoinLevelEvent> callback = event -> {
                if (event.getLevel() != helper.getLevel() || !(event.getEntity() instanceof ItemEntity item)
                        || !item.getItem().is(entry.item().get()) || item.distanceToSqr(player) >= 4) { return; }
                if (action == 0) { event.setCanceled(true); }
                if (action == 1) { item.setItem(new ItemStack(Items.DIRT)); }
                if (action == 2) { ArcadeKioskNetwork.handlePrize(player, request); }
            };
            NeoForge.EVENT_BUS.addListener(callback);
            try { ArcadeKioskNetwork.handlePrize(player, request); }
            finally { NeoForge.EVENT_BUS.unregister(callback); }
            if (mode < 2) {
                helper.assertTrue(ItemStack.matches(before, player.getInventory().getItem(0)), "Canceled or substituted prize delivery charged the wallet");
                noDrops(helper, 0);
            } else {
                helper.assertTrue(data(player, 0).prizePoints() == price && data(player, 0).credits() == 99,
                    "Reentrant callback charged more than once");
                helper.assertItemEntityCountIs(entry.item().get(), BASE, 5, 1);
                noDrops(helper, 1);
            }
        }
        helper.succeed();
    }

    @GameTest(template = "nostalgia_test", timeoutTicks = 80)
    public static void arcadeCreativePrizeDeliverySurvivesUntilAnInventorySlotOpens(GameTestHelper helper) {
        ServerPlayer player = createPlayer(helper, "PassPickup", GameType.CREATIVE);
        ArcadeKioskMenu menu = setup(helper, player);
        var entry = ArcadePrizeCatalog.entries().getFirst();
        player.getInventory().setItem(0, pass(0, ArcadeEconomyConfig.prizePrice(entry.id()))); full(player);
        ArcadeKioskNetwork.handlePrize(player, prize(menu, player, entry.id()));
        ItemEntity output = helper.getEntities(EntityType.ITEM, BASE, 5).getFirst();
        helper.runAfterDelay(15, () -> {
            output.playerTouch(player);
            helper.assertTrue(!output.isRemoved() && data(player, 0).prizePoints() == 0 && output.getItem().getCount() == 1,
                "Full creative inventory deleted a paid prize or restored its points");
            player.getInventory().setItem(5, ItemStack.EMPTY); output.playerTouch(player);
            helper.assertTrue(output.isRemoved() && ArcadeOrderCatalog.count(player, entry.item().get()) == 1, "Paid prize failed to collect exactly once");
            helper.succeed();
        });
    }

    @GameTest(template = "nostalgia_test")
    public static void arcadeReopeningTheKioskDuringDeliveryCannotBypassTheTransactionGuard(GameTestHelper helper) {
        ServerPlayer player = createPlayer(helper, "PassReentry", GameType.SURVIVAL);
        ArcadeKioskMenu original = setup(helper, player);
        var entry = ArcadePrizeCatalog.entries().getFirst();
        int price = ArcadeEconomyConfig.prizePrice(entry.id());
        player.getInventory().setItem(0, pass(0, price*2L)); full(player);
        ItemStack before = player.getInventory().getItem(0).copy();
        Consumer<EntityJoinLevelEvent> callback = event -> {
            if (event.getLevel() == helper.getLevel() && event.getEntity() instanceof ItemEntity item
                    && item.getItem().is(entry.item().get()) && item.distanceToSqr(player) < 4) {
                player.closeContainer();
                ArcadeKioskMenu replacement = open(helper, player);
                ArcadeKioskNetwork.handlePrize(player, prize(replacement, player, entry.id()));
            }
        };
        NeoForge.EVENT_BUS.addListener(callback);
        try { ArcadeKioskNetwork.handlePrize(player, prize(original, player, entry.id())); }
        finally { NeoForge.EVENT_BUS.unregister(callback); }
        helper.assertTrue(ItemStack.matches(before, player.getInventory().getItem(0)), "A callback reopened the kiosk and changed a pass during an unfinished delivery");
        noDrops(helper, 0);
        ArcadeKioskMenu replacement = (ArcadeKioskMenu)player.containerMenu;
        ArcadeKioskNetwork.handlePrize(player, prize(replacement, player, entry.id()));
        helper.assertTrue(data(player, 0).prizePoints() == price, "The completed transaction guard failed to release the next legitimate order");
        helper.assertItemEntityCountIs(entry.item().get(), BASE, 5, 1);
        helper.succeed();
    }

    @GameTest(template = "nostalgia_test")
    public static void arcadeLiveConfigRebalancesExchangePrizesAndMachineRankProfiles(GameTestHelper helper) {
        ServerPlayer player = createPlayer(helper, "PassConfig", GameType.SURVIVAL);
        ArcadeKioskMenu menu = setup(helper, player);
        ModConfigSpec.IntValue iron = ArcadeEconomyConfig.SPEC.getValues().get("exchange.iron");
        ModConfigSpec.IntValue poster = ArcadeEconomyConfig.SPEC.getValues().get("prizes.arcade_poster");
        ModConfigSpec.IntValue defaultCost = ArcadeEconomyConfig.SPEC.getValues().get("play.defaultCreditCost");
        ModConfigSpec.ConfigValue<List<? extends String>> ranks = ArcadeEconomyConfig.SPEC.getValues().get("play.rankProfiles");
        ModConfigSpec.ConfigValue<List<? extends String>> machines = ArcadeEconomyConfig.SPEC.getValues().get("play.machineOverrides");
        int oldIron = iron.get(), oldPoster = poster.get(), oldCost = defaultCost.get();
        List<? extends String> oldRanks = List.copyOf(ranks.get()), oldMachines = List.copyOf(machines.get());
        try {
            // Synchronous on the server thread. Restore in finally before any
            // delayed test or another player's action can see this test config.
            iron.set(37); poster.set(73); defaultCost.set(19);
            ranks.set(List.of("standard|Config C|1|29", "test_config|Config S|1|83"));
            machines.set(List.of("funpackcustom:initial_d|23|test_config"));
            player.getInventory().setItem(0, pass(0, 500));
            player.getInventory().setItem(1, new ItemStack(Items.IRON_INGOT, 3));
            ArcadeKioskNetwork.handleExchange(player, exchange(menu, player, 0, BuiltInRegistries.ITEM.getKey(Items.IRON_INGOT)));
            helper.assertTrue(data(player, 0).credits() == 37 && player.getInventory().getItem(1).getCount() == 2,
                "A changed server exchange rate was ignored by a real kiosk transaction");
            ArcadeKioskNetwork.handlePrize(player, prize(menu, player, id("arcade_poster")));
            var prize = ArcadePrizeCatalog.find(id("arcade_poster")).orElseThrow();
            helper.assertTrue(data(player, 0).prizePoints() == 427 && data(player, 0).credits() == 37
                && ArcadeOrderCatalog.count(player, prize.item().get()) == 1, "A changed server prize price was not charged exactly");
            var standard = ArcadeEconomyConfig.profile(id("nostalgia_op3"));
            var override = ArcadeEconomyConfig.profile(id("initial_d"));
            helper.assertTrue(standard.credits() == 19 && standard.name().equals("standard")
                && ArcadeEconomyConfig.roll(standard, RandomSource.create(17)).points() == 29,
                "Configured default cost or standard rank points were ignored");
            helper.assertTrue(override.credits() == 23 && override.name().equals("test_config")
                && ArcadeEconomyConfig.roll(override, RandomSource.create(17)).points() == 83,
                "A machine-specific cost/profile override did not select its configured single-rank reward");
        } finally {
            iron.set(oldIron); poster.set(oldPoster); defaultCost.set(oldCost); ranks.set(oldRanks); machines.set(oldMachines);
        }
        helper.assertTrue(ArcadeEconomyConfig.exchangeRates().stream().filter(rate -> rate.material() == Items.IRON_INGOT).findFirst().orElseThrow().credits() == oldIron
            && ArcadeEconomyConfig.prizePrice(id("arcade_poster")) == oldPoster
            && defaultCost.get() == oldCost && ranks.get().equals(oldRanks) && machines.get().equals(oldMachines),
            "Config test failed to restore the server's original economy");
        helper.succeed();
    }
}
