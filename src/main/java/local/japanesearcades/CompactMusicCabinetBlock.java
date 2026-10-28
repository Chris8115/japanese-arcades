package local.japanesearcades;

import javax.annotation.Nullable;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.context.BlockPlaceContext;
import net.minecraft.world.level.BlockGetter;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.material.PushReaction;
import net.minecraft.world.phys.shapes.BooleanOp;
import net.minecraft.world.phys.shapes.CollisionContext;
import net.minecraft.world.phys.shapes.Shapes;
import net.minecraft.world.phys.shapes.VoxelShape;

/** Shared cached shapes and complete placement checks for the new one-column cabinets. */
public abstract class CompactMusicCabinetBlock extends NostalgiaCabinetBlock {
    private final VoxelShape[][] shapes = new VoxelShape[3][4];

    protected CompactMusicCabinetBlock(Properties properties, double[][] volumes) {
        super(properties);
        for (Part part : Part.values()) {
            double bottom = part.ordinal() * 16;
            for (Direction facing : Direction.Plane.HORIZONTAL) {
                VoxelShape shape = Shapes.empty();
                for (double[] volume : volumes) {
                    double y0 = Math.max(bottom, volume[1]), y1 = Math.min(bottom + 16, volume[4]);
                    if (y0 < y1) { shape = Shapes.or(shape, box(facing, volume[0], y0 - bottom, volume[2], volume[3], y1 - bottom, volume[5])); }
                }
                shapes[part.ordinal()][facing.get2DDataValue()] = shape.optimize();
            }
        }
    }

    @Nullable @Override public BlockState getStateForPlacement(BlockPlaceContext context) {
        Level level = context.getLevel();
        BlockPos anchor = context.getClickedPos();
        Player player = context.getPlayer();
        if (anchor.getY() < level.getMinBuildHeight() || anchor.getY() + 2 >= level.getMaxBuildHeight()
                || player != null && (!player.isAlive() || player.isSpectator())) { return null; }
        BlockState base = defaultBlockState().setValue(FACING, context.getHorizontalDirection().getOpposite());
        if (!base.canSurvive(level, anchor)) { return null; }
        CollisionContext collision = player == null ? CollisionContext.empty() : CollisionContext.of(player);
        for (Part part : Part.values()) {
            BlockPos target = anchor.above(part.ordinal());
            BlockState section = base.setValue(PART, part);
            if (!level.hasChunkAt(target) || !level.getBlockState(target).canBeReplaced(context)
                    || !level.getWorldBorder().isWithinBounds(target)
                    || player != null && (!level.mayInteract(player, target)
                        || !player.mayUseItemAt(target, context.getClickedFace(), context.getItemInHand()))
                    || !level.isUnobstructed(section, target, collision)) { return null; }
            VoxelShape shape = shapes[part.ordinal()][base.getValue(FACING).get2DDataValue()];
            var bounds = shape.bounds().move(target);
            var border = level.getWorldBorder();
            if (bounds.minX < border.getMinX() || bounds.maxX > border.getMaxX()
                    || bounds.minZ < border.getMinZ() || bounds.maxZ > border.getMaxZ()) { return null; }
            // Guitar controllers can project slightly beyond the central cell. Respect nearby solid blocks.
            for (int x = -1; x <= 1; x++) for (int z = -1; z <= 1; z++) {
                if (x == 0 && z == 0) { continue; }
                BlockPos neighbor = target.offset(x, 0, z);
                if (!level.hasChunkAt(neighbor) || Shapes.joinIsNotEmpty(shape,
                        level.getBlockState(neighbor).getCollisionShape(level, neighbor).move(x, 0, z), BooleanOp.AND)) {
                    return null;
                }
            }
        }
        return base;
    }

    @Override protected VoxelShape getShape(BlockState state, BlockGetter level, BlockPos pos, CollisionContext context) {
        return shapes[state.getValue(PART).ordinal()][state.getValue(FACING).get2DDataValue()];
    }
    @Override public PushReaction getPistonPushReaction(BlockState state) { return PushReaction.BLOCK; }

    @Override public BlockState playerWillDestroy(Level level, BlockPos pos, BlockState state, Player player) {
        if (!level.isClientSide && player.hasInfiniteMaterials()) {
            BlockPos anchor = basePosition(pos, state);
            Direction facing = state.getValue(FACING);
            // Clear the complete column before publishing shape changes. Removing an upper
            // sibling first would make the still-present base drop through support teardown.
            for (Part part : Part.values()) {
                BlockPos target = anchor.above(part.ordinal());
                BlockState current = level.getBlockState(target);
                if (current.is(this) && current.getValue(FACING) == facing && current.getValue(PART) == part) {
                    level.setBlock(target, Blocks.AIR.defaultBlockState(), 18);
                }
            }
            for (Part part : Part.values()) {
                BlockPos target = anchor.above(part.ordinal());
                level.getBlockState(target).updateNeighbourShapes(level, target, 3);
                level.updateNeighborsAt(target, this);
            }
        }
        return super.playerWillDestroy(level, pos, state, player);
    }

    static VoxelShape box(Direction facing, double x0, double y0, double z0, double x1, double y1, double z1) {
        return switch (facing) {
            case EAST -> net.minecraft.world.level.block.Block.box(16-z1, y0, x0, 16-z0, y1, x1);
            case SOUTH -> net.minecraft.world.level.block.Block.box(16-x1, y0, 16-z1, 16-x0, y1, 16-z0);
            case WEST -> net.minecraft.world.level.block.Block.box(z0, y0, 16-x1, z1, y1, 16-x0);
            default -> net.minecraft.world.level.block.Block.box(x0, y0, z0, x1, y1, z1);
        };
    }
}
