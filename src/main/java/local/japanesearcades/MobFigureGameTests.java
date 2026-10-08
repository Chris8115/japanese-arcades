package local.japanesearcades;

import static local.japanesearcades.GachaponTransactionGameTests.aimAt;
import static local.japanesearcades.GachaponTransactionGameTests.createPlayer;

import java.util.List;
import java.util.function.Consumer;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.registries.Registries;
import net.minecraft.gametest.framework.GameTest;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.nbt.NbtUtils;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.item.ItemEntity;
import net.minecraft.world.item.BlockItem;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.item.context.BlockPlaceContext;
import net.minecraft.world.level.GameType;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.Mirror;
import net.minecraft.world.level.block.Rotation;
import net.minecraft.world.phys.BlockHitResult;
import net.minecraft.world.phys.Vec3;
import net.neoforged.neoforge.common.NeoForge;
import net.neoforged.neoforge.event.entity.EntityJoinLevelEvent;
import net.neoforged.neoforge.gametest.GameTestHolder;
import net.neoforged.neoforge.gametest.PrefixGameTestTemplate;

/** Real collectible placement, reversible packaging, and atomic overflow delivery. */
@GameTestHolder(JapaneseArcades.MOD_ID)
@PrefixGameTestTemplate(false)
public final class MobFigureGameTests {
    private static final BlockPos BASE = new BlockPos(3, 1, 3);

    private static void place(GameTestHelper helper, ServerPlayer player, Item item, BlockPos pos, Direction facing) {
        helper.setBlock(pos.below(), Blocks.STONE);
        aimAt(player, helper.absolutePos(pos));
        player.setYRot(facing.getOpposite().toYRot());
        player.setItemInHand(InteractionHand.MAIN_HAND, new ItemStack(item, 2));
        BlockPos floor = helper.absolutePos(pos.below());
        var hit = new BlockHitResult(Vec3.atCenterOf(floor).add(0, .5, 0), Direction.UP, floor, false);
        helper.assertTrue(((BlockItem)item).place(new BlockPlaceContext(player, InteractionHand.MAIN_HAND,
            player.getMainHandItem(), hit)).consumesAction(), "Mob collectible placement failed: " + item + " " + facing);
        helper.assertTrue(player.getMainHandItem().getCount() == (player.isCreative() ? 2 : 1),
            "Mob collectible placement consumed the wrong quantity");
    }

    private static void use(GameTestHelper helper, ServerPlayer player, InteractionHand hand) {
        BlockPos pos = helper.absolutePos(BASE);
        var state = helper.getLevel().getBlockState(pos);
        var hit = new BlockHitResult(Vec3.atCenterOf(pos), Direction.NORTH, pos, false);
        ((MobFigureBlock)state.getBlock()).useItemOn(player.getItemInHand(hand), state, helper.getLevel(), pos, player, hand, hit);
    }

    private static void useEmptyMainHand(GameTestHelper helper, ServerPlayer player) {
        BlockPos pos = helper.absolutePos(BASE);
        var state = helper.getLevel().getBlockState(pos);
        ((MobFigureBlock)state.getBlock()).useWithoutItem(state, helper.getLevel(), pos, player,
            new BlockHitResult(Vec3.atCenterOf(pos), Direction.NORTH, pos, false));
    }

    private static void full(ServerPlayer player) {
        player.getInventory().clearContent();
        for (int slot = 0; slot < 36; slot++) player.getInventory().setItem(slot, new ItemStack(Items.COBBLESTONE, 64));
    }

    private static int inventory(ServerPlayer player, Item item) {
        return ArcadeOrderCatalog.count(player, item);
    }

    private static void clearDrops(GameTestHelper helper) {
        helper.getEntities(EntityType.ITEM, BASE, 6).forEach(ItemEntity::discard);
    }

    private static void noDrops(GameTestHelper helper) {
        helper.assertTrue(helper.getEntities(EntityType.ITEM, BASE, 6).isEmpty(), "Packaging left an unexpected or partial ground delivery");
    }

    @GameTest(template = "nostalgia_test")
    public static void mobCollectiblesPlaceRotateAndDropTheirCurrentFormInEveryFacing(GameTestHelper helper) {
        ServerPlayer player = createPlayer(helper, "MobPlacement", GameType.SURVIVAL);
        for (var set : JapaneseArcades.MOB_FIGURES) {
            for (Item item : List.of(set.figureItem().get(), set.emptyBoxItem().get(), set.boxedFigureItem().get())) {
                boolean loose = item == set.figureItem().get();
                for (Direction facing : Direction.Plane.HORIZONTAL) {
                    place(helper, player, item, BASE, facing);
                    helper.assertBlockPresent(((BlockItem)item).getBlock(), BASE);
                    helper.assertBlockProperty(BASE, MobFigureBlock.FACING, facing);
                    BlockPos pos = helper.absolutePos(BASE);
                    var state = helper.getLevel().getBlockState(pos);
                    var bounds = state.getCollisionShape(helper.getLevel(), pos).bounds();
                    double minX = (loose || facing.getAxis() == Direction.Axis.X ? 4 : 3)/16.0;
                    double minZ = (loose || facing.getAxis() == Direction.Axis.Z ? 4 : 3)/16.0;
                    helper.assertTrue(bounds.minX == minX && bounds.maxX == 1-minX
                        && bounds.minZ == minZ && bounds.maxZ == 1-minZ
                        && bounds.minY == 0 && bounds.maxY == (loose ? 11.5 : 14)/16.0,
                        "Collectible collision did not match its placed form or facing: " + item + " " + facing);
                    var saved = NbtUtils.writeBlockState(state);
                    helper.setBlock(BASE, Blocks.AIR);
                    var restored = NbtUtils.readBlockState(helper.getLevel().holderLookup(Registries.BLOCK), saved);
                    helper.getLevel().setBlock(pos, restored, 3);
                    helper.assertTrue(restored.equals(state)
                        && restored.getBlock().getCloneItemStack(helper.getLevel(), pos, restored).is(item),
                        "Saved collectible lost its mob, form, facing or pick-block item: " + item + " " + facing);
                    helper.getLevel().setBlock(pos, state.rotate(Rotation.CLOCKWISE_90), 3);
                    helper.assertBlockProperty(BASE, MobFigureBlock.FACING, facing.getClockWise());
                    helper.getLevel().setBlock(pos, state.mirror(Mirror.LEFT_RIGHT), 3);
                    helper.assertBlockProperty(BASE, MobFigureBlock.FACING,
                        facing.getAxis() == Direction.Axis.Z ? facing.getOpposite() : facing);
                    helper.getLevel().destroyBlock(pos, true, player);
                    helper.assertBlockPresent(Blocks.AIR, BASE);
                    helper.assertItemEntityCountIs(item, BASE, 6, 1);
                    helper.assertTrue(helper.getEntities(EntityType.ITEM, BASE, 6).size() == 1,
                        "Breaking a collectible dropped packaging contents in addition to its current form");
                    clearDrops(helper);
                }
            }
        }
        helper.succeed();
    }

    @GameTest(template = "nostalgia_test")
    public static void placedMobBoxesOpenRepackAndRejectMismatchesWithoutChangingNeighbors(GameTestHelper helper) {
        for (GameType mode : new GameType[]{GameType.SURVIVAL, GameType.CREATIVE}) {
            ServerPlayer player = createPlayer(helper, "MobBoxes" + mode.getName(), mode);
            for (int index = 0; index < JapaneseArcades.MOB_FIGURES.size(); index++) {
                var set = JapaneseArcades.MOB_FIGURES.get(index);
                var neighbor = JapaneseArcades.MOB_FIGURES.get((index+1)%JapaneseArcades.MOB_FIGURES.size());
                for (Direction facing : Direction.Plane.HORIZONTAL) {
                    place(helper, player, neighbor.boxedFigureItem().get(), BASE.east(), facing);
                    place(helper, player, set.boxedFigureItem().get(), BASE, facing);
                    player.getInventory().clearContent();
                    useEmptyMainHand(helper, player);
                    helper.assertBlockPresent(set.emptyBox().get(), BASE);
                    helper.assertBlockProperty(BASE, MobFigureBlock.FACING, facing);
                    helper.assertBlockPresent(neighbor.boxedFigure().get(), BASE.east());
                    helper.assertTrue(inventory(player, set.figureItem().get()) == 1
                        && inventory(player, set.emptyBoxItem().get()) == 0,
                        "Opening a placed box did not deliver exactly its figure while leaving packaging placed");

                    player.getInventory().clearContent();
                    player.setItemInHand(InteractionHand.MAIN_HAND, new ItemStack(neighbor.figureItem().get(), 2));
                    use(helper, player, InteractionHand.MAIN_HAND);
                    helper.assertBlockPresent(set.emptyBox().get(), BASE);
                    helper.assertTrue(player.getMainHandItem().getCount() == 2, "A different mob's figure was consumed by the box");
                    player.setItemInHand(InteractionHand.MAIN_HAND, ItemStack.EMPTY);
                    useEmptyMainHand(helper, player);
                    helper.assertBlockPresent(set.emptyBox().get(), BASE);
                    helper.assertTrue(inventory(player, set.figureItem().get()) == 0, "An empty box generated a second figure");

                    player.setItemInHand(InteractionHand.OFF_HAND, new ItemStack(set.figureItem().get(), 2));
                    use(helper, player, InteractionHand.OFF_HAND);
                    helper.assertBlockPresent(set.boxedFigure().get(), BASE);
                    helper.assertBlockProperty(BASE, MobFigureBlock.FACING, facing);
                    helper.assertTrue(player.getOffhandItem().getCount() == 1, "Repacking must consume one figure, including creative and offhand use");
                    player.setItemInHand(InteractionHand.MAIN_HAND, new ItemStack(Items.STICK));
                    use(helper, player, InteractionHand.MAIN_HAND);
                    useEmptyMainHand(helper, player);
                    helper.assertBlockPresent(set.boxedFigure().get(), BASE);
                    helper.assertTrue(inventory(player, set.figureItem().get()) == 1, "A nonempty main hand opened a filled box");
                    helper.assertBlockPresent(neighbor.boxedFigure().get(), BASE.east());
                    helper.assertBlockProperty(BASE.east(), MobFigureBlock.FACING, facing);
                    noDrops(helper);

                    BlockPos pos = helper.absolutePos(BASE);
                    var state = helper.getLevel().getBlockState(pos);
                    state.getBlock().playerWillDestroy(helper.getLevel(), pos, state, player);
                    helper.getLevel().destroyBlock(pos, !player.isCreative(), player);
                    helper.assertBlockPresent(neighbor.boxedFigure().get(), BASE.east());
                    if (player.isCreative()) noDrops(helper);
                    else helper.assertItemEntityCountIs(set.boxedFigureItem().get(), BASE, 6, 1);
                    clearDrops(helper);
                    helper.getLevel().destroyBlock(helper.absolutePos(BASE.east()), false, player);
                }
            }
        }
        helper.succeed();
    }

    @GameTest(template = "nostalgia_test")
    public static void heldMobBoxesRequireSneakingAndReturnBothPartsInEitherHandAndGameMode(GameTestHelper helper) {
        for (GameType mode : new GameType[]{GameType.SURVIVAL, GameType.CREATIVE}) {
            ServerPlayer player = createPlayer(helper, "MobHeld" + mode.getName(), mode);
            for (var set : JapaneseArcades.MOB_FIGURES) {
                for (InteractionHand hand : InteractionHand.values()) {
                    player.getInventory().clearContent();
                    player.setItemInHand(hand, new ItemStack(set.boxedFigureItem().get(), 2));
                    player.setShiftKeyDown(false);
                    set.boxedFigureItem().get().use(helper.getLevel(), player, hand);
                    helper.assertTrue(player.getItemInHand(hand).getCount() == 2
                        && inventory(player, set.figureItem().get()) == 0 && inventory(player, set.emptyBoxItem().get()) == 0,
                        "A boxed item opened without sneaking");
                    player.setShiftKeyDown(true);
                    set.boxedFigureItem().get().use(helper.getLevel(), player, hand);
                    helper.assertTrue(inventory(player, set.boxedFigureItem().get()) == 1
                        && inventory(player, set.figureItem().get()) == 1 && inventory(player, set.emptyBoxItem().get()) == 1,
                        "Sneak-use failed to exchange exactly one filled box for both parts: " + set.mob() + " " + mode + " " + hand);
                    noDrops(helper);
                }
            }
            player.setShiftKeyDown(false);
        }
        helper.succeed();
    }

    @GameTest(template = "nostalgia_test")
    public static void placedMobBoxOverflowRollsBackCanceledOrSubstitutedFigureDrops(GameTestHelper helper) {
        var set = JapaneseArcades.MOB_FIGURES.getFirst();
        ServerPlayer player = createPlayer(helper, "MobPlacedFull", GameType.SURVIVAL);
        place(helper, player, set.boxedFigureItem().get(), BASE, Direction.WEST);
        for (int action = 0; action < 3; action++) {
            full(player);
            int failure = action;
            Consumer<EntityJoinLevelEvent> callback = event -> {
                if (event.getLevel() == helper.getLevel() && event.getEntity() instanceof ItemEntity item
                    && item.getItem().is(set.figureItem().get()) && item.distanceToSqr(player) < 16) {
                    if (failure == 0) event.setCanceled(true);
                    if (failure == 1) item.setItem(new ItemStack(Items.DIRT));
                }
            };
            NeoForge.EVENT_BUS.addListener(callback);
            try { use(helper, player, InteractionHand.OFF_HAND); }
            finally { NeoForge.EVENT_BUS.unregister(callback); }
            helper.assertBlockProperty(BASE, MobFigureBlock.FACING, Direction.WEST);
            helper.assertTrue(inventory(player, Items.COBBLESTONE) == 36*64 && player.getOffhandItem().isEmpty(),
                "Overflow delivery changed an unrelated inventory slot");
            if (action < 2) {
                helper.assertBlockPresent(set.boxedFigure().get(), BASE);
                noDrops(helper);
            } else {
                helper.assertBlockPresent(set.emptyBox().get(), BASE);
                helper.assertItemEntityCountIs(set.figureItem().get(), BASE, 6, 1);
                helper.assertTrue(helper.getEntities(EntityType.ITEM, BASE, 6).size() == 1, "Opening overflow duplicated a figure");
            }
        }
        helper.succeed();
    }

    @GameTest(template = "nostalgia_test")
    public static void heldMobBoxOverflowRollsBackBothOutputsWhenTheSecondDropIsVetoed(GameTestHelper helper) {
        var set = JapaneseArcades.MOB_FIGURES.getLast();
        for (GameType mode : new GameType[]{GameType.SURVIVAL, GameType.CREATIVE}) {
            ServerPlayer player = createPlayer(helper, "MobHeldFull" + mode.getName(), mode);
            player.setShiftKeyDown(true);
            // One source frees an inventory slot; two sources require both outputs on the ground.
            for (int sourceCount : new int[]{1, 2}) {
                for (int action = 0; action < 3; action++) {
                    full(player);
                    player.setItemInHand(InteractionHand.MAIN_HAND, new ItemStack(set.boxedFigureItem().get(), sourceCount));
                    int failure = action;
                    Consumer<EntityJoinLevelEvent> callback = event -> {
                        if (event.getLevel() == helper.getLevel() && event.getEntity() instanceof ItemEntity item
                            && item.getItem().is(set.emptyBoxItem().get()) && item.distanceToSqr(player) < 16) {
                            if (failure == 0) event.setCanceled(true);
                            if (failure == 1) item.setItem(new ItemStack(Items.DIRT));
                        }
                    };
                    NeoForge.EVENT_BUS.addListener(callback);
                    try { set.boxedFigureItem().get().use(helper.getLevel(), player, InteractionHand.MAIN_HAND); }
                    finally { NeoForge.EVENT_BUS.unregister(callback); }
                    helper.assertTrue(inventory(player, Items.COBBLESTONE) == 35*64, "Held opening changed unrelated full inventory slots");
                    if (action < 2) {
                        helper.assertTrue(inventory(player, set.boxedFigureItem().get()) == sourceCount
                            && inventory(player, set.figureItem().get()) == 0 && inventory(player, set.emptyBoxItem().get()) == 0,
                            "Failed second output consumed a filled box or committed the first inventory output");
                        noDrops(helper);
                    } else {
                        helper.assertTrue(inventory(player, set.boxedFigureItem().get()) == sourceCount-1,
                            "Successful overflow did not consume exactly one boxed figure");
                        for (Item output : List.of(set.figureItem().get(), set.emptyBoxItem().get())) {
                            int ground = helper.getEntities(EntityType.ITEM, BASE, 6).stream()
                                .filter(entity -> entity.getItem().is(output)).mapToInt(entity -> entity.getItem().getCount()).sum();
                            helper.assertTrue(inventory(player, output)+ground == 1, "Successful overflow lost or duplicated a packaging output");
                        }
                    }
                    clearDrops(helper);
                }
            }
            player.setShiftKeyDown(false);
        }
        helper.succeed();
    }
}
