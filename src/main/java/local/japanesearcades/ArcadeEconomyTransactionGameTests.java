package local.japanesearcades;

import static local.japanesearcades.GachaponTransactionGameTests.aimAt;
import static local.japanesearcades.ArcadeKioskMenu.SOURCE_PASS_SLOT;
import static local.japanesearcades.ArcadeKioskMenu.TARGET_PASS_SLOT;
import static local.japanesearcades.GachaponTransactionGameTests.createPlayer;

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
import net.minecraft.world.inventory.ClickType;
import net.minecraft.world.entity.player.Player;
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
@GameTestHolder(JapaneseArcades.MOD_ID)
@PrefixGameTestTemplate(false)
public final class ArcadeEconomyTransactionGameTests {
    private static final BlockPos BASE = new BlockPos(3, 1, 3);
    private static ResourceLocation id(String path) { return ResourceLocation.fromNamespaceAndPath(JapaneseArcades.MOD_ID, path); }
    private static ArcadeKioskMenu setup(GameTestHelper helper, ServerPlayer player) {
        helper.setBlock(BASE.below(), Blocks.STONE);
        player.setYRot(180);
        player.setItemInHand(InteractionHand.MAIN_HAND, new ItemStack(JapaneseArcades.ARCADE_KIOSK_ITEM.get()));
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
        ArcadeKioskMenu menu = (ArcadeKioskMenu)player.containerMenu;
        menu.clickMenuButton(player, 2);
        return menu;
    }
    private static ItemStack pass(long credits, long points) {
        ItemStack result = ArcadePassItem.createPass();
        ArcadePassItem.setData(result, new ArcadePassData(1, ArcadePassItem.data(result).id(), id("custom_festival_design"), credits, points, 7));
        result.set(DataComponents.CUSTOM_NAME, Component.literal("Festival pass"));
        return result;
    }
    private static ArcadePassData data(ServerPlayer player, int slot) { return ArcadePassItem.data(player.getInventory().getItem(slot)); }
    private static ArcadePassData targetData(ArcadeKioskMenu menu) { return ArcadePassItem.data(menu.getTargetPass()); }
    private static ArcadePassData sourceData(ArcadeKioskMenu menu) { return ArcadePassItem.data(menu.getSourcePass()); }
    private static void target(ArcadeKioskMenu menu, ItemStack pass) { menu.getSlot(TARGET_PASS_SLOT).set(pass); }
    private static void source(ArcadeKioskMenu menu, ItemStack pass) { menu.getSlot(SOURCE_PASS_SLOT).set(pass); }
    private static ArcadeKioskNetwork.ExchangePayload exchange(ArcadeKioskMenu menu, ServerPlayer player, int slot, ResourceLocation material) {
        ArcadePassData pass = targetData(menu);
        return new ArcadeKioskNetwork.ExchangePayload(menu.containerId, TARGET_PASS_SLOT, pass.id(), pass.revision(), material);
    }
    private static ArcadeKioskNetwork.TransferPayload transfer(ArcadeKioskMenu menu, ServerPlayer player, int source, int target) {
        ArcadePassData from = source == target ? targetData(menu) : sourceData(menu), to = targetData(menu);
        return new ArcadeKioskNetwork.TransferPayload(menu.containerId, source == target ? TARGET_PASS_SLOT : SOURCE_PASS_SLOT, from.id(), from.revision(), TARGET_PASS_SLOT, to.id(), to.revision());
    }
    private static ArcadeKioskNetwork.PrizePayload prize(ArcadeKioskMenu menu, ServerPlayer player, ResourceLocation prize) {
        ArcadePassData pass = targetData(menu);
        return new ArcadeKioskNetwork.PrizePayload(menu.containerId, prize, TARGET_PASS_SLOT, pass.id(), pass.revision());
    }
    private static void full(ServerPlayer player) {
        for (int slot = 0; slot < 36; slot++) { player.getInventory().setItem(slot, new ItemStack(Items.COBBLESTONE, 64)); }
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
        ItemStack issued = menu.getTargetPass().copy();
        ArcadePassData first = targetData(menu);
        helper.assertTrue(first != null && first.credits() == 0 && first.prizePoints() == 0
            && !first.id().equals(ArcadePassData.UNASSIGNED) && issued.getMaxStackSize() == 1, "Issued pass must be a unique nonstackable empty wallet");
        for (int location = 0; location < 5; location++) {
            player.getInventory().clearContent(); menu.setCarried(ItemStack.EMPTY); source(menu, ItemStack.EMPTY); target(menu, ItemStack.EMPTY);
            if (location == 0) { player.getInventory().setItem(5, issued.copy()); }
            if (location == 1) { player.getInventory().setItem(40, issued.copy()); }
            if (location == 2) { menu.setCarried(issued.copy()); }
            if (location == 3) { source(menu, issued.copy()); }
            if (location == 4) { target(menu, issued.copy()); }
            int revision = menu.getStatusRevision();
            ArcadeKioskNetwork.handleIssuePass(player, request);
            helper.assertTrue(menu.getStatus() == ArcadeKioskMenu.STATUS_PASS_EXISTS && menu.getStatusRevision() != revision,
                "A pass already held in inventory, offhand, cursor or kiosk allowed repeated issuance");
            helper.assertTrue(player.getInventory().getItem(0).isEmpty(), "Repeated issuance generated another wallet");
        }
        menu.setCarried(ItemStack.EMPTY); target(menu, ItemStack.EMPTY); source(menu, ItemStack.EMPTY);
        player.getInventory().clearContent();
        full(player);
        ArcadeKioskNetwork.handleIssuePass(player, request);
        helper.assertTrue(menu.getStatus() == ArcadeKioskMenu.STATUS_PASS_ISSUED && targetData(menu) != null,
            "A full player inventory prevented direct issuance into the empty To slot");
        noDrops(helper, 0);
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
        ItemStack raw = new ItemStack(JapaneseArcades.ARCADE_PASS.get());
        helper.assertTrue(ArcadePassItem.data(raw) != null && ArcadePassItem.data(raw).credits() == 0, "A raw creative pass cannot start empty");
        helper.succeed();
    }

    @GameTest(template = "nostalgia_test")
    public static void arcadeMaterialExchangeUsesEveryConfiguredRateOnceAndNeverArmor(GameTestHelper helper) {
        ServerPlayer player = createPlayer(helper, "PassRates", GameType.SURVIVAL);
        ArcadeKioskMenu menu = setup(helper, player);
        target(menu, pass(0, 55));
        long expected = 0;
        for (var rate : ArcadeEconomyConfig.exchangeRates()) {
            player.getInventory().setItem(40, new ItemStack(rate.material(), 2));
            var request = exchange(menu, player, 0, BuiltInRegistries.ITEM.getKey(rate.material()));
            ArcadeKioskNetwork.handleExchange(player, request);
            expected += rate.credits();
            helper.assertTrue(targetData(menu).credits() == expected && targetData(menu).prizePoints() == 55
                && player.getInventory().getItem(40).getCount() == 1, "Exchange charged more than one material or ignored the server rate");
            ArcadeKioskNetwork.handleExchange(player, request);
            helper.assertTrue(targetData(menu).credits() == expected && player.getInventory().getItem(40).getCount() == 1,
                "Repeated exchange packet credited or charged twice");
        }
        player.getInventory().setItem(40, ItemStack.EMPTY);
        player.getInventory().setItem(36, new ItemStack(Items.IRON_INGOT, 64));
        ArcadeKioskNetwork.handleExchange(player, exchange(menu, player, 0, BuiltInRegistries.ITEM.getKey(Items.IRON_INGOT)));
        helper.assertTrue(targetData(menu).credits() == expected && player.getInventory().getItem(36).getCount() == 64,
            "Exchange consumed an armor slot or generated credits without material");
        helper.succeed();
    }

    @GameTest(template = "nostalgia_test")
    public static void arcadePassTransferConservesBothBalancesAndPreservesBothCards(GameTestHelper helper) {
        ServerPlayer player = createPlayer(helper, "PassTransfer", GameType.SURVIVAL);
        ArcadeKioskMenu menu = setup(helper, player);
        target(menu, pass(11, 17)); source(menu, pass(31, 47));
        ItemStack beforeA = menu.getTargetPass().copy(), beforeB = menu.getSourcePass().copy();
        var request = transfer(menu, player, 1, 0);
        ArcadeKioskNetwork.handleTransfer(player, request);
        helper.assertTrue(targetData(menu).credits() == 42 && targetData(menu).prizePoints() == 64
            && sourceData(menu).credits() == 0 && sourceData(menu).prizePoints() == 0, "B to A transfer lost or duplicated either balance");
        ArcadePassItem.setData(beforeA, ArcadePassItem.data(beforeA).withBalances(42, 64));
        ArcadePassItem.setData(beforeB, ArcadePassItem.data(beforeB).withBalances(0, 0));
        helper.assertTrue(ItemStack.matches(beforeA, menu.getTargetPass()) && ItemStack.matches(beforeB, menu.getSourcePass()),
            "Transfer changed a skin, name, identity or destroyed the emptied card");
        ArcadeKioskNetwork.handleTransfer(player, request);
        helper.assertTrue(ItemStack.matches(beforeA, menu.getTargetPass()) && ItemStack.matches(beforeB, menu.getSourcePass()),
            "Stale transfer replay changed either pass");
        ArcadeKioskNetwork.handleTransfer(player, transfer(menu, player, 0, 0));
        helper.assertTrue(ItemStack.matches(beforeA, menu.getTargetPass()), "Transfer to the same slot destroyed its balance");
        source(menu, beforeA.copy());
        ArcadeKioskNetwork.handleTransfer(player, transfer(menu, player, 1, 0));
        helper.assertTrue(ItemStack.matches(beforeA, menu.getTargetPass()) && ItemStack.matches(beforeA, menu.getSourcePass()),
            "Two copies of one assigned pass identity were allowed to transfer");
        target(menu, pass(ArcadePassData.MAX_BALANCE, ArcadePassData.MAX_BALANCE));
        source(menu, pass(1, 1));
        ArcadeKioskNetwork.handleTransfer(player, transfer(menu, player, 1, 0));
        helper.assertTrue(menu.getStatus() == ArcadeKioskMenu.STATUS_BALANCE_LIMIT && sourceData(menu).credits() == 1 && sourceData(menu).prizePoints() == 1,
            "Overflowing transfer partially drained its source");
        target(menu, new ItemStack(JapaneseArcades.ARCADE_PASS.get()));
        ItemStack rawSource = new ItemStack(JapaneseArcades.ARCADE_PASS.get());
        ArcadePassItem.setData(rawSource, new ArcadePassData(1, ArcadePassData.UNASSIGNED, id("custom_festival_design"), 7, 12, 0));
        source(menu, rawSource);
        ArcadeKioskNetwork.handleTransfer(player, transfer(menu, player, 1, 0));
        helper.assertTrue(targetData(menu).credits() == 7 && targetData(menu).prizePoints() == 12 && sourceData(menu).credits() == 0
            && !targetData(menu).id().equals(ArcadePassData.UNASSIGNED) && !sourceData(menu).id().equals(ArcadePassData.UNASSIGNED)
            && !targetData(menu).id().equals(sourceData(menu).id()), "Valid unassigned cards failed to initialize independent identities during transfer");
        helper.succeed();
    }

    @GameTest(template = "nostalgia_test")
    public static void arcadePassRejectsStaleSlotsIdentitiesSessionsAndBalanceOverflow(GameTestHelper helper) {
        ServerPlayer player = createPlayer(helper, "PassStale", GameType.SURVIVAL);
        ArcadeKioskMenu menu = setup(helper, player);
        target(menu, pass(4, 9)); player.getInventory().setItem(1, new ItemStack(Items.IRON_INGOT, 20));
        var original = exchange(menu, player, 0, BuiltInRegistries.ITEM.getKey(Items.IRON_INGOT));
        player.getInventory().setItem(2, menu.getTargetPass()); target(menu, ItemStack.EMPTY);
        ArcadeKioskNetwork.handleExchange(player, original);
        target(menu, pass(4, 9));
        ArcadeKioskNetwork.handleExchange(player, original);
        helper.assertTrue(targetData(menu).credits() == 4 && data(player, 2).credits() == 4 && player.getInventory().getItem(1).getCount() == 20,
            "A stale slot or changed card identity spent materials");
        var valid = exchange(menu, player, 0, original.materialId());
        ServerPlayer visitor = createPlayer(helper, "PassVisitor", GameType.SURVIVAL);
        visitor.getInventory().setItem(0, pass(91, 13)); visitor.getInventory().setItem(1, new ItemStack(Items.IRON_INGOT, 3));
        var visitorMenu = visitor.containerMenu;
        visitor.containerMenu = menu;
        try {
            ArcadeKioskNetwork.handleExchange(visitor, exchange(menu, visitor, 0, original.materialId()));
            helper.assertTrue(data(visitor, 0).credits() == 91 && visitor.getInventory().getItem(1).getCount() == 3
                && targetData(menu).credits() == 4 && player.getInventory().getItem(1).getCount() == 20,
                "A different player reused another viewer's kiosk session");
        } finally { visitor.containerMenu = visitorMenu; }
        ArcadeKioskNetwork.handleExchange(player, new ArcadeKioskNetwork.ExchangePayload(menu.containerId+1, 0, valid.passId(), valid.revision(), valid.materialId()));
        ArcadeKioskNetwork.handleExchange(player, new ArcadeKioskNetwork.ExchangePayload(menu.containerId, 40, valid.passId(), valid.revision(), valid.materialId()));
        ArcadeKioskNetwork.handleExchange(player, new ArcadeKioskNetwork.ExchangePayload(menu.containerId, 0, valid.passId(), valid.revision(), valid.materialId()));
        ArcadeKioskNetwork.handleExchange(player, new ArcadeKioskNetwork.ExchangePayload(menu.containerId, TARGET_PASS_SLOT, valid.passId(), valid.revision(), id("forged_material")));
        player.closeContainer(); ArcadeKioskNetwork.handleExchange(player, valid); menu.exchange(player, TARGET_PASS_SLOT, valid.passId(), valid.revision(), valid.materialId());
        menu = open(helper, player);
        target(menu, player.getInventory().getItem(0)); player.getInventory().setItem(0, ItemStack.EMPTY);
        valid = exchange(menu, player, 0, original.materialId());
        player.setPos(player.getX()+20, player.getY(), player.getZ()); ArcadeKioskNetwork.handleExchange(player, valid);
        aimAt(player, helper.absolutePos(BASE));
        helper.assertTrue(targetData(menu).credits() == 4 && player.getInventory().getItem(1).getCount() == 20, "An invalid or stale menu request was accepted");
        target(menu, pass(ArcadePassData.MAX_BALANCE, 9));
        ArcadeKioskNetwork.handleExchange(player, exchange(menu, player, 0, original.materialId()));
        helper.assertTrue(menu.getStatus() == ArcadeKioskMenu.STATUS_BALANCE_LIMIT && player.getInventory().getItem(1).getCount() == 20, "Balance overflow consumed material");
        target(menu, pass(0, 0));
        helper.getLevel().destroyBlock(helper.absolutePos(BASE.above()), false);
        ArcadeKioskNetwork.handleExchange(player, exchange(menu, player, 0, original.materialId()));
        helper.assertTrue(targetData(menu).credits() == 0 && player.getInventory().getItem(1).getCount() == 20, "Destroyed kiosk changed a wallet");
        helper.succeed();
    }

    @GameTest(template = "nostalgia_test")
    public static void arcadeEveryConfiguredPrizeChargesOnlyItsPointPrice(GameTestHelper helper) {
        ServerPlayer player = createPlayer(helper, "PassPrizes", GameType.SURVIVAL);
        ArcadeKioskMenu menu = setup(helper, player);
        helper.assertTrue(ArcadePrizeCatalog.entries().size() == 117
            && ArcadePrizeCatalog.find(id("hatsune_miku_figure")).isPresent()
            && ArcadePrizeCatalog.find(id("kasane_teto_figure")).isPresent()
            && ArcadePrizeCatalog.find(id("wacca_poster")).isPresent()
            && ArcadePrizeCatalog.find(id("hatsune_miku_cutout")).isPresent()
            && ArcadePrizeCatalog.find(id("kasane_teto_cutout")).isPresent()
            && ArcadePrizeCatalog.find(id("kagamine_rin_cutout")).isPresent()
            && ArcadePrizeCatalog.find(id("kagamine_len_cutout")).isPresent()
            && ArcadePrizeCatalog.find(id("sleeping_fox_plush")).isPresent()
            && ArcadePrizeCatalog.find(id("mech_suit")).isPresent(),
            "The shop must retain its figures, four character cutouts, glow sticks, fox plush, mech reward, twenty posters and all 82 vanilla mob prizes");
        for (String mob : MobFigureBlock.MOBS) {
            helper.assertTrue(ArcadePrizeCatalog.find(id("boxed_" + mob + "_figure")).isPresent()
                && ArcadePrizeCatalog.find(id(mob + "_figure")).isEmpty()
                && ArcadePrizeCatalog.find(id(mob + "_figure_box")).isEmpty(),
                "Mob prizes must arrive boxed, with loose figures and empty boxes obtained by opening them");
        }
        for (String color : List.of("blue", "red", "yellow", "green", "pink", "purple", "orange")) {
            helper.assertTrue(ArcadePrizeCatalog.find(id(color + "_glow_stick")).isPresent(),
                "Missing glow-stick reward in the real redemption test: " + color);
        }
        // Exercise real server redemption after browsing has reordered the rewards.
        var browsed = ArcadePrizeCatalog.browse(ArcadePrizeCatalog.snapshot(), ArcadePrizeCatalog.Category.ALL,
            "", ArcadePrizeCatalog.Sort.PRICE_DESCENDING, Long.MAX_VALUE, false);
        for (var offer : browsed) {
            var entry = offer.entry();
            player.getInventory().clearContent();
            int price = ArcadeEconomyConfig.prizePrice(entry.id());
            target(menu, pass(1234, price-1));
            ArcadeKioskNetwork.handlePrize(player, prize(menu, player, entry.id()));
            helper.assertTrue(menu.getStatus() == ArcadeKioskMenu.STATUS_MISSING_POINTS && targetData(menu).prizePoints() == price-1,
                "Unaffordable prize charged points");
            target(menu, pass(1234, price));
            var request = prize(menu, player, entry.id());
            ArcadeKioskNetwork.handlePrize(player, request);
            helper.assertTrue(targetData(menu).credits() == 1234 && targetData(menu).prizePoints() == 0
                && ArcadeOrderCatalog.count(player, entry.item().get()) == 1, "Prize order used credits, mispriced points or lost its prize");
            ArcadeKioskNetwork.handlePrize(player, request);
            helper.assertTrue(ArcadeOrderCatalog.count(player, entry.item().get()) == 1, "Prize packet replay dispensed twice");
        }
        target(menu, pass(1000, 1000));
        ArcadeKioskNetwork.handlePrize(player, prize(menu, player, id("initial_d")));
        helper.assertTrue(targetData(menu).prizePoints() == 1000, "A machine forged as a prize charged points");
        helper.succeed();
    }

    @GameTest(template = "nostalgia_test")
    public static void arcadeRemovedPrizesCannotBeOrderedWithAnOldClientRequest(GameTestHelper helper) {
        ServerPlayer player = createPlayer(helper, "OldPrizes", GameType.SURVIVAL);
        ArcadeKioskMenu menu = setup(helper, player);
        target(menu, pass(1500, 1_000_000));
        ItemStack before = menu.getTargetPass().copy();
        for (String removed : List.of("arcade_poster", "arcade_cat_plush", "rhythm_star_trophy", "mini_arcade_cabinet")) {
            var removedId = id(removed);
            ArcadeKioskNetwork.handlePrize(player, prize(menu, player, removedId));
            helper.assertTrue(menu.getStatus() == ArcadeKioskMenu.STATUS_UNAVAILABLE
                && ItemStack.matches(before, menu.getTargetPass()), "Removed prize request changed its pass: " + removed);
            helper.assertTrue(ArcadePrizeCatalog.find(removedId).isEmpty() && ArcadeEconomyConfig.prizePrice(removedId) == -1
                && !BuiltInRegistries.ITEM.containsKey(removedId) && !BuiltInRegistries.BLOCK.containsKey(removedId),
                "Removed prize remains registered or purchasable: " + removed);
        }
        helper.assertTrue(player.getInventory().isEmpty(), "Removed prize request delivered an item");
        noDrops(helper, 0);
        helper.succeed();
    }

    @GameTest(template = "nostalgia_test")
    public static void arcadePrizeOverflowVetoMutationAndReentryNeverDuplicateOrCharge(GameTestHelper helper) {
        ServerPlayer player = createPlayer(helper, "PassOverflow", GameType.SURVIVAL);
        ArcadeKioskMenu menu = setup(helper, player);
        var entry = ArcadePrizeCatalog.entries().getFirst();
        int price = ArcadeEconomyConfig.prizePrice(entry.id());
        for (int mode = 0; mode < 3; mode++) {
            target(menu, pass(99, price*2L)); full(player);
            ItemStack before = menu.getTargetPass().copy();
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
                helper.assertTrue(ItemStack.matches(before, menu.getTargetPass()), "Canceled or substituted prize delivery charged the wallet");
                noDrops(helper, 0);
            } else {
                helper.assertTrue(targetData(menu).prizePoints() == price && targetData(menu).credits() == 99,
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
        target(menu, pass(0, ArcadeEconomyConfig.prizePrice(entry.id()))); full(player);
        ArcadeKioskNetwork.handlePrize(player, prize(menu, player, entry.id()));
        ItemEntity output = helper.getEntities(EntityType.ITEM, BASE, 5).getFirst();
        helper.runAfterDelay(15, () -> {
            output.playerTouch(player);
            helper.assertTrue(!output.isRemoved() && targetData(menu).prizePoints() == 0 && output.getItem().getCount() == 1,
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
        target(original, pass(0, price*2L)); full(player);
        ItemStack before = original.getTargetPass().copy();
        Consumer<EntityJoinLevelEvent> callback = event -> {
            if (event.getLevel() == helper.getLevel() && event.getEntity() instanceof ItemEntity item
                    && item.getItem().is(entry.item().get()) && item.distanceToSqr(player) < 4) {
                player.closeContainer();
                ArcadeKioskMenu replacement = open(helper, player);
                var old = ArcadePassItem.data(before);
                ArcadeKioskNetwork.handlePrize(player, new ArcadeKioskNetwork.PrizePayload(replacement.containerId, entry.id(), TARGET_PASS_SLOT, old.id(), old.revision()));
            }
        };
        NeoForge.EVENT_BUS.addListener(callback);
        try { ArcadeKioskNetwork.handlePrize(player, prize(original, player, entry.id())); }
        finally { NeoForge.EVENT_BUS.unregister(callback); }
        helper.assertTrue(original.getTargetPass().isEmpty(), "Closed menu retained the old card");
        var returned = helper.getEntities(EntityType.ITEM, BASE, 5).stream().filter(item -> ArcadePassItem.isPass(item.getItem())).findFirst().orElseThrow();
        helper.assertTrue(ItemStack.matches(before, returned.getItem()), "A callback reopened the kiosk and changed a pass during an unfinished delivery");
        noDrops(helper, 1);
        ArcadeKioskMenu replacement = (ArcadeKioskMenu)player.containerMenu;
        target(replacement, returned.getItem().copy()); returned.discard();
        ArcadeKioskNetwork.handlePrize(player, prize(replacement, player, entry.id()));
        helper.assertTrue(targetData(replacement).prizePoints() == price, "The completed transaction guard failed to release the next legitimate order");
        helper.assertItemEntityCountIs(entry.item().get(), BASE, 5, 1);
        helper.succeed();
    }

    @GameTest(template = "nostalgia_test")
    public static void arcadeLiveConfigRebalancesExchangePrizesAndMachineRankProfiles(GameTestHelper helper) {
        ServerPlayer player = createPlayer(helper, "PassConfig", GameType.SURVIVAL);
        ArcadeKioskMenu menu = setup(helper, player);
        ModConfigSpec.IntValue iron = ArcadeEconomyConfig.SPEC.getValues().get("exchange.iron");
        ModConfigSpec.IntValue miku = ArcadeEconomyConfig.SPEC.getValues().get("prizes.hatsune_miku_figure");
        ModConfigSpec.IntValue blueGlowStick = ArcadeEconomyConfig.SPEC.getValues().get("prizes.blue_glow_stick");
        ModConfigSpec.IntValue defaultCost = ArcadeEconomyConfig.SPEC.getValues().get("play.defaultCreditCost");
        ModConfigSpec.ConfigValue<List<? extends String>> ranks = ArcadeEconomyConfig.SPEC.getValues().get("play.rankProfiles");
        ModConfigSpec.ConfigValue<List<? extends String>> machines = ArcadeEconomyConfig.SPEC.getValues().get("play.machineOverrides");
        int oldIron = iron.get(), oldMiku = miku.get(), oldGlowStick = blueGlowStick.get(), oldCost = defaultCost.get();
        List<? extends String> oldRanks = List.copyOf(ranks.get()), oldMachines = List.copyOf(machines.get());
        try {
            // Synchronous on the server thread. Restore in finally before any
            // delayed test or another player's action can see this test config.
            iron.set(37); miku.set(73); blueGlowStick.set(17); defaultCost.set(19);
            ranks.set(List.of("standard|Config C|1|29", "test_config|Config S|1|83"));
            machines.set(List.of("japanesearcades:initial_d|23|test_config"));
            target(menu, pass(0, 500));
            player.getInventory().setItem(1, new ItemStack(Items.IRON_INGOT, 3));
            ArcadeKioskNetwork.handleExchange(player, exchange(menu, player, 0, BuiltInRegistries.ITEM.getKey(Items.IRON_INGOT)));
            helper.assertTrue(targetData(menu).credits() == 37 && player.getInventory().getItem(1).getCount() == 2,
                "A changed server exchange rate was ignored by a real kiosk transaction");
            ArcadeKioskNetwork.handlePrize(player, prize(menu, player, id("hatsune_miku_figure")));
            var prize = ArcadePrizeCatalog.find(id("hatsune_miku_figure")).orElseThrow();
            helper.assertTrue(targetData(menu).prizePoints() == 427 && targetData(menu).credits() == 37
                && ArcadeOrderCatalog.count(player, prize.item().get()) == 1, "A changed server prize price was not charged exactly");
            var glowStick = ArcadePrizeCatalog.find(id("blue_glow_stick")).orElseThrow();
            for (int order = 0; order < 2; order++) {
                ArcadeKioskNetwork.handlePrize(player, prize(menu, player, glowStick.id()));
            }
            helper.assertTrue(targetData(menu).prizePoints() == 393 && targetData(menu).credits() == 37
                && ArcadeOrderCatalog.count(player, glowStick.item().get()) == 2
                && player.getInventory().items.stream().anyMatch(stack -> stack.is(glowStick.item().get()) && stack.getCount() == 2),
                "Repeated glow-stick purchases ignored the color's configured price or lost a stackable reward");
            var standard = ArcadeEconomyConfig.profile(id("nostalgia_op3"));
            var override = ArcadeEconomyConfig.profile(id("initial_d"));
            helper.assertTrue(standard.credits() == 19 && standard.name().equals("standard")
                && ArcadeEconomyConfig.roll(standard, RandomSource.create(17)).points() == 29,
                "Configured default cost or standard rank points were ignored");
            helper.assertTrue(override.credits() == 23 && override.name().equals("test_config")
                && ArcadeEconomyConfig.roll(override, RandomSource.create(17)).points() == 83,
                "A machine-specific cost/profile override did not select its configured single-rank reward");
        } finally {
            iron.set(oldIron); miku.set(oldMiku); blueGlowStick.set(oldGlowStick); defaultCost.set(oldCost); ranks.set(oldRanks); machines.set(oldMachines);
        }
        helper.assertTrue(ArcadeEconomyConfig.exchangeRates().stream().filter(rate -> rate.material() == Items.IRON_INGOT).findFirst().orElseThrow().credits() == oldIron
            && ArcadeEconomyConfig.prizePrice(id("hatsune_miku_figure")) == oldMiku
            && ArcadeEconomyConfig.prizePrice(id("blue_glow_stick")) == oldGlowStick
            && defaultCost.get() == oldCost && ranks.get().equals(oldRanks) && machines.get().equals(oldMachines),
            "Config test failed to restore the server's original economy");
        helper.succeed();
    }

    @GameTest(template = "nostalgia_test")
    public static void arcadePhysicalPassSlotsRestrictItemsRespectTabsAndInvalidateReinsertedCards(GameTestHelper helper) {
        ServerPlayer player = createPlayer(helper, "PassSlots", GameType.SURVIVAL);
        ArcadeKioskMenu menu = setup(helper, player);
        helper.assertTrue(menu.slots.size() == 38 && menu.getSlot(SOURCE_PASS_SLOT).getMaxStackSize() == 1
            && menu.getSlot(TARGET_PASS_SLOT).getMaxStackSize() == 1, "Kiosk must expose two single-card slots after the 36 player slots");
        menu.setCarried(new ItemStack(Items.DIRT));
        menu.clicked(TARGET_PASS_SLOT, 0, ClickType.PICKUP, player);
        helper.assertTrue(menu.getTargetPass().isEmpty() && menu.getCarried().is(Items.DIRT), "A non-pass item entered the To slot");
        helper.assertFalse(menu.getSlot(TARGET_PASS_SLOT).mayPlace(new ItemStack(JapaneseArcades.ARCADE_PASS.get(), 2)), "An invalid stacked pass entered a single-card slot");
        menu.setCarried(new ItemStack(JapaneseArcades.ARCADE_PASS.get()));
        menu.clicked(TARGET_PASS_SLOT, 0, ClickType.PICKUP, player);
        helper.assertTrue(menu.getCarried().isEmpty() && targetData(menu) != null && !targetData(menu).id().equals(ArcadePassData.UNASSIGNED),
            "A real slot click failed to insert and initialize the pass");
        player.getInventory().setItem(0, new ItemStack(Items.IRON_INGOT, 2));
        var oldRequest = exchange(menu, player, 0, BuiltInRegistries.ITEM.getKey(Items.IRON_INGOT));
        menu.clicked(TARGET_PASS_SLOT, 0, ClickType.PICKUP, player);
        menu.clicked(TARGET_PASS_SLOT, 0, ClickType.PICKUP, player);
        ArcadeKioskNetwork.handleExchange(player, oldRequest);
        helper.assertTrue(targetData(menu).credits() == 0 && player.getInventory().getItem(0).getCount() == 2,
            "Removing and reinserting a pass allowed an old confirmation to spend");
        menu.quickMoveStack(player, TARGET_PASS_SLOT);
        helper.assertTrue(menu.getTargetPass().isEmpty(), "Shift click did not remove a pass into player inventory");
        player.getInventory().clearContent();
        player.getInventory().setItem(0, pass(10, 20));
        menu.clickMenuButton(player, 0);
        menu.quickMoveStack(player, 27);
        helper.assertTrue(menu.getSourcePass().isEmpty() && menu.getTargetPass().isEmpty(), "Machines tab silently inserted a pass into a hidden slot");
        player.getInventory().clearContent(); player.getInventory().setItem(0, pass(10, 20));
        menu.clickMenuButton(player, 1); menu.quickMoveStack(player, 27);
        helper.assertTrue(targetData(menu).credits() == 10 && menu.getSourcePass().isEmpty(), "Prizes tab failed to shift a pass into To");
        player.getInventory().setItem(0, pass(30, 40));
        menu.clickMenuButton(player, 2); menu.quickMoveStack(player, 27);
        helper.assertTrue(sourceData(menu).credits() == 30, "With To occupied, Passes tab failed to shift the second card into From");
        menu.clickMenuButton(player, 1);
        menu.clicked(SOURCE_PASS_SLOT, 0, ClickType.PICKUP, player);
        helper.assertTrue(menu.getCarried().isEmpty() && sourceData(menu).credits() == 30, "A hidden slot accepted a forged click");
        player.closeContainer();
        helper.assertTrue(menu.getSourcePass().isEmpty() && menu.getTargetPass().isEmpty()
            && ArcadeOrderCatalog.count(player, JapaneseArcades.ARCADE_PASS.get()) == 2, "Closing with a hidden From card did not return both cards");
        menu.removed(player);
        helper.assertTrue(ArcadeOrderCatalog.count(player, JapaneseArcades.ARCADE_PASS.get()) == 2, "Closing twice duplicated temporary cards");
        helper.succeed();
    }

    @GameTest(template = "nostalgia_test", timeoutTicks = 80)
    public static void arcadePhysicalCardsReturnOnKioskBreakLogoutAndDeath(GameTestHelper helper) {
        ServerPlayer owner = createPlayer(helper, "PassReturn", GameType.SURVIVAL);
        ArcadeKioskMenu menu = setup(helper, owner);
        ItemStack a = pass(100, 200), b = pass(300, 400);
        target(menu, a.copy()); source(menu, b.copy());
        ServerPlayer visitor = createPlayer(helper, "PassOther", GameType.SURVIVAL);
        ArcadeKioskMenu other = open(helper, visitor);
        helper.assertTrue(other.getTargetPass().isEmpty() && other.getSourcePass().isEmpty(), "Two visitors shared physical kiosk storage");
        visitor.closeContainer();
        helper.getLevel().destroyBlock(helper.absolutePos(BASE.above()), false);
        helper.runAfterDelay(2, () -> {
            helper.assertTrue(owner.containerMenu == owner.inventoryMenu && menu.getTargetPass().isEmpty() && menu.getSourcePass().isEmpty(),
                "A broken kiosk failed to close and release inserted cards");
            helper.assertTrue(owner.getInventory().items.stream().anyMatch(stack -> ItemStack.matches(stack, a))
                && owner.getInventory().items.stream().anyMatch(stack -> ItemStack.matches(stack, b)), "Kiosk break lost either card or its balances");
            ArcadeKioskMenu logout = setup(helper, owner);
            target(logout, a.copy()); source(logout, b.copy());
            helper.getLevel().getServer().getPlayerList().remove(owner);
            helper.assertTrue(logout.getTargetPass().isEmpty() && logout.getSourcePass().isEmpty()
                && ArcadeOrderCatalog.count(owner, JapaneseArcades.ARCADE_PASS.get()) == 2, "Logout did not return both cards before player save");
            ServerPlayer dead = createPlayer(helper, "PassDeath", GameType.SURVIVAL);
            ArcadeKioskMenu death = open(helper, dead);
            target(death, a.copy()); source(death, b.copy());
            dead.setHealth(0); dead.closeContainer();
            helper.assertTrue(death.getTargetPass().isEmpty() && death.getSourcePass().isEmpty(), "Dead player retained a detached menu inventory");
            helper.assertItemEntityCountIs(JapaneseArcades.ARCADE_PASS.get(), BASE, 5, 2);
            helper.succeed();
        });
    }

    @GameTest(template = "nostalgia_test", timeoutTicks = 100)
    public static void arcadeClosedCreativeCardsSurviveFullInventoryAndVetoedReturn(GameTestHelper helper) {
        ServerPlayer player = createPlayer(helper, "PassReturnFull", GameType.CREATIVE);
        ArcadeKioskMenu menu = setup(helper, player);
        ItemStack a = pass(101, 202), b = pass(303, 404), cursor = pass(505, 606);
        target(menu, a.copy()); source(menu, b.copy()); menu.setCarried(cursor.copy()); full(player);
        Consumer<EntityJoinLevelEvent> veto = event -> {
            if (event.getLevel() == helper.getLevel() && event.getEntity() instanceof ItemEntity item
                && ArcadePassItem.isPass(item.getItem()) && item.distanceToSqr(player) < 4) { event.setCanceled(true); }
        };
        NeoForge.EVENT_BUS.addListener(veto);
        try {
            player.closeContainer(); menu.removed(player); ArcadeKioskMenu.recoverReturns(player);
            helper.assertTrue(menu.getTargetPass().isEmpty() && menu.getSourcePass().isEmpty() && menu.getCarried().isEmpty(), "Close failed to detach cards before callbacks");
            noDrops(helper, 0);
            helper.assertTrue(!player.getPersistentData().getCompound(Player.PERSISTED_NBT_TAG).isEmpty(), "A canceled return lost its persistent owner recovery record");
        } finally { NeoForge.EVENT_BUS.unregister(veto); }
        ArcadeKioskMenu.recoverReturns(player);
        helper.assertItemEntityCountIs(JapaneseArcades.ARCADE_PASS.get(), BASE, 5, 3);
        helper.assertTrue(!player.getPersistentData().getCompound(Player.PERSISTED_NBT_TAG).contains("japanesearcades:kiosk_pass_returns"), "Completed returns retained a replayable recovery queue");
        helper.runAfterDelay(15, () -> {
            var dropped = helper.getEntities(EntityType.ITEM, BASE, 5);
            for (ItemEntity item : dropped) { item.playerTouch(player); }
            helper.assertTrue(dropped.size() == 3 && dropped.stream().noneMatch(ItemEntity::isRemoved), "Full creative inventory deleted a returned card");
            player.getInventory().setItem(0, ItemStack.EMPTY); player.getInventory().setItem(1, ItemStack.EMPTY); player.getInventory().setItem(2, ItemStack.EMPTY);
            for (ItemEntity item : dropped) { item.playerTouch(player); }
            helper.assertTrue(ArcadeOrderCatalog.count(player, JapaneseArcades.ARCADE_PASS.get()) == 3
                && player.getInventory().items.stream().anyMatch(stack -> ItemStack.matches(stack, a))
                && player.getInventory().items.stream().anyMatch(stack -> ItemStack.matches(stack, b))
                && player.getInventory().items.stream().anyMatch(stack -> ItemStack.matches(stack, cursor)), "Returned cards lost names, balances, identity or quantity");
            ArcadeKioskMenu.recoverReturns(player); noDrops(helper, 0);
            helper.succeed();
        });
    }

    @GameTest(template = "nostalgia_test")
    public static void arcadeChangingAnInsertedPassDuringPrizeDeliveryCancelsItsDebit(GameTestHelper helper) {
        ServerPlayer player = createPlayer(helper, "PassSwap", GameType.SURVIVAL);
        ArcadeKioskMenu menu = setup(helper, player);
        var prize = ArcadePrizeCatalog.entries().getFirst();
        ItemStack original = pass(77, 10000), replacement = pass(88, 20000);
        target(menu, original.copy()); full(player);
        Consumer<EntityJoinLevelEvent> swap = event -> {
            if (event.getEntity() instanceof ItemEntity item && item.getItem().is(prize.item().get()) && item.distanceToSqr(player) < 4) {
                player.getInventory().setItem(0, menu.getTargetPass()); target(menu, replacement.copy());
            }
        };
        NeoForge.EVENT_BUS.addListener(swap);
        try { ArcadeKioskNetwork.handlePrize(player, prize(menu, player, prize.id())); }
        finally { NeoForge.EVENT_BUS.unregister(swap); }
        helper.assertTrue(ItemStack.matches(menu.getTargetPass(), replacement) && ItemStack.matches(player.getInventory().getItem(0), original),
            "An inserted-card change debited or overwrote one of the cards");
        noDrops(helper, 0);
        helper.succeed();
    }
}
