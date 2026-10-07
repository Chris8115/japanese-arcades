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

/** The same persistent package can be carried, displayed, and opened without losing its label. */
public final class CustomDisplayBoxItem extends BlockItem {
    public CustomDisplayBoxItem(CustomDisplayBoxBlock block, Properties properties) { super(block, properties); }

    @Override public InteractionResultHolder<ItemStack> use(Level level, Player player, InteractionHand hand) {
        ItemStack stack = player.getItemInHand(hand);
        if (!player.isShiftKeyDown() || CustomDisplayBoxData.from(stack).isEmpty()) { return InteractionResultHolder.pass(stack); }
        if (level.isClientSide) { return InteractionResultHolder.success(stack); }
        return player instanceof ServerPlayer serverPlayer && CustomDisplayBoxInteraction.openHeld(serverPlayer, hand)
            ? InteractionResultHolder.consume(player.getItemInHand(hand)) : InteractionResultHolder.fail(player.getItemInHand(hand));
    }
    @Override public void appendHoverText(ItemStack stack, TooltipContext context, List<Component> lines, TooltipFlag flags) {
        super.appendHoverText(stack, context, lines, flags);
        var data = CustomDisplayBoxData.from(stack);
        ItemStack reference = data.retainedItem();
        if (!reference.isEmpty()) {
            lines.add(Component.translatable(data.isEmpty() ? "tooltip.japanesearcades.custom_display_box.previous"
                : "tooltip.japanesearcades.custom_display_box.contains", reference.getHoverName()).withStyle(ChatFormatting.GRAY));
        }
        lines.add(Component.translatable(data.isEmpty() ? "tooltip.japanesearcades.custom_display_box.empty"
            : "tooltip.japanesearcades.custom_display_box.filled").withStyle(ChatFormatting.GRAY));
    }
}
