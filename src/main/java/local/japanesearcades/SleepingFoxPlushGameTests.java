package local.japanesearcades;

import static local.japanesearcades.GachaponTransactionGameTests.aimAt;
import static local.japanesearcades.GachaponTransactionGameTests.createPlayer;

import java.util.ArrayList;
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
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.context.BlockPlaceContext;
import net.minecraft.world.level.GameType;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.Mirror;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.material.PushReaction;
import net.minecraft.world.phys.BlockHitResult;
import net.minecraft.world.phys.Vec3;
import net.neoforged.neoforge.gametest.GameTestHolder;
import net.neoforged.neoforge.gametest.PrefixGameTestTemplate;

/** Real four-cell placement, saved states, collision rejection, and one-prize removal. */
@GameTestHolder(JapaneseArcades.MOD_ID)
@PrefixGameTestTemplate(false)
public final class SleepingFoxPlushGameTests {
    private static final BlockPos BASE = new BlockPos(3, 1, 3);

    private static BlockPos part(BlockPos anchor, Direction facing, int index) {
        return SleepingFoxPlushBlock.partPosition(anchor, facing, index);
    }
    private static void floors(GameTestHelper helper, BlockPos anchor, Direction facing) {
        for (int i = 0; i < 4; i++) { helper.setBlock(part(anchor, facing, i).below(), Blocks.STONE); }
    }
    private static boolean placeAbsolute(GameTestHelper helper, ServerPlayer player, BlockPos anchor, Direction facing) {
        aimAt(player, anchor);
        player.setYRot(facing.getOpposite().toYRot());
        player.setItemInHand(InteractionHand.MAIN_HAND, new ItemStack(JapaneseArcades.SLEEPING_FOX_PLUSH_ITEM.get(), 2));
        BlockPos floor = anchor.below();
        var hit = new BlockHitResult(Vec3.atCenterOf(floor).add(0, .5, 0), Direction.UP, floor, false);
        return JapaneseArcades.SLEEPING_FOX_PLUSH_ITEM.get().place(new BlockPlaceContext(player,
            InteractionHand.MAIN_HAND, player.getMainHandItem(), hit)).consumesAction();
    }
    private static void place(GameTestHelper helper, ServerPlayer player, BlockPos anchor, Direction facing) {
        floors(helper, anchor, facing);
        helper.assertTrue(placeAbsolute(helper, player, helper.absolutePos(anchor), facing), "Fox placement failed: " + facing);
        helper.assertTrue(player.getMainHandItem().getCount() == (player.isCreative() ? 2 : 1), "Fox placement consumed the wrong quantity");
        complete(helper, anchor, facing);
    }
    private static void complete(GameTestHelper helper, BlockPos anchor, Direction facing) {
        for (int i = 0; i < 4; i++) {
            BlockPos pos = part(anchor, facing, i), absolute = helper.absolutePos(pos);
            BlockState state = helper.getBlockState(pos);
            helper.assertTrue(state.is(JapaneseArcades.SLEEPING_FOX_PLUSH.get())
                && state.getValue(SleepingFoxPlushBlock.PART) == i && state.getValue(SleepingFoxPlushBlock.FACING) == facing
                && SleepingFoxPlushBlock.getAnchor(state, absolute).equals(helper.absolutePos(anchor)), "Incorrect connected fox section");
            helper.assertTrue(state.canSurvive(helper.getLevel(), absolute) && helper.getLevel().getBlockEntity(absolute) == null,
                "Placed fox is unsupported or created a block entity");
            var shape = state.getShape(helper.getLevel(), absolute);
            helper.assertTrue(!shape.isEmpty() && shape == state.getShape(helper.getLevel(), absolute)
                && shape.bounds().minX >= -1.0E-8 && shape.bounds().minZ >= -1.0E-8
                && shape.bounds().maxX <= 1.00000001 && shape.bounds().maxZ <= 1.00000001
                && state.getPistonPushReaction() == PushReaction.BLOCK, "Fox selection escaped its cell, allocated anew, or allowed piston movement");
        }
    }
    private static void gone(GameTestHelper helper, BlockPos anchor, Direction facing) {
        for (int i = 0; i < 4; i++) { helper.assertBlockPresent(Blocks.AIR, part(anchor, facing, i)); }
    }
    private static void drops(GameTestHelper helper, int count) {
        var items = helper.getEntities(EntityType.ITEM, BASE, 8);
        helper.assertTrue(items.stream().allMatch(item -> item.getItem().is(JapaneseArcades.SLEEPING_FOX_PLUSH_ITEM.get()))
            && items.stream().mapToInt(item -> item.getItem().getCount()).sum() == count, "Fox removal lost or duplicated its reward");
        items.forEach(ItemEntity::discard);
    }
    private static void rejected(GameTestHelper helper, ServerPlayer player, BlockPos anchor, Direction facing) {
        helper.assertTrue(!placeAbsolute(helper, player, anchor, facing) && player.getMainHandItem().getCount() == 2,
            "Obstructed fox placed partially or consumed the reward");
        for (int i = 0; i < 4; i++) {
            helper.assertTrue(!helper.getLevel().getBlockState(part(anchor, facing, i)).is(JapaneseArcades.SLEEPING_FOX_PLUSH.get()),
                "Rejected placement left a fox section behind");
        }
    }

    @GameTest(template = "nostalgia_test")
    public static void foxPlacesSavesAndBreaksEachSectionInEveryFacing(GameTestHelper helper) {
        ServerPlayer player = createPlayer(helper, "FoxPlacement", GameType.SURVIVAL);
        for (Direction facing : Direction.Plane.HORIZONTAL) {
            for (int broken = 0; broken < 4; broken++) {
                place(helper, player, BASE, facing);
                // Round-trip the same block-state codec used by structures and saved palettes.
                for (int i = 0; i < 4; i++) {
                    BlockPos pos = part(BASE, facing, i);
                    var saved = BlockState.CODEC.encodeStart(NbtOps.INSTANCE, helper.getBlockState(pos)).getOrThrow();
                    var restored = BlockState.CODEC.parse(NbtOps.INSTANCE, saved).getOrThrow();
                    helper.getLevel().setBlock(helper.absolutePos(pos), restored, 18);
                }
                complete(helper, BASE, facing);
                helper.assertTrue(player.gameMode.destroyBlock(helper.absolutePos(part(BASE, facing, broken))), "Native survival break failed");
                gone(helper, BASE, facing);
                drops(helper, 1);
            }
        }
        helper.succeed();
    }

    @GameTest(template = "nostalgia_test")
    public static void foxRejectsBlockedCellsMissingSupportAndIntersectingCeilings(GameTestHelper helper) {
        ServerPlayer player = createPlayer(helper, "FoxSpace", GameType.SURVIVAL);
        for (Direction facing : Direction.Plane.HORIZONTAL) {
            floors(helper, BASE, facing);
            for (int i = 0; i < 4; i++) {
                BlockPos target = part(BASE, facing, i);
                helper.setBlock(target, Blocks.STONE);
                rejected(helper, player, helper.absolutePos(BASE), facing);
                helper.assertBlockPresent(Blocks.STONE, target);
                helper.setBlock(target, Blocks.AIR);
                // A bottom slab is an actual clicked block but is not sturdy at its upper cell edge.
                helper.setBlock(target.below(), Blocks.STONE_SLAB);
                rejected(helper, player, helper.absolutePos(BASE), facing);
                helper.setBlock(target.below(), Blocks.STONE);
            }
            helper.setBlock(BASE.above(), Blocks.STONE);
            rejected(helper, player, helper.absolutePos(BASE), facing);
            helper.setBlock(BASE.above(), Blocks.AIR);
            // A ceiling above the low right-hand tail/body is high enough and must remain usable.
            BlockPos lowCeiling = part(BASE, facing, 1).above();
            BlockPos headCeiling = part(BASE, facing, 2).above();
            helper.setBlock(lowCeiling, Blocks.STONE);
            helper.setBlock(headCeiling, Blocks.STONE);
            place(helper, player, BASE, facing);
            helper.getLevel().destroyBlock(helper.absolutePos(BASE), true);
            gone(helper, BASE, facing);
            drops(helper, 1);
            helper.setBlock(lowCeiling, Blocks.AIR);
            helper.setBlock(headCeiling, Blocks.AIR);
        }
        helper.succeed();
    }

    @GameTest(template = "nostalgia_test")
    public static void foxRejectsEntitiesWorldBorderAndTopBuildLimitWithoutTakingThePrize(GameTestHelper helper) {
        ServerPlayer player = createPlayer(helper, "FoxLimits", GameType.SURVIVAL);
        Direction facing = Direction.NORTH;
        floors(helper, BASE, facing);
        BlockPos anchor = helper.absolutePos(BASE);
        for (int i = 0; i < 4; i++) {
            var pig = EntityType.PIG.create(helper.getLevel());
            BlockPos target = part(anchor, facing, i);
            pig.setPos(target.getX() + .5, target.getY(), target.getZ() + .5);
            pig.setNoAi(true);
            helper.assertTrue(helper.getLevel().addFreshEntity(pig), "Could not create placement obstruction");
            try { rejected(helper, player, anchor, facing); }
            finally { pig.discard(); }
        }
        var border = helper.getLevel().getWorldBorder();
        double oldX = border.getCenterX(), oldZ = border.getCenterZ(), oldSize = border.getSize();
        try {
            border.setCenter(anchor.getX() + .5, anchor.getZ() + .5);
            border.setSize(1);
            rejected(helper, player, anchor, facing);
        } finally { border.setCenter(oldX, oldZ); border.setSize(oldSize); }
        BlockPos top = new BlockPos(anchor.getX(), helper.getLevel().getMaxBuildHeight() - 1, anchor.getZ());
        List<BlockState> old = new ArrayList<>();
        for (int i = 0; i < 4; i++) {
            BlockPos target = part(top, facing, i);
            old.add(helper.getLevel().getBlockState(target.below()));
            old.add(helper.getLevel().getBlockState(target));
            helper.getLevel().setBlock(target.below(), Blocks.STONE.defaultBlockState(), 3);
            helper.getLevel().setBlock(target, Blocks.AIR.defaultBlockState(), 3);
        }
        try { rejected(helper, player, top, facing); }
        finally {
            for (int i = 0; i < 4; i++) {
                BlockPos target = part(top, facing, i);
                helper.getLevel().setBlock(target, old.get(i * 2 + 1), 3);
                helper.getLevel().setBlock(target.below(), old.get(i * 2), 3);
            }
        }
        drops(helper, 0);
        helper.succeed();
    }

    @GameTest(template = "nostalgia_test")
    public static void foxCreativeBreakAndSupportLossKeepAdjacentPlushesIntact(GameTestHelper helper) {
        ServerPlayer player = createPlayer(helper, "FoxRemoval", GameType.CREATIVE);
        for (Direction facing : Direction.Plane.HORIZONTAL) {
            BlockPos neighbor = BASE.relative(facing.getClockWise(), 2);
            for (int removed = 0; removed < 4; removed++) {
                place(helper, player, BASE, facing);
                place(helper, player, neighbor, facing);
                helper.assertTrue(player.gameMode.destroyBlock(helper.absolutePos(part(BASE, facing, removed))), "Native creative break failed");
                gone(helper, BASE, facing);
                complete(helper, neighbor, facing);
                drops(helper, 0);
                player.gameMode.destroyBlock(helper.absolutePos(neighbor));
                gone(helper, neighbor, facing);
                place(helper, player, BASE, facing);
                place(helper, player, neighbor, facing);
                helper.setBlock(part(BASE, facing, removed).below(), Blocks.AIR);
                gone(helper, BASE, facing);
                complete(helper, neighbor, facing);
                drops(helper, 1);
                player.gameMode.destroyBlock(helper.absolutePos(neighbor));
                gone(helper, neighbor, facing);
                drops(helper, 0);
            }
        }
        helper.succeed();
    }

    @GameTest(template = "nostalgia_test")
    public static void foxMirroredSavedStructuresRemainConnectedAndDropOnce(GameTestHelper helper) {
        ServerPlayer player = createPlayer(helper, "FoxMirror", GameType.CREATIVE);
        for (Direction facing : Direction.Plane.HORIZONTAL) {
            for (Mirror mirror : new Mirror[]{Mirror.LEFT_RIGHT, Mirror.FRONT_BACK}) {
                place(helper, player, BASE, facing);
                var original = new ArrayList<BlockState>();
                for (int i = 0; i < 4; i++) { original.add(helper.getBlockState(part(BASE, facing, i))); }
                player.gameMode.destroyBlock(helper.absolutePos(BASE));
                BlockPos mirroredAnchor = null;
                Direction mirroredFacing = facing;
                for (int i = 0; i < 4; i++) {
                    BlockPos relative = part(BlockPos.ZERO, facing, i);
                    BlockPos target = BASE.offset(mirror == Mirror.FRONT_BACK ? -relative.getX() : relative.getX(), 0,
                        mirror == Mirror.LEFT_RIGHT ? -relative.getZ() : relative.getZ());
                    BlockState mirrored = original.get(i).mirror(mirror);
                    helper.setBlock(target.below(), Blocks.STONE);
                    helper.getLevel().setBlock(helper.absolutePos(target), mirrored, 18);
                    if (mirrored.getValue(SleepingFoxPlushBlock.PART) == 0) { mirroredAnchor = target; }
                    mirroredFacing = mirrored.getValue(SleepingFoxPlushBlock.FACING);
                }
                helper.assertTrue(mirroredAnchor != null, "Mirrored fox has no anchor");
                for (int i = 0; i < 4; i++) {
                    BlockPos target = helper.absolutePos(part(mirroredAnchor, mirroredFacing, i));
                    helper.getLevel().getBlockState(target).updateNeighbourShapes(helper.getLevel(), target, 3);
                }
                complete(helper, mirroredAnchor, mirroredFacing);
                helper.getLevel().destroyBlock(helper.absolutePos(part(mirroredAnchor, mirroredFacing, 3)), true);
                gone(helper, mirroredAnchor, mirroredFacing);
                drops(helper, 1);
            }
        }
        helper.succeed();
    }
}
