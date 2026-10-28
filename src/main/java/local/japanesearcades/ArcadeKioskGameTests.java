package local.japanesearcades;

import static local.japanesearcades.GachaponTransactionGameTests.aimAt;
import static local.japanesearcades.GachaponTransactionGameTests.createPlayer;

import java.util.ArrayList;
import java.util.List;
import java.util.function.Consumer;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.component.DataComponents;
import net.minecraft.gametest.framework.GameTest;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.network.chat.Component;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.item.ItemEntity;
import net.minecraft.world.item.BlockItem;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.item.context.BlockPlaceContext;
import net.minecraft.world.item.crafting.CraftingInput;
import net.minecraft.world.item.crafting.RecipeType;
import net.minecraft.world.level.GameType;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.properties.DoubleBlockHalf;
import net.minecraft.world.phys.BlockHitResult;
import net.minecraft.world.phys.Vec3;
import net.neoforged.neoforge.common.NeoForge;
import net.neoforged.neoforge.event.entity.EntityJoinLevelEvent;
import net.neoforged.neoforge.gametest.GameTestHolder;
import net.neoforged.neoforge.gametest.PrefixGameTestTemplate;

/** Real placements, network requests, recipe lookup and inventory/drop transactions. */
@GameTestHolder(JapaneseArcades.MOD_ID)
@PrefixGameTestTemplate(false)
public final class ArcadeKioskGameTests {
    private static final BlockPos BASE = new BlockPos(3, 1, 3);

    private static ResourceLocation id(String path) { return ResourceLocation.fromNamespaceAndPath(JapaneseArcades.MOD_ID, path); }

    private static boolean place(GameTestHelper helper, ServerPlayer player, BlockPos pos, Direction facing) {
        player.setYRot(facing.getOpposite().toYRot());
        player.setItemInHand(InteractionHand.MAIN_HAND, new ItemStack(JapaneseArcades.ARCADE_KIOSK_ITEM.get(), 2));
        BlockPos floor = helper.absolutePos(pos.below());
        var hit = new BlockHitResult(Vec3.atCenterOf(floor).add(0, .5, 0), Direction.UP, floor, false);
        return ((BlockItem)player.getMainHandItem().getItem()).place(
            new BlockPlaceContext(player, InteractionHand.MAIN_HAND, player.getMainHandItem(), hit)).consumesAction();
    }

    private static ArcadeKioskMenu open(GameTestHelper helper, ServerPlayer player, BlockPos pos) {
        player.setItemInHand(InteractionHand.MAIN_HAND, ItemStack.EMPTY);
        aimAt(player, helper.absolutePos(BASE));
        helper.useBlock(pos, player);
        helper.assertTrue(player.containerMenu instanceof ArcadeKioskMenu, "Either kiosk half must open the ordering menu");
        return (ArcadeKioskMenu)player.containerMenu;
    }

    private static ArcadeKioskMenu setup(GameTestHelper helper, ServerPlayer player) {
        helper.setBlock(BASE.below(), Blocks.STONE);
        helper.assertTrue(place(helper, player, BASE, Direction.NORTH), "Kiosk placement failed");
        player.getInventory().clearContent();
        return open(helper, player, BASE);
    }

    private static void materials(ServerPlayer player, ArcadeOrderCatalog.Entry entry, int multiplier) {
        player.getInventory().clearContent();
        int slot = 0;
        for (var cost : entry.costs()) { player.getInventory().setItem(slot++, new ItemStack(cost.item(), cost.count() * multiplier)); }
    }

    private static void order(ServerPlayer player, ArcadeKioskMenu menu, ResourceLocation entryId) {
        ArcadeKioskNetwork.handleOrder(player, new ArcadeKioskNetwork.OrderPayload(menu.containerId, entryId));
    }

    private static void discardDrops(GameTestHelper helper) {
        helper.getEntities(EntityType.ITEM, BASE, 5).forEach(ItemEntity::discard);
    }

    @GameTest(template = "nostalgia_test")
    public static void kioskBothHalvesOpenAndBreakOnceInEveryFacing(GameTestHelper helper) {
        ServerPlayer player = createPlayer(helper, "KioskPlace", GameType.SURVIVAL);
        helper.setBlock(BASE.below(), Blocks.STONE);
        for (Direction facing : Direction.Plane.HORIZONTAL) {
            for (int broken = 0; broken < 2; broken++) {
                helper.assertTrue(place(helper, player, BASE, facing), "Placement failed facing " + facing);
                helper.assertTrue(player.getMainHandItem().getCount() == 1, "Placement must consume exactly one kiosk");
                helper.assertBlockProperty(BASE, ArcadeKioskBlock.HALF, DoubleBlockHalf.LOWER);
                helper.assertBlockProperty(BASE.above(), ArcadeKioskBlock.HALF, DoubleBlockHalf.UPPER);
                helper.assertBlockProperty(BASE.above(), ArcadeKioskBlock.FACING, facing);
                for (int clicked = 0; clicked < 2; clicked++) {
                    var menu = open(helper, player, BASE.above(clicked));
                    helper.assertTrue(menu.getBlockPos().equals(helper.absolutePos(BASE)) && menu.stillValid(player),
                        "Upper and lower interactions did not resolve to the same valid base");
                    if (clicked == 1) {
                        BlockPos base = helper.absolutePos(BASE);
                        player.setPos(base.getX() + .5, base.getY() + 2, base.getZ() - player.blockInteractionRange() + .5);
                        helper.assertTrue(!player.canInteractWithBlock(base, 0) && player.canInteractWithBlock(base.above(), 0),
                            "Reach fixture must target only the upper half");
                        helper.assertTrue(menu.stillValid(player), "Upper-only reach closed an otherwise valid ordering session");
                        aimAt(player, base);
                    }
                    player.closeContainer();
                }
                helper.getLevel().destroyBlock(helper.absolutePos(BASE.above(broken)), true);
                helper.assertBlockPresent(Blocks.AIR, BASE);
                helper.assertBlockPresent(Blocks.AIR, BASE.above());
                helper.assertItemEntityCountIs(JapaneseArcades.ARCADE_KIOSK_ITEM.get(), BASE, 4, 1);
                discardDrops(helper);
            }
        }
        helper.succeed();
    }

    @GameTest(template = "nostalgia_test")
    public static void kioskObstructionsSupportsAndCreativeRemovalDoNotLeaveFragments(GameTestHelper helper) {
        ServerPlayer player = createPlayer(helper, "KioskSupport", GameType.SURVIVAL);
        helper.setBlock(BASE.below(), Blocks.STONE);
        helper.setBlock(BASE.above(), Blocks.STONE);
        helper.assertFalse(place(helper, player, BASE, Direction.NORTH), "Kiosk placed through an occupied upper cell");
        helper.assertTrue(player.getMainHandItem().getCount() == 2, "Blocked placement consumed an item");
        helper.assertBlockPresent(Blocks.AIR, BASE);
        helper.setBlock(BASE.above(), Blocks.AIR);
        helper.assertTrue(place(helper, player, BASE, Direction.NORTH), "Unobstructed placement failed");
        helper.getLevel().destroyBlock(helper.absolutePos(BASE.below()), false);
        helper.assertBlockPresent(Blocks.AIR, BASE);
        helper.assertBlockPresent(Blocks.AIR, BASE.above());
        helper.assertItemEntityCountIs(JapaneseArcades.ARCADE_KIOSK_ITEM.get(), BASE, 4, 1);
        discardDrops(helper);
        helper.setBlock(BASE.below(), Blocks.STONE);
        helper.setBlock(BASE.east().below(), Blocks.STONE);
        player.setGameMode(GameType.CREATIVE);
        for (Direction facing : Direction.Plane.HORIZONTAL) {
            for (int broken = 0; broken < 2; broken++) {
                helper.assertTrue(place(helper, player, BASE, facing), "Creative kiosk placement failed");
                helper.assertTrue(place(helper, player, BASE.east(), facing), "Adjacent kiosk placement failed");
                var pos = helper.absolutePos(BASE.above(broken));
                var state = helper.getLevel().getBlockState(pos);
                state.getBlock().playerWillDestroy(helper.getLevel(), pos, state, player);
                helper.getLevel().destroyBlock(pos, false, player);
                helper.assertBlockPresent(Blocks.AIR, BASE);
                helper.assertBlockPresent(Blocks.AIR, BASE.above());
                helper.assertTrue(ArcadeKioskBlock.isComplete(helper.getLevel(), helper.absolutePos(BASE.east())),
                    "Removing a kiosk damaged its independent neighbor");
                helper.assertItemEntityCountIs(JapaneseArcades.ARCADE_KIOSK_ITEM.get(), BASE, 4, 0);
                var neighbor = helper.absolutePos(BASE.east());
                var neighborState = helper.getLevel().getBlockState(neighbor);
                neighborState.getBlock().playerWillDestroy(helper.getLevel(), neighbor, neighborState, player);
                helper.getLevel().destroyBlock(neighbor, false, player);
            }
        }
        helper.succeed();
    }

    @GameTest(template = "nostalgia_test")
    public static void kioskEveryMachineOrdersExactlyOnceForItsMaterials(GameTestHelper helper) {
        ServerPlayer player = createPlayer(helper, "KioskCatalog", GameType.SURVIVAL);
        ArcadeKioskMenu menu = setup(helper, player);
        helper.assertTrue(ArcadeOrderCatalog.entries(ArcadeOrderCatalog.MACHINES).size() == 25
            && List.of("bombergirl", "gitadora_guitarfreaks", "gitadora_drummania", "compact_claw_machine").stream()
                .allMatch(name -> ArcadeOrderCatalog.find(id(name)).isPresent()),
            "The complete cabinet ordering catalog must include the new cabinets and compact claw machine");
        for (var entry : ArcadeOrderCatalog.entries(ArcadeOrderCatalog.MACHINES)) {
            materials(player, entry, 1);
            helper.assertTrue(ArcadeOrderCatalog.canAfford(player, entry), "An exact material set was marked unaffordable");
            order(player, menu, entry.id());
            helper.assertTrue(menu.getStatus() == ArcadeKioskMenu.STATUS_ORDERED, "Catalog item did not order: " + entry.id());
            helper.assertTrue(ArcadeOrderCatalog.count(player, entry.result().get()) == 1, "Order must deliver one selected machine");
            for (var cost : entry.costs()) {
                helper.assertTrue(ArcadeOrderCatalog.count(player, cost.item()) == 0, "Order charged the wrong material quantity");
            }
            order(player, menu, entry.id());
            helper.assertTrue(menu.getStatus() == ArcadeKioskMenu.STATUS_MISSING_MATERIALS
                && ArcadeOrderCatalog.count(player, entry.result().get()) == 1, "Repeated packet produced a free second machine");
        }
        helper.assertTrue(ArcadeOrderCatalog.entries(ArcadeOrderCatalog.PRIZES).isEmpty()
            && !ArcadePrizeCatalog.entries().isEmpty()
            && ArcadePrizeCatalog.entries().stream().allMatch(entry -> ArcadeOrderCatalog.find(entry.id()).isEmpty()),
            "Point prizes must remain separate from ordinary material orders");
        helper.succeed();
    }

    @GameTest(template = "nostalgia_test")
    public static void kioskPaymentCombinesMainAndOffhandButNeverArmor(GameTestHelper helper) {
        ServerPlayer player = createPlayer(helper, "KioskPayment", GameType.SURVIVAL);
        ArcadeKioskMenu menu = setup(helper, player);
        var entry = ArcadeOrderCatalog.find(id("gachapon")).orElseThrow();
        materials(player, entry, 1);
        ItemStack namedIron = new ItemStack(Items.IRON_INGOT, 3);
        namedIron.set(DataComponents.CUSTOM_NAME, Component.literal("Workshop iron"));
        player.getInventory().setItem(0, namedIron);
        player.getInventory().setItem(7, new ItemStack(Items.IRON_INGOT, 4));
        player.getInventory().setItem(36, new ItemStack(Items.IRON_INGOT, 64));
        order(player, menu, entry.id());
        helper.assertTrue(menu.getStatus() == ArcadeKioskMenu.STATUS_MISSING_MATERIALS, "Armor slots were counted as available ingredients");
        helper.assertTrue(player.getInventory().getItem(0).getCount() == 3
            && player.getInventory().getItem(1).getCount() == 2, "A failed quote partially consumed materials");
        player.getInventory().setItem(40, new ItemStack(Items.IRON_INGOT));
        order(player, menu, entry.id());
        helper.assertTrue(menu.getStatus() == ArcadeKioskMenu.STATUS_ORDERED, "Split main/offhand ingredients were not accepted");
        helper.assertTrue(ArcadeOrderCatalog.count(player, Items.IRON_INGOT) == 0
            && player.getInventory().getItem(36).getCount() == 64, "Payment consumed armor or missed an ingredient stack");
        helper.assertTrue(ArcadeOrderCatalog.count(player, JapaneseArcades.GACHAPON_ITEM.get()) == 1, "Split payment lost its machine");
        helper.succeed();
    }

    @GameTest(template = "nostalgia_test")
    public static void kioskRejectsForgedStaleDistantAndDestroyedOrders(GameTestHelper helper) {
        ServerPlayer player = createPlayer(helper, "KioskRequests", GameType.SURVIVAL);
        ArcadeKioskMenu menu = setup(helper, player);
        var entry = ArcadeOrderCatalog.find(id("gachapon")).orElseThrow();
        materials(player, entry, 2);
        ArcadeKioskNetwork.handleOrder(player, new ArcadeKioskNetwork.OrderPayload(menu.containerId + 1, entry.id()));
        order(player, menu, id("gachapon_capsule"));
        helper.assertTrue(ArcadeOrderCatalog.count(player, Items.IRON_INGOT) == 16, "Forged request consumed ingredients");
        player.closeContainer();
        order(player, menu, entry.id());
        menu = open(helper, player, BASE.above());
        materials(player, entry, 2);
        player.setPos(player.getX() + 30, player.getY(), player.getZ());
        order(player, menu, entry.id());
        helper.assertTrue(ArcadeOrderCatalog.count(player, Items.IRON_INGOT) == 16, "Out-of-reach request was accepted");
        aimAt(player, helper.absolutePos(BASE));
        player.setGameMode(GameType.SPECTATOR);
        order(player, menu, entry.id());
        helper.assertTrue(ArcadeOrderCatalog.count(player, Items.IRON_INGOT) == 16, "Spectator bought through a stale menu");
        player.setGameMode(GameType.SURVIVAL);
        helper.getLevel().destroyBlock(helper.absolutePos(BASE.above()), false);
        order(player, menu, entry.id());
        helper.assertTrue(ArcadeOrderCatalog.count(player, Items.IRON_INGOT) == 16
            && ArcadeOrderCatalog.count(player, JapaneseArcades.GACHAPON_ITEM.get()) == 0, "Destroyed kiosk still processed an order");
        helper.succeed();
    }

    private static void fullInventory(ServerPlayer player) {
        for (int slot = 0; slot < 36; slot++) { player.getInventory().setItem(slot, new ItemStack(Items.COBBLESTONE, 64)); }
        player.getInventory().setItem(0, new ItemStack(Items.IRON_INGOT, 64));
        player.getInventory().setItem(1, new ItemStack(Items.GOLD_INGOT, 64));
        player.getInventory().setItem(2, new ItemStack(Items.GLASS, 64));
        player.getInventory().setItem(3, new ItemStack(Items.REDSTONE, 64));
    }

    @GameTest(template = "nostalgia_test")
    public static void kioskOverflowDropsPurchaseForSurvivalAndCreative(GameTestHelper helper) {
        ServerPlayer player = createPlayer(helper, "KioskOverflow", GameType.SURVIVAL);
        ArcadeKioskMenu menu = setup(helper, player);
        for (GameType mode : new GameType[]{GameType.SURVIVAL, GameType.CREATIVE}) {
            player.setGameMode(mode);
            fullInventory(player);
            order(player, menu, id("gachapon"));
            helper.assertTrue(menu.getStatus() == ArcadeKioskMenu.STATUS_ORDERED, "A full inventory prevented paid ground delivery");
            helper.assertTrue(ArcadeOrderCatalog.count(player, Items.IRON_INGOT) == 56, "Overflow order did not charge exactly eight iron");
            helper.assertItemEntityCountIs(JapaneseArcades.GACHAPON_ITEM.get(), BASE, 4, 1);
            helper.assertTrue(ArcadeOrderCatalog.count(player, JapaneseArcades.GACHAPON_ITEM.get()) == 0,
                "Full inventory order duplicated into an inventory slot");
            discardDrops(helper);
        }
        helper.succeed();
    }

    @GameTest(template = "nostalgia_test", timeoutTicks = 80)
    public static void kioskCreativeGroundPurchaseSurvivesPickupUntilSpaceIsAvailable(GameTestHelper helper) {
        ServerPlayer player = createPlayer(helper, "KioskPickup", GameType.CREATIVE);
        ArcadeKioskMenu menu = setup(helper, player);
        fullInventory(player);
        order(player, menu, id("gachapon"));
        ItemEntity purchase = helper.getEntities(EntityType.ITEM, BASE, 4).stream()
            .filter(entity -> entity.getItem().is(JapaneseArcades.GACHAPON_ITEM.get())).findFirst().orElseThrow();
        CompoundTag saved = new CompoundTag();
        purchase.save(saved);
        ItemEntity reloaded = new ItemEntity(helper.getLevel(), purchase.getX(), purchase.getY(), purchase.getZ(), purchase.getItem().copy());
        reloaded.load(saved);
        helper.assertTrue(reloaded.getPersistentData().getBoolean(ArcadeKioskMenu.OVERFLOW_MARKER),
            "A saved ground purchase lost protection from full creative inventory pickup");
        // Replace the live entity with its actual saved form so the delayed
        // pickup verifies both runtime behavior and persistent protection.
        purchase.discard();
        helper.assertTrue(helper.getLevel().addFreshEntity(reloaded), "Saved purchase could not rejoin the world");
        helper.runAfterDelay(15, () -> {
            reloaded.playerTouch(player);
            helper.assertTrue(!reloaded.isRemoved() && reloaded.getItem().is(JapaneseArcades.GACHAPON_ITEM.get())
                && reloaded.getItem().getCount() == 1, "Full creative inventory silently destroyed a paid ground purchase");
            helper.assertTrue(ArcadeOrderCatalog.count(player, Items.IRON_INGOT) == 56
                && ArcadeOrderCatalog.count(player, JapaneseArcades.GACHAPON_ITEM.get()) == 0,
                "Delayed pickup changed the payment or inserted without room");
            player.getInventory().setItem(8, ItemStack.EMPTY);
            reloaded.playerTouch(player);
            helper.assertTrue(reloaded.isRemoved() && ArcadeOrderCatalog.count(player, JapaneseArcades.GACHAPON_ITEM.get()) == 1,
                "Protected purchase failed to collect when the buyer made room");
            helper.succeed();
        });
    }

    @GameTest(template = "nostalgia_test")
    public static void kioskCanceledOverflowSpawnKeepsEveryIngredient(GameTestHelper helper) {
        ServerPlayer player = createPlayer(helper, "KioskVeto", GameType.SURVIVAL);
        ArcadeKioskMenu menu = setup(helper, player);
        fullInventory(player);
        Consumer<EntityJoinLevelEvent> veto = event -> {
            if (event.getLevel() == helper.getLevel() && event.getEntity() instanceof ItemEntity item
                    && item.getItem().is(JapaneseArcades.GACHAPON_ITEM.get())
                    && item.distanceToSqr(player) < 4) { event.setCanceled(true); }
        };
        NeoForge.EVENT_BUS.addListener(veto);
        try {
            order(player, menu, id("gachapon"));
            helper.assertTrue(menu.getStatus() == ArcadeKioskMenu.STATUS_UNAVAILABLE, "Vetoed delivery reported success");
            helper.assertTrue(ArcadeOrderCatalog.count(player, Items.IRON_INGOT) == 64
                && ArcadeOrderCatalog.count(player, Items.GOLD_INGOT) == 64
                && ArcadeOrderCatalog.count(player, Items.GLASS) == 64
                && ArcadeOrderCatalog.count(player, Items.REDSTONE) == 64, "Failed delivery charged material costs");
            helper.assertItemEntityCountIs(JapaneseArcades.GACHAPON_ITEM.get(), BASE, 4, 0);
        } finally { NeoForge.EVENT_BUS.unregister(veto); }
        Consumer<EntityJoinLevelEvent> substitute = event -> {
            if (event.getLevel() == helper.getLevel() && event.getEntity() instanceof ItemEntity item
                    && item.getItem().is(JapaneseArcades.GACHAPON_ITEM.get())
                    && item.distanceToSqr(player) < 4) { item.setItem(new ItemStack(Items.DIRT)); }
        };
        NeoForge.EVENT_BUS.addListener(substitute);
        try {
            order(player, menu, id("gachapon"));
            helper.assertTrue(menu.getStatus() == ArcadeKioskMenu.STATUS_UNAVAILABLE, "A substituted purchase reported success");
            helper.assertTrue(ArcadeOrderCatalog.count(player, Items.IRON_INGOT) == 64
                && ArcadeOrderCatalog.count(player, Items.GOLD_INGOT) == 64
                && ArcadeOrderCatalog.count(player, Items.GLASS) == 64
                && ArcadeOrderCatalog.count(player, Items.REDSTONE) == 64, "Changed delivery charged material costs");
            helper.assertItemEntityCountIs(Items.DIRT, BASE, 4, 0);
            helper.assertItemEntityCountIs(JapaneseArcades.GACHAPON_ITEM.get(), BASE, 4, 0);
        } finally { NeoForge.EVENT_BUS.unregister(substitute); }
        helper.succeed();
    }

    @GameTest(template = "nostalgia_test")
    public static void kioskShapedRecipeWorksOnlyWithTheRightArrangement(GameTestHelper helper) {
        var ingredients = new ArrayList<>(List.of(new ItemStack(Items.GLASS), new ItemStack(Items.IRON_INGOT), new ItemStack(Items.GLASS),
            new ItemStack(Items.REDSTONE), new ItemStack(Items.GOLD_INGOT), new ItemStack(Items.REDSTONE),
            new ItemStack(Items.IRON_INGOT), new ItemStack(Items.IRON_INGOT), new ItemStack(Items.IRON_INGOT)));
        CraftingInput input = CraftingInput.of(3, 3, ingredients);
        var recipe = helper.getLevel().getRecipeManager().getRecipeFor(RecipeType.CRAFTING, input, helper.getLevel()).orElseThrow();
        ItemStack result = recipe.value().assemble(input, helper.getLevel().registryAccess());
        helper.assertTrue(recipe.id().equals(id("arcade_kiosk")) && result.is(JapaneseArcades.ARCADE_KIOSK_ITEM.get())
            && result.getCount() == 1, "Loaded shaped recipe did not craft one ordering kiosk");
        ingredients.set(4, new ItemStack(Items.GLASS));
        ingredients.set(0, new ItemStack(Items.GOLD_INGOT));
        CraftingInput wrong = CraftingInput.of(3, 3, ingredients);
        helper.assertFalse(recipe.value().matches(wrong, helper.getLevel()), "Kiosk recipe ignored its required arrangement");
        helper.succeed();
    }
}
