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
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.entity.BlockEntityTicker;
import net.minecraft.world.level.block.entity.BlockEntityType;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.StateDefinition;
import net.minecraft.world.level.block.state.properties.IntegerProperty;
import net.minecraft.world.level.material.PushReaction;
import net.minecraft.world.phys.Vec3;
import net.minecraft.world.phys.shapes.CollisionContext;
import net.minecraft.world.phys.shapes.Shapes;
import net.minecraft.world.phys.shapes.VoxelShape;

/** Ten connected cells; drum hardware is static and shares one rear-left disc inventory. */
public final class GitadoraDrummaniaCabinetBlock extends NostalgiaCabinetBlock {
    public static final MapCodec<GitadoraDrummaniaCabinetBlock> CODEC = simpleCodec(GitadoraDrummaniaCabinetBlock::new);
    public static final IntegerProperty SECTION = IntegerProperty.create("section", 0, 9);
    public static final int SECTION_COUNT = 10;
    private static final VoxelShape[][] SHAPES = createShapes();

    public GitadoraDrummaniaCabinetBlock(Properties properties) {
        super(properties);
        registerDefaultState(defaultBlockState().setValue(SECTION, 0));
    }
    @Override protected MapCodec<? extends HorizontalDirectionalBlock> codec() { return CODEC; }
    public static int height(int section) { return section < 4 ? 0 : section < 6 || section >= 8 ? 1 : 2; }
    public static int depth(int section) { return section == 2 || section == 3 || section >= 8 ? 1 : 0; }
    public static BlockPos sectionPosition(BlockPos anchor, Direction facing, int section) {
        return anchor.relative(facing.getClockWise(), section % 2).relative(facing, depth(section)).above(height(section));
    }
    public static BlockPos getAnchor(BlockState state, BlockPos pos) {
        int section = state.getValue(SECTION);
        Direction facing = state.getValue(FACING);
        return pos.relative(facing.getClockWise(), -(section % 2)).relative(facing, -depth(section)).below(height(section));
    }
    private static BlockState sectionState(BlockState base, int section) {
        return base.setValue(SECTION, section).setValue(PART, Part.values()[height(section)]).setValue(HAS_RECORD, false);
    }
    @Override protected BlockPos basePosition(BlockPos pos, BlockState state) { return getAnchor(state, pos); }
    private boolean matches(BlockState state, Direction facing, int section) {
        return state.is(this) && state.getValue(FACING) == facing && state.getValue(SECTION) == section
            && state.getValue(PART).ordinal() == height(section);
    }
    private static boolean isAnchor(BlockState state) { return state.getValue(SECTION) == 0; }

    @Nullable @Override public BlockState getStateForPlacement(BlockPlaceContext context) {
        Level level = context.getLevel();
        BlockPos anchor = context.getClickedPos();
        Player player = context.getPlayer();
        Direction facing = context.getHorizontalDirection().getOpposite();
        if (anchor.getY() < level.getMinBuildHeight() || anchor.getY() + 2 >= level.getMaxBuildHeight()
                || player != null && (!player.isAlive() || player.isSpectator())) { return null; }
        BlockState base = defaultBlockState().setValue(FACING, facing);
        CollisionContext collision = player == null ? CollisionContext.empty() : CollisionContext.of(player);
        for (int section = 0; section < SECTION_COUNT; section++) {
            BlockPos target = sectionPosition(anchor, facing, section);
            if (!level.hasChunkAt(target) || !level.getWorldBorder().isWithinBounds(target)
                    || !level.getBlockState(target).canBeReplaced(context)
                    || section < 4 && !level.getBlockState(target.below()).isFaceSturdy(level, target.below(), Direction.UP)
                    || player != null && (!level.mayInteract(player, target)
                        || !player.mayUseItemAt(target, context.getClickedFace(), context.getItemInHand()))
                    || !level.isUnobstructed(sectionState(base, section), target, collision)) { return null; }
        }
        return base;
    }
    @Override public void setPlacedBy(Level level, BlockPos pos, BlockState state, @Nullable LivingEntity placer, ItemStack stack) {
        Direction facing = state.getValue(FACING);
        for (int section = 1; section < SECTION_COUNT; section++) {
            level.setBlock(sectionPosition(pos, facing, section), sectionState(state, section), 18);
        }
        notifySections(level, pos, facing);
        if (level.getBlockEntity(pos) instanceof NostalgiaJukeboxBlockEntity cabinet && !cabinet.isEmpty()) {
            level.setBlock(pos, state.setValue(HAS_RECORD, true), 2);
        }
    }
    private void notifySections(Level level, BlockPos anchor, Direction facing) {
        for (int section = 0; section < SECTION_COUNT; section++) {
            BlockPos target = sectionPosition(anchor, facing, section);
            level.getBlockState(target).updateNeighbourShapes(level, target, 3);
            level.updateNeighborsAt(target, this);
        }
    }
    @Override protected boolean canSurvive(BlockState state, LevelReader level, BlockPos pos) {
        int section = state.getValue(SECTION);
        if (section < 4) { return level.getBlockState(pos.below()).isFaceSturdy(level, pos.below(), Direction.UP); }
        int below = section >= 8 ? section - 6 : section >= 6 ? section - 2 : section - 4;
        return matches(level.getBlockState(pos.below()), state.getValue(FACING), below);
    }
    @Override protected BlockState updateShape(BlockState state, Direction direction, BlockState neighbor,
            LevelAccessor level, BlockPos pos, BlockPos neighborPos) {
        if (direction == Direction.DOWN && !state.canSurvive(level, pos)) { return Blocks.AIR.defaultBlockState(); }
        BlockPos anchor = getAnchor(state, pos);
        Direction facing = state.getValue(FACING);
        for (int section = 0; section < SECTION_COUNT; section++) {
            if (sectionPosition(anchor, facing, section).equals(neighborPos) && !matches(neighbor, facing, section)) {
                return Blocks.AIR.defaultBlockState();
            }
        }
        return state;
    }
    @Override public BlockState playerWillDestroy(Level level, BlockPos pos, BlockState state, Player player) {
        if (!level.isClientSide && player.hasInfiniteMaterials()) {
            BlockPos anchor = getAnchor(state, pos);
            Direction facing = state.getValue(FACING);
            for (int section = 0; section < SECTION_COUNT; section++) {
                BlockPos target = sectionPosition(anchor, facing, section);
                if (matches(level.getBlockState(target), facing, section)) { level.setBlock(target, Blocks.AIR.defaultBlockState(), 18); }
            }
            notifySections(level, anchor, facing);
        }
        return super.playerWillDestroy(level, pos, state, player);
    }
    @Override protected void onRemove(BlockState state, Level level, BlockPos pos, BlockState next, boolean moving) {
        if (isAnchor(state) && (!next.is(this) || !isAnchor(next))) {
            if (level.getBlockEntity(pos) instanceof NostalgiaJukeboxBlockEntity cabinet) { cabinet.ejectDisc(); }
            level.removeBlockEntity(pos);
        }
        super.onRemove(state, level, pos, next, moving);
    }
    @Nullable @Override public BlockEntity newBlockEntity(BlockPos pos, BlockState state) {
        return isAnchor(state) ? super.newBlockEntity(pos, state) : null;
    }
    @Nullable @Override public <T extends BlockEntity> BlockEntityTicker<T> getTicker(Level level, BlockState state, BlockEntityType<T> type) {
        return isAnchor(state) ? super.getTicker(level, state, type) : null;
    }
    @Override public boolean isSignalSource(BlockState state) { return isAnchor(state); }
    @Override protected boolean hasAnalogOutputSignal(BlockState state) { return isAnchor(state); }
    @Override public PushReaction getPistonPushReaction(BlockState state) { return PushReaction.BLOCK; }
    @Override protected Vec3 discEjectionPosition(BlockPos pos, BlockState state) {
        Direction facing = state.getValue(FACING), right = facing.getClockWise();
        return Vec3.atCenterOf(pos).add(right.getStepX() * .5 + facing.getStepX() * 1.9, .4,
            right.getStepZ() * .5 + facing.getStepZ() * 1.9);
    }
    @Override protected VoxelShape getShape(BlockState state, BlockGetter level, BlockPos pos, CollisionContext context) {
        return SHAPES[state.getValue(SECTION)][state.getValue(FACING).get2DDataValue()];
    }
    @Override protected BlockState mirror(BlockState state, Mirror mirror) {
        return mirror == Mirror.NONE ? state : state.rotate(mirror.getRotation(state.getValue(FACING)))
            .setValue(SECTION, state.getValue(SECTION) ^ 1);
    }
    @Override protected void createBlockStateDefinition(StateDefinition.Builder<Block, BlockState> builder) {
        super.createBlockStateDefinition(builder);
        builder.add(SECTION);
    }

    private static VoxelShape[][] createShapes() {
        double[][] volumes = {
            {.65, 0, -15.3, 31.35, 1.1, 15.5}, {5, 1.1, 5, 27, 24, 15.3},
            {5, 23, 5, 27, 38.2, 15.3}, {4.1, 38.2, 7.3, 27.9, 46.8, 14.7},
            {5.15, 1.4, 2.7, 9.45, 22.2, 8}, {24.6, 27.1, -5.3, 31.2, 29.2, 1.3},
            {25.5, 21, -11, 30.9, 23.5, -5.7}, {18.6, 16.1, -13.5, 25, 18.3, -7.1},
            {17.4, 21.8, -4.7, 23.6, 25, 1.4}, {8.9, 21.8, -4.7, 15.1, 25, 1.4},
            {1.9, 16.5, -12, 8.1, 19, -5.7}, {.8, 26.6, -4.1, 7.4, 30.7, 2.1},
            {2.75, 1.1, -6.3, 3.25, 23, -5.7}, {28.75, 1.1, -6.3, 29.25, 23, -5.7},
            {10, 1.1, -14.6, 13.2, 4.7, -7.6}, {18.5, 1.1, -14.6, 21.7, 4.7, -7.6}
        };
        VoxelShape[][] shapes = new VoxelShape[SECTION_COUNT][4];
        for (int section = 0; section < SECTION_COUNT; section++) {
            double left = section % 2 * 16, bottom = height(section) * 16, back = -depth(section) * 16;
            for (Direction facing : Direction.Plane.HORIZONTAL) {
                VoxelShape shape = Shapes.empty();
                for (double[] volume : volumes) {
                    double x0 = Math.max(left, volume[0]), y0 = Math.max(bottom, volume[1]), z0 = Math.max(back, volume[2]);
                    double x1 = Math.min(left + 16, volume[3]), y1 = Math.min(bottom + 16, volume[4]), z1 = Math.min(back + 16, volume[5]);
                    if (x0 < x1 && y0 < y1 && z0 < z1) {
                        shape = Shapes.or(shape, CompactMusicCabinetBlock.box(facing, x0-left, y0-bottom, z0-back, x1-left, y1-bottom, z1-back));
                    }
                }
                shapes[section][facing.get2DDataValue()] = shape.optimize();
            }
        }
        return shapes;
    }
}
