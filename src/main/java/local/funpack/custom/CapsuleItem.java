package local.funpack.custom;

import java.util.List;
import net.minecraft.ChatFormatting;
import net.minecraft.core.component.DataComponents;
import net.minecraft.network.chat.Component;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResultHolder;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.TooltipFlag;
import net.minecraft.world.item.component.ItemContainerContents;
import net.minecraft.world.level.Level;

/** A sealed, persistent reward. Opening consumes one capsule even in creative. */
public final class CapsuleItem extends Item {
    public CapsuleItem(Properties properties) { super(properties); }

    public static ItemStack create(ItemStack reward) {
        if (reward.isEmpty()) { return ItemStack.EMPTY; }
        ItemStack capsule = new ItemStack(FunPackCustom.GACHAPON_CAPSULE.get());
        capsule.set(DataComponents.CONTAINER, ItemContainerContents.fromItems(List.of(reward.copy())));
        return capsule;
    }

    @Override
    public InteractionResultHolder<ItemStack> use(Level level, Player player, InteractionHand hand) {
        ItemStack capsule = player.getItemInHand(hand);
        if (capsule.getOrDefault(DataComponents.CONTAINER, ItemContainerContents.EMPTY).nonEmptyStream().findAny().isEmpty()) {
            if (!level.isClientSide) {
                player.displayClientMessage(Component.translatable("message.funpackcustom.capsule_empty"), true);
            }
            return InteractionResultHolder.fail(capsule);
        }
        if (!level.isClientSide) { openCapsule(player, hand); }
        return InteractionResultHolder.sidedSuccess(player.getItemInHand(hand), level.isClientSide);
    }

    public static boolean openCapsule(Player player, InteractionHand hand) {
        if (player.level().isClientSide) { return false; }
        ItemStack capsule = player.getItemInHand(hand);
        if (!capsule.is(FunPackCustom.GACHAPON_CAPSULE.get())) { return false; }
        List<ItemStack> rewards = capsule.getOrDefault(DataComponents.CONTAINER, ItemContainerContents.EMPTY)
            .nonEmptyStream().toList();
        if (rewards.isEmpty()) { return false; }
        // Copy the component before consuming. Repeated use can never open this
        // particular capsule again, including when all inventory slots are full.
        capsule.shrink(1);
        for (ItemStack reward : rewards) {
            // Inventory.add(stack) deliberately destroys overflow for creative
            // players. Insert only into confirmed space so their prizes survive too.
            var inventory = player.getInventory();
            while (!reward.isEmpty()) {
                int slot = inventory.getSlotWithRemainingSpace(reward);
                if (slot < 0) { slot = inventory.getFreeSlot(); }
                if (slot < 0) { break; }
                int room = Math.min(inventory.getMaxStackSize(), reward.getMaxStackSize()) - inventory.getItem(slot).getCount();
                if (room <= 0) { break; }
                inventory.add(slot, reward.split(room));
            }
            if (!reward.isEmpty()) {
                var drop = player.drop(reward, false);
                if (drop != null) { drop.setTarget(player.getUUID()); }
            }
        }
        player.getInventory().setChanged();
        player.getCooldowns().addCooldown(FunPackCustom.GACHAPON_CAPSULE.get(), 8);
        player.level().playSound(null, player.blockPosition(), SoundEvents.BUNDLE_DROP_CONTENTS,
            SoundSource.PLAYERS, .6F, 1.3F);
        return true;
    }

    @Override
    public void appendHoverText(ItemStack stack, TooltipContext context, List<Component> lines, TooltipFlag flags) {
        lines.add(Component.translatable("tooltip.funpackcustom.gachapon_capsule").withStyle(ChatFormatting.GRAY));
    }
}
