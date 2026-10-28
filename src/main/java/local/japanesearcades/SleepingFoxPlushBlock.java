package local.japanesearcades;

import com.mojang.serialization.MapCodec;
import javax.annotation.Nullable;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.context.BlockPlaceContext;
import net.minecraft.world.level.BlockGetter;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.LevelAccessor;
import net.minecraft.world.level.LevelReader;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.HorizontalDirectionalBlock;
import net.minecraft.world.level.block.Mirror;
import net.minecraft.world.level.block.Rotation;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.StateDefinition;
import net.minecraft.world.level.block.state.properties.IntegerProperty;
import net.minecraft.world.level.material.PushReaction;
import net.minecraft.world.phys.shapes.BooleanOp;
import net.minecraft.world.phys.shapes.CollisionContext;
import net.minecraft.world.phys.shapes.Shapes;
import net.minecraft.world.phys.shapes.VoxelShape;

/** A static, four-cell cloth prize. No block entity, scheduled tick, or live fox entity. */
public final class SleepingFoxPlushBlock extends HorizontalDirectionalBlock {
    public static final MapCodec<SleepingFoxPlushBlock> CODEC = simpleCodec(SleepingFoxPlushBlock::new);
    public static final IntegerProperty PART = IntegerProperty.create("part", 0, 3);
    public static final int PART_COUNT = 4;
    public static final double MODEL_HEIGHT = 1.01;
    private static final VoxelShape[][] SHAPES = createShapes();

    public SleepingFoxPlushBlock(Properties properties) {
        super(properties);
        registerDefaultState(stateDefinition.any().setValue(FACING, Direction.NORTH).setValue(PART, 0));
    }

    @Override protected MapCodec<SleepingFoxPlushBlock> codec() { return CODEC; }

    /** Front-left anchor, front-right, back-left, back-right; FACING points towards the viewer. */
    public static BlockPos partPosition(BlockPos anchor, Direction facing, int part) {
        return anchor.relative(facing.getClockWise(), part % 2).relative(facing.getOpposite(), part / 2);
    }

    public static BlockPos getAnchor(BlockState state, BlockPos pos) {
        int part = state.getValue(PART);
        Direction facing = state.getValue(FACING);
        return pos.relative(facing.getClockWise(), -(part % 2)).relative(facing.getOpposite(), -(part / 2));
    }

    private boolean matches(BlockState state, Direction facing, int part) {
        return state.is(this) && state.getValue(FACING) == facing && state.getValue(PART) == part;
    }

    @Nullable @Override public BlockState getStateForPlacement(BlockPlaceContext context) {
        Level level = context.getLevel();
        BlockPos anchor = context.getClickedPos();
        Direction facing = context.getHorizontalDirection().getOpposite();
        Player player = context.getPlayer();
        if (anchor.getY() < level.getMinBuildHeight() || anchor.getY() + MODEL_HEIGHT > level.getMaxBuildHeight()
                || player != null && (!player.isAlive() || player.isSpectator())) { return null; }
        CollisionContext collision = player == null ? CollisionContext.empty() : CollisionContext.of(player);
        BlockState base = defaultBlockState().setValue(FACING, facing);
        for (int part = 0; part < PART_COUNT; part++) {
            BlockPos target = partPosition(anchor, facing, part);
            BlockState section = base.setValue(PART, part);
            if (!level.hasChunkAt(target) || !level.getWorldBorder().isWithinBounds(target)
                    || !level.getBlockState(target).canBeReplaced(context) || !section.canSurvive(level, target)
                    || player != null && (!level.mayInteract(player, target)
                        || !player.mayUseItemAt(target, context.getClickedFace(), context.getItemInHand()))
                    || !level.isUnobstructed(section, target, collision)) { return null; }
            // The ears extend 0.01 block above their cells. Do not place them through a ceiling.
            VoxelShape shape = SHAPES[facing.get2DDataValue()][part];
            if (shape.max(Direction.Axis.Y) > 1 && Shapes.joinIsNotEmpty(shape,
                    level.getBlockState(target.above()).getCollisionShape(level, target.above()).move(0, 1, 0), BooleanOp.AND)) {
                return null;
            }
        }
        return base;
    }

    @Override public void setPlacedBy(Level level, BlockPos pos, BlockState state, @Nullable LivingEntity placer, ItemStack stack) {
        Direction facing = state.getValue(FACING);
        // Install the connected structure before neighbor checks can see missing sections.
        for (int part = 1; part < PART_COUNT; part++) {
            level.setBlock(partPosition(pos, facing, part), state.setValue(PART, part), 18);
        }
        notifyParts(level, pos, facing);
    }

    private void notifyParts(Level level, BlockPos anchor, Direction facing) {
        for (int part = 0; part < PART_COUNT; part++) {
            BlockPos target = partPosition(anchor, facing, part);
            level.getBlockState(target).updateNeighbourShapes(level, target, 3);
            level.updateNeighborsAt(target, this);
        }
    }

    @Override protected boolean canSurvive(BlockState state, LevelReader level, BlockPos pos) {
        return level.getBlockState(pos.below()).isFaceSturdy(level, pos.below(), Direction.UP);
    }

    @Override protected BlockState updateShape(BlockState state, Direction direction, BlockState neighbor,
            LevelAccessor level, BlockPos pos, BlockPos neighborPos) {
        if (direction == Direction.DOWN && !state.canSurvive(level, pos)) { return Blocks.AIR.defaultBlockState(); }
        BlockPos anchor = getAnchor(state, pos);
        Direction facing = state.getValue(FACING);
        for (int part = 0; part < PART_COUNT; part++) {
            if (partPosition(anchor, facing, part).equals(neighborPos) && !matches(neighbor, facing, part)) {
                return Blocks.AIR.defaultBlockState();
            }
        }
        return state;
    }

    @Override public BlockState playerWillDestroy(Level level, BlockPos pos, BlockState state, Player player) {
        if (!level.isClientSide && player.hasInfiniteMaterials()) {
            BlockPos anchor = getAnchor(state, pos);
            Direction facing = state.getValue(FACING);
            // Remove the loot-bearing anchor before propagating a creative removal.
            for (int part = 0; part < PART_COUNT; part++) {
                BlockPos target = partPosition(anchor, facing, part);
                if (matches(level.getBlockState(target), facing, part)) { level.setBlock(target, Blocks.AIR.defaultBlockState(), 18); }
            }
            notifyParts(level, anchor, facing);
        }
        return super.playerWillDestroy(level, pos, state, player);
    }

    @Override public PushReaction getPistonPushReaction(BlockState state) { return PushReaction.BLOCK; }
    @Override protected VoxelShape getShape(BlockState state, BlockGetter level, BlockPos pos, CollisionContext context) {
        return SHAPES[state.getValue(FACING).get2DDataValue()][state.getValue(PART)];
    }
    @Override protected BlockState rotate(BlockState state, Rotation rotation) { return state.setValue(FACING, rotation.rotate(state.getValue(FACING))); }
    @Override protected BlockState mirror(BlockState state, Mirror mirror) {
        // Reflection reverses the footprint's across direction as well as its facing.
        return mirror == Mirror.NONE ? state : state.rotate(mirror.getRotation(state.getValue(FACING)))
            .setValue(PART, state.getValue(PART) ^ 1);
    }
    @Override protected void createBlockStateDefinition(StateDefinition.Builder<Block, BlockState> builder) { builder.add(FACING, PART); }

    private static VoxelShape[][] createShapes() {
        // Four head/ear/body/tail proxies, independent of the visual mesh and its texture pixels.
        double[][] boxes = {{.18, .20, .3375, .98, .81, 1.2375},
            {.18, .81, .7375, .98, MODEL_HEIGHT, .8375},
            {.54, 0, 1.0125, 1.80, .645, 1.6625}, {.29, 0, .3875, 1.82, .30, 1.2075}};
        VoxelShape[][] shapes = new VoxelShape[4][PART_COUNT];
        for (Direction facing : Direction.Plane.HORIZONTAL) {
            Direction right = facing.getClockWise(), back = facing.getOpposite();
            for (int part = 0; part < PART_COUNT; part++) {
                int column = part % 2, row = part / 2;
                VoxelShape shape = Shapes.empty();
                for (double[] box : boxes) {
                    double x0 = Math.max(box[0], column) - column, x1 = Math.min(box[3], column + 1) - column;
                    double z0 = Math.max(box[2], row) - row, z1 = Math.min(box[5], row + 1) - row;
                    if (x0 >= x1 || z0 >= z1) { continue; }
                    double ax = .5 + right.getStepX() * (x0 - .5) + back.getStepX() * (z0 - .5);
                    double az = .5 + right.getStepZ() * (x0 - .5) + back.getStepZ() * (z0 - .5);
                    double bx = .5 + right.getStepX() * (x1 - .5) + back.getStepX() * (z1 - .5);
                    double bz = .5 + right.getStepZ() * (x1 - .5) + back.getStepZ() * (z1 - .5);
                    shape = Shapes.or(shape, Shapes.box(Math.min(ax, bx), box[1], Math.min(az, bz),
                        Math.max(ax, bx), box[4], Math.max(az, bz)));
                }
                shapes[facing.get2DDataValue()][part] = shape.optimize();
            }
        }
        return shapes;
    }
}
