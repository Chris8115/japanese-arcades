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

/** Connected twin cabinet, four standable stage cells, and two open rail cells. */
public final class DdrCabinetBlock extends NostalgiaCabinetBlock {
    public static final MapCodec<DdrCabinetBlock> CODEC = simpleCodec(DdrCabinetBlock::new);
    public static final EnumProperty<Side> SIDE = EnumProperty.create("side", Side.class);
    public static final EnumProperty<Section> SECTION = EnumProperty.create("section", Section.class);
    static final double STAGE_HEIGHT = 2.4 / 16.0;

    public DdrCabinetBlock(Properties properties) {
        super(properties);
        registerDefaultState(defaultBlockState().setValue(SIDE, Side.PRIMARY)
            .setValue(SECTION, Section.CABINET_BASE));
    }

    @Override
    protected MapCodec<? extends HorizontalDirectionalBlock> codec() { return CODEC; }

    static BlockPos sectionPosition(BlockPos anchor, Direction facing, Side side, Section section) {
        return anchor.relative(facing.getClockWise(), side.ordinal())
            .relative(facing, section.depth).above(section.height);
    }

    private boolean matches(BlockState state, Direction facing, Side side, Section section) {
        return state.is(this) && state.getValue(FACING) == facing
            && state.getValue(SIDE) == side && state.getValue(SECTION) == section;
    }

    @Override
    protected BlockPos basePosition(BlockPos pos, BlockState state) {
        Section section = state.getValue(SECTION);
        Direction facing = state.getValue(FACING);
        return pos.below(section.height).relative(facing, -section.depth)
            .relative(facing.getClockWise(), -state.getValue(SIDE).ordinal());
    }

    @Nullable
    @Override
    public BlockState getStateForPlacement(BlockPlaceContext context) {
        BlockPos anchor = context.getClickedPos();
        Level level = context.getLevel();
        Direction facing = context.getHorizontalDirection().getOpposite();
        if (anchor.getY()+2 >= level.getMaxBuildHeight()) { return null; }
        for (Side side : Side.values()) {
            for (int depth=0; depth<3; depth++) {
                BlockPos floor = anchor.relative(facing.getClockWise(), side.ordinal()).relative(facing, depth).below();
                if (!level.getBlockState(floor).isFaceSturdy(level, floor, Direction.UP)) { return null; }
            }
            for (Section section : Section.values()) {
                BlockPos target = sectionPosition(anchor, facing, side, section);
                if (!level.getWorldBorder().isWithinBounds(target)
                        || !level.getBlockState(target).canBeReplaced(context)) { return null; }
            }
        }
        return defaultBlockState().setValue(FACING, facing);
    }

    @Override
    public void setPlacedBy(Level level, BlockPos pos, BlockState state, @Nullable LivingEntity placer, ItemStack stack) {
        Direction facing = state.getValue(FACING);
        for (Side side : Side.values()) {
            for (Section section : Section.values()) {
                if (side == Side.PRIMARY && section == Section.CABINET_BASE) { continue; }
                level.setBlock(sectionPosition(pos, facing, side, section), state.setValue(SIDE, side)
                    .setValue(SECTION, section).setValue(PART, Part.values()[section.height]).setValue(HAS_RECORD, false), 18);
            }
        }
        if (level.getBlockEntity(pos) instanceof NostalgiaJukeboxBlockEntity cabinet && !cabinet.isEmpty()) {
            level.setBlock(pos, state.setValue(HAS_RECORD, true), 18);
        }
        notifySections(level, pos, facing);
    }

    private void notifySections(Level level, BlockPos anchor, Direction facing) {
        for (Side side : Side.values()) {
            for (Section section : Section.values()) {
                BlockPos target = sectionPosition(anchor, facing, side, section);
                level.getBlockState(target).updateNeighbourShapes(level, target, 3);
                level.updateNeighborsAt(target, this);
            }
        }
    }

    @Override
    protected boolean canSurvive(BlockState state, LevelReader level, BlockPos pos) {
        Section section = state.getValue(SECTION);
        if (section.height == 0) {
            return level.getBlockState(pos.below()).isFaceSturdy(level, pos.below(), Direction.UP);
        }
        Section below = section == Section.RAIL ? Section.STAGE_FRONT
            : section == Section.CABINET_MARQUEE ? Section.CABINET_CONSOLE : Section.CABINET_BASE;
        return matches(level.getBlockState(pos.below()), state.getValue(FACING), state.getValue(SIDE), below);
    }

    @Override
    protected BlockState updateShape(BlockState state, Direction direction, BlockState neighbor,
            LevelAccessor level, BlockPos pos, BlockPos neighborPos) {
        if (direction == Direction.DOWN && !canSurvive(state, level, pos)) {
            return Blocks.AIR.defaultBlockState();
        }
        Direction facing = state.getValue(FACING);
        BlockPos anchor = basePosition(pos, state);
        // Every physically adjacent occupied cell is an edge in the structure's graph.
        for (Side side : Side.values()) {
            for (Section section : Section.values()) {
                if (sectionPosition(anchor, facing, side, section).equals(neighborPos)
                        && !matches(neighbor, facing, side, section)) { return Blocks.AIR.defaultBlockState(); }
            }
        }
        return state;
    }

    @Override
    public BlockState playerWillDestroy(Level level, BlockPos pos, BlockState state, Player player) {
        if (!level.isClientSide && player.isCreative()) {
            BlockPos anchor = basePosition(pos, state);
            Direction facing = state.getValue(FACING);
            // Clear the saved inventory first, then the whole matched structure before propagation.
            for (Side side : Side.values()) {
                for (Section section : Section.values()) {
                    BlockPos target = sectionPosition(anchor, facing, side, section);
                    if (matches(level.getBlockState(target), facing, side, section)) {
                        level.setBlock(target, Blocks.AIR.defaultBlockState(), 18);
                    }
                }
            }
            notifySections(level, anchor, facing);
        }
        return super.playerWillDestroy(level, pos, state, player);
    }

    private boolean isAnchor(BlockState state) {
        return state.getValue(SECTION) == Section.CABINET_BASE && state.getValue(SIDE) == Side.PRIMARY;
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
        return Vec3.atCenterOf(pos).add(across.getStepX()*.5 + front.getStepX()*1.1, .35,
            across.getStepZ()*.5 + front.getStepZ()*1.1);
    }

    private static VoxelShape box(Direction facing, double x0, double y0, double z0,
            double x1, double y1, double z1) {
        return switch (facing) {
            case EAST -> Block.box(16-z1, y0, x0, 16-z0, y1, x1);
            case SOUTH -> Block.box(16-x1, y0, 16-z1, 16-x0, y1, 16-z0);
            case WEST -> Block.box(z0, y0, 16-x1, z1, y1, 16-x0);
            default -> Block.box(x0, y0, z0, x1, y1, z1);
        };
    }

    private static VoxelShape cabinetBox(Direction facing, boolean primary, double x0, double y0,
            double z0, double x1, double y1, double z1) {
        x0 = 16 + .78*(x0-16);
        x1 = 16 + .78*(x1-16);
        double offset = primary ? 0 : 16;
        return box(facing, Math.max(x0, primary ? x0 : 16)-offset, y0, z0,
            Math.min(x1, primary ? 16 : x1)-offset, y1, z1);
    }

    @Override
    protected VoxelShape getShape(BlockState state, BlockGetter level, BlockPos pos, CollisionContext context) {
        Direction facing = state.getValue(FACING);
        boolean primary = state.getValue(SIDE) == Side.PRIMARY;
        Section section = state.getValue(SECTION);
        double x0 = primary ? -3.1 : 0, x1 = primary ? 16 : 19.1;
        if (section == Section.CABINET_BASE) {
            return Shapes.or(cabinetBox(facing, primary, -.6, 0, -.3, 32.6, 16, 15.5),
                cabinetBox(facing, primary, 15.7, 1.25, -3.35, 16.3, 2.55, .1));
        }
        if (section == Section.CABINET_CONSOLE) {
            return Shapes.or(cabinetBox(facing, primary, -.7, 0, -.4, 32.7, 1.8, 15.5),
                cabinetBox(facing, primary, 4.4, 1.8, -.4, 27.6, 16, 13.8));
        }
        if (section == Section.CABINET_MARQUEE) {
            double supportX = primary ? 8.2 : 22.5;
            return Shapes.or(cabinetBox(facing, primary, 4.4, 0, 2.6, 27.6, 1.8, 12),
                cabinetBox(facing, primary, supportX, 0, 7.1, supportX+1.3, 3.1, 8.9),
                cabinetBox(facing, primary, 4.6, 2.1, 5.85, 27.4, 16, 9.9),
                cabinetBox(facing, primary, -.5, 4, 5.85, 32.5, 14, 10.7));
        }
        VoxelShape floor = section == Section.RAIL ? Shapes.empty()
            : box(facing, x0, 0, section == Section.STAGE_FRONT ? 1.85 : 0, x1, 2.4,
                section == Section.STAGE_REAR ? 13 : 16);
        if (section == Section.STAGE_REAR) { return floor; }
        double center = primary ? 7.1 : 8.9;
        double postA = center-5.8, postB = center+5.8;
        double bottom = section == Section.RAIL ? 0 : 2.4;
        double top = section == Section.RAIL ? 2.5 : 16;
        VoxelShape posts = Shapes.or(box(facing, postA-.4, bottom, 4.1, postA+.4, top, 4.9),
            box(facing, postB-.4, bottom, 4.1, postB+.4, top, 4.9));
        if (section == Section.RAIL) {
            VoxelShape grip = Shapes.or(posts, box(facing, center-4.2, 3.7, 4.1, center+4.2, 4.5, 4.9));
            for (int shoulder : new int[]{-1, 1}) {
                for (int step=0; step<4; step++) {
                    double a=step*Math.PI/8, b=(step+1)*Math.PI/8;
                    double xa=center+shoulder*(4.2+1.6*Math.cos(a));
                    double xb=center+shoulder*(4.2+1.6*Math.cos(b));
                    grip=Shapes.or(grip, box(facing, Math.min(xa,xb)-.4, 2.5+1.6*Math.sin(a)-.4,
                        4.1, Math.max(xa,xb)+.4, 2.5+1.6*Math.sin(b)+.4, 4.9));
                }
            }
            return grip;
        }
        VoxelShape stage = Shapes.or(floor, posts,
            box(facing, postA-.73, 2.4, 3.77, postA+.73, 2.82, 5.23),
            box(facing, postB-.73, 2.4, 3.77, postB+.73, 2.82, 5.23));
        double rampX0=primary ? -1.36 : 13.17, rampX1=primary ? 2.83 : 17.36;
        for (int step=0; step<4; step++) {
            double z0=step*2.3/4, z1=(step+1)*2.3/4;
            stage=Shapes.or(stage, box(facing, rampX0, 0, z0, rampX1, .28+2.085*z1/2.3, z1));
        }
        return stage;
    }

    @Override
    protected void createBlockStateDefinition(StateDefinition.Builder<Block, BlockState> builder) {
        super.createBlockStateDefinition(builder);
        builder.add(SIDE, SECTION);
    }

    public enum Side implements StringRepresentable {
        PRIMARY, SECONDARY;
        @Override
        public String getSerializedName() { return name().toLowerCase(java.util.Locale.ROOT); }
    }

    public enum Section implements StringRepresentable {
        CABINET_BASE(0,0), CABINET_CONSOLE(0,1), CABINET_MARQUEE(0,2),
        STAGE_REAR(1,0), STAGE_FRONT(2,0), RAIL(2,1);
        final int depth, height;
        Section(int depth, int height) { this.depth=depth; this.height=height; }
        @Override
        public String getSerializedName() { return name().toLowerCase(java.util.Locale.ROOT); }
    }
}
