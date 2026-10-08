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

/** Connected lantern cabinet and two playable drums on a two-by-two footprint. */
public final class TaikoCabinetBlock extends NostalgiaCabinetBlock {
    public static final MapCodec<TaikoCabinetBlock> CODEC = simpleCodec(TaikoCabinetBlock::new);
    public static final EnumProperty<Side> SIDE = EnumProperty.create("side", Side.class);
    public static final EnumProperty<Section> SECTION = EnumProperty.create("section", Section.class);

    public TaikoCabinetBlock(Properties properties) {
        super(properties);
        registerDefaultState(defaultBlockState().setValue(SIDE, Side.PRIMARY)
            .setValue(SECTION, Section.REAR_BASE));
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
            for (int depth=0; depth<2; depth++) {
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
                if (side == Side.PRIMARY && section == Section.REAR_BASE) { continue; }
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
        Section below = section == Section.DRUMS ? Section.DRUM_BASE
            : section == Section.REAR_MARQUEE ? Section.REAR_CONSOLE : Section.REAR_BASE;
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
        return state.getValue(SECTION) == Section.REAR_BASE && state.getValue(SIDE) == Side.PRIMARY;
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
        // Eject beyond the front plinth, leaving both drum pedestals unobstructed.
        Direction front = state.getValue(FACING);
        Direction across = front.getClockWise();
        return Vec3.atCenterOf(pos).add(across.getStepX()*.5 + front.getStepX()*1.9, .4,
            across.getStepZ()*.5 + front.getStepZ()*1.9);
    }

    @Override
    protected net.minecraft.world.ItemInteractionResult useItemOn(ItemStack stack, BlockState state, Level level,
            BlockPos pos, Player player, net.minecraft.world.InteractionHand hand, net.minecraft.world.phys.BlockHitResult hit) {
        if (state.getValue(SECTION).depth == 0) { return super.useItemOn(stack, state, level, pos, player, hand, hit); }
        if (!player.isShiftKeyDown() && hand == net.minecraft.world.InteractionHand.MAIN_HAND
                && TaikoDrumInteraction.tryHit(player, pos)) {
            return net.minecraft.world.ItemInteractionResult.sidedSuccess(level.isClientSide);
        }
        return net.minecraft.world.ItemInteractionResult.SKIP_DEFAULT_BLOCK_INTERACTION;
    }

    @Override
    protected net.minecraft.world.InteractionResult useWithoutItem(BlockState state, Level level,
            BlockPos pos, Player player, net.minecraft.world.phys.BlockHitResult hit) {
        if (state.getValue(SECTION).depth == 0) { return super.useWithoutItem(state, level, pos, player, hit); }
        if (!player.isShiftKeyDown() && TaikoDrumInteraction.tryHit(player, pos)) {
            return net.minecraft.world.InteractionResult.sidedSuccess(level.isClientSide);
        }
        return net.minecraft.world.InteractionResult.PASS;
    }

    private final java.util.Map<Integer, VoxelShape> shapeCache = new java.util.HashMap<>();

    private static VoxelShape box(Direction facing, double x0, double y0, double z0,
            double x1, double y1, double z1) {
        return switch (facing) {
            case EAST -> Block.box(16-z1, y0, x0, 16-z0, y1, x1);
            case SOUTH -> Block.box(16-x1, y0, 16-z1, 16-x0, y1, 16-z0);
            case WEST -> Block.box(z0, y0, 16-x1, z1, y1, 16-x0);
            default -> Block.box(x0, y0, z0, x1, y1, z1);
        };
    }

    private static void addClipped(java.util.List<VoxelShape> shapes, Direction facing, Side side, Section section,
            double x0, double y0, double z0, double x1, double y1, double z1) {
        double ox = side.ordinal()*16, oy = section.height*16, oz = -section.depth*16;
        x0 = Math.max(x0, ox); y0 = Math.max(y0, oy); z0 = Math.max(z0, oz);
        x1 = Math.min(x1, ox+16); y1 = Math.min(y1, oy+16); z1 = Math.min(z1, oz+16);
        if (x1 > x0 && y1 > y0 && z1 > z0) {
            shapes.add(box(facing, x0-ox, y0-oy, z0-oz, x1-ox, y1-oy, z1-oz));
        }
    }

    @Override
    protected VoxelShape getShape(BlockState state, BlockGetter level, BlockPos pos, CollisionContext context) {
        Direction facing = state.getValue(FACING);
        Side side = state.getValue(SIDE);
        Section section = state.getValue(SECTION);
        int key = facing.ordinal()*10 + side.ordinal()*5 + section.ordinal();
        synchronized (shapeCache) {
            // Preserve the exact barrel slices while avoiding full-grid rescans
            // whenever vanilla draws the outline or raycasts the targeted drum.
            return shapeCache.computeIfAbsent(key, ignored -> CachedCabinetShape.of(buildShape(facing, side, section)));
        }
    }

    private static VoxelShape buildShape(Direction facing, Side side, Section section) {
        var shapes = new java.util.ArrayList<VoxelShape>();
        addClipped(shapes, facing, side, section, 1, .5, 1.3, 31, 39.4, 14.6);
        addClipped(shapes, facing, side, section, .35, 39.4, 1.2, 31.65, 48, 5);
        addClipped(shapes, facing, side, section, .5, .2, -15.2, 31.5, 13.7, 4.8);
        // Narrow voxel slices follow each tilted barrel instead of filling the
        // open space above the plinth with a full rectangular collision box.
        for (int center : new int[]{8,24}) {
            addClipped(shapes, facing, side, section, center-4, 13.7, -6, center+4, 20, 1);
            Vec3 normal = TaikoDrumInteraction.drumNormal(Direction.NORTH, center == 8 ? Side.PRIMARY : Side.SECONDARY);
            for (double y = 13; y < 30; y += 1) {
                for (double z = -14; z < 5; z += 1) {
                    double dy = y+.5-24, dz = z+.5+9;
                    double projected = normal.y*dy + normal.z*dz;
                    // Solve distance-to-axis <= seven along this horizontal
                    // slice. The X component accounts for the outward yaw.
                    double a = 1-normal.x*normal.x;
                    double b = -2*normal.x*projected;
                    double c = dy*dy+dz*dz-projected*projected-49;
                    double discriminant = b*b-4*a*c;
                    if (discriminant <= 0) { continue; }
                    double root = Math.sqrt(discriminant);
                    double x0 = (-b-root)/(2*a), x1 = (-b+root)/(2*a);
                    double capA = (-8.45-projected)/normal.x, capB = (.45-projected)/normal.x;
                    x0 = Math.max(x0, Math.min(capA, capB));
                    x1 = Math.min(x1, Math.max(capA, capB));
                    if (x1 <= x0) { continue; }
                    addClipped(shapes, facing, side, section, center+x0, y, z, center+x1, y+1, z+1);
                }
            }
        }
        return Shapes.or(Shapes.empty(), shapes.toArray(VoxelShape[]::new)).optimize();
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
        REAR_BASE(0,0), REAR_CONSOLE(0,1), REAR_MARQUEE(0,2),
        DRUM_BASE(1,0), DRUMS(1,1);
        final int depth, height;
        Section(int depth, int height) { this.depth=depth; this.height=height; }
        @Override
        public String getSerializedName() { return name().toLowerCase(java.util.Locale.ROOT); }
    }
}
