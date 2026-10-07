package local.japanesearcades;

import java.util.List;
import javax.annotation.Nullable;
import net.minecraft.ChatFormatting;
import net.minecraft.network.chat.Component;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResultHolder;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.TooltipFlag;
import net.minecraft.world.level.Level;

/** Nonstackable transferable wallet; balances are never trusted from client requests. */
public final class ArcadePassItem extends Item {
    public ArcadePassItem(Properties properties) { super(properties); }
    public static boolean isPass(ItemStack stack) { return !stack.isEmpty() && stack.getItem() instanceof ArcadePassItem && stack.getCount() == 1; }
    @Nullable public static ArcadePassData data(ItemStack stack) {
        if (!isPass(stack)) { return null; }
        ArcadePassData value = stack.getOrDefault(JapaneseArcades.PASS_DATA.get(), ArcadePassData.empty());
        return value.version() == 1 && value.revision() < Long.MAX_VALUE-1 ? value : null;
    }
    public static void setData(ItemStack stack, ArcadePassData value) {
        if (!isPass(stack)) { throw new IllegalArgumentException("An arcade wallet requires one pass"); }
        stack.set(JapaneseArcades.PASS_DATA.get(), value);
    }
    public static ItemStack createPass() {
        ItemStack pass = new ItemStack(JapaneseArcades.ARCADE_PASS.get());
        setData(pass, ArcadePassData.create());
        return pass;
    }
    public static Component designName(ArcadePassData data) {
        return data.design().equals(ArcadePassData.DEFAULT_DESIGN)
            ? Component.translatable("pass.design.japanesearcades.default") : Component.literal(data.design().toString());
    }
    @Override public InteractionResultHolder<ItemStack> use(Level level, Player player, InteractionHand hand) {
        ItemStack pass = player.getItemInHand(hand);
        ArcadePassData value = data(pass);
        if (!level.isClientSide && value != null) {
            player.displayClientMessage(Component.translatable("arcade.pass.balance", value.credits(), value.prizePoints()), true);
        }
        return InteractionResultHolder.sidedSuccess(pass, level.isClientSide);
    }
    @Override public void appendHoverText(ItemStack stack, TooltipContext context, List<Component> lines, TooltipFlag flags) {
        ArcadePassData value = data(stack);
        if (value == null) { lines.add(Component.translatable("arcade.pass.invalid").withStyle(ChatFormatting.RED)); return; }
        lines.add(Component.translatable("arcade.pass.credits", value.credits()).withStyle(ChatFormatting.AQUA));
        lines.add(Component.translatable("arcade.pass.points", value.prizePoints()).withStyle(ChatFormatting.LIGHT_PURPLE));
        lines.add(designName(value).copy().withStyle(ChatFormatting.GRAY));
        if (!value.id().equals(ArcadePassData.UNASSIGNED)) {
            lines.add(Component.translatable("arcade.pass.id", value.id().toString().substring(0, 8)).withStyle(ChatFormatting.DARK_GRAY));
        }
        lines.add(Component.translatable("arcade.pass.hint").withStyle(ChatFormatting.GRAY));
    }
}
