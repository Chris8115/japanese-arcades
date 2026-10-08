package local.japanesearcades;

import com.mojang.serialization.Codec;
import com.mojang.serialization.MapCodec;
import com.mojang.serialization.codecs.RecordCodecBuilder;
import java.util.List;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.ItemInteractionResult;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.context.BlockPlaceContext;
import net.minecraft.world.level.BlockGetter;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.HorizontalDirectionalBlock;
import net.minecraft.world.level.block.Mirror;
import net.minecraft.world.level.block.Rotation;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.StateDefinition;
import net.minecraft.world.phys.BlockHitResult;
import net.minecraft.world.phys.shapes.CollisionContext;
import net.minecraft.world.phys.shapes.VoxelShape;

/** Three persistent, decorative forms of each collectible: loose, empty box and boxed. */
public final class MobFigureBlock extends HorizontalDirectionalBlock {
    public enum Form { FIGURE, BOX, BOXED }
    /** All 82 vanilla 1.21.1 Mob entity types; original six retain their collection order. */
    public static final List<String> MOBS = List.of(
        "creeper", "zombie", "skeleton", "enderman", "slime", "axolotl",
        "allay", "armadillo", "bat", "bee", "blaze", "bogged", "breeze", "camel", "cat", "cave_spider",
        "chicken", "cod", "cow", "dolphin", "donkey", "drowned", "elder_guardian", "ender_dragon", "endermite",
        "evoker", "fox", "frog", "ghast", "giant", "glow_squid", "goat", "guardian", "hoglin", "horse", "husk",
        "illusioner", "iron_golem", "llama", "magma_cube", "mooshroom", "mule", "ocelot", "panda", "parrot",
        "phantom", "pig", "piglin", "piglin_brute", "pillager", "polar_bear", "pufferfish", "rabbit", "ravager",
        "salmon", "sheep", "shulker", "silverfish", "skeleton_horse", "sniffer", "snow_golem", "spider", "squid",
        "stray", "strider", "tadpole", "trader_llama", "tropical_fish", "turtle", "vex", "villager", "vindicator",
        "wandering_trader", "warden", "witch", "wither", "wither_skeleton", "wolf", "zoglin", "zombie_horse",
        "zombie_villager", "zombified_piglin"
    );
    public static final MapCodec<MobFigureBlock> CODEC = RecordCodecBuilder.mapCodec(instance -> instance.group(
        Codec.STRING.fieldOf("mob").forGetter(block -> block.mob),
        Codec.STRING.xmap(Form::valueOf, Form::name).fieldOf("form").forGetter(block -> block.form),
        propertiesCodec()).apply(instance, MobFigureBlock::new));
    private static final VoxelShape FIGURE_SHAPE = Block.box(4, 0, 4, 12, 11.5, 12);
    private static final VoxelShape BOX_NORTH_SOUTH = Block.box(3, 0, 4, 13, 14, 12);
    private static final VoxelShape BOX_EAST_WEST = Block.box(4, 0, 3, 12, 14, 13);
    private final String mob;
    private final Form form;

    public MobFigureBlock(String mob, Form form, Properties properties) {
        super(properties);
        this.mob = mob;
        this.form = form;
        registerDefaultState(stateDefinition.any().setValue(FACING, Direction.NORTH));
    }

    public String mob() { return mob; }
    public Form form() { return form; }
    public static String path(String mob, Form form) {
        return switch (form) {
            case FIGURE -> mob + "_figure";
            case BOX -> mob + "_figure_box";
            case BOXED -> "boxed_" + mob + "_figure";
        };
    }
    public Block counterpart(Form target) {
        return BuiltInRegistries.BLOCK.get(ResourceLocation.fromNamespaceAndPath(JapaneseArcades.MOD_ID, path(mob, target)));
    }

    @Override protected MapCodec<MobFigureBlock> codec() { return CODEC; }
    @Override public BlockState getStateForPlacement(BlockPlaceContext context) {
        return defaultBlockState().setValue(FACING, context.getHorizontalDirection().getOpposite());
    }
    @Override protected VoxelShape getShape(BlockState state, BlockGetter level, BlockPos pos, CollisionContext context) {
        return form == Form.FIGURE ? FIGURE_SHAPE
            : state.getValue(FACING).getAxis() == Direction.Axis.X ? BOX_EAST_WEST : BOX_NORTH_SOUTH;
    }
    @Override protected BlockState rotate(BlockState state, Rotation rotation) {
        return state.setValue(FACING, rotation.rotate(state.getValue(FACING)));
    }
    @Override protected BlockState mirror(BlockState state, Mirror mirror) { return state.rotate(mirror.getRotation(state.getValue(FACING))); }
    @Override protected void createBlockStateDefinition(StateDefinition.Builder<Block, BlockState> builder) { builder.add(FACING); }

    @Override protected ItemInteractionResult useItemOn(ItemStack stack, BlockState state, Level level, BlockPos pos,
            Player player, InteractionHand hand, BlockHitResult hit) {
        boolean opening = form == Form.BOXED && stack.isEmpty();
        boolean packing = form == Form.BOX && stack.is(counterpart(Form.FIGURE).asItem());
        if (!opening && !packing) { return ItemInteractionResult.SKIP_DEFAULT_BLOCK_INTERACTION; }
        if (level.isClientSide) { return ItemInteractionResult.SUCCESS; }
        return player instanceof ServerPlayer serverPlayer
            && MobFigureInteraction.exchangePlaced(serverPlayer, hand, pos, state, opening)
                ? ItemInteractionResult.CONSUME : ItemInteractionResult.FAIL;
    }

    @Override protected InteractionResult useWithoutItem(BlockState state, Level level, BlockPos pos, Player player, BlockHitResult hit) {
        if (form != Form.BOXED || !player.getMainHandItem().isEmpty()) { return InteractionResult.PASS; }
        if (level.isClientSide) { return InteractionResult.SUCCESS; }
        return player instanceof ServerPlayer serverPlayer
            && MobFigureInteraction.exchangePlaced(serverPlayer, InteractionHand.MAIN_HAND, pos, state, true)
                ? InteractionResult.CONSUME : InteractionResult.FAIL;
    }
}
