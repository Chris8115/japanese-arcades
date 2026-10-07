package local.funpack.custom;

import static local.funpack.custom.GachaponTransactionGameTests.aimAt;
import static local.funpack.custom.GachaponTransactionGameTests.createPlayer;

import java.util.List;
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
public final class CardboardCutoutGameTests {
    private static final BlockPos BASE = new BlockPos(3, 1, 3);

    private static List<CardboardCutoutBlock> cutouts() {
        return List.of(FunPackCustom.HATSUNE_MIKU_CUTOUT.get(), FunPackCustom.KASANE_TETO_CUTOUT.get());
    }

    private static boolean placeAbsolute(GameTestHelper helper, ServerPlayer player, CardboardCutoutBlock cutout, BlockPos pos, float yaw) {
        aimAt(player, pos);
        player.setYRot(yaw);
        player.setItemInHand(InteractionHand.MAIN_HAND, new ItemStack(cutout.asItem(), 2));
        BlockPos floor = pos.below();
        var hit = new BlockHitResult(Vec3.atCenterOf(floor).add(0, .5, 0), Direction.UP, floor, false);
        return ((BlockItem)player.getMainHandItem().getItem()).place(new BlockPlaceContext(player,
            InteractionHand.MAIN_HAND, player.getMainHandItem(), hit)).consumesAction();
    }

    private static void place(GameTestHelper helper, ServerPlayer player, CardboardCutoutBlock cutout, BlockPos base, int rotation) {
        helper.setBlock(base.below(), Blocks.STONE);
        helper.assertTrue(placeAbsolute(helper, player, cutout, helper.absolutePos(base), rotation*22.5F-175),
            "Cutout placement failed at a non-cardinal player yaw: " + rotation);
        helper.assertTrue(player.getMainHandItem().getCount() == (player.isCreative() ? 2 : 1),
            "Cutout placement consumed the wrong quantity");
        pair(helper, cutout, base, rotation);
    }

    private static void pair(GameTestHelper helper, CardboardCutoutBlock cutout, BlockPos base, int rotation) {
        for (DoubleBlockHalf half : DoubleBlockHalf.values()) {
            BlockPos part = half == DoubleBlockHalf.LOWER ? base : base.above();
            helper.assertBlockPresent(cutout, part);
            helper.assertBlockProperty(part, CardboardCutoutBlock.HALF, half);
            helper.assertBlockProperty(part, CardboardCutoutBlock.ROTATION, rotation);
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

    private static void exactlyOneDrop(GameTestHelper helper, CardboardCutoutBlock cutout) {
        helper.assertItemEntityCountIs(cutout.asItem(), BASE, 6, 1);
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
    public static void cardboardCutoutsQuantizeAllSixteenYawsAndBreakingEitherHalfReturnsOnePrize(GameTestHelper helper) {
        ServerPlayer player = createPlayer(helper, "CutoutPlace", GameType.SURVIVAL);
        for (var cutout : cutouts()) {
            for (int rotation = 0; rotation < 16; rotation++) {
                for (int half = 0; half < 2; half++) {
                    place(helper, player, cutout, BASE, rotation);
                    helper.getLevel().destroyBlock(helper.absolutePos(BASE.above(half)), true, player);
                    gone(helper, BASE);
                    exactlyOneDrop(helper, cutout);
                    clearDrops(helper);
                }
            }
            // Exercise the rounding boundary and wraparound, not just the center of each segment.
            float[] yaws = {-169, -168, 179, -181};
            int[] expected = {0, 1, 0, 0};
            for (int n = 0; n < yaws.length; n++) {
                helper.assertTrue(placeAbsolute(helper, player, cutout, helper.absolutePos(BASE), yaws[n]), "Boundary-yaw placement failed");
                pair(helper, cutout, BASE, expected[n]);
                helper.getLevel().destroyBlock(helper.absolutePos(BASE), true, player);
                gone(helper, BASE);
                exactlyOneDrop(helper, cutout);
                clearDrops(helper);
            }
        }
        helper.succeed();
    }

    @GameTest(template = "nostalgia_test")
    public static void cardboardCutoutsRefuseBlockedUnsupportedAndTooHighPlacementsWithoutConsumingThePrize(GameTestHelper helper) {
        ServerPlayer player = createPlayer(helper, "CutoutSpace", GameType.SURVIVAL);
        for (var cutout : cutouts()) {
            helper.setBlock(BASE.below(), Blocks.STONE);
            helper.setBlock(BASE.above(), Blocks.STONE);
            helper.assertTrue(!placeAbsolute(helper, player, cutout, helper.absolutePos(BASE), -147), "A blocked upper half allowed partial placement");
            helper.assertBlockPresent(Blocks.AIR, BASE);
            helper.assertBlockPresent(Blocks.STONE, BASE.above());
            helper.assertTrue(player.getMainHandItem().getCount() == 2, "Rejected headroom consumed the reward");
            helper.setBlock(BASE.above(), Blocks.AIR);
            // A bottom slab is not sturdy on its upper block boundary and cannot support the stand.
            helper.setBlock(BASE.below(), Blocks.STONE_SLAB);
            helper.assertTrue(!placeAbsolute(helper, player, cutout, helper.absolutePos(BASE), -147), "A cutout floated over an insufficient support face");
            gone(helper, BASE);
            helper.assertTrue(player.getMainHandItem().getCount() == 2, "Rejected support consumed the reward");

            BlockPos top = new BlockPos(helper.absolutePos(BASE).getX(), helper.getLevel().getMaxBuildHeight()-1, helper.absolutePos(BASE).getZ());
            var originalFloor = helper.getLevel().getBlockState(top.below());
            var originalTop = helper.getLevel().getBlockState(top);
            try {
                helper.getLevel().setBlock(top.below(), Blocks.STONE.defaultBlockState(), 3);
                helper.getLevel().setBlock(top, Blocks.AIR.defaultBlockState(), 3);
                helper.assertTrue(!placeAbsolute(helper, player, cutout, top, -147), "The last world-height cell accepted a two-block stand");
                helper.assertTrue(helper.getLevel().getBlockState(top).isAir() && player.getMainHandItem().getCount() == 2,
                    "World-height rejection left half a cutout or consumed the reward");
            } finally {
                helper.getLevel().setBlock(top, originalTop, 3);
                helper.getLevel().setBlock(top.below(), originalFloor, 3);
                aimAt(player, helper.absolutePos(BASE));
            }
            helper.assertTrue(helper.getEntities(EntityType.ITEM, BASE, 6).isEmpty(), "Failed placement spawned a collectible");
        }
        helper.succeed();
    }

    @GameTest(template = "nostalgia_test")
    public static void cardboardCutoutsCreativeRemovalOfEitherHalfKeepsAnAdjacentCutoutIntact(GameTestHelper helper) {
        ServerPlayer player = createPlayer(helper, "CutoutCreative", GameType.CREATIVE);
        for (var cutout : cutouts()) {
            for (int rotation = 0; rotation < 16; rotation++) {
                for (int half = 0; half < 2; half++) {
                    place(helper, player, cutout, BASE, rotation);
                    place(helper, player, cutout, BASE.east(), rotation);
                    removeCreative(helper, player, BASE.above(half));
                    gone(helper, BASE);
                    pair(helper, cutout, BASE.east(), rotation);
                    helper.assertTrue(helper.getEntities(EntityType.ITEM, BASE, 6).isEmpty(), "Creative removal duplicated a reward");
                    removeCreative(helper, player, BASE.east().above(1-half));
                    gone(helper, BASE.east());
                    helper.assertTrue(helper.getEntities(EntityType.ITEM, BASE, 6).isEmpty(), "Creative removal of the neighbor dropped a reward");
                }
            }
        }
        helper.succeed();
    }

    @GameTest(template = "nostalgia_test")
    public static void cardboardCutoutsSupportLossDropsOnePrizeAndPreservesAdjacentAndReplacementBlocks(GameTestHelper helper) {
        ServerPlayer player = createPlayer(helper, "CutoutSupport", GameType.SURVIVAL);
        for (var cutout : cutouts()) {
            for (int rotation : new int[]{0, 1, 4, 7, 8, 11, 12, 15}) {
                place(helper, player, cutout, BASE, rotation);
                place(helper, player, cutout, BASE.east(), rotation);
                helper.getLevel().destroyBlock(helper.absolutePos(BASE.below()), false, player);
                gone(helper, BASE);
                pair(helper, cutout, BASE.east(), rotation);
                exactlyOneDrop(helper, cutout);
                clearDrops(helper);
                // Replacing an upper half must remove the old lower half without deleting the replacement.
                helper.getLevel().setBlock(helper.absolutePos(BASE.east().above()), Blocks.STONE.defaultBlockState(), 3);
                helper.assertBlockPresent(Blocks.AIR, BASE.east());
                helper.assertBlockPresent(Blocks.STONE, BASE.east().above());
                exactlyOneDrop(helper, cutout);
                clearDrops(helper);
                helper.setBlock(BASE.east().above(), Blocks.AIR);
            }
        }
        helper.succeed();
    }

    @GameTest(template = "nostalgia_test")
    public static void cardboardCutoutsStructureRotationsMirrorsAndSavedStatesKeepBothHalvesCoherent(GameTestHelper helper) {
        ServerPlayer player = createPlayer(helper, "CutoutStates", GameType.SURVIVAL);
        for (var cutout : cutouts()) {
            for (int rotation = 0; rotation < 16; rotation++) {
                place(helper, player, cutout, BASE, rotation);
                var lower = helper.getBlockState(BASE).rotate(Rotation.CLOCKWISE_90);
                var upper = helper.getBlockState(BASE.above()).rotate(Rotation.CLOCKWISE_90);
                // Structures transform both cells together, with no intermediate neighbor notifications.
                helper.getLevel().setBlock(helper.absolutePos(BASE), lower, 18);
                helper.getLevel().setBlock(helper.absolutePos(BASE.above()), upper, 18);
                pair(helper, cutout, BASE, (rotation+4)&15);
                lower = lower.mirror(Mirror.LEFT_RIGHT);
                upper = upper.mirror(Mirror.LEFT_RIGHT);
                helper.getLevel().setBlock(helper.absolutePos(BASE), lower, 18);
                helper.getLevel().setBlock(helper.absolutePos(BASE.above()), upper, 18);
                int mirrored = (8-(rotation+4)+16)&15;
                pair(helper, cutout, BASE, mirrored);
                lower = lower.mirror(Mirror.FRONT_BACK);
                upper = upper.mirror(Mirror.FRONT_BACK);
                lower = BlockState.CODEC.parse(NbtOps.INSTANCE, BlockState.CODEC.encodeStart(NbtOps.INSTANCE, lower).getOrThrow()).getOrThrow();
                upper = BlockState.CODEC.parse(NbtOps.INSTANCE, BlockState.CODEC.encodeStart(NbtOps.INSTANCE, upper).getOrThrow()).getOrThrow();
                helper.getLevel().setBlock(helper.absolutePos(BASE), lower, 18);
                helper.getLevel().setBlock(helper.absolutePos(BASE.above()), upper, 18);
                pair(helper, cutout, BASE, (16-mirrored)&15);
                helper.getLevel().destroyBlock(helper.absolutePos(BASE.above()), true, player);
                gone(helper, BASE);
                exactlyOneDrop(helper, cutout);
                clearDrops(helper);
            }
        }
        helper.succeed();
    }

    @GameTest(template = "nostalgia_test")
    public static void mixedMikuAndTetoCutoutsRemainIndependentWhenEitherCharacterIsRemoved(GameTestHelper helper) {
        for (GameType mode : new GameType[]{GameType.SURVIVAL, GameType.CREATIVE}) {
            ServerPlayer player = createPlayer(helper, "MixedCutouts" + mode.getName(), mode);
            for (int first = 0; first < cutouts().size(); first++) {
                var cutout = cutouts().get(first);
                var neighbor = cutouts().get(1-first);
                for (int half = 0; half < 2; half++) {
                    place(helper, player, cutout, BASE, 3);
                    place(helper, player, neighbor, BASE.east(), 11);
                    if (player.isCreative()) removeCreative(helper, player, BASE.above(half));
                    else helper.getLevel().destroyBlock(helper.absolutePos(BASE.above(half)), true, player);
                    gone(helper, BASE);
                    pair(helper, neighbor, BASE.east(), 11);
                    if (player.isCreative()) {
                        helper.assertTrue(helper.getEntities(EntityType.ITEM, BASE, 6).isEmpty(), "Creative removal of a mixed pair duplicated a reward");
                    } else {
                        exactlyOneDrop(helper, cutout);
                    }
                    clearDrops(helper);
                    if (player.isCreative()) removeCreative(helper, player, BASE.east().above(1-half));
                    else helper.getLevel().destroyBlock(helper.absolutePos(BASE.east().above(1-half)), true, player);
                    gone(helper, BASE.east());
                    if (player.isCreative()) {
                        helper.assertTrue(helper.getEntities(EntityType.ITEM, BASE, 6).isEmpty(), "Creative neighbor removal duplicated the other character");
                    } else {
                        exactlyOneDrop(helper, neighbor);
                    }
                    clearDrops(helper);
                }
            }
        }
        helper.succeed();
    }

    @GameTest(template = "nostalgia_test")
    public static void mismatchedCharacterHalvesCannotFormASurvivingCutoutOrDuplicateItsPrize(GameTestHelper helper) {
        ServerPlayer player = createPlayer(helper, "MixedCutoutHalves", GameType.SURVIVAL);
        for (int first = 0; first < cutouts().size(); first++) {
            var lowerCharacter = cutouts().get(first);
            var upperCharacter = cutouts().get(1-first);
            for (int rotation : new int[]{0, 3, 8, 11}) {
                place(helper, player, lowerCharacter, BASE, rotation);
                var wrongUpper = upperCharacter.defaultBlockState().setValue(CardboardCutoutBlock.HALF, DoubleBlockHalf.UPPER)
                    .setValue(CardboardCutoutBlock.ROTATION, rotation);
                // Simulate mismatched structure/save data without allowing intermediate neighbor repair.
                helper.getLevel().setBlock(helper.absolutePos(BASE.above()), wrongUpper, 18);
                helper.assertTrue(!wrongUpper.canSurvive(helper.getLevel(), helper.absolutePos(BASE.above())),
                    "A different character's lower half was accepted as the standee's matching support");
                helper.assertBlockPresent(lowerCharacter, BASE);
                helper.assertBlockPresent(upperCharacter, BASE.above());
                // An ordinary neighboring state update must discard the unsupported upper half and its orphaned lower half.
                var changedLower = helper.getBlockState(BASE).rotate(Rotation.CLOCKWISE_90);
                helper.getLevel().setBlock(helper.absolutePos(BASE), changedLower, 3);
                gone(helper, BASE);
                exactlyOneDrop(helper, lowerCharacter);
                clearDrops(helper);
            }
        }
        helper.succeed();
    }
}
