package local.funpack.custom;

import static local.funpack.custom.GachaponTransactionGameTests.aimAt;
import static local.funpack.custom.GachaponTransactionGameTests.createPlayer;

import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.gametest.framework.GameTest;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.nbt.NbtOps;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.item.ItemEntity;
import net.minecraft.world.item.BlockItem;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.context.BlockPlaceContext;
import net.minecraft.world.level.GameType;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.Mirror;
import net.minecraft.world.level.block.Rotation;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.properties.DoubleBlockHalf;
import net.minecraft.world.phys.BlockHitResult;
import net.minecraft.world.phys.Vec3;
import net.neoforged.neoforge.gametest.GameTestHolder;
import net.neoforged.neoforge.gametest.PrefixGameTestTemplate;

/** Real sign-style placement, coherent two-block state, and one-prize removal. */
@GameTestHolder(FunPackCustom.MOD_ID)
@PrefixGameTestTemplate(false)
public final class HatsuneMikuCutoutGameTests {
    private static final BlockPos BASE = new BlockPos(3, 1, 3);

    private static boolean placeAbsolute(GameTestHelper helper, ServerPlayer player, BlockPos pos, float yaw) {
        aimAt(player, pos);
        player.setYRot(yaw);
        player.setItemInHand(InteractionHand.MAIN_HAND, new ItemStack(FunPackCustom.HATSUNE_MIKU_CUTOUT_ITEM.get(), 2));
        BlockPos floor = pos.below();
        var hit = new BlockHitResult(Vec3.atCenterOf(floor).add(0, .5, 0), Direction.UP, floor, false);
        return ((BlockItem)player.getMainHandItem().getItem()).place(new BlockPlaceContext(player,
            InteractionHand.MAIN_HAND, player.getMainHandItem(), hit)).consumesAction();
    }

    private static void place(GameTestHelper helper, ServerPlayer player, BlockPos base, int rotation) {
        helper.setBlock(base.below(), Blocks.STONE);
        helper.assertTrue(placeAbsolute(helper, player, helper.absolutePos(base), rotation*22.5F-175),
            "Cutout placement failed at a non-cardinal player yaw: " + rotation);
        helper.assertTrue(player.getMainHandItem().getCount() == (player.isCreative() ? 2 : 1),
            "Cutout placement consumed the wrong quantity");
        pair(helper, base, rotation);
    }

    private static void pair(GameTestHelper helper, BlockPos base, int rotation) {
        for (DoubleBlockHalf half : DoubleBlockHalf.values()) {
            BlockPos part = half == DoubleBlockHalf.LOWER ? base : base.above();
            helper.assertBlockPresent(FunPackCustom.HATSUNE_MIKU_CUTOUT.get(), part);
            helper.assertBlockProperty(part, HatsuneMikuCutoutBlock.HALF, half);
            helper.assertBlockProperty(part, HatsuneMikuCutoutBlock.ROTATION, rotation);
            BlockPos absolute = helper.absolutePos(part);
            var state = helper.getLevel().getBlockState(absolute);
            helper.assertTrue(state.canSurvive(helper.getLevel(), absolute), "Placed or restored cutout half cannot survive");
            helper.assertTrue(!state.getShape(helper.getLevel(), absolute).isEmpty(), "A cutout half has no selectable shape");
            helper.assertTrue(helper.getLevel().getBlockEntity(absolute) == null, "A static cardboard cutout created a ticking block entity");
        }
    }

    private static void gone(GameTestHelper helper, BlockPos base) {
        helper.assertBlockPresent(Blocks.AIR, base);
        helper.assertBlockPresent(Blocks.AIR, base.above());
    }

    private static void exactlyOneDrop(GameTestHelper helper) {
        helper.assertItemEntityCountIs(FunPackCustom.HATSUNE_MIKU_CUTOUT_ITEM.get(), BASE, 6, 1);
        helper.assertTrue(helper.getEntities(EntityType.ITEM, BASE, 6).size() == 1,
            "A two-part cutout generated additional prize or cardboard drops");
    }

    private static void clearDrops(GameTestHelper helper) {
        helper.getEntities(EntityType.ITEM, BASE, 6).forEach(ItemEntity::discard);
    }

    private static void removeCreative(GameTestHelper helper, ServerPlayer player, BlockPos pos) {
        BlockPos absolute = helper.absolutePos(pos);
        var state = helper.getLevel().getBlockState(absolute);
        state.getBlock().playerWillDestroy(helper.getLevel(), absolute, state, player);
        helper.getLevel().destroyBlock(absolute, false, player);
    }

    @GameTest(template = "nostalgia_test")
    public static void mikuCutoutQuantizesAllSixteenYawsAndBreakingEitherHalfReturnsOnePrize(GameTestHelper helper) {
        ServerPlayer player = createPlayer(helper, "MikuCutoutPlace", GameType.SURVIVAL);
        for (int rotation = 0; rotation < 16; rotation++) {
            for (int half = 0; half < 2; half++) {
                place(helper, player, BASE, rotation);
                helper.getLevel().destroyBlock(helper.absolutePos(BASE.above(half)), true, player);
                gone(helper, BASE);
                exactlyOneDrop(helper);
                clearDrops(helper);
            }
        }
        // Exercise the rounding boundary and wraparound, not just the center of each segment.
        float[] yaws = {-169, -168, 179, -181};
        int[] expected = {0, 1, 0, 0};
        for (int n = 0; n < yaws.length; n++) {
            helper.assertTrue(placeAbsolute(helper, player, helper.absolutePos(BASE), yaws[n]), "Boundary-yaw placement failed");
            pair(helper, BASE, expected[n]);
            helper.getLevel().destroyBlock(helper.absolutePos(BASE), true, player);
            gone(helper, BASE);
            exactlyOneDrop(helper);
            clearDrops(helper);
        }
        helper.succeed();
    }

    @GameTest(template = "nostalgia_test")
    public static void mikuCutoutRefusesBlockedUnsupportedAndTooHighPlacementsWithoutConsumingThePrize(GameTestHelper helper) {
        ServerPlayer player = createPlayer(helper, "MikuCutoutSpace", GameType.SURVIVAL);
        helper.setBlock(BASE.below(), Blocks.STONE);
        helper.setBlock(BASE.above(), Blocks.STONE);
        helper.assertTrue(!placeAbsolute(helper, player, helper.absolutePos(BASE), -147), "A blocked upper half allowed partial placement");
        helper.assertBlockPresent(Blocks.AIR, BASE);
        helper.assertBlockPresent(Blocks.STONE, BASE.above());
        helper.assertTrue(player.getMainHandItem().getCount() == 2, "Rejected headroom consumed the reward");
        helper.setBlock(BASE.above(), Blocks.AIR);
        // A bottom slab is not sturdy on its upper block boundary and cannot support the stand.
        helper.setBlock(BASE.below(), Blocks.STONE_SLAB);
        helper.assertTrue(!placeAbsolute(helper, player, helper.absolutePos(BASE), -147), "A cutout floated over an insufficient support face");
        gone(helper, BASE);
        helper.assertTrue(player.getMainHandItem().getCount() == 2, "Rejected support consumed the reward");

        BlockPos top = new BlockPos(helper.absolutePos(BASE).getX(), helper.getLevel().getMaxBuildHeight()-1, helper.absolutePos(BASE).getZ());
        var originalFloor = helper.getLevel().getBlockState(top.below());
        var originalTop = helper.getLevel().getBlockState(top);
        try {
            helper.getLevel().setBlock(top.below(), Blocks.STONE.defaultBlockState(), 3);
            helper.getLevel().setBlock(top, Blocks.AIR.defaultBlockState(), 3);
            helper.assertTrue(!placeAbsolute(helper, player, top, -147), "The last world-height cell accepted a two-block stand");
            helper.assertTrue(helper.getLevel().getBlockState(top).isAir() && player.getMainHandItem().getCount() == 2,
                "World-height rejection left half a cutout or consumed the reward");
        } finally {
            helper.getLevel().setBlock(top, originalTop, 3);
            helper.getLevel().setBlock(top.below(), originalFloor, 3);
            aimAt(player, helper.absolutePos(BASE));
        }
        helper.assertTrue(helper.getEntities(EntityType.ITEM, BASE, 6).isEmpty(), "Failed placement spawned a collectible");
        helper.succeed();
    }

    @GameTest(template = "nostalgia_test")
    public static void mikuCutoutCreativeRemovalOfEitherHalfKeepsAnAdjacentCutoutIntact(GameTestHelper helper) {
        ServerPlayer player = createPlayer(helper, "MikuCutoutCreative", GameType.CREATIVE);
        for (int rotation = 0; rotation < 16; rotation++) {
            for (int half = 0; half < 2; half++) {
                place(helper, player, BASE, rotation);
                place(helper, player, BASE.east(), rotation);
                removeCreative(helper, player, BASE.above(half));
                gone(helper, BASE);
                pair(helper, BASE.east(), rotation);
                helper.assertTrue(helper.getEntities(EntityType.ITEM, BASE, 6).isEmpty(), "Creative removal duplicated a reward");
                removeCreative(helper, player, BASE.east().above(1-half));
                gone(helper, BASE.east());
                helper.assertTrue(helper.getEntities(EntityType.ITEM, BASE, 6).isEmpty(), "Creative removal of the neighbor dropped a reward");
            }
        }
        helper.succeed();
    }

    @GameTest(template = "nostalgia_test")
    public static void mikuCutoutSupportLossDropsOnePrizeAndPreservesAdjacentAndReplacementBlocks(GameTestHelper helper) {
        ServerPlayer player = createPlayer(helper, "MikuCutoutSupport", GameType.SURVIVAL);
        for (int rotation : new int[]{0, 1, 4, 7, 8, 11, 12, 15}) {
            place(helper, player, BASE, rotation);
            place(helper, player, BASE.east(), rotation);
            helper.getLevel().destroyBlock(helper.absolutePos(BASE.below()), false, player);
            gone(helper, BASE);
            pair(helper, BASE.east(), rotation);
            exactlyOneDrop(helper);
            clearDrops(helper);
            // Replacing an upper half must remove the old lower half without deleting the replacement.
            helper.getLevel().setBlock(helper.absolutePos(BASE.east().above()), Blocks.STONE.defaultBlockState(), 3);
            helper.assertBlockPresent(Blocks.AIR, BASE.east());
            helper.assertBlockPresent(Blocks.STONE, BASE.east().above());
            exactlyOneDrop(helper);
            clearDrops(helper);
            helper.setBlock(BASE.east().above(), Blocks.AIR);
        }
        helper.succeed();
    }

    @GameTest(template = "nostalgia_test")
    public static void mikuCutoutStructureRotationsMirrorsAndSavedStatesKeepBothHalvesCoherent(GameTestHelper helper) {
        ServerPlayer player = createPlayer(helper, "MikuCutoutStates", GameType.SURVIVAL);
        for (int rotation = 0; rotation < 16; rotation++) {
            place(helper, player, BASE, rotation);
            var lower = helper.getBlockState(BASE).rotate(Rotation.CLOCKWISE_90);
            var upper = helper.getBlockState(BASE.above()).rotate(Rotation.CLOCKWISE_90);
            // Structures transform both cells together, with no intermediate neighbor notifications.
            helper.getLevel().setBlock(helper.absolutePos(BASE), lower, 18);
            helper.getLevel().setBlock(helper.absolutePos(BASE.above()), upper, 18);
            pair(helper, BASE, (rotation+4)&15);
            lower = lower.mirror(Mirror.LEFT_RIGHT);
            upper = upper.mirror(Mirror.LEFT_RIGHT);
            helper.getLevel().setBlock(helper.absolutePos(BASE), lower, 18);
            helper.getLevel().setBlock(helper.absolutePos(BASE.above()), upper, 18);
            int mirrored = (8-(rotation+4)+16)&15;
            pair(helper, BASE, mirrored);
            lower = lower.mirror(Mirror.FRONT_BACK);
            upper = upper.mirror(Mirror.FRONT_BACK);
            lower = BlockState.CODEC.parse(NbtOps.INSTANCE, BlockState.CODEC.encodeStart(NbtOps.INSTANCE, lower).getOrThrow()).getOrThrow();
            upper = BlockState.CODEC.parse(NbtOps.INSTANCE, BlockState.CODEC.encodeStart(NbtOps.INSTANCE, upper).getOrThrow()).getOrThrow();
            helper.getLevel().setBlock(helper.absolutePos(BASE), lower, 18);
            helper.getLevel().setBlock(helper.absolutePos(BASE.above()), upper, 18);
            pair(helper, BASE, (16-mirrored)&15);
            helper.getLevel().destroyBlock(helper.absolutePos(BASE.above()), true, player);
            gone(helper, BASE);
            exactlyOneDrop(helper);
            clearDrops(helper);
        }
        helper.succeed();
    }
}
