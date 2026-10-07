package local.japanesearcades;

import com.mojang.serialization.MapCodec;
import javax.annotation.Nullable;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.util.StringRepresentable;
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
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.entity.BlockEntityTicker;
import net.minecraft.world.level.block.entity.BlockEntityType;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.StateDefinition;
import net.minecraft.world.level.block.state.properties.EnumProperty;
import net.minecraft.world.phys.Vec3;
import net.minecraft.world.phys.shapes.CollisionContext;
import net.minecraft.world.phys.shapes.Shapes;
import net.minecraft.world.phys.shapes.VoxelShape;

/** One connected two-column, three-row cabinet with a single primary-base jukebox. */
public final class MaimaiCabinetBlock extends NostalgiaCabinetBlock {
    public static final MapCodec<MaimaiCabinetBlock> CODEC = simpleCodec(MaimaiCabinetBlock::new);
    public static final EnumProperty<Side> SIDE = EnumProperty.create("side", Side.class);

    public MaimaiCabinetBlock(Properties properties) {
        super(properties);
        registerDefaultState(defaultBlockState().setValue(SIDE, Side.PRIMARY));
    }

    @Override
    protected MapCodec<? extends HorizontalDirectionalBlock> codec() { return CODEC; }

    static BlockPos sectionPosition(BlockPos anchor, Direction facing, Side side, Part part) {
        return anchor.relative(facing.getClockWise(), side.ordinal()).above(part.ordinal());
    }

    private boolean matchesSection(BlockState state, Direction facing, Side side, Part part) {
        return state.is(this) && state.getValue(FACING) == facing
            && state.getValue(SIDE) == side && state.getValue(PART) == part;
    }

    @Override
    protected BlockPos basePosition(BlockPos pos, BlockState state) {
        return pos.below(state.getValue(PART).ordinal())
            .relative(state.getValue(FACING).getClockWise(), -state.getValue(SIDE).ordinal());
    }

    @Nullable
    @Override
    public BlockState getStateForPlacement(BlockPlaceContext context) {
        BlockPos anchor = context.getClickedPos();
        Level level = context.getLevel();
        Direction facing = context.getHorizontalDirection().getOpposite();
        if (anchor.getY()+2 >= level.getMaxBuildHeight()) { return null; }
        for (Side side : Side.values()) {
            BlockPos base = sectionPosition(anchor, facing, side, Part.BASE);
            if (!level.getBlockState(base.below()).isFaceSturdy(level, base.below(), Direction.UP)) {
                return null;
            }
            for (Part part : Part.values()) {
                BlockPos target = sectionPosition(anchor, facing, side, part);
                if (!level.getWorldBorder().isWithinBounds(target)
                        || !level.getBlockState(target).canBeReplaced(context)) { return null; }
            }
        }
        return defaultBlockState().setValue(FACING, facing);
    }

    @Override
    public void setPlacedBy(Level level, BlockPos pos, BlockState state, @Nullable LivingEntity placer, ItemStack stack) {
        Direction facing = state.getValue(FACING);
        // Assemble all six cells before sending shape updates across their connections.
        for (Side side : Side.values()) {
            for (Part part : Part.values()) {
                if (side == Side.PRIMARY && part == Part.BASE) { continue; }
                level.setBlock(sectionPosition(pos, facing, side, part),
                    state.setValue(SIDE, side).setValue(PART, part).setValue(HAS_RECORD, false), 18);
            }
        }
        if (level.getBlockEntity(pos) instanceof NostalgiaJukeboxBlockEntity cabinet && !cabinet.isEmpty()) {
            level.setBlock(pos, state.setValue(HAS_RECORD, true), 18);
        }
        notifySectionNeighbors(level, pos, facing);
    }

    private void notifySectionNeighbors(Level level, BlockPos anchor, Direction facing) {
        for (Side side : Side.values()) {
            for (Part part : Part.values()) {
                BlockPos target = sectionPosition(anchor, facing, side, part);
                level.getBlockState(target).updateNeighbourShapes(level, target, 3);
                level.updateNeighborsAt(target, this);
            }
        }
    }

    @Override
    protected boolean canSurvive(BlockState state, LevelReader level, BlockPos pos) {
        Part part = state.getValue(PART);
        return part == Part.BASE
            ? level.getBlockState(pos.below()).isFaceSturdy(level, pos.below(), Direction.UP)
            : matchesSection(level.getBlockState(pos.below()), state.getValue(FACING), state.getValue(SIDE), part.below());
    }

    @Override
    protected BlockState updateShape(BlockState state, Direction direction, BlockState neighbor,
            LevelAccessor level, BlockPos pos, BlockPos neighborPos) {
        Direction facing = state.getValue(FACING);
        Side side = state.getValue(SIDE);
        Part part = state.getValue(PART);
        Direction partner = side == Side.PRIMARY ? facing.getClockWise() : facing.getCounterClockWise();
        if (direction == partner && !matchesSection(neighbor, facing, side.other(), part)) {
            return Blocks.AIR.defaultBlockState();
        }
        if (direction == Direction.DOWN && !canSurvive(state, level, pos)) {
            return Blocks.AIR.defaultBlockState();
        }
        if (direction == Direction.UP && part != Part.MARQUEE
                && !matchesSection(neighbor, facing, side, part.above())) {
            return Blocks.AIR.defaultBlockState();
        }
        return state;
    }

    @Override
    public BlockState playerWillDestroy(Level level, BlockPos pos, BlockState state, Player player) {
        if (!level.isClientSide && player.isCreative()) {
            BlockPos anchor = basePosition(pos, state);
            Direction facing = state.getValue(FACING);
            // Remove the primary inventory first without loot, then the other cells.
            // Shape propagation resumes only after the complete six-cell cabinet is gone.
            for (Side side : Side.values()) {
                for (Part part : Part.values()) {
                    BlockPos target = sectionPosition(anchor, facing, side, part);
                    if (matchesSection(level.getBlockState(target), facing, side, part)) {
                        level.setBlock(target, Blocks.AIR.defaultBlockState(), 18);
                    }
                }
            }
            notifySectionNeighbors(level, anchor, facing);
        }
        return super.playerWillDestroy(level, pos, state, player);
    }

    private boolean isAnchor(BlockState state) {
        return state.getValue(PART) == Part.BASE && state.getValue(SIDE) == Side.PRIMARY;
    }

    @Nullable
    @Override
    public BlockEntity newBlockEntity(BlockPos pos, BlockState state) {
        return isAnchor(state) ? super.newBlockEntity(pos, state) : null;
    }

    @Nullable
    @Override
    public <T extends BlockEntity> BlockEntityTicker<T> getTicker(Level level, BlockState state, BlockEntityType<T> type) {
        return isAnchor(state) ? super.getTicker(level, state, type) : null;
    }

    @Override
    public boolean isSignalSource(BlockState state) { return isAnchor(state); }

    @Override
    protected boolean hasAnalogOutputSignal(BlockState state) { return isAnchor(state); }

    @Override
    protected Vec3 discEjectionPosition(BlockPos pos, BlockState state) {
        Direction front = state.getValue(FACING);
        Direction across = front.getClockWise();
        return Vec3.atCenterOf(pos).add(across.getStepX()*.5 + front.getStepX(), .35,
            across.getStepZ()*.5 + front.getStepZ());
    }

    @Override
    protected VoxelShape getShape(BlockState state, BlockGetter level, BlockPos pos, CollisionContext context) {
        Direction facing = state.getValue(FACING);
        boolean primary = state.getValue(SIDE) == Side.PRIMARY;
        Part part = state.getValue(PART);
        double overhang = switch (part) { case BASE -> 3.2; case CONSOLE -> 2.6; case MARQUEE -> 3.7; };
        double front = switch (part) { case BASE -> -1.0; case CONSOLE -> -1.15; case MARQUEE -> -1.4; };
        VoxelShape body = rotatedBox(facing, primary ? -overhang : 0, front,
            primary ? 16 : 16+overhang, 15.6);
        if (part != Part.BASE) { return body; }
        double x0 = primary ? -3.3 : 0;
        double x1 = primary ? 16 : 19.3;
        VoxelShape floor = switch (facing) {
            case EAST -> Block.box(16, 0, x0, 29.1, .35, x1);
            case SOUTH -> Block.box(16-x1, 0, 16, 16-x0, .35, 29.1);
            case WEST -> Block.box(-13.1, 0, 16-x1, 0, .35, 16-x0);
            default -> Block.box(x0, 0, -13.1, x1, .35, 0);
        };
        return Shapes.or(body, floor);
    }

    @Override
    protected void createBlockStateDefinition(StateDefinition.Builder<Block, BlockState> builder) {
        super.createBlockStateDefinition(builder);
        builder.add(SIDE);
    }

    public enum Side implements StringRepresentable {
        PRIMARY, SECONDARY;

        Side other() { return this == PRIMARY ? SECONDARY : PRIMARY; }

        @Override
        public String getSerializedName() { return name().toLowerCase(java.util.Locale.ROOT); }
    }
}
