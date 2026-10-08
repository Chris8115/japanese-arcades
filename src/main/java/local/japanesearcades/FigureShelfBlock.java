package local.japanesearcades;

import com.mojang.serialization.Codec;
import com.mojang.serialization.MapCodec;
import com.mojang.serialization.codecs.RecordCodecBuilder;
import java.util.List;
import javax.annotation.Nullable;
import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.network.chat.Component;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.ItemInteractionResult;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.TooltipFlag;
import net.minecraft.world.item.context.BlockPlaceContext;
import net.minecraft.world.level.BlockGetter;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.LevelAccessor;
import net.minecraft.world.level.LevelReader;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.EntityBlock;
import net.minecraft.world.level.block.HorizontalDirectionalBlock;
import net.minecraft.world.level.block.Mirror;
import net.minecraft.world.level.block.Rotation;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.StateDefinition;
import net.minecraft.world.level.material.PushReaction;
import net.minecraft.world.phys.BlockHitResult;
import net.minecraft.world.phys.shapes.CollisionContext;
import net.minecraft.world.phys.shapes.VoxelShape;

/** A compact, unticked collectible display: four figures per shelf. */
public final class FigureShelfBlock extends HorizontalDirectionalBlock implements EntityBlock {
    public static final MapCodec<FigureShelfBlock> CODEC = RecordCodecBuilder.mapCodec(instance -> instance.group(
        Codec.intRange(1, 2).fieldOf("rows").forGetter(FigureShelfBlock::rows),
        propertiesCodec()).apply(instance, FigureShelfBlock::new));
    private final int rows;
    private final VoxelShape[] shapes = new VoxelShape[4];

    public FigureShelfBlock(int rows, Properties properties) {
        super(properties);
        if (rows < 1 || rows > 2) { throw new IllegalArgumentException("Shelf rows must be one or two"); }
        this.rows = rows;
        double front = rows == 2 ? 6 : 8;
        double height = rows == 2 ? 16 : 4;
        shapes[Direction.NORTH.get2DDataValue()] = Block.box(0, 0, front, 16, height, 16);
        shapes[Direction.SOUTH.get2DDataValue()] = Block.box(0, 0, 0, 16, height, 16 - front);
        shapes[Direction.WEST.get2DDataValue()] = Block.box(front, 0, 0, 16, height, 16);
        shapes[Direction.EAST.get2DDataValue()] = Block.box(0, 0, 0, 16 - front, height, 16);
        registerDefaultState(stateDefinition.any().setValue(FACING, Direction.NORTH));
    }

    public int rows() { return rows; }
    @Override public void appendHoverText(ItemStack stack, Item.TooltipContext context, List<Component> lines, TooltipFlag flag) {
        super.appendHoverText(stack, context, lines, flag);
        lines.add(Component.translatable("tooltip.japanesearcades.figure_shelf.capacity", rows * 4).withStyle(ChatFormatting.GRAY));
        lines.add(Component.translatable(rows == 2 ? "tooltip.japanesearcades.figure_shelf.placement"
            : "tooltip.japanesearcades.figure_shelf.wall_placement").withStyle(ChatFormatting.GRAY));
        lines.add(Component.translatable("tooltip.japanesearcades.figure_shelf.inventory").withStyle(ChatFormatting.GRAY));
    }
    @Override protected MapCodec<FigureShelfBlock> codec() { return CODEC; }
    @Override public BlockEntity newBlockEntity(BlockPos pos, BlockState state) { return new FigureShelfBlockEntity(pos, state); }
    @Override protected void createBlockStateDefinition(StateDefinition.Builder<Block, BlockState> builder) { builder.add(FACING); }
    @Override protected VoxelShape getShape(BlockState state, BlockGetter level, BlockPos pos, CollisionContext context) {
        return shapes[state.getValue(FACING).get2DDataValue()];
    }

    @Nullable @Override public BlockState getStateForPlacement(BlockPlaceContext context) {
        Direction face = context.getClickedFace();
        if (face == Direction.DOWN) { return null; }
        Direction facing = face.getAxis().isHorizontal() ? face : context.getHorizontalDirection().getOpposite();
        BlockState state = defaultBlockState().setValue(FACING, facing);
        return state.canSurvive(context.getLevel(), context.getClickedPos()) ? state : null;
    }

    @Override protected boolean canSurvive(BlockState state, LevelReader level, BlockPos pos) {
        Direction facing = state.getValue(FACING);
        BlockPos back = pos.relative(facing.getOpposite());
        if (level.getBlockState(back).isFaceSturdy(level, back, facing)) { return true; }
        if (rows != 2) { return false; }
        BlockPos below = pos.below();
        BlockState support = level.getBlockState(below);
        return support.isFaceSturdy(level, below, Direction.UP)
            || support.getBlock() instanceof FigureShelfBlock shelf && shelf.rows() == 2;
    }

    @Override protected BlockState updateShape(BlockState state, Direction direction, BlockState neighbor,
            LevelAccessor level, BlockPos pos, BlockPos neighborPos) {
        if ((direction == Direction.DOWN || direction == state.getValue(FACING).getOpposite())
                && !state.canSurvive(level, pos)) { return Blocks.AIR.defaultBlockState(); }
        return super.updateShape(state, direction, neighbor, level, pos, neighborPos);
    }

    @Override protected ItemInteractionResult useItemOn(ItemStack stack, BlockState state, Level level, BlockPos pos,
            Player player, InteractionHand hand, BlockHitResult hit) {
        if (player.isShiftKeyDown() && !stack.isEmpty()) { return ItemInteractionResult.SKIP_DEFAULT_BLOCK_INTERACTION; }
        if (!level.isClientSide && player instanceof ServerPlayer serverPlayer
                && level.getBlockEntity(pos) instanceof FigureShelfBlockEntity shelf) { shelf.open(serverPlayer); }
        return ItemInteractionResult.sidedSuccess(level.isClientSide);
    }

    @Override protected InteractionResult useWithoutItem(BlockState state, Level level, BlockPos pos, Player player, BlockHitResult hit) {
        if (!player.getMainHandItem().isEmpty()) { return InteractionResult.PASS; }
        if (!level.isClientSide && player instanceof ServerPlayer serverPlayer
                && level.getBlockEntity(pos) instanceof FigureShelfBlockEntity shelf) { shelf.open(serverPlayer); }
        return InteractionResult.sidedSuccess(level.isClientSide);
    }

    @Override protected void onRemove(BlockState state, Level level, BlockPos pos, BlockState replacement, boolean moving) {
        if (!state.is(replacement.getBlock()) && level.getBlockEntity(pos) instanceof FigureShelfBlockEntity shelf) {
            if (!level.isClientSide) { shelf.dropContents(); }
            level.removeBlockEntity(pos);
        }
        super.onRemove(state, level, pos, replacement, moving);
    }

    @Override public PushReaction getPistonPushReaction(BlockState state) { return PushReaction.BLOCK; }
    @Override protected BlockState rotate(BlockState state, Rotation rotation) { return state.setValue(FACING, rotation.rotate(state.getValue(FACING))); }
    @Override protected BlockState mirror(BlockState state, Mirror mirror) { return state.rotate(mirror.getRotation(state.getValue(FACING))); }
}
