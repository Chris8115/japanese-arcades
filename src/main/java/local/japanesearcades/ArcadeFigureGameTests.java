package local.japanesearcades;

import static local.japanesearcades.GachaponTransactionGameTests.createPlayer;

import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.gametest.framework.GameTest;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.item.ItemEntity;
import net.minecraft.world.item.BlockItem;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.context.BlockPlaceContext;
import net.minecraft.world.level.GameType;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.Mirror;
import net.minecraft.world.level.block.Rotation;
import net.minecraft.world.phys.BlockHitResult;
import net.minecraft.world.phys.Vec3;
import net.neoforged.neoforge.gametest.GameTestHolder;
import net.neoforged.neoforge.gametest.PrefixGameTestTemplate;

/** Exercises the real collectible BlockItems, oriented collision and loot tables. */
@GameTestHolder(JapaneseArcades.MOD_ID)
@PrefixGameTestTemplate(false)
public final class ArcadeFigureGameTests {
    private static final BlockPos BASE = new BlockPos(3, 1, 3);

    private static boolean place(GameTestHelper helper, ServerPlayer player, Item item, BlockPos pos, Direction facing) {
        player.setYRot(facing.getOpposite().toYRot());
        player.setItemInHand(InteractionHand.MAIN_HAND, new ItemStack(item, 2));
        BlockPos floor = helper.absolutePos(pos.below());
        var hit = new BlockHitResult(Vec3.atCenterOf(floor).add(0, .5, 0), Direction.UP, floor, false);
        return ((BlockItem)item).place(new BlockPlaceContext(player, InteractionHand.MAIN_HAND,
            player.getMainHandItem(), hit)).consumesAction();
    }

    @GameTest(template = "nostalgia_test")
    public static void bothFiguresPlaceRotateAndDropExactlyOneInEveryFacing(GameTestHelper helper) {
        ServerPlayer player = createPlayer(helper, "FigurePlace", GameType.SURVIVAL);
        helper.setBlock(BASE.below(), Blocks.STONE);
        for (var entry : ArcadePrizeCatalog.entries()) {
            Item item = entry.item().get();
            if (!(item instanceof BlockItem blockItem) || !(blockItem.getBlock() instanceof ArcadePrizeBlock)) { continue; }
            var block = blockItem.getBlock();
            for (Direction facing : Direction.Plane.HORIZONTAL) {
                helper.assertTrue(place(helper, player, item, BASE, facing), "Figure placement failed: " + entry.id() + " " + facing);
                helper.assertTrue(player.getMainHandItem().getCount() == 1, "Survival placement did not consume one figure");
                helper.assertBlockPresent(block, BASE);
                helper.assertBlockProperty(BASE, ArcadePrizeBlock.FACING, facing);
                var absolute = helper.absolutePos(BASE);
                var state = helper.getLevel().getBlockState(absolute);
                var bounds = state.getCollisionShape(helper.getLevel(), absolute).bounds();
                double minX = (facing.getAxis() == Direction.Axis.X ? 3 : 2) / 16.0;
                double minZ = (facing.getAxis() == Direction.Axis.X ? 2 : 3) / 16.0;
                helper.assertTrue(bounds.minX == minX && bounds.maxX == 1-minX
                    && bounds.minZ == minZ && bounds.maxZ == 1-minZ && bounds.minY == 0 && bounds.maxY == 15/16.0,
                    "Placed figure collision failed to rotate or protrudes beyond its single cell");
                helper.getLevel().setBlock(absolute, state.rotate(Rotation.CLOCKWISE_90), 3);
                helper.assertBlockProperty(BASE, ArcadePrizeBlock.FACING, facing.getClockWise());
                helper.getLevel().setBlock(absolute, state.mirror(Mirror.LEFT_RIGHT), 3);
                helper.assertBlockProperty(BASE, ArcadePrizeBlock.FACING,
                    facing.getAxis() == Direction.Axis.Z ? facing.getOpposite() : facing);
                helper.getLevel().destroyBlock(absolute, true, player);
                helper.assertBlockPresent(Blocks.AIR, BASE);
                helper.assertItemEntityCountIs(item, BASE, 4, 1);
                helper.getEntities(EntityType.ITEM, BASE, 4).forEach(ItemEntity::discard);
            }
        }
        helper.succeed();
    }

    @GameTest(template = "nostalgia_test")
    public static void adjacentFiguresRemainIndependentWhenCreativePlayersRemoveEitherOne(GameTestHelper helper) {
        ServerPlayer player = createPlayer(helper, "FigureCreative", GameType.CREATIVE);
        helper.setBlock(BASE.below(), Blocks.STONE);
        helper.setBlock(BASE.east().below(), Blocks.STONE);
        Item miku = JapaneseArcades.HATSUNE_MIKU_FIGURE_ITEM.get();
        Item teto = JapaneseArcades.KASANE_TETO_FIGURE_ITEM.get();
        for (Direction facing : Direction.Plane.HORIZONTAL) {
            helper.assertTrue(place(helper, player, miku, BASE, facing)
                && place(helper, player, teto, BASE.east(), facing), "Adjacent figure placement failed");
            helper.assertTrue(player.getMainHandItem().getCount() == 2, "Creative placement consumed a figure");
            for (BlockPos pos : new BlockPos[]{BASE, BASE.east()}) {
                var absolute = helper.absolutePos(pos);
                var state = helper.getLevel().getBlockState(absolute);
                state.getBlock().playerWillDestroy(helper.getLevel(), absolute, state, player);
                helper.getLevel().destroyBlock(absolute, false, player);
                helper.assertBlockPresent(Blocks.AIR, pos);
                if (pos.equals(BASE)) { helper.assertBlockPresent(JapaneseArcades.KASANE_TETO_FIGURE.get(), BASE.east()); }
            }
            helper.assertTrue(helper.getEntities(EntityType.ITEM, BASE, 4).isEmpty(), "Creative removal duplicated a collectible");
        }
        helper.succeed();
    }
}
