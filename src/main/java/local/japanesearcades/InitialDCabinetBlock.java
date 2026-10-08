package local.japanesearcades;

import com.mojang.serialization.MapCodec;
import javax.annotation.Nullable;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.util.StringRepresentable;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.ItemInteractionResult;
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
import net.minecraft.world.phys.BlockHitResult;
import net.minecraft.world.phys.Vec3;
import net.minecraft.world.phys.shapes.CollisionContext;
import net.minecraft.world.phys.shapes.Shapes;
import net.minecraft.world.phys.shapes.VoxelShape;

/** Seven connected cells: a narrow cabinet, controls, and usable single seat. */
public final class InitialDCabinetBlock extends NostalgiaCabinetBlock {
    public static final MapCodec<InitialDCabinetBlock> CODEC = simpleCodec(InitialDCabinetBlock::new);
    public static final EnumProperty<Section> SECTION = EnumProperty.create("section", Section.class);
    private final java.util.Map<Integer, VoxelShape> shapeCache = new java.util.concurrent.ConcurrentHashMap<>();

    public InitialDCabinetBlock(Properties properties) {
        super(properties);
        registerDefaultState(defaultBlockState().setValue(SECTION, Section.CABINET_BASE));
    }
    @Override protected MapCodec<? extends HorizontalDirectionalBlock> codec() { return CODEC; }

    static BlockPos sectionPosition(BlockPos anchor, Direction facing, Section section) {
        return anchor.relative(facing, section.depth).above(section.height);
    }
    @Override protected BlockPos basePosition(BlockPos pos, BlockState state) {
        Section section = state.getValue(SECTION);
        return pos.below(section.height).relative(state.getValue(FACING), -section.depth);
    }
    private boolean matches(BlockState state, Direction facing, Section section) {
        return state.is(this) && state.getValue(FACING) == facing && state.getValue(SECTION) == section;
    }
    boolean isComplete(LevelReader level, BlockPos anchor, Direction facing) {
        for (Section section : Section.values()) {
            if (!matches(level.getBlockState(sectionPosition(anchor, facing, section)), facing, section)) { return false; }
        }
        return true;
    }

    @Nullable
    @Override public BlockState getStateForPlacement(BlockPlaceContext context) {
        Level level = context.getLevel();
        BlockPos anchor = context.getClickedPos();
        Direction facing = context.getHorizontalDirection().getOpposite();
        if (anchor.getY()+2 >= level.getMaxBuildHeight()) { return null; }
        for (int depth = 0; depth < 3; depth++) {
            BlockPos floor = anchor.relative(facing, depth).below();
            if (!level.getBlockState(floor).isFaceSturdy(level, floor, Direction.UP)) { return null; }
        }
        for (Section section : Section.values()) {
            BlockPos target = sectionPosition(anchor, facing, section);
            if (!level.getWorldBorder().isWithinBounds(target) || !level.getBlockState(target).canBeReplaced(context)) { return null; }
        }
        return defaultBlockState().setValue(FACING, facing);
    }

    @Override public void setPlacedBy(Level level, BlockPos pos, BlockState state, @Nullable LivingEntity placer, ItemStack stack) {
        Direction facing = state.getValue(FACING);
        for (Section section : Section.values()) {
            if (section == Section.CABINET_BASE) { continue; }
            level.setBlock(sectionPosition(pos, facing, section), state.setValue(SECTION, section)
                .setValue(PART, Part.values()[section.height]).setValue(HAS_RECORD, false), 18);
        }
        if (level.getBlockEntity(pos) instanceof NostalgiaJukeboxBlockEntity cabinet && !cabinet.isEmpty()) {
            level.setBlock(pos, state.setValue(HAS_RECORD, true), 18);
        }
        notifySections(level, pos, facing);
    }
    private void notifySections(Level level, BlockPos anchor, Direction facing) {
        for (Section section : Section.values()) {
            BlockPos target = sectionPosition(anchor, facing, section);
            level.getBlockState(target).updateNeighbourShapes(level, target, 3);
            level.updateNeighborsAt(target, this);
        }
    }

    @Override protected boolean canSurvive(BlockState state, LevelReader level, BlockPos pos) {
        Section section = state.getValue(SECTION);
        if (section.height == 0) { return level.getBlockState(pos.below()).isFaceSturdy(level, pos.below(), Direction.UP); }
        Section below = switch (section) {
            case CABINET_MARQUEE -> Section.CABINET_CONSOLE;
            case CONTROLS -> Section.FOOTWELL;
            case SEAT_BACK -> Section.SEAT_BASE;
            default -> Section.CABINET_BASE;
        };
        return matches(level.getBlockState(pos.below()), state.getValue(FACING), below);
    }
    @Override protected BlockState updateShape(BlockState state, Direction direction, BlockState neighbor,
            LevelAccessor level, BlockPos pos, BlockPos neighborPos) {
        if (direction == Direction.DOWN && !canSurvive(state, level, pos)) { return Blocks.AIR.defaultBlockState(); }
        Direction facing = state.getValue(FACING);
        BlockPos anchor = basePosition(pos, state);
        for (Section section : Section.values()) {
            if (sectionPosition(anchor, facing, section).equals(neighborPos) && !matches(neighbor, facing, section)) {
                return Blocks.AIR.defaultBlockState();
            }
        }
        return state;
    }
    @Override public BlockState playerWillDestroy(Level level, BlockPos pos, BlockState state, Player player) {
        if (!level.isClientSide && player.isCreative()) {
            BlockPos anchor = basePosition(pos, state);
            Direction facing = state.getValue(FACING);
            InitialDSeatEntity.removeFor(level, anchor);
            for (Section section : Section.values()) {
                BlockPos target = sectionPosition(anchor, facing, section);
                if (matches(level.getBlockState(target), facing, section)) { level.setBlock(target, Blocks.AIR.defaultBlockState(), 18); }
            }
            notifySections(level, anchor, facing);
        }
        return super.playerWillDestroy(level, pos, state, player);
    }
    @Override protected void onRemove(BlockState state, Level level, BlockPos pos, BlockState next, boolean moving) {
        if (!level.isClientSide && (!next.is(this) || next.getValue(SECTION) != state.getValue(SECTION))) {
            InitialDSeatEntity.removeFor(level, basePosition(pos, state));
        }
        super.onRemove(state, level, pos, next, moving);
    }

    @Nullable @Override public BlockEntity newBlockEntity(BlockPos pos, BlockState state) {
        return state.getValue(SECTION) == Section.CABINET_BASE ? super.newBlockEntity(pos, state) : null;
    }
    @Nullable @Override public <T extends BlockEntity> BlockEntityTicker<T> getTicker(Level level, BlockState state, BlockEntityType<T> type) {
        return state.getValue(SECTION) == Section.CABINET_BASE ? super.getTicker(level, state, type) : null;
    }
    @Override public boolean isSignalSource(BlockState state) { return state.getValue(SECTION) == Section.CABINET_BASE; }
    @Override protected boolean hasAnalogOutputSignal(BlockState state) { return state.getValue(SECTION) == Section.CABINET_BASE; }
    @Override protected Vec3 discEjectionPosition(BlockPos pos, BlockState state) {
        Direction front = state.getValue(FACING);
        return Vec3.atCenterOf(pos).add(front.getStepX()*2.9, .3, front.getStepZ()*2.9);
    }

    @Override protected ItemInteractionResult useItemOn(ItemStack stack, BlockState state, Level level, BlockPos pos,
            Player player, InteractionHand hand, BlockHitResult hit) {
        if (state.getValue(SECTION).depth == 0) { return super.useItemOn(stack, state, level, pos, player, hand, hit); }
        return ItemInteractionResult.PASS_TO_DEFAULT_BLOCK_INTERACTION;
    }
    @Override protected InteractionResult useWithoutItem(BlockState state, Level level, BlockPos pos, Player player, BlockHitResult hit) {
        if (state.getValue(SECTION).depth == 0) { return super.useWithoutItem(state, level, pos, player, hit); }
        if (state.getValue(SECTION).depth == 2 && player.getMainHandItem().isEmpty() && !player.isShiftKeyDown()) {
            if (!level.isClientSide) { InitialDSeatEntity.mount(player, pos); }
            return InteractionResult.sidedSuccess(level.isClientSide);
        }
        return InteractionResult.PASS;
    }

    private static VoxelShape box(Direction facing, double x0, double y0, double z0, double x1, double y1, double z1) {
        return switch (facing) {
            case EAST -> Block.box(16-z1, y0, x0, 16-z0, y1, x1);
            case SOUTH -> Block.box(16-x1, y0, 16-z1, 16-x0, y1, 16-z0);
            case WEST -> Block.box(z0, y0, 16-x1, z1, y1, 16-x0);
            default -> Block.box(x0, y0, z0, x1, y1, z1);
        };
    }
    @Override protected VoxelShape getShape(BlockState state, BlockGetter level, BlockPos pos, CollisionContext context) {
        Direction facing = state.getValue(FACING);
        Section section = state.getValue(SECTION);
        int key = facing.ordinal()*7 + section.ordinal();
        return shapeCache.computeIfAbsent(key, ignored -> CachedCabinetShape.of(buildShape(facing, section)));
    }

    static VoxelShape buildShape(Direction facing, Section section) {
        return switch (section) {
            case CABINET_BASE -> Shapes.or(box(facing, .64, .05, 3.6, 15.36, 15.2, 15.1),
                box(facing, .64, 15.2, 2.8, 15.36, 16, 14.87));
            case CABINET_CONSOLE -> Shapes.or(box(facing, .64, 0, .6, 15.36, 4, 14.87),
                box(facing, .64, 4, 1.7, 15.36, 8, 14.87), box(facing, .64, 8, 2.7, 15.36, 12, 14.87),
                box(facing, .64, 12, 3.7, 15.36, 16, 14.87));
            case CABINET_MARQUEE -> Shapes.or(box(facing, .64, 0, 4.1, 15.36, 1.12, 14.87),
                box(facing, .82, 1.12, 4.1, 15.18, 2.3, 8.5), box(facing, .32, 2.15, 5.75, 15.68, 9, 8.83));
            case FOOTWELL -> Shapes.or(box(facing, .67, .05, 0, 15.33, 1.55, 16),
                box(facing, .83, 1.55, 12, 2.8, 16, 16), box(facing, 13.2, 1.55, 12, 15.17, 16, 16),
                box(facing, 3.4, 1.5, 9.37, 12.6, 5.65, 15.7), box(facing, .83, 15.76, 8.4, 15.17, 16, 16));
            case CONTROLS -> Shapes.or(box(facing, .83, 0, 8.4, 15.17, 4.35, 16),
                box(facing, 3.7, .9, 7.3, 10.5, 7.5, 10));
            case SEAT_BASE -> Shapes.or(box(facing, .67, .05, .61, 15.33, 1.24, 16),
                box(facing, 2.73, 1.32, 3.46, 13.27, 5.53, 12.8), box(facing, 3.13, 5.53, 3.88, 12.87, 11.58, 13.43),
                box(facing, 2.1, 10.5, 2.7, 13.9, 16, 4.8));
            case SEAT_BACK -> box(facing, 2.1, 0, 1.7, 13.9, 12.1, 4.3);
        };
    }
    @Override protected void createBlockStateDefinition(StateDefinition.Builder<Block, BlockState> builder) {
        super.createBlockStateDefinition(builder);
        builder.add(SECTION);
    }
    public enum Section implements StringRepresentable {
        CABINET_BASE(0,0), CABINET_CONSOLE(0,1), CABINET_MARQUEE(0,2), FOOTWELL(1,0), CONTROLS(1,1), SEAT_BASE(2,0), SEAT_BACK(2,1);
        final int depth, height;
        Section(int depth, int height) { this.depth = depth; this.height = height; }
        @Override public String getSerializedName() { return name().toLowerCase(java.util.Locale.ROOT); }
    }
}
