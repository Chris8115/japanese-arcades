package local.funpack.custom;

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
import net.minecraft.world.level.block.Mirror;
import net.minecraft.world.level.block.Rotation;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.StateDefinition;
import net.minecraft.world.level.block.state.properties.BlockStateProperties;
import net.minecraft.world.level.block.state.properties.DoubleBlockHalf;
import net.minecraft.world.level.block.state.properties.EnumProperty;
import net.minecraft.world.level.block.state.properties.IntegerProperty;
import net.minecraft.world.level.block.state.properties.RotationSegment;
import net.minecraft.world.level.material.PushReaction;
import net.minecraft.world.phys.shapes.CollisionContext;
import net.minecraft.world.phys.shapes.Shapes;
import net.minecraft.world.phys.shapes.VoxelShape;

/** Freestanding two-cell cardboard standee, oriented in the same 16 steps as a standing sign. */
public final class HatsuneMikuCutoutBlock extends Block {
    public static final MapCodec<HatsuneMikuCutoutBlock> CODEC = simpleCodec(HatsuneMikuCutoutBlock::new);
    public static final EnumProperty<DoubleBlockHalf> HALF = BlockStateProperties.DOUBLE_BLOCK_HALF;
    public static final IntegerProperty ROTATION = BlockStateProperties.ROTATION_16;
    private static final VoxelShape[] LOWER_SHAPES = new VoxelShape[16];
    private static final VoxelShape[] UPPER_SHAPES = new VoxelShape[16];
    static {
        for (int rotation = 0; rotation < 16; rotation++) {
            LOWER_SHAPES[rotation] = shape(rotation, true);
            UPPER_SHAPES[rotation] = shape(rotation, false);
        }
    }

    public HatsuneMikuCutoutBlock(Properties properties) {
        super(properties);
        registerDefaultState(stateDefinition.any().setValue(HALF, DoubleBlockHalf.LOWER).setValue(ROTATION, 0));
    }
    @Override protected MapCodec<HatsuneMikuCutoutBlock> codec() { return CODEC; }

    @Nullable
    @Override public BlockState getStateForPlacement(BlockPlaceContext context) {
        BlockPos pos = context.getClickedPos();
        BlockPos upperPos = pos.above();
        Level level = context.getLevel();
        Player player = context.getPlayer();
        BlockState lower = defaultBlockState().setValue(ROTATION, RotationSegment.convertToSegment(context.getRotation() + 180.0F));
        if (pos.getY() < level.getMinBuildHeight() || upperPos.getY() >= level.getMaxBuildHeight()
                || !level.getBlockState(upperPos).canBeReplaced(context) || !lower.canSurvive(level, pos)) { return null; }
        if (player != null && (!player.isAlive() || player.isSpectator()
                || !player.mayUseItemAt(pos, context.getClickedFace(), context.getItemInHand())
                || !player.mayUseItemAt(upperPos, context.getClickedFace(), context.getItemInHand())
                || !level.mayInteract(player, pos) || !level.mayInteract(player, upperPos))) { return null; }
        CollisionContext collision = player == null ? CollisionContext.empty() : CollisionContext.of(player);
        return level.isUnobstructed(lower.setValue(HALF, DoubleBlockHalf.UPPER), upperPos, collision) ? lower : null;
    }

    @Override public void setPlacedBy(Level level, BlockPos pos, BlockState state, @Nullable LivingEntity placer, ItemStack stack) {
        level.setBlock(pos.above(), state.setValue(HALF, DoubleBlockHalf.UPPER), 3);
    }
    @Override protected boolean canSurvive(BlockState state, LevelReader level, BlockPos pos) {
        return state.getValue(HALF) == DoubleBlockHalf.LOWER
            ? level.getBlockState(pos.below()).isFaceSturdy(level, pos.below(), Direction.UP)
            : matches(level.getBlockState(pos.below()), DoubleBlockHalf.LOWER, state.getValue(ROTATION));
    }
    @Override protected BlockState updateShape(BlockState state, Direction direction, BlockState neighbor,
            LevelAccessor level, BlockPos pos, BlockPos neighborPos) {
        if ((state.getValue(HALF) == DoubleBlockHalf.LOWER && direction == Direction.UP
                && !matches(neighbor, DoubleBlockHalf.UPPER, state.getValue(ROTATION)))
                || (direction == Direction.DOWN && !state.canSurvive(level, pos))) {
            return Blocks.AIR.defaultBlockState();
        }
        return super.updateShape(state, direction, neighbor, level, pos, neighborPos);
    }
    private boolean matches(BlockState state, DoubleBlockHalf half, int rotation) {
        return state.is(this) && state.getValue(HALF) == half && state.getValue(ROTATION) == rotation;
    }
    @Override public BlockState playerWillDestroy(Level level, BlockPos pos, BlockState state, Player player) {
        if (!level.isClientSide && player.hasInfiniteMaterials() && state.getValue(HALF) == DoubleBlockHalf.UPPER) {
            BlockPos lower = pos.below();
            if (matches(level.getBlockState(lower), DoubleBlockHalf.LOWER, state.getValue(ROTATION))) {
                // Only the lower half has loot. Suppress its neighbor-triggered drop in creative,
                // exactly as vanilla tall plants do when their upper half is removed first.
                level.setBlock(lower, Blocks.AIR.defaultBlockState(), 35);
            }
        }
        return super.playerWillDestroy(level, pos, state, player);
    }
    @Override public PushReaction getPistonPushReaction(BlockState state) { return PushReaction.BLOCK; }
    @Override protected VoxelShape getShape(BlockState state, BlockGetter level, BlockPos pos, CollisionContext context) {
        return (state.getValue(HALF) == DoubleBlockHalf.LOWER ? LOWER_SHAPES : UPPER_SHAPES)[state.getValue(ROTATION)];
    }
    @Override protected BlockState rotate(BlockState state, Rotation rotation) {
        return state.setValue(ROTATION, rotation.rotate(state.getValue(ROTATION), 16));
    }
    @Override protected BlockState mirror(BlockState state, Mirror mirror) {
        return state.setValue(ROTATION, mirror.mirror(state.getValue(ROTATION), 16));
    }
    @Override protected void createBlockStateDefinition(StateDefinition.Builder<Block, BlockState> builder) { builder.add(HALF, ROTATION); }

    /** Eight disjoint slices bound the thin rotated plate; a separate low foot keeps nine boxes maximum. */
    private static VoxelShape shape(int rotation, boolean lower) {
        double angle = rotation * Math.PI / 8;
        double[][] plate = corners(.4, 7.68, 15.6, 8.32, angle);
        double minX = Double.POSITIVE_INFINITY, maxX = Double.NEGATIVE_INFINITY;
        for (double[] point : plate) { minX = Math.min(minX, point[0]); maxX = Math.max(maxX, point[0]); }
        VoxelShape result = Shapes.empty();
        for (int slice = 0; slice < 8; slice++) {
            double x0 = minX + (maxX - minX) * slice / 8;
            double x1 = minX + (maxX - minX) * (slice + 1) / 8;
            double minZ = Double.POSITIVE_INFINITY, maxZ = Double.NEGATIVE_INFINITY;
            for (int edge = 0; edge < 4; edge++) {
                double[] start = plate[edge], end = plate[(edge + 1) % 4];
                if (start[0] >= x0 - 1.0E-9 && start[0] <= x1 + 1.0E-9) {
                    minZ = Math.min(minZ, start[1]); maxZ = Math.max(maxZ, start[1]);
                }
                if (Math.abs(end[0] - start[0]) < 1.0E-9) { continue; }
                for (double x : new double[]{x0, x1}) {
                    double t = (x - start[0]) / (end[0] - start[0]);
                    if (t >= -1.0E-9 && t <= 1 + 1.0E-9) {
                        double z = start[1] + Math.clamp(t, 0, 1) * (end[1] - start[1]);
                        minZ = Math.min(minZ, z); maxZ = Math.max(maxZ, z);
                    }
                }
            }
            result = Shapes.or(result, Block.box(x0, lower ? 1 : 0, minZ, x1, lower ? 16 : 9.64449438, maxZ));
        }
        if (lower) {
            double[][] foot = corners(3.6, 4.8, 12.4, 11.2, angle);
            double x0 = 16, z0 = 16, x1 = 0, z1 = 0;
            for (double[] point : foot) {
                x0 = Math.min(x0, point[0]); x1 = Math.max(x1, point[0]);
                z0 = Math.min(z0, point[1]); z1 = Math.max(z1, point[1]);
            }
            result = Shapes.or(result, Block.box(x0, 0, z0, x1, 1, z1));
        }
        return result.optimize();
    }
    private static double[][] corners(double x0, double z0, double x1, double z1, double angle) {
        double cos = Math.cos(angle), sin = Math.sin(angle);
        double[][] points = {{x0, z0}, {x1, z0}, {x1, z1}, {x0, z1}};
        for (double[] point : points) {
            double x = point[0] - 8, z = point[1] - 8;
            point[0] = 8 + cos * x - sin * z;
            point[1] = 8 + sin * x + cos * z;
        }
        return points;
    }
}
