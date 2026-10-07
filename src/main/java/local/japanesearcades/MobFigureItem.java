package local.japanesearcades;

import java.util.List;
import net.minecraft.ChatFormatting;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResultHolder;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.BlockItem;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.TooltipFlag;
import net.minecraft.world.level.Level;

/** Normal placement remains available; sneaking in air opens one boxed figure. */
public final class MobFigureItem extends BlockItem {
    public MobFigureItem(MobFigureBlock block, Properties properties) { super(block, properties); }

    @Override public InteractionResultHolder<ItemStack> use(Level level, Player player, InteractionHand hand) {
        ItemStack stack = player.getItemInHand(hand);
        if (((MobFigureBlock)getBlock()).form() != MobFigureBlock.Form.BOXED || !player.isShiftKeyDown()) {
            return InteractionResultHolder.pass(stack);
        }
        if (level.isClientSide) { return InteractionResultHolder.success(stack); }
        return player instanceof ServerPlayer serverPlayer && MobFigureInteraction.openHeld(serverPlayer, hand)
            ? InteractionResultHolder.consume(player.getItemInHand(hand)) : InteractionResultHolder.fail(stack);
    }

    @Override public void appendHoverText(ItemStack stack, TooltipContext context, List<Component> lines, TooltipFlag flags) {
        super.appendHoverText(stack, context, lines, flags);
        String key = switch (((MobFigureBlock)getBlock()).form()) {
            case FIGURE -> "figure";
            case BOX -> "empty_box";
            case BOXED -> "boxed";
        };
        lines.add(Component.translatable("tooltip.japanesearcades.mob_figure." + key).withStyle(ChatFormatting.GRAY));
    }
}
