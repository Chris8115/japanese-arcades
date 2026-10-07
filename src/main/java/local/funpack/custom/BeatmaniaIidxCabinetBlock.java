package local.funpack.custom;

import com.mojang.serialization.MapCodec;
import java.util.EnumMap;
import java.util.Map;
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

/** Two cabinet columns and two low standing-platform cells share one saved jukebox. */
public final class BeatmaniaIidxCabinetBlock extends NostalgiaCabinetBlock {
    public static final MapCodec<BeatmaniaIidxCabinetBlock> CODEC = simpleCodec(BeatmaniaIidxCabinetBlock::new);
    public static final EnumProperty<Side> SIDE = EnumProperty.create("side", Side.class);
    public static final EnumProperty<Section> SECTION = EnumProperty.create("section", Section.class);
    static final double PLATFORM_HEIGHT = 1.1 / 16.0;
    private static final Map<Section, Map<Side, Map<Direction, VoxelShape>>> SHAPES = createShapes();

    public BeatmaniaIidxCabinetBlock(Properties properties) {
        super(properties);
        registerDefaultState(defaultBlockState().setValue(SIDE, Side.PRIMARY).setValue(SECTION, Section.CABINET_BASE));
    }

    @Override
    protected MapCodec<? extends HorizontalDirectionalBlock> codec() { return CODEC; }

    public static BlockPos sectionPosition(BlockPos anchor, Direction facing, Side side, Section section) {
        return anchor.relative(facing.getClockWise(), side.ordinal()).relative(facing, section.depth).above(section.height);
    }

    /** Convert model units to world coordinates, including the floor in front of the anchor. */
    public static Vec3 localToWorld(BlockPos anchor, Direction facing, double x, double y, double z) {
        Direction across = facing.getClockWise();
        return Vec3.atCenterOf(anchor).add(across.getStepX() * (x / 16 - .5) + facing.getStepX() * (.5 - z / 16),
            y / 16 - .5, across.getStepZ() * (x / 16 - .5) + facing.getStepZ() * (.5 - z / 16));
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
        Level level = context.getLevel();
        BlockPos anchor = context.getClickedPos();
        Direction facing = context.getHorizontalDirection().getOpposite();
        if (anchor.getY() < level.getMinBuildHeight() || anchor.getY() + 2 >= level.getMaxBuildHeight()) { return null; }
        CollisionContext collision = context.getPlayer() == null ? CollisionContext.empty() : CollisionContext.of(context.getPlayer());
        BlockState base = defaultBlockState().setValue(FACING, facing);
        for (Side side : Side.values()) {
            for (Section section : Section.values()) {
                BlockPos target = sectionPosition(anchor, facing, side, section);
                if (!level.getWorldBorder().isWithinBounds(target) || !level.getBlockState(target).canBeReplaced(context)) { return null; }
                if (section.height == 0 && !level.getBlockState(target.below()).isFaceSturdy(level, target.below(), Direction.UP)) { return null; }
                if (!level.isUnobstructed(sectionState(base, side, section), target, collision)) { return null; }
            }
        }
        return base;
    }

    private static BlockState sectionState(BlockState base, Side side, Section section) {
        return base.setValue(SIDE, side).setValue(SECTION, section)
            .setValue(PART, Part.values()[section.height]).setValue(HAS_RECORD, false);
    }

    @Override
    public void setPlacedBy(Level level, BlockPos pos, BlockState state, @Nullable LivingEntity placer, ItemStack stack) {
        Direction facing = state.getValue(FACING);
        // Assemble the complete footprint before propagating structure checks.
        for (Side side : Side.values()) {
            for (Section section : Section.values()) {
                if (side != Side.PRIMARY || section != Section.CABINET_BASE) {
                    level.setBlock(sectionPosition(pos, facing, side, section), sectionState(state, side, section), 18);
                }
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
        if (section.height == 0) { return level.getBlockState(pos.below()).isFaceSturdy(level, pos.below(), Direction.UP); }
        Section below = section == Section.CABINET_MARQUEE ? Section.CABINET_CONSOLE : Section.CABINET_BASE;
        return matches(level.getBlockState(pos.below()), state.getValue(FACING), state.getValue(SIDE), below);
    }

    @Override
    protected BlockState updateShape(BlockState state, Direction direction, BlockState neighbor,
            LevelAccessor level, BlockPos pos, BlockPos neighborPos) {
        if (direction == Direction.DOWN && !canSurvive(state, level, pos)) { return Blocks.AIR.defaultBlockState(); }
        Direction facing = state.getValue(FACING);
        BlockPos anchor = basePosition(pos, state);
        // Connections include the low front row, but never claim the air above it.
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
            // Remove the anchor first, ejecting its disc once; suppress cabinet loot
            // until all matched cells are gone so neighboring cabinets remain intact.
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

    private static boolean isAnchor(BlockState state) {
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
        return localToWorld(pos, state.getValue(FACING), 16, 6, -9);
    }

    @Override
    protected VoxelShape getShape(BlockState state, BlockGetter level, BlockPos pos, CollisionContext context) {
        return SHAPES.get(state.getValue(SECTION)).get(state.getValue(SIDE)).get(state.getValue(FACING));
    }

    private static Map<Section, Map<Side, Map<Direction, VoxelShape>>> createShapes() {
        double[][] cabinet = {
            {0, 0, 0, 32, 1.13, 15.75},
            // Pedestal, separate lower legs and recessed woofer chambers.
            {10.13, 1.1, .82, 21.88, 18.02, 14.72},
            {1.12, 1.12, .05, 5.58, 17.96, 13.76},
            {26.42, 1.12, .05, 30.88, 17.96, 13.76},
            {5.58, 3.4, 3.95, 10.48, 17.55, 12.82},
            {21.52, 3.4, 3.95, 26.42, 17.55, 12.82},
            // Broad controls, sloped touchscreen and setback landscape monitor.
            {.32, 16.96, -3.69, 31.68, 19.71, 9.51},
            {5.57, 19.12, 4.9, 26.43, 25.05, 10.12},
            {4.32, 24.45, 8.148, 27.68, 38.12, 11.26},
            {3.16, 17.6, 11.05, 28.84, 38.03, 15.238},
            {3.16, 38.03, 14.82, 28.84, 44, 15.18},
            {1.94, 17.72, 13.79, 3.28, 44.77, 15.21},
            {28.72, 17.72, 13.79, 30.06, 44.77, 15.21},
            {1.46, 20.8, 12.95, 4.34, 44.7, 13.15},
            {27.66, 20.8, 12.95, 30.54, 44.7, 13.15},
            // Four speaker boxes, their slim mounts, and the two printed banners.
            {1.045, 29.905, 7.944, 4.355, 34.415, 10.64},
            {27.645, 29.905, 7.944, 30.955, 34.415, 10.64},
            {8.28, 39.16, 7.994, 11.8, 41.94, 10.69},
            {20.2, 39.16, 7.994, 23.72, 41.94, 10.69},
            {9.85, 41.94, 9.06, 10.23, 44.24, 9.51},
            {21.77, 41.94, 9.06, 22.15, 44.24, 9.51},
            {1.46, 37.12, 9.044, 4.34, 44.77, 9.19},
            {27.66, 37.12, 9.044, 30.54, 44.77, 9.19},
            // Three coarse slices follow each leaning pillar without filling the open frame.
            {.86, 19.2, 3.06, 3.47, 32, 9.11},
            {28.53, 19.2, 3.06, 31.14, 32, 9.11},
            {.86, 32, .87, 3.47, 38, 4.438},
            {28.53, 32, .87, 31.14, 38, 4.438},
            {.86, 38, -1.286, 3.47, 44.09, 2.248},
            {28.53, 38, -1.286, 31.14, 44.09, 2.248},
            {1.89, 41.92, .29, 3.04, 44.44, 6.58},
            {28.96, 41.92, .29, 30.11, 44.44, 6.58},
            {.87, 42.99, 4.93, 31.13, 47.85, 14.96}
        };
        Map<Section, Map<Side, Map<Direction, VoxelShape>>> shapes = new EnumMap<>(Section.class);
        for (Section section : Section.values()) {
            Map<Side, Map<Direction, VoxelShape>> sides = new EnumMap<>(Side.class);
            for (Side side : Side.values()) {
                Map<Direction, VoxelShape> rotations = new EnumMap<>(Direction.class);
                double left = side.ordinal() * 16, bottom = section.height * 16;
                for (Direction facing : Direction.Plane.HORIZONTAL) {
                    VoxelShape shape = Shapes.empty();
                    if (section == Section.PLATFORM) {
                        shape = box(facing, 0, 0, 0, 16, PLATFORM_HEIGHT * 16, 16);
                    } else {
                        for (double[] volume : cabinet) {
                            double x1 = Math.max(left, volume[0]), x2 = Math.min(left + 16, volume[3]);
                            double y1 = Math.max(bottom, volume[1]), y2 = Math.min(bottom + 16, volume[4]);
                            if (x2 > x1 && y2 > y1) {
                                shape = Shapes.or(shape, box(facing, x1 - left, y1 - bottom, volume[2],
                                    x2 - left, y2 - bottom, volume[5]));
                            }
                        }
                    }
                    rotations.put(facing, shape.optimize());
                }
                sides.put(side, rotations);
            }
            shapes.put(section, sides);
        }
        return shapes;
    }

    private static VoxelShape box(Direction facing, double x1, double y1, double z1,
            double x2, double y2, double z2) {
        return switch (facing) {
            case EAST -> Block.box(16-z2, y1, x1, 16-z1, y2, x2);
            case SOUTH -> Block.box(16-x2, y1, 16-z2, 16-x1, y2, 16-z1);
            case WEST -> Block.box(z1, y1, 16-x2, z2, y2, 16-x1);
            default -> Block.box(x1, y1, z1, x2, y2, z2);
        };
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
        CABINET_BASE(0, 0), CABINET_CONSOLE(0, 1), CABINET_MARQUEE(0, 2), PLATFORM(1, 0);
        final int depth, height;
        Section(int depth, int height) { this.depth = depth; this.height = height; }
        @Override
        public String getSerializedName() { return name().toLowerCase(java.util.Locale.ROOT); }
    }
}
