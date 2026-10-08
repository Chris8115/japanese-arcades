package local.japanesearcades;

import static local.japanesearcades.GachaponTransactionGameTests.aimAt;
import static local.japanesearcades.GachaponTransactionGameTests.createPlayer;

import java.util.List;
import java.util.function.Consumer;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.component.DataComponents;
import net.minecraft.gametest.framework.GameTest;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.item.ItemEntity;
import net.minecraft.world.inventory.ClickType;
import net.minecraft.world.item.BlockItem;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.item.component.CustomData;
import net.minecraft.world.item.context.BlockPlaceContext;
import net.minecraft.world.level.GameType;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.Rotation;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.entity.HopperBlockEntity;
import net.minecraft.world.phys.BlockHitResult;
import net.minecraft.world.phys.Vec3;
import net.neoforged.neoforge.common.NeoForge;
import net.neoforged.neoforge.event.entity.EntityJoinLevelEvent;
import net.neoforged.neoforge.gametest.GameTestHolder;
import net.neoforged.neoforge.gametest.PrefixGameTestTemplate;

/** Native placement/menu transactions plus persistence and exact-once contents recovery. */
@GameTestHolder(JapaneseArcades.MOD_ID)
@PrefixGameTestTemplate(false)
public final class FigureShelfGameTests {
    private static final BlockPos BASE = new BlockPos(3, 1, 3);

    private static void clean(GameTestHelper helper) {
        helper.setBlock(BASE.above(), Blocks.AIR);
        helper.setBlock(BASE, Blocks.AIR);
        helper.setBlock(BASE.below(), Blocks.AIR);
        for (Direction direction : Direction.Plane.HORIZONTAL) { helper.setBlock(BASE.relative(direction), Blocks.AIR); }
        helper.getEntities(EntityType.ITEM, BASE, 6).forEach(ItemEntity::discard);
    }

    private static void place(GameTestHelper helper, ServerPlayer player, FigureShelfBlock block,
            BlockPos relative, Direction facing, boolean wall) {
        BlockPos support = wall ? relative.relative(facing.getOpposite()) : relative.below();
        if (!(helper.getBlockState(support).getBlock() instanceof FigureShelfBlock)) { helper.setBlock(support, Blocks.STONE); }
        BlockPos absolute = helper.absolutePos(relative);
        aimAt(player, absolute);
        player.setYRot(facing.getOpposite().toYRot());
        player.setItemInHand(InteractionHand.MAIN_HAND, new ItemStack(block, 2));
        Direction face = wall ? facing : Direction.UP;
        BlockPos absoluteSupport = helper.absolutePos(support);
        var hit = new BlockHitResult(Vec3.atCenterOf(absoluteSupport).relative(face, .5), face, absoluteSupport, false);
        helper.assertTrue(((BlockItem)block.asItem()).place(new BlockPlaceContext(player, InteractionHand.MAIN_HAND,
            player.getMainHandItem(), hit)).consumesAction(), "Shelf did not place on its supported surface");
        helper.assertBlockPresent(block, relative);
        helper.assertBlockProperty(relative, FigureShelfBlock.FACING, facing);
        helper.assertTrue(player.getMainHandItem().getCount() == (player.isCreative() ? 2 : 1), "Shelf placement consumed the wrong count");
    }

    private static FigureShelfBlockEntity shelf(GameTestHelper helper) { return (FigureShelfBlockEntity)helper.getBlockEntity(BASE); }
    private static FigureShelfMenu open(GameTestHelper helper, ServerPlayer player) {
        aimAt(player, helper.absolutePos(BASE));
        player.setShiftKeyDown(false);
        var hit = new BlockHitResult(Vec3.atCenterOf(helper.absolutePos(BASE)), Direction.NORTH, helper.absolutePos(BASE), false);
        helper.assertTrue(player.gameMode.useItemOn(player, helper.getLevel(), player.getMainHandItem(),
            InteractionHand.MAIN_HAND, hit).consumesAction(), "Native shelf interaction did not consume exactly one use");
        helper.assertTrue(player.containerMenu instanceof FigureShelfMenu, "Shelf interaction did not open its inventory");
        return (FigureShelfMenu)player.containerMenu;
    }
    private static ItemStack figure(int count) { return new ItemStack(JapaneseArcades.MOB_FIGURES.getFirst().figureItem().get(), count); }
    private static ItemStack marked() {
        ItemStack stack = figure(1);
        stack.set(DataComponents.CUSTOM_NAME, Component.literal("Museum original"));
        CompoundTag tag = new CompoundTag(); tag.putInt("serial", 791); tag.putString("collection", "shelf-test");
        stack.set(DataComponents.CUSTOM_DATA, CustomData.of(tag));
        stack.set(DataComponents.ENCHANTMENT_GLINT_OVERRIDE, true);
        return stack;
    }
    private static int stored(FigureShelfBlockEntity shelf) {
        int count = 0;
        for (int slot = 0; slot < shelf.size(); slot++) { count += shelf.item(slot).getCount(); }
        return count;
    }
    private static int dropped(GameTestHelper helper, ItemStack expected) {
        return helper.getEntities(EntityType.ITEM, BASE, 6).stream()
            .filter(drop -> ItemStack.isSameItemSameComponents(drop.getItem(), expected)).mapToInt(drop -> drop.getItem().getCount()).sum();
    }

    @GameTest(template = "nostalgia_test")
    public static void figureShelvesPlaceOnWallsFloorsAndStackInEveryFacing(GameTestHelper helper) {
        for (GameType mode : new GameType[]{GameType.SURVIVAL, GameType.CREATIVE}) {
            ServerPlayer player = createPlayer(helper, "ShelfPlace" + mode.getName(), mode);
            for (Direction facing : Direction.Plane.HORIZONTAL) {
                for (FigureShelfBlock block : List.of(JapaneseArcades.FIGURE_DISPLAY_UNIT.get(), JapaneseArcades.FIGURE_WALL_SHELF.get())) {
                    clean(helper);
                    place(helper, player, block, BASE, facing, true);
                    helper.assertTrue(shelf(helper).size() == block.rows() * 4, "Wrong capacity for placed shelf");
                    helper.assertTrue(HopperBlockEntity.getContainerAt(helper.getLevel(), helper.absolutePos(BASE)) == null,
                        "Hopper automation accessed a decorative shelf");
                    var state = helper.getBlockState(BASE);
                    helper.assertTrue(state.rotate(Rotation.CLOCKWISE_90).getValue(FigureShelfBlock.FACING) == facing.getClockWise(),
                        "Shelf rotation did not retain the correct facing");
                }
                clean(helper);
                place(helper, player, JapaneseArcades.FIGURE_DISPLAY_UNIT.get(), BASE, facing, false);
                place(helper, player, JapaneseArcades.FIGURE_DISPLAY_UNIT.get(), BASE.above(), facing, false);
                helper.assertTrue(((FigureShelfBlockEntity)helper.getBlockEntity(BASE.above())).size() == 8, "Stacked unit missing inventory");
            }
        }
        clean(helper);
        ServerPlayer player = createPlayer(helper, "ShelfUnsupported", GameType.SURVIVAL);
        helper.setBlock(BASE.below(), Blocks.STONE);
        var floor = helper.absolutePos(BASE.below());
        player.setItemInHand(InteractionHand.MAIN_HAND, new ItemStack(JapaneseArcades.FIGURE_WALL_SHELF_ITEM.get(), 2));
        var hit = new BlockHitResult(Vec3.atCenterOf(floor).add(0, .5, 0), Direction.UP, floor, false);
        helper.assertTrue(!JapaneseArcades.FIGURE_WALL_SHELF_ITEM.get().place(new BlockPlaceContext(player,
            InteractionHand.MAIN_HAND, player.getMainHandItem(), hit)).consumesAction()
                && player.getMainHandItem().getCount() == 2, "A wall shelf placed without a wall or consumed an item");
        helper.succeed();
    }

    @GameTest(template = "nostalgia_test")
    public static void shelfMenusAcceptEveryCollectibleAndRejectOtherItems(GameTestHelper helper) {
        ServerPlayer player = createPlayer(helper, "ShelfKinds", GameType.SURVIVAL);
        place(helper, player, JapaneseArcades.FIGURE_DISPLAY_UNIT.get(), BASE, Direction.NORTH, false);
        player.setItemInHand(InteractionHand.MAIN_HAND, new ItemStack(Items.STICK));
        FigureShelfMenu menu = open(helper, player);
        helper.assertTrue(menu.shelfSize() == 8 && menu.slots.size() == 44, "Two-row menu has wrong slots");
        for (var set : JapaneseArcades.MOB_FIGURES) {
            for (Item item : List.of(set.figureItem().get(), set.emptyBoxItem().get(), set.boxedFigureItem().get())) {
                player.getInventory().clearContent();
                player.getInventory().setItem(9, new ItemStack(item, 2));
                menu.quickMoveStack(player, menu.shelfSize());
                helper.assertTrue(shelf(helper).item(0).is(item) && shelf(helper).item(1).is(item)
                    && shelf(helper).item(0).getCount() == 1 && shelf(helper).item(1).getCount() == 1,
                    "Supported mob form did not move into separate display slots: " + item);
                menu.quickMoveStack(player, 0); menu.quickMoveStack(player, 1);
                helper.assertTrue(stored(shelf(helper)) == 0 && ArcadeOrderCatalog.count(player, item) == 2,
                    "Retrieval duplicated or lost a collectible");
            }
        }
        for (Item item : List.of(JapaneseArcades.HATSUNE_MIKU_FIGURE_ITEM.get(), JapaneseArcades.KASANE_TETO_FIGURE_ITEM.get())) {
            player.getInventory().clearContent(); player.getInventory().setItem(9, new ItemStack(item));
            menu.quickMoveStack(player, 8);
            helper.assertTrue(shelf(helper).item(0).is(item), "Character figure was rejected");
            menu.quickMoveStack(player, 0);
        }
        for (Item item : List.of(Items.DIRT, Items.DIAMOND_SWORD, JapaneseArcades.CUSTOM_DISPLAY_BOX_ITEM.get(),
                JapaneseArcades.HATSUNE_MIKU_CUTOUT_ITEM.get(), JapaneseArcades.FIGURE_DISPLAY_UNIT_ITEM.get())) {
            player.getInventory().clearContent(); player.getInventory().setItem(9, new ItemStack(item));
            helper.assertTrue(!menu.getSlot(0).mayPlace(new ItemStack(item)) && menu.quickMoveStack(player, 8).isEmpty()
                && stored(shelf(helper)) == 0 && player.getInventory().getItem(9).is(item), "Shelf accepted an unrelated or nested display item");
        }
        player.closeContainer();
        clean(helper);
        place(helper, player, JapaneseArcades.FIGURE_WALL_SHELF.get(), BASE, Direction.NORTH, true);
        FigureShelfMenu wall = open(helper, player);
        helper.assertTrue(wall.shelfSize() == 4 && wall.slots.size() == 40, "Single-row menu has wrong slots");
        helper.succeed();
    }

    @GameTest(template = "nostalgia_test")
    public static void shelfMenuMovesOnePerCellAndRetainsOverflowInBothGameModes(GameTestHelper helper) {
        for (GameType mode : new GameType[]{GameType.SURVIVAL, GameType.CREATIVE}) {
            clean(helper);
            ServerPlayer player = createPlayer(helper, "ShelfTransfer" + mode.getName(), mode);
            place(helper, player, JapaneseArcades.FIGURE_DISPLAY_UNIT.get(), BASE, Direction.NORTH, false);
            player.getInventory().clearContent(); player.getInventory().setItem(9, figure(12));
            FigureShelfMenu menu = open(helper, player);
            menu.quickMoveStack(player, 8);
            helper.assertTrue(stored(shelf(helper)) == 8 && player.getInventory().getItem(9).getCount() == 4,
                "Shift-click did not fill eight cells once and preserve the remainder");
            helper.assertTrue(menu.quickMoveStack(player, 8).isEmpty() && player.getInventory().getItem(9).getCount() == 4,
                "Full shelf consumed overflow");
            for (int index = 0; index < 36; index++) { player.getInventory().setItem(index, new ItemStack(Items.COBBLESTONE, 64)); }
            helper.assertTrue(menu.quickMoveStack(player, 0).isEmpty() && stored(shelf(helper)) == 8,
                "Full player inventory consumed a displayed figure");
            player.getInventory().clearContent();
            for (int index = 0; index < 8; index++) { menu.quickMoveStack(player, index); }
            helper.assertTrue(stored(shelf(helper)) == 0 && ArcadeOrderCatalog.count(player, figure(1).getItem()) == 8,
                "Collectibles were duplicated or lost during batch retrieval");
            player.getInventory().clearContent();
            menu.setCarried(figure(12));
            menu.clicked(0, 0, ClickType.PICKUP, player);
            menu.clicked(1, 1, ClickType.PICKUP, player);
            helper.assertTrue(stored(shelf(helper)) == 2 && menu.getCarried().getCount() == 10,
                "Normal or right-click insertion did not honor the one-item limit");
            player.closeContainer();
            helper.assertTrue(stored(shelf(helper)) == 2 && ArcadeOrderCatalog.count(player, figure(1).getItem()) == 10,
                "Closing shelf lost the cursor stack or returned stored display contents");
        }
        helper.succeed();
    }

    @GameTest(template = "nostalgia_test")
    public static void shelfComponentsRoundTripInSaveAndClientUpdates(GameTestHelper helper) {
        ServerPlayer player = createPlayer(helper, "ShelfSave", GameType.SURVIVAL);
        place(helper, player, JapaneseArcades.FIGURE_DISPLAY_UNIT.get(), BASE, Direction.WEST, false);
        ItemStack original = marked();
        FigureShelfMenu menu = open(helper, player);
        menu.getSlot(7).setByPlayer(original.copy());
        var state = helper.getBlockState(BASE);
        var source = shelf(helper);
        var saved = source.saveWithFullMetadata(helper.getLevel().registryAccess());
        var restored = (FigureShelfBlockEntity)BlockEntity.loadStatic(helper.absolutePos(BASE), state, saved, helper.getLevel().registryAccess());
        helper.assertTrue(restored != null && restored.size() == 8 && ItemStack.matches(restored.item(7), original)
            && stored(restored) == 1, "Saved shelf omitted the exact item components or slot");
        var synced = new FigureShelfBlockEntity(helper.absolutePos(BASE), state);
        synced.handleUpdateTag(source.getUpdatePacket().getTag(), helper.getLevel().registryAccess());
        helper.assertTrue(ItemStack.matches(synced.item(7), original) && stored(synced) == 1,
            "Block update did not retain displayed item components");
        menu.quickMoveStack(player, 7);
        helper.assertTrue(stored(source) == 0 && player.getInventory().items.stream().anyMatch(stack -> ItemStack.matches(stack, original)),
            "Retrieval changed the stored item's custom components");
        helper.succeed();
    }

    @GameTest(template = "nostalgia_test")
    public static void shelfBreakAndSupportLossDropContentsExactlyOnce(GameTestHelper helper) {
        ItemStack original = marked();
        for (GameType mode : new GameType[]{GameType.SURVIVAL, GameType.CREATIVE}) {
            clean(helper);
            ServerPlayer player = createPlayer(helper, "ShelfBreak" + mode.getName(), mode);
            place(helper, player, JapaneseArcades.FIGURE_DISPLAY_UNIT.get(), BASE, Direction.NORTH, false);
            FigureShelfBlockEntity removed = shelf(helper);
            open(helper, player).getSlot(0).setByPlayer(original.copy());
            var state = helper.getBlockState(BASE);
            state.getBlock().playerWillDestroy(helper.getLevel(), helper.absolutePos(BASE), state, player);
            helper.getLevel().destroyBlock(helper.absolutePos(BASE), !player.isCreative(), player);
            removed.dropContents();
            helper.assertTrue(dropped(helper, original) == 1, "Breaking in " + mode + " lost or duplicated displayed contents");
        }
        clean(helper);
        ServerPlayer player = createPlayer(helper, "ShelfSupport", GameType.SURVIVAL);
        place(helper, player, JapaneseArcades.FIGURE_DISPLAY_UNIT.get(), BASE, Direction.NORTH, false);
        place(helper, player, JapaneseArcades.FIGURE_DISPLAY_UNIT.get(), BASE.above(), Direction.NORTH, false);
        shelf(helper).inventory().setItem(0, original.copy());
        ((FigureShelfBlockEntity)helper.getBlockEntity(BASE.above())).inventory().setItem(0, original.copy());
        helper.setBlock(BASE.below(), Blocks.AIR);
        helper.assertBlockPresent(Blocks.AIR, BASE); helper.assertBlockPresent(Blocks.AIR, BASE.above());
        helper.assertTrue(dropped(helper, original) == 2, "Stack support loss did not return both figures exactly once");
        clean(helper);
        place(helper, player, JapaneseArcades.FIGURE_WALL_SHELF.get(), BASE, Direction.NORTH, true);
        shelf(helper).inventory().setItem(0, original.copy());
        helper.setBlock(BASE.south(), Blocks.AIR);
        helper.assertBlockPresent(Blocks.AIR, BASE);
        helper.assertTrue(dropped(helper, original) == 1, "Wall support loss did not return its figure");
        clean(helper);
        place(helper, player, JapaneseArcades.FIGURE_DISPLAY_UNIT.get(), BASE, Direction.NORTH, true);
        shelf(helper).inventory().setItem(0, original.copy());
        Vec3 center = Vec3.atCenterOf(helper.absolutePos(BASE));
        helper.getLevel().explode(null, center.x, center.y, center.z, 2F, Level.ExplosionInteraction.BLOCK);
        helper.assertBlockPresent(Blocks.AIR, BASE);
        helper.assertTrue(dropped(helper, original) == 1, "Explosion lost or duplicated the display's contents");
        helper.succeed();
    }

    @GameTest(template = "nostalgia_test")
    public static void shelfRecoveryRetainsCanceledDropsWithoutDuplicatingOnRetry(GameTestHelper helper) {
        ServerPlayer player = createPlayer(helper, "ShelfRecovery", GameType.SURVIVAL);
        place(helper, player, JapaneseArcades.FIGURE_DISPLAY_UNIT.get(), BASE, Direction.NORTH, false);
        ItemStack original = marked();
        FigureShelfBlockEntity removed = shelf(helper);
        removed.inventory().setItem(0, original.copy());
        Consumer<EntityJoinLevelEvent> veto = event -> {
            if (event.getLevel() == helper.getLevel() && event.getEntity() instanceof ItemEntity item
                    && ItemStack.isSameItemSameComponents(item.getItem(), original)
                    && item.position().distanceToSqr(Vec3.atCenterOf(helper.absolutePos(BASE))) < 4) {
                event.setCanceled(true);
            }
        };
        NeoForge.EVENT_BUS.addListener(veto);
        try { helper.getLevel().destroyBlock(helper.absolutePos(BASE), true, player); }
        finally { NeoForge.EVENT_BUS.unregister(veto); }
        helper.assertTrue(dropped(helper, original) == 0 && stored(removed) == 0, "Canceled recovery left a live or retained duplicate");
        removed.dropContents();
        ClawMachineRecovery.retry(helper.getLevel()); ClawMachineRecovery.retry(helper.getLevel());
        helper.assertTrue(dropped(helper, original) == 1, "Queued shelf recovery did not deliver exactly once after the veto ended");
        helper.succeed();
    }

    @GameTest(template = "nostalgia_test")
    public static void staleShelfMenusCannotMutateRemovedOrUnreachableDisplays(GameTestHelper helper) {
        ServerPlayer player = createPlayer(helper, "ShelfSession", GameType.SURVIVAL);
        ServerPlayer other = createPlayer(helper, "ShelfOther", GameType.SURVIVAL);
        place(helper, player, JapaneseArcades.FIGURE_DISPLAY_UNIT.get(), BASE, Direction.NORTH, false);
        player.getInventory().clearContent(); player.getInventory().setItem(9, figure(3));
        FigureShelfMenu menu = open(helper, player);
        helper.assertTrue(!menu.stillValid(other) && menu.quickMoveStack(other, 8).isEmpty(), "Foreign player reused a shelf menu");
        player.setGameMode(GameType.SPECTATOR);
        helper.assertTrue(!menu.stillValid(player) && menu.quickMoveStack(player, 8).isEmpty(), "Spectator changed a shelf");
        player.setGameMode(GameType.SURVIVAL);
        player.setPos(player.getX() + 30, player.getY(), player.getZ());
        helper.assertTrue(!menu.stillValid(player) && menu.quickMoveStack(player, 8).isEmpty(), "Unreachable shelf accepted a transaction");
        aimAt(player, helper.absolutePos(BASE));
        player.setHealth(0);
        helper.assertTrue(!menu.stillValid(player) && menu.quickMoveStack(player, 8).isEmpty(), "Dead player changed a shelf");
        player.setHealth(20);
        menu.quickMoveStack(player, 8);
        helper.assertTrue(stored(shelf(helper)) == 3, "Valid shelf session did not recover after invalid access checks");
        helper.getLevel().destroyBlock(helper.absolutePos(BASE), true, player);
        helper.assertTrue(!menu.stillValid(player) && menu.quickMoveStack(player, 0).isEmpty(), "Stale menu extracted a removed shelf's contents");
        menu.clicked(0, 0, ClickType.PICKUP, player);
        helper.assertTrue(menu.getCarried().isEmpty() && dropped(helper, figure(1)) == 3,
            "A stale slot click duplicated the already dropped contents");
        player.closeContainer();
        helper.succeed();
    }

    @GameTest(template = "nostalgia_test")
    public static void deathAndRemovedViewersKeepShelfAndCursorItemsSeparate(GameTestHelper helper) {
        ServerPlayer player = createPlayer(helper, "ShelfDeath", GameType.SURVIVAL);
        place(helper, player, JapaneseArcades.FIGURE_DISPLAY_UNIT.get(), BASE, Direction.NORTH, false);
        player.getInventory().clearContent();
        FigureShelfMenu menu = open(helper, player);
        menu.setCarried(marked().copyWithCount(2));
        menu.clicked(0, 0, ClickType.PICKUP, player);
        player.setHealth(0);
        player.closeContainer();
        helper.assertTrue(stored(shelf(helper)) == 1 && dropped(helper, marked()) == 1,
            "Death returned the stored figure or lost/duplicated the carried figure");
        ServerPlayer removed = createPlayer(helper, "ShelfRemoved", GameType.SURVIVAL);
        removed.getInventory().clearContent(); removed.getInventory().setItem(9, figure(3));
        FigureShelfMenu removedMenu = open(helper, removed);
        removed.discard();
        helper.assertTrue(!removedMenu.stillValid(removed) && removedMenu.quickMoveStack(removed, 8).isEmpty()
            && stored(shelf(helper)) == 1, "Removed viewer retained access to shelf contents");
        helper.succeed();
    }
}
