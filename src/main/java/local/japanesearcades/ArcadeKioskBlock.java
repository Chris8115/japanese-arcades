package local.japanesearcades;

import com.mojang.serialization.MapCodec;
import javax.annotation.Nullable;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.ItemInteractionResult;
import net.minecraft.world.SimpleMenuProvider;
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
import net.minecraft.world.level.block.state.properties.BlockStateProperties;
import net.minecraft.world.level.block.state.properties.DoubleBlockHalf;
import net.minecraft.world.level.block.state.properties.EnumProperty;
import net.minecraft.world.level.material.PushReaction;
import net.minecraft.world.phys.BlockHitResult;
import net.minecraft.world.phys.shapes.CollisionContext;
import net.minecraft.world.phys.shapes.VoxelShape;

/** A public ordering terminal, one block wide and two blocks tall. */
public final class ArcadeKioskBlock extends HorizontalDirectionalBlock {
    public static final MapCodec<ArcadeKioskBlock> CODEC = simpleCodec(ArcadeKioskBlock::new);
    public static final EnumProperty<DoubleBlockHalf> HALF = BlockStateProperties.DOUBLE_BLOCK_HALF;

    public ArcadeKioskBlock(Properties properties) {
        super(properties);
        registerDefaultState(stateDefinition.any().setValue(FACING, Direction.NORTH).setValue(HALF, DoubleBlockHalf.LOWER));
    }

    @Override protected MapCodec<? extends HorizontalDirectionalBlock> codec() { return CODEC; }

    @Nullable
    @Override public BlockState getStateForPlacement(BlockPlaceContext context) {
        BlockPos pos = context.getClickedPos();
        Level level = context.getLevel();
        BlockState state = defaultBlockState().setValue(FACING, context.getHorizontalDirection().getOpposite());
        if (pos.getY() + 1 >= level.getMaxBuildHeight()
                || !level.getBlockState(pos.above()).canBeReplaced(context)
                || !state.canSurvive(level, pos)) { return null; }
        return state;
    }

    @Override public void setPlacedBy(Level level, BlockPos pos, BlockState state, @Nullable LivingEntity placer, ItemStack stack) {
        level.setBlock(pos.above(), state.setValue(HALF, DoubleBlockHalf.UPPER), 3);
    }

    @Override protected boolean canSurvive(BlockState state, LevelReader level, BlockPos pos) {
        if (state.getValue(HALF) == DoubleBlockHalf.LOWER) {
            return level.getBlockState(pos.below()).isFaceSturdy(level, pos.below(), Direction.UP);
        }
        return matches(level.getBlockState(pos.below()), DoubleBlockHalf.LOWER, state.getValue(FACING));
    }

    @Override protected BlockState updateShape(BlockState state, Direction direction, BlockState neighbor,
            LevelAccessor level, BlockPos pos, BlockPos neighborPos) {
        DoubleBlockHalf half = state.getValue(HALF);
        if ((half == DoubleBlockHalf.LOWER && direction == Direction.UP
                && !matches(neighbor, DoubleBlockHalf.UPPER, state.getValue(FACING)))
                || (direction == Direction.DOWN && !state.canSurvive(level, pos))) {
            return Blocks.AIR.defaultBlockState();
        }
        return super.updateShape(state, direction, neighbor, level, pos, neighborPos);
    }

    private boolean matches(BlockState state, DoubleBlockHalf half, Direction facing) {
        return state.is(this) && state.getValue(HALF) == half && state.getValue(FACING) == facing;
    }

    public static BlockPos basePosition(BlockPos pos, BlockState state) {
        return state.getValue(HALF) == DoubleBlockHalf.UPPER ? pos.below() : pos;
    }

    public static boolean isComplete(LevelReader level, BlockPos base) {
        BlockState lower = level.getBlockState(base);
        BlockState upper = level.getBlockState(base.above());
        return lower.is(JapaneseArcades.ARCADE_KIOSK.get()) && lower.getValue(HALF) == DoubleBlockHalf.LOWER
            && upper.is(lower.getBlock()) && upper.getValue(HALF) == DoubleBlockHalf.UPPER
            && upper.getValue(FACING) == lower.getValue(FACING);
    }

    private InteractionResult open(BlockState state, Level level, BlockPos pos, Player player) {
        BlockPos base = basePosition(pos, state);
        if (!isComplete(level, base) || player.isSpectator()) { return InteractionResult.PASS; }
        if (player instanceof ServerPlayer serverPlayer) {
            serverPlayer.openMenu(new SimpleMenuProvider((id, inventory, viewer) -> new ArcadeKioskMenu(id, inventory, base),
                Component.translatable("menu.japanesearcades.arcade_kiosk")), buffer -> buffer.writeBlockPos(base));
        }
        return InteractionResult.sidedSuccess(level.isClientSide);
    }

    @Override protected InteractionResult useWithoutItem(BlockState state, Level level, BlockPos pos,
            Player player, BlockHitResult hit) { return open(state, level, pos, player); }

    @Override protected ItemInteractionResult useItemOn(ItemStack stack, BlockState state, Level level, BlockPos pos,
            Player player, InteractionHand hand, BlockHitResult hit) {
        if (player.isShiftKeyDown()) { return ItemInteractionResult.SKIP_DEFAULT_BLOCK_INTERACTION; }
        open(state, level, pos, player);
        return ItemInteractionResult.sidedSuccess(level.isClientSide);
    }

    @Override public BlockState playerWillDestroy(Level level, BlockPos pos, BlockState state, Player player) {
        if (!level.isClientSide && player.isCreative() && state.getValue(HALF) == DoubleBlockHalf.UPPER) {
            BlockPos lowerPos = pos.below();
            if (matches(level.getBlockState(lowerPos), DoubleBlockHalf.LOWER, state.getValue(FACING))) {
                // As with vanilla double plants, only the loot-bearing lower
                // half needs pre-removal when the player breaks the upper half.
                // Removing the upper first while breaking the lower would cause
                // its neighbor update to drop the lower block prematurely.
                level.setBlock(lowerPos, Blocks.AIR.defaultBlockState(), 35);
            }
        }
        return super.playerWillDestroy(level, pos, state, player);
    }

    @Override public PushReaction getPistonPushReaction(BlockState state) { return PushReaction.BLOCK; }

    @Override protected VoxelShape getShape(BlockState state, BlockGetter level, BlockPos pos, CollisionContext context) {
        return NostalgiaCabinetBlock.rotatedBox(state.getValue(FACING), 2.4, 2.4, 13.6, 14);
    }

    @Override protected BlockState rotate(BlockState state, Rotation rotation) {
        return state.setValue(FACING, rotation.rotate(state.getValue(FACING)));
    }
    @Override protected BlockState mirror(BlockState state, Mirror mirror) {
        return state.rotate(mirror.getRotation(state.getValue(FACING)));
    }
    @Override protected void createBlockStateDefinition(StateDefinition.Builder<Block, BlockState> builder) { builder.add(FACING, HALF); }
}
