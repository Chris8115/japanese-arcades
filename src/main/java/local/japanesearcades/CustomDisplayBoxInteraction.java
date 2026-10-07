package local.japanesearcades;

import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Set;
import java.util.UUID;
import net.minecraft.core.BlockPos;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.entity.item.ItemEntity;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.block.state.BlockState;

/** Server-owned item exchanges; rejected delivery leaves the original package intact. */
public final class CustomDisplayBoxInteraction {
    private static final Set<UUID> ACTIVE_PLAYERS = new HashSet<>();
    private static final Set<CustomDisplayBoxBlockEntity> ACTIVE_BOXES = new HashSet<>();
    private CustomDisplayBoxInteraction() {}

    public static boolean openHeld(ServerPlayer player, InteractionHand hand) {
        ItemStack held = player.getItemInHand(hand);
        if (!(held.getItem() instanceof CustomDisplayBoxItem) || !player.isShiftKeyDown()
                || CustomDisplayBoxData.from(held).isEmpty()) { return false; }
        return exchange(player, hand, null);
    }

    static boolean exchangePlaced(ServerPlayer player, InteractionHand hand, CustomDisplayBoxBlockEntity box) {
        ItemStack held = player.getItemInHand(hand);
        if (held.getItem() instanceof CustomDisplayBoxItem || held.isEmpty() == box.data().isEmpty()) { return false; }
        return exchange(player, hand, box);
    }

    private static boolean valid(ServerPlayer player, ServerLevel level, CustomDisplayBoxBlockEntity box,
            BlockState expectedState, CustomDisplayBoxData expectedData, long revision) {
        if (!player.isAlive() || player.isSpectator() || !player.mayBuild() || player.serverLevel() != level) { return false; }
        if (box == null) { return true; }
        BlockPos pos = box.getBlockPos();
        return box.getLevel() == level && !box.isRemoved() && level.getBlockEntity(pos) == box
            && level.getBlockState(pos) == expectedState && box.revision() == revision && box.data().equals(expectedData)
            && player.canInteractWithBlock(pos, 0) && level.mayInteract(player, pos);
    }

    private static boolean exchange(ServerPlayer player, InteractionHand hand, CustomDisplayBoxBlockEntity box) {
        ServerLevel level = player.serverLevel();
        BlockState expectedState = box == null ? null : box.getBlockState();
        CustomDisplayBoxData data = box == null ? CustomDisplayBoxData.from(player.getItemInHand(hand)) : box.data();
        long revision = box == null ? 0 : box.revision();
        boolean opening = box == null || !data.isEmpty();
        if (!valid(player, level, box, expectedState, data, revision) || !ACTIVE_PLAYERS.add(player.getUUID())) { return false; }
        if (box != null && !ACTIVE_BOXES.add(box)) { ACTIVE_PLAYERS.remove(player.getUUID()); return false; }
        List<ItemEntity> drops = new ArrayList<>();
        List<ItemStack> expectedDrops = new ArrayList<>();
        boolean committed = false;
        try {
            // Both block interaction entry points share this dispatch. A consumed normal
            // right-click adjusts only orientation; sneaking follows the extraction path.
            if (box != null && opening && !player.isShiftKeyDown()) {
                CustomDisplayBoxData replacement = data.toggledOrientation();
                box.setData(replacement);
                committed = true;
                player.displayClientMessage(Component.translatable(replacement.straightOn()
                    ? "message.japanesearcades.custom_display_box.straight"
                    : "message.japanesearcades.custom_display_box.angled"), true);
                return true;
            }
            var inventory = player.getInventory();
            int selected = inventory.selected;
            List<ItemStack> before = new ArrayList<>(), after = new ArrayList<>();
            for (int slot = 0; slot < inventory.getContainerSize(); slot++) {
                before.add(inventory.getItem(slot).copy());
                after.add(inventory.getItem(slot).copy());
            }
            int handSlot = hand == InteractionHand.MAIN_HAND ? selected : 40;
            ItemStack held = before.get(handSlot);
            CustomDisplayBoxData replacement = opening ? data.emptied() : data.filledWith(held);
            // Consuming the source in creative also prevents a conversion from copying its contents.
            if (box == null || !opening) { after.get(handSlot).shrink(1); }
            List<ItemStack> outputs = new ArrayList<>();
            if (opening) { outputs.add(data.containedItem()); }
            if (box == null) {
                ItemStack emptyBox = held.copyWithCount(1);
                emptyBox.set(JapaneseArcades.DISPLAY_BOX_DATA.get(), replacement);
                outputs.add(emptyBox);
            }
            for (ItemStack output : outputs) {
                insert(after, output);
                if (output.isEmpty()) { continue; }
                ItemStack expectedDrop = output.copy();
                ItemEntity drop = new ItemEntity(level, player.getX(), player.getY() + .4, player.getZ(), output);
                drop.getPersistentData().putBoolean(ArcadeKioskMenu.OVERFLOW_MARKER, true);
                drop.setTarget(player.getUUID());
                drop.setDefaultPickUpDelay();
                drops.add(drop);
                expectedDrops.add(expectedDrop);
                if (!level.addFreshEntity(drop) || drop.isRemoved() || !ItemStack.matches(drop.getItem(), expectedDrop)) { return false; }
            }
            if (!valid(player, level, box, expectedState, data, revision) || inventory.selected != selected) { return false; }
            for (int slot = 0; slot < before.size(); slot++) {
                if (!ItemStack.matches(before.get(slot), inventory.getItem(slot))) { return false; }
            }
            // A later output's spawn callback can change an earlier accepted entity too.
            for (int index = 0; index < drops.size(); index++) {
                ItemEntity drop = drops.get(index);
                if (drop.isRemoved() || !ItemStack.matches(drop.getItem(), expectedDrops.get(index))) { return false; }
            }
            for (int slot = 0; slot < after.size(); slot++) { inventory.setItem(slot, after.get(slot)); }
            if (box != null) { box.setData(replacement); }
            inventory.setChanged();
            player.inventoryMenu.broadcastChanges();
            committed = true;
            level.playSound(null, box == null ? player.blockPosition() : box.getBlockPos(), SoundEvents.BUNDLE_DROP_CONTENTS,
                SoundSource.PLAYERS, .6F, opening ? 1.2F : .9F);
            return true;
        } finally {
            if (!committed) { drops.forEach(ItemEntity::discard); }
            ACTIVE_PLAYERS.remove(player.getUUID());
            if (box != null) { ACTIVE_BOXES.remove(box); }
        }
    }

    private static void insert(List<ItemStack> inventory, ItemStack output) {
        for (int slot = 0; slot < inventory.size() && !output.isEmpty(); slot++) {
            if (slot >= 36 && slot != 40) { continue; }
            ItemStack target = inventory.get(slot);
            if (!target.isEmpty() && ItemStack.isSameItemSameComponents(target, output)) {
                int amount = Math.min(output.getCount(), Math.max(0, target.getMaxStackSize() - target.getCount()));
                target.grow(amount);
                output.shrink(amount);
            }
        }
        for (int slot = 0; slot < 36 && !output.isEmpty(); slot++) {
            if (inventory.get(slot).isEmpty()) { inventory.set(slot, output.split(output.getMaxStackSize())); }
        }
    }
}
