package local.japanesearcades;

import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Set;
import java.util.UUID;
import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.entity.item.ItemEntity;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.block.state.BlockState;

/** Plans conversions before delivering overflow, so a canceled spawn cannot lose a collectible. */
public final class MobFigureInteraction {
    private record BoxKey(ServerLevel level, BlockPos pos) {}
    private static final Set<UUID> ACTIVE_PLAYERS = new HashSet<>();
    private static final Set<BoxKey> ACTIVE_BOXES = new HashSet<>();
    private MobFigureInteraction() {}

    public static boolean openHeld(ServerPlayer player, InteractionHand hand) {
        ItemStack held = player.getItemInHand(hand);
        if (!(held.getItem() instanceof MobFigureItem item)
                || !(item.getBlock() instanceof MobFigureBlock block) || block.form() != MobFigureBlock.Form.BOXED
                || !player.isShiftKeyDown()) { return false; }
        return exchange(player, hand, null, null, block, true);
    }

    static boolean exchangePlaced(ServerPlayer player, InteractionHand hand, BlockPos pos, BlockState state, boolean opening) {
        if (!(state.getBlock() instanceof MobFigureBlock block)
                || block.form() != (opening ? MobFigureBlock.Form.BOXED : MobFigureBlock.Form.BOX)
                || (opening ? !player.getItemInHand(hand).isEmpty()
                    : !player.getItemInHand(hand).is(block.counterpart(MobFigureBlock.Form.FIGURE).asItem()))) { return false; }
        return exchange(player, hand, pos, state, block, opening);
    }

    private static boolean valid(ServerPlayer player, ServerLevel level, BlockPos pos, BlockState expected) {
        return player.isAlive() && !player.isSpectator() && player.mayBuild() && player.serverLevel() == level
            && (pos == null || (player.canInteractWithBlock(pos, 0) && level.mayInteract(player, pos)
                && level.getBlockState(pos) == expected));
    }

    private static boolean exchange(ServerPlayer player, InteractionHand hand, BlockPos pos, BlockState expected,
            MobFigureBlock block, boolean opening) {
        ServerLevel level = player.serverLevel();
        if (!valid(player, level, pos, expected) || !ACTIVE_PLAYERS.add(player.getUUID())) { return false; }
        BoxKey key = pos == null ? null : new BoxKey(level, pos.immutable());
        if (key != null && !ACTIVE_BOXES.add(key)) { ACTIVE_PLAYERS.remove(player.getUUID()); return false; }
        List<ItemEntity> drops = new ArrayList<>();
        List<ItemStack> expectedDrops = new ArrayList<>();
        boolean committed = false;
        try {
            var inventory = player.getInventory();
            int selected = inventory.selected;
            List<ItemStack> before = new ArrayList<>(), after = new ArrayList<>();
            for (int slot = 0; slot < inventory.getContainerSize(); slot++) {
                before.add(inventory.getItem(slot).copy());
                after.add(inventory.getItem(slot).copy());
            }
            // Conversions consume the source even in creative, just like sealed capsules.
            if (pos == null || !opening) { after.get(hand == InteractionHand.MAIN_HAND ? selected : 40).shrink(1); }
            List<ItemStack> outputs = new ArrayList<>();
            if (opening) { outputs.add(new ItemStack(block.counterpart(MobFigureBlock.Form.FIGURE))); }
            if (pos == null) { outputs.add(new ItemStack(block.counterpart(MobFigureBlock.Form.BOX))); }
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
            if (!valid(player, level, pos, expected) || inventory.selected != selected) { return false; }
            for (int slot = 0; slot < before.size(); slot++) {
                if (!ItemStack.matches(before.get(slot), inventory.getItem(slot))) { return false; }
            }
            // A second spawn callback may also remove or replace the first output.
            for (int index = 0; index < drops.size(); index++) {
                ItemEntity drop = drops.get(index);
                if (drop.isRemoved() || !ItemStack.matches(drop.getItem(), expectedDrops.get(index))) { return false; }
            }
            if (pos != null) {
                BlockState replacement = block.counterpart(opening ? MobFigureBlock.Form.BOX : MobFigureBlock.Form.BOXED)
                    .defaultBlockState().setValue(MobFigureBlock.FACING, expected.getValue(MobFigureBlock.FACING));
                if (!level.setBlock(pos, replacement, 3)) { return false; }
            }
            for (int slot = 0; slot < after.size(); slot++) { inventory.setItem(slot, after.get(slot)); }
            inventory.setChanged();
            player.inventoryMenu.broadcastChanges();
            committed = true;
            level.playSound(null, pos == null ? player.blockPosition() : pos, SoundEvents.BUNDLE_DROP_CONTENTS,
                SoundSource.PLAYERS, .6F, opening ? 1.2F : .9F);
            return true;
        } finally {
            if (!committed) { drops.forEach(ItemEntity::discard); }
            ACTIVE_PLAYERS.remove(player.getUUID());
            if (key != null) { ACTIVE_BOXES.remove(key); }
        }
    }

    private static void insert(List<ItemStack> inventory, ItemStack output) {
        // Merge into main inventory or existing offhand stacks, never armor slots.
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
