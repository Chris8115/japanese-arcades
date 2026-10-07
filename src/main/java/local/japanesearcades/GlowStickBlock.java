package local.japanesearcades;

import com.mojang.serialization.MapCodec;
import java.util.List;
import javax.annotation.Nullable;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.tags.FluidTags;
import net.minecraft.world.item.context.BlockPlaceContext;
import net.minecraft.world.level.BlockGetter;
import net.minecraft.world.level.LevelAccessor;
import net.minecraft.world.level.LevelReader;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.Mirror;
import net.minecraft.world.level.block.Rotation;
import net.minecraft.world.level.block.SimpleWaterloggedBlock;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.StateDefinition;
import net.minecraft.world.level.block.state.properties.BlockStateProperties;
import net.minecraft.world.level.block.state.properties.BooleanProperty;
import net.minecraft.world.level.block.state.properties.DirectionProperty;
import net.minecraft.world.level.material.FluidState;
import net.minecraft.world.level.material.Fluids;
import net.minecraft.world.phys.shapes.CollisionContext;
import net.minecraft.world.phys.shapes.VoxelShape;

/** A waterproof concert light: ordinary block lighting, without a block entity or ticking animation. */
public final class GlowStickBlock extends Block implements SimpleWaterloggedBlock {
    public static final MapCodec<GlowStickBlock> CODEC = simpleCodec(GlowStickBlock::new);
    public static final List<String> COLORS = List.of("blue", "red", "yellow", "green", "pink", "purple", "orange");
    public static final DirectionProperty FACING = DirectionProperty.create("facing", direction -> direction != Direction.DOWN);
    public static final BooleanProperty WATERLOGGED = BlockStateProperties.WATERLOGGED;
    private static final VoxelShape FLOOR = Block.box(6.5, 0, 6.5, 10.7, 13.5, 9.5);
    private static final VoxelShape NORTH = Block.box(5.3, 1, 8.2, 9.5, 14.5, 16);
    private static final VoxelShape SOUTH = Block.box(6.5, 1, 0, 10.7, 14.5, 7.8);
    private static final VoxelShape WEST = Block.box(8.2, 1, 6.5, 16, 14.5, 10.7);
    private static final VoxelShape EAST = Block.box(0, 1, 5.3, 7.8, 14.5, 9.5);

    public GlowStickBlock(Properties properties) {
        super(properties);
        registerDefaultState(stateDefinition.any().setValue(FACING, Direction.UP).setValue(WATERLOGGED, false));
    }

    @Override protected MapCodec<GlowStickBlock> codec() { return CODEC; }

    @Nullable
    @Override public BlockState getStateForPlacement(BlockPlaceContext context) {
        Direction facing = context.getClickedFace();
        if (facing == Direction.DOWN) { return null; }
        FluidState fluid = context.getLevel().getFluidState(context.getClickedPos());
        if (!fluid.isEmpty() && !fluid.is(FluidTags.WATER)) { return null; }
        BlockState state = defaultBlockState().setValue(FACING, facing).setValue(WATERLOGGED, fluid.is(FluidTags.WATER));
        return state.canSurvive(context.getLevel(), context.getClickedPos()) ? state : null;
    }

    @Override protected boolean canSurvive(BlockState state, LevelReader level, BlockPos pos) {
        Direction facing = state.getValue(FACING);
        BlockPos support = pos.relative(facing.getOpposite());
        return facing == Direction.UP ? Block.canSupportCenter(level, support, Direction.UP)
            : level.getBlockState(support).isFaceSturdy(level, support, facing);
    }

    @Override protected BlockState updateShape(BlockState state, Direction direction, BlockState neighbor,
            LevelAccessor level, BlockPos pos, BlockPos neighborPos) {
        if (state.getValue(WATERLOGGED)) { level.scheduleTick(pos, Fluids.WATER, Fluids.WATER.getTickDelay(level)); }
        if (direction == state.getValue(FACING).getOpposite() && !state.canSurvive(level, pos)) {
            // Air requests the normal destruction path, which drops the item and restores the old state's water.
            return Blocks.AIR.defaultBlockState();
        }
        return super.updateShape(state, direction, neighbor, level, pos, neighborPos);
    }

    @Override protected FluidState getFluidState(BlockState state) {
        return state.getValue(WATERLOGGED) ? Fluids.WATER.getSource(false) : super.getFluidState(state);
    }

    @Override protected VoxelShape getShape(BlockState state, BlockGetter level, BlockPos pos, CollisionContext context) {
        return switch (state.getValue(FACING)) {
            case UP -> FLOOR;
            case NORTH -> NORTH;
            case SOUTH -> SOUTH;
            case WEST -> WEST;
            case EAST -> EAST;
            default -> throw new IllegalStateException("Glow sticks cannot face down");
        };
    }

    @Override protected BlockState rotate(BlockState state, Rotation rotation) {
        return state.setValue(FACING, rotation.rotate(state.getValue(FACING)));
    }

    @Override protected BlockState mirror(BlockState state, Mirror mirror) {
        return state.rotate(mirror.getRotation(state.getValue(FACING)));
    }

    @Override protected void createBlockStateDefinition(StateDefinition.Builder<Block, BlockState> builder) {
        builder.add(FACING, WATERLOGGED);
    }
}
