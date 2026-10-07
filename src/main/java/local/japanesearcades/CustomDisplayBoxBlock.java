package local.japanesearcades;

import com.mojang.serialization.MapCodec;
import java.util.List;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.ItemInteractionResult;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.context.BlockPlaceContext;
import net.minecraft.world.level.BlockGetter;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.LevelReader;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.EntityBlock;
import net.minecraft.world.level.block.HorizontalDirectionalBlock;
import net.minecraft.world.level.block.Mirror;
import net.minecraft.world.level.block.RenderShape;
import net.minecraft.world.level.block.Rotation;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.StateDefinition;
import net.minecraft.world.phys.BlockHitResult;
import net.minecraft.world.phys.Vec3;
import net.minecraft.world.phys.shapes.CollisionContext;
import net.minecraft.world.phys.shapes.VoxelShape;

/** A reusable package: empty-hand use changes the view, and sneaking unpacks its contents. */
public final class CustomDisplayBoxBlock extends HorizontalDirectionalBlock implements EntityBlock {
    public static final MapCodec<CustomDisplayBoxBlock> CODEC = simpleCodec(CustomDisplayBoxBlock::new);
    private static final VoxelShape NORTH_SOUTH = Block.box(3, 0, 4, 13, 14, 12);
    private static final VoxelShape EAST_WEST = Block.box(4, 0, 3, 12, 14, 13);

    public CustomDisplayBoxBlock(Properties properties) {
        super(properties);
        registerDefaultState(stateDefinition.any().setValue(FACING, Direction.NORTH));
    }
    @Override protected MapCodec<CustomDisplayBoxBlock> codec() { return CODEC; }
    @Override public BlockEntity newBlockEntity(BlockPos pos, BlockState state) { return new CustomDisplayBoxBlockEntity(pos, state); }
    @Override protected RenderShape getRenderShape(BlockState state) { return RenderShape.ENTITYBLOCK_ANIMATED; }
    @Override public BlockState getStateForPlacement(BlockPlaceContext context) {
        return defaultBlockState().setValue(FACING, context.getHorizontalDirection().getOpposite());
    }
    @Override protected VoxelShape getShape(BlockState state, BlockGetter level, BlockPos pos, CollisionContext context) {
        return state.getValue(FACING).getAxis() == Direction.Axis.X ? EAST_WEST : NORTH_SOUTH;
    }
    @Override protected BlockState rotate(BlockState state, Rotation rotation) { return state.setValue(FACING, rotation.rotate(state.getValue(FACING))); }
    @Override protected BlockState mirror(BlockState state, Mirror mirror) { return state.rotate(mirror.getRotation(state.getValue(FACING))); }
    @Override protected void createBlockStateDefinition(StateDefinition.Builder<Block, BlockState> builder) { builder.add(FACING); }

    @Override protected ItemInteractionResult useItemOn(ItemStack stack, BlockState state, Level level, BlockPos pos,
            Player player, InteractionHand hand, BlockHitResult hit) {
        if (!(level.getBlockEntity(pos) instanceof CustomDisplayBoxBlockEntity box)) { return ItemInteractionResult.FAIL; }
        if (stack.getItem() instanceof CustomDisplayBoxItem) { return ItemInteractionResult.FAIL; }
        if (stack.isEmpty() == box.data().isEmpty()) { return ItemInteractionResult.SKIP_DEFAULT_BLOCK_INTERACTION; }
        if (level.isClientSide) { return ItemInteractionResult.SUCCESS; }
        return player instanceof ServerPlayer serverPlayer && CustomDisplayBoxInteraction.exchangePlaced(serverPlayer, hand, box)
            ? ItemInteractionResult.CONSUME : ItemInteractionResult.FAIL;
    }
    @Override protected InteractionResult useWithoutItem(BlockState state, Level level, BlockPos pos, Player player, BlockHitResult hit) {
        if (!player.getMainHandItem().isEmpty() || !(level.getBlockEntity(pos) instanceof CustomDisplayBoxBlockEntity box)
                || box.data().isEmpty()) { return InteractionResult.PASS; }
        if (level.isClientSide) { return InteractionResult.SUCCESS; }
        return player instanceof ServerPlayer serverPlayer && CustomDisplayBoxInteraction.exchangePlaced(serverPlayer, InteractionHand.MAIN_HAND, box)
            ? InteractionResult.CONSUME : InteractionResult.FAIL;
    }
    @Override public ItemStack getCloneItemStack(LevelReader level, BlockPos pos, BlockState state) {
        ItemStack stack = new ItemStack(this);
        if (level.getBlockEntity(pos) instanceof CustomDisplayBoxBlockEntity box) { box.saveToItem(stack, level.registryAccess()); }
        return stack;
    }
    @Override public BlockState playerWillDestroy(Level level, BlockPos pos, BlockState state, Player player) {
        // Like a shulker box, creative destruction preserves an actual stored item.
        if (level instanceof ServerLevel server && player.hasInfiniteMaterials()
                && level.getBlockEntity(pos) instanceof CustomDisplayBoxBlockEntity box && !box.data().isEmpty()) {
            ItemStack drop = getCloneItemStack(level, pos, state);
            box.setData(CustomDisplayBoxData.EMPTY);
            Vec3 position = Vec3.atCenterOf(pos);
            if (!ClawMachineRecovery.spawn(server, drop, position, player.getUUID())) {
                ClawMachineRecovery.enqueue(server, List.of(drop), position, player.getUUID());
            }
        }
        return super.playerWillDestroy(level, pos, state, player);
    }
}
