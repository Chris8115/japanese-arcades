package local.japanesearcades;

import java.util.List;
import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.Holder;
import net.minecraft.core.registries.Registries;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.ResourceKey;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.decoration.PaintingVariant;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.TooltipFlag;
import net.minecraft.world.item.context.UseOnContext;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.gameevent.GameEvent;

/** Each collectible fixes its artwork; item entity-data cannot replace its art or behavior. */
public class ArcadePosterItem extends Item {
    private final ResourceKey<PaintingVariant> variant;

    public ArcadePosterItem(Properties properties, String path) {
        super(properties);
        this.variant = ArcadePosterEntity.variantKey(path);
    }

    protected ArcadePosterEntity createPoster(Level level, BlockPos anchor, Direction facing,
                                               Holder<PaintingVariant> artwork) {
        return new ArcadePosterEntity(level, anchor, facing, artwork);
    }

    @Override
    public InteractionResult useOn(UseOnContext context) {
        Direction facing = context.getClickedFace();
        if (!facing.getAxis().isHorizontal()) { return InteractionResult.FAIL; }
        var level = context.getLevel();
        var player = context.getPlayer();
        ItemStack stack = context.getItemInHand();
        BlockPos anchor = context.getClickedPos().relative(facing);
        if (player != null && (!player.isAlive() || player.isSpectator()
            || !player.mayUseItemAt(anchor, facing, stack))) { return InteractionResult.FAIL; }
        var artwork = level.registryAccess().registryOrThrow(Registries.PAINTING_VARIANT).getHolder(variant);
        if (artwork.isEmpty()) { return InteractionResult.FAIL; }
        var poster = createPoster(level, anchor, facing, artwork.get());
        if (!poster.survives()) { return InteractionResult.FAIL; }
        if (!level.isClientSide) {
            if (!level.addFreshEntity(poster)) { return InteractionResult.FAIL; }
            poster.playPlacementSound();
            level.gameEvent(player, GameEvent.ENTITY_PLACE, poster.position());
        }
        stack.consume(1, player);
        return InteractionResult.sidedSuccess(level.isClientSide);
    }

    @Override
    public void appendHoverText(ItemStack stack, TooltipContext context, List<Component> tooltip, TooltipFlag flag) {
        tooltip.add(Component.translatable("tooltip.japanesearcades.arcade_poster").withStyle(ChatFormatting.GRAY));
    }
}
