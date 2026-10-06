package local.funpack.custom;

import com.mojang.serialization.MapCodec;
import javax.annotation.Nullable;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.util.StringRepresentable;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.ItemInteractionResult;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.JukeboxSong;
import net.minecraft.stats.Stats;
import net.minecraft.world.item.context.BlockPlaceContext;
import net.minecraft.world.level.BlockGetter;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.LevelAccessor;
import net.minecraft.world.level.LevelReader;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.HorizontalDirectionalBlock;
import net.minecraft.world.level.block.EntityBlock;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.entity.BlockEntityTicker;
import net.minecraft.world.level.block.entity.BlockEntityType;
import net.minecraft.world.level.block.Mirror;
import net.minecraft.world.level.block.Rotation;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.StateDefinition;
import net.minecraft.world.level.block.state.properties.EnumProperty;
import net.minecraft.world.level.block.state.properties.BlockStateProperties;
import net.minecraft.world.level.block.state.properties.BooleanProperty;
import net.minecraft.world.level.gameevent.GameEvent;
import net.minecraft.world.phys.BlockHitResult;
import net.minecraft.world.phys.shapes.CollisionContext;
import net.minecraft.world.phys.shapes.VoxelShape;

/** Shared three-block-tall arcade behavior; the original class name is retained for compatibility. */
public class NostalgiaCabinetBlock extends HorizontalDirectionalBlock implements EntityBlock {
    public static final MapCodec<NostalgiaCabinetBlock> CODEC = simpleCodec(NostalgiaCabinetBlock::new);
    public static final EnumProperty<Part> PART = EnumProperty.create("part", Part.class);
    public static final BooleanProperty HAS_RECORD = BlockStateProperties.HAS_RECORD;

    public NostalgiaCabinetBlock(Properties properties) {
        super(properties);
        registerDefaultState(stateDefinition.any().setValue(FACING, Direction.NORTH).setValue(PART, Part.BASE)
            .setValue(HAS_RECORD, false));
    }

    @Override
    protected MapCodec<? extends HorizontalDirectionalBlock> codec() {
        return CODEC;
    }

    @Nullable
    @Override
    public BlockState getStateForPlacement(BlockPlaceContext context) {
        BlockPos pos = context.getClickedPos();
        Level level = context.getLevel();
        if (pos.getY() + 2 >= level.getMaxBuildHeight()
                || !level.getBlockState(pos.above()).canBeReplaced(context)
                || !level.getBlockState(pos.above(2)).canBeReplaced(context)) {
            return null;
        }
        return defaultBlockState().setValue(FACING, context.getHorizontalDirection().getOpposite());
    }

    @Override
    public void setPlacedBy(Level level, BlockPos pos, BlockState state, @Nullable LivingEntity placer, ItemStack stack) {
        level.setBlock(pos.above(), state.setValue(PART, Part.CONSOLE), 2);
        level.setBlock(pos.above(2), state.setValue(PART, Part.MARQUEE), 3);
        if (level.getBlockEntity(pos) instanceof NostalgiaJukeboxBlockEntity cabinet && !cabinet.isEmpty()) {
            level.setBlock(pos, state.setValue(HAS_RECORD, true), 2);
        }
    }

    @Override
    protected boolean canSurvive(BlockState state, LevelReader level, BlockPos pos) {
        Part part = state.getValue(PART);
        if (part == Part.BASE) {
            return level.getBlockState(pos.below()).isFaceSturdy(level, pos.below(), Direction.UP);
        }
        return matches(level.getBlockState(pos.below()), part.below(), state.getValue(FACING));
    }

    @Override
    protected BlockState updateShape(BlockState state, Direction direction, BlockState neighbor,
            LevelAccessor level, BlockPos pos, BlockPos neighborPos) {
        Part part = state.getValue(PART);
        if (direction == Direction.DOWN) {
            boolean supported = part == Part.BASE ? state.canSurvive(level, pos)
                : matches(neighbor, part.below(), state.getValue(FACING));
            if (!supported) { return Blocks.AIR.defaultBlockState(); }
        }
        if (direction == Direction.UP && part != Part.MARQUEE
                && !matches(neighbor, part.above(), state.getValue(FACING))) {
            return Blocks.AIR.defaultBlockState();
        }
        return super.updateShape(state, direction, neighbor, level, pos, neighborPos);
    }

    private boolean matches(BlockState state, Part part, Direction facing) {
        return state.is(this) && state.getValue(PART) == part && state.getValue(FACING) == facing;
    }

    private BlockPos basePosition(BlockPos pos, BlockState state) { return pos.below(state.getValue(PART).ordinal()); }

    @Nullable
    private NostalgiaJukeboxBlockEntity jukebox(Level level, BlockPos pos, BlockState state) {
        BlockPos base = basePosition(pos, state);
        if (matches(level.getBlockState(base), Part.BASE, state.getValue(FACING))
                && level.getBlockEntity(base) instanceof NostalgiaJukeboxBlockEntity cabinet) {
            return cabinet;
        }
        return null;
    }

    @Override
    protected ItemInteractionResult useItemOn(ItemStack stack, BlockState state, Level level, BlockPos pos,
            Player player, InteractionHand hand, BlockHitResult hit) {
        var cabinet = jukebox(level, pos, state);
        BlockPos base = basePosition(pos, state);
        if (cabinet == null || level.getBlockState(base).getValue(HAS_RECORD)
                || JukeboxSong.fromStack(level.registryAccess(), stack).isEmpty()) {
            return ItemInteractionResult.PASS_TO_DEFAULT_BLOCK_INTERACTION;
        }
        if (!level.isClientSide) {
            cabinet.setTheItem(stack.consumeAndReturn(1, player));
            player.awardStat(Stats.PLAY_RECORD);
            level.gameEvent(GameEvent.BLOCK_CHANGE, base, GameEvent.Context.of(player, level.getBlockState(base)));
        }
        return ItemInteractionResult.sidedSuccess(level.isClientSide);
    }

    @Override
    protected InteractionResult useWithoutItem(BlockState state, Level level, BlockPos pos, Player player, BlockHitResult hit) {
        var cabinet = jukebox(level, pos, state);
        if (cabinet != null && level.getBlockState(basePosition(pos, state)).getValue(HAS_RECORD)) {
            cabinet.ejectDisc();
            return InteractionResult.sidedSuccess(level.isClientSide);
        }
        return InteractionResult.PASS;
    }

    @Override
    protected void onRemove(BlockState state, Level level, BlockPos pos, BlockState newState, boolean moving) {
        if (state.getValue(PART) == Part.BASE && (!newState.is(this) || newState.getValue(PART) != Part.BASE)) {
            if (level.getBlockEntity(pos) instanceof NostalgiaJukeboxBlockEntity cabinet) { cabinet.ejectDisc(); }
            level.removeBlockEntity(pos);
        }
        super.onRemove(state, level, pos, newState, moving);
    }

    @Nullable
    @Override
    public BlockEntity newBlockEntity(BlockPos pos, BlockState state) {
        return state.getValue(PART) == Part.BASE ? new NostalgiaJukeboxBlockEntity(pos, state) : null;
    }

    @Nullable
    @Override
    public <T extends BlockEntity> BlockEntityTicker<T> getTicker(Level level, BlockState state, BlockEntityType<T> type) {
        if (level.isClientSide || state.getValue(PART) != Part.BASE || type != FunPackCustom.NOSTALGIA_JUKEBOX.get()) { return null; }
        return (world, pos, current, entity) -> NostalgiaJukeboxBlockEntity.tick(world, pos, current, (NostalgiaJukeboxBlockEntity)entity);
    }

    @Override
    public boolean isSignalSource(BlockState state) { return state.getValue(PART) == Part.BASE; }

    @Override
    protected int getSignal(BlockState state, BlockGetter level, BlockPos pos, Direction direction) {
        return state.getValue(PART) == Part.BASE && level.getBlockEntity(pos) instanceof NostalgiaJukeboxBlockEntity cabinet
            && cabinet.getSongPlayer().isPlaying() ? 15 : 0;
    }

    @Override
    protected boolean hasAnalogOutputSignal(BlockState state) { return state.getValue(PART) == Part.BASE; }

    @Override
    protected int getAnalogOutputSignal(BlockState state, Level level, BlockPos pos) {
        return level.getBlockEntity(pos) instanceof NostalgiaJukeboxBlockEntity cabinet ? cabinet.comparatorOutput() : 0;
    }

    @Override
    public BlockState playerWillDestroy(Level level, BlockPos pos, BlockState state, Player player) {
        // Creative removal must not drop the base when a different section is punched.
        if (!level.isClientSide && player.isCreative()) {
            BlockPos base = pos.below(state.getValue(PART).ordinal());
            for (Part part : Part.values()) {
                BlockPos target = base.above(part.ordinal());
                if (!target.equals(pos) && matches(level.getBlockState(target), part, state.getValue(FACING))) {
                    level.setBlock(target, Blocks.AIR.defaultBlockState(), 35);
                }
            }
        }
        return super.playerWillDestroy(level, pos, state, player);
    }

    @Override
    protected VoxelShape getShape(BlockState state, BlockGetter level, BlockPos pos, CollisionContext context) {
        Part part = state.getValue(PART);
        double minX = part == Part.CONSOLE ? 0 : 1;
        double minZ = part == Part.BASE ? 4 : part == Part.CONSOLE ? 0 : 5.2;
        double maxX = part == Part.CONSOLE ? 16 : 15;
        double maxZ = 15;
        return rotatedBox(state.getValue(FACING), minX, minZ, maxX, maxZ);
    }

    protected static VoxelShape rotatedBox(Direction facing, double minX, double minZ, double maxX, double maxZ) {
        return switch (facing) {
            case EAST -> Block.box(16 - maxZ, 0, minX, 16 - minZ, 16, maxX);
            case SOUTH -> Block.box(16 - maxX, 0, 16 - maxZ, 16 - minX, 16, 16 - minZ);
            case WEST -> Block.box(minZ, 0, 16 - maxX, maxZ, 16, 16 - minX);
            default -> Block.box(minX, 0, minZ, maxX, 16, maxZ);
        };
    }

    @Override
    protected BlockState rotate(BlockState state, Rotation rotation) {
        return state.setValue(FACING, rotation.rotate(state.getValue(FACING)));
    }

    @Override
    protected BlockState mirror(BlockState state, Mirror mirror) {
        return state.rotate(mirror.getRotation(state.getValue(FACING)));
    }

    @Override
    protected void createBlockStateDefinition(StateDefinition.Builder<Block, BlockState> builder) {
        builder.add(FACING, PART, HAS_RECORD);
    }

    public enum Part implements StringRepresentable {
        BASE, CONSOLE, MARQUEE;

        @Override
        public String getSerializedName() { return name().toLowerCase(java.util.Locale.ROOT); }

        Part below() { return values()[ordinal() - 1]; }
        Part above() { return values()[ordinal() + 1]; }
    }
}
