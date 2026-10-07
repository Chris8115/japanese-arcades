package local.japanesearcades;

import com.mojang.serialization.MapCodec;
import javax.annotation.Nullable;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.server.level.ServerPlayer;
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
import net.minecraft.world.level.block.EntityBlock;
import net.minecraft.world.level.block.HorizontalDirectionalBlock;
import net.minecraft.world.level.block.Mirror;
import net.minecraft.world.level.block.Rotation;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.entity.BlockEntityTicker;
import net.minecraft.world.level.block.entity.BlockEntityType;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.StateDefinition;
import net.minecraft.world.level.block.state.properties.IntegerProperty;
import net.minecraft.world.level.material.PushReaction;
import net.minecraft.world.phys.BlockHitResult;
import net.minecraft.world.phys.Vec3;

/** One inventory and controller shared by a connected 3 x 2 x 3 glass cabinet. */
public final class ClawMachineBlock extends HorizontalDirectionalBlock implements EntityBlock {
    public static final MapCodec<ClawMachineBlock> CODEC = simpleCodec(ClawMachineBlock::new);
    public static final IntegerProperty PART = IntegerProperty.create("part", 0, 17);
    public static final int PART_COUNT = 18;

    public ClawMachineBlock(Properties properties) {
        super(properties);
        registerDefaultState(stateDefinition.any().setValue(FACING, Direction.NORTH).setValue(PART, 0));
    }

    @Override
    protected MapCodec<? extends HorizontalDirectionalBlock> codec() { return CODEC; }

    public static BlockPos partPosition(BlockPos anchor, Direction facing, int part) {
        return anchor.relative(facing.getClockWise(), part % 3)
            .relative(facing.getOpposite(), (part / 3) % 2).above(part / 6);
    }

    public static BlockPos getAnchor(BlockState state, BlockPos pos) {
        int part = state.getValue(PART);
        Direction facing = state.getValue(FACING);
        return pos.relative(facing.getClockWise(), -(part % 3))
            .relative(facing.getOpposite(), -((part / 3) % 2)).below(part / 6);
    }

    /** Model coordinates are sixteenths of a block, rotated about the anchor cell. */
    public static Vec3 localToWorld(BlockPos anchor, Direction facing, double x, double y, double z) {
        double localX = x / 16.0 - .5, localZ = z / 16.0 - .5;
        Direction across = facing.getClockWise(), back = facing.getOpposite();
        return new Vec3(anchor.getX() + .5 + across.getStepX()*localX + back.getStepX()*localZ,
            anchor.getY() + y/16.0,
            anchor.getZ() + .5 + across.getStepZ()*localX + back.getStepZ()*localZ);
    }

    @Nullable
    public static ClawMachineBlockEntity machineAt(BlockGetter level, BlockPos pos) {
        BlockState state = level.getBlockState(pos);
        if (!(state.getBlock() instanceof ClawMachineBlock)) { return null; }
        return level.getBlockEntity(getAnchor(state, pos)) instanceof ClawMachineBlockEntity machine ? machine : null;
    }

    private boolean matches(BlockState state, Direction facing, int part) {
        return state.is(this) && state.getValue(FACING) == facing && state.getValue(PART) == part;
    }

    @Nullable
    @Override
    public BlockState getStateForPlacement(BlockPlaceContext context) {
        Level level = context.getLevel();
        BlockPos anchor = context.getClickedPos();
        Direction facing = context.getHorizontalDirection().getOpposite();
        if (anchor.getY() < level.getMinBuildHeight() || anchor.getY()+2 >= level.getMaxBuildHeight()) { return null; }
        for (int part=0; part<PART_COUNT; part++) {
            BlockPos target = partPosition(anchor, facing, part);
            if (!level.getWorldBorder().isWithinBounds(target)
                    || !level.getBlockState(target).canBeReplaced(context)) { return null; }
            if (part < 6 && !level.getBlockState(target.below()).isFaceSturdy(level, target.below(), Direction.UP)) { return null; }
            if (!level.isUnobstructed(defaultBlockState(), target, context.getPlayer() == null
                    ? net.minecraft.world.phys.shapes.CollisionContext.empty()
                    : net.minecraft.world.phys.shapes.CollisionContext.of(context.getPlayer()))) {
                return null;
            }
        }
        return defaultBlockState().setValue(FACING, facing);
    }

    @Override
    public void setPlacedBy(Level level, BlockPos pos, BlockState state, @Nullable LivingEntity placer, ItemStack stack) {
        Direction facing = state.getValue(FACING);
        for (int part=1; part<PART_COUNT; part++) {
            level.setBlock(partPosition(pos, facing, part), state.setValue(PART, part), 18);
        }
        notifyParts(level, pos, facing);
        if (placer instanceof ServerPlayer player && level.getBlockEntity(pos) instanceof ClawMachineBlockEntity machine) {
            machine.assignOwner(player);
            ClawMachineAccessMenu.open(player, machine, true);
        }
    }

    private void notifyParts(Level level, BlockPos anchor, Direction facing) {
        for (int part=0; part<PART_COUNT; part++) {
            BlockPos target = partPosition(anchor, facing, part);
            level.getBlockState(target).updateNeighbourShapes(level, target, 3);
            level.updateNeighborsAt(target, this);
        }
    }

    @Override
    protected boolean canSurvive(BlockState state, LevelReader level, BlockPos pos) {
        int part = state.getValue(PART);
        return part < 6 ? level.getBlockState(pos.below()).isFaceSturdy(level, pos.below(), Direction.UP)
            : matches(level.getBlockState(pos.below()), state.getValue(FACING), part-6);
    }

    @Override
    protected BlockState updateShape(BlockState state, Direction direction, BlockState neighbor,
            LevelAccessor level, BlockPos pos, BlockPos neighborPos) {
        if (direction == Direction.DOWN && !canSurvive(state, level, pos)) { return Blocks.AIR.defaultBlockState(); }
        BlockPos anchor = getAnchor(state, pos);
        Direction facing = state.getValue(FACING);
        for (int part=0; part<PART_COUNT; part++) {
            if (partPosition(anchor, facing, part).equals(neighborPos) && !matches(neighbor, facing, part)) {
                return Blocks.AIR.defaultBlockState();
            }
        }
        return state;
    }

    @Override
    public BlockState playerWillDestroy(Level level, BlockPos pos, BlockState state, Player player) {
        if (!level.isClientSide && player.isCreative()) {
            BlockPos anchor = getAnchor(state, pos);
            Direction facing = state.getValue(FACING);
            for (int part=0; part<PART_COUNT; part++) {
                BlockPos target = partPosition(anchor, facing, part);
                if (matches(level.getBlockState(target), facing, part)) { level.setBlock(target, Blocks.AIR.defaultBlockState(), 18); }
            }
            notifyParts(level, anchor, facing);
        }
        return super.playerWillDestroy(level, pos, state, player);
    }

    public static void openOperator(ServerPlayer player, ClawMachineBlockEntity machine) {
        if (machine.isOwnerOrCreative(player)) { ClawMachineMenu.openOperator(player, machine, false); }
        else { ClawMachineAccessMenu.open(player, machine, false); }
    }

    private void interact(Level level, BlockPos pos, Player player) {
        ClawMachineBlockEntity machine = machineAt(level, pos);
        if (player instanceof ServerPlayer serverPlayer && machine != null) {
            if (player.isShiftKeyDown()) { openOperator(serverPlayer, machine); }
            else { ClawMachineMenu.openPlay(serverPlayer, machine); }
        }
    }

    @Override
    protected ItemInteractionResult useItemOn(ItemStack stack, BlockState state, Level level, BlockPos pos,
            Player player, InteractionHand hand, BlockHitResult hit) {
        if (hand != InteractionHand.MAIN_HAND || (player.isShiftKeyDown() && !stack.isEmpty())) {
            return ItemInteractionResult.SKIP_DEFAULT_BLOCK_INTERACTION;
        }
        interact(level, pos, player);
        return ItemInteractionResult.sidedSuccess(level.isClientSide);
    }

    @Override
    protected InteractionResult useWithoutItem(BlockState state, Level level, BlockPos pos, Player player, BlockHitResult hit) {
        interact(level, pos, player);
        return InteractionResult.sidedSuccess(level.isClientSide);
    }

    @Override
    protected void onRemove(BlockState state, Level level, BlockPos pos, BlockState replacement, boolean moving) {
        if (!state.is(replacement.getBlock())) {
            if (level.getBlockEntity(pos) instanceof ClawMachineBlockEntity machine) { machine.dropInventory(); }
            super.onRemove(state, level, pos, replacement, moving);
            level.removeBlockEntity(pos);
        }
    }

    @Nullable
    @Override
    public BlockEntity newBlockEntity(BlockPos pos, BlockState state) {
        return state.getValue(PART) == 0 ? new ClawMachineBlockEntity(pos, state) : null;
    }

    @Nullable
    @Override
    public <T extends BlockEntity> BlockEntityTicker<T> getTicker(Level level, BlockState state, BlockEntityType<T> type) {
        return !level.isClientSide && state.getValue(PART) == 0 && type == JapaneseArcades.CLAW_MACHINE_ENTITY.get()
            ? (world, pos, current, entity) -> ClawMachineBlockEntity.serverTick(world, pos, current, (ClawMachineBlockEntity)entity) : null;
    }

    @Override
    public PushReaction getPistonPushReaction(BlockState state) { return PushReaction.BLOCK; }
    @Override
    protected BlockState rotate(BlockState state, Rotation rotation) { return state.setValue(FACING, rotation.rotate(state.getValue(FACING))); }
    @Override
    protected BlockState mirror(BlockState state, Mirror mirror) { return state.rotate(mirror.getRotation(state.getValue(FACING))); }
    @Override
    protected void createBlockStateDefinition(StateDefinition.Builder<Block, BlockState> builder) { builder.add(FACING, PART); }
}
