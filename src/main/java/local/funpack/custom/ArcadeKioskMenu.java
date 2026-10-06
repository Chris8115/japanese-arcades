package local.funpack.custom;

import java.util.ArrayList;
import java.util.List;
import java.util.UUID;
import net.minecraft.core.BlockPos;
import net.minecraft.network.RegistryFriendlyByteBuf;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.entity.item.ItemEntity;
import net.minecraft.world.entity.player.Inventory;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.inventory.AbstractContainerMenu;
import net.minecraft.world.inventory.ClickType;
import net.minecraft.world.inventory.ContainerData;
import net.minecraft.world.inventory.SimpleContainerData;
import net.minecraft.world.inventory.Slot;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;
import net.neoforged.neoforge.common.util.TriState;
import net.neoforged.neoforge.event.entity.player.ItemEntityPickupEvent;

/** Inventory-backed quotes and atomic server-side ordering at one nearby kiosk. */
public final class ArcadeKioskMenu extends AbstractContainerMenu {
    static final String OVERFLOW_MARKER = "funpackcustom:arcade_order_overflow";
    public static final int STATUS_IDLE = 0;
    public static final int STATUS_ORDERED = 1;
    public static final int STATUS_MISSING_MATERIALS = 2;
    public static final int STATUS_UNAVAILABLE = 3;
    private final BlockPos blockPos;
    private final Level level;
    private final UUID viewer;
    private final ContainerData data = new SimpleContainerData(1);

    public ArcadeKioskMenu(int id, Inventory inventory, RegistryFriendlyByteBuf buffer) {
        this(id, inventory, buffer.readBlockPos());
    }

    ArcadeKioskMenu(int id, Inventory inventory, BlockPos pos) {
        super(FunPackCustom.ARCADE_KIOSK_MENU.get(), id);
        blockPos = pos.immutable();
        level = inventory.player.level();
        viewer = inventory.player.getUUID();
        for (int row = 0; row < 3; row++) {
            for (int column = 0; column < 9; column++) {
                addSlot(new Slot(inventory, 9 + row * 9 + column, 79 + column * 18, 154 + row * 18));
            }
        }
        for (int column = 0; column < 9; column++) { addSlot(new Slot(inventory, column, 79 + column * 18, 212)); }
        addDataSlots(data);
    }

    public BlockPos getBlockPos() { return blockPos; }
    public int getStatus() { return data.get(0); }

    @Override public boolean stillValid(Player player) {
        if (!viewer.equals(player.getUUID()) || !player.isAlive() || player.isSpectator() || player.level() != level) { return false; }
        if (level.isClientSide) { return true; }
        return (player.canInteractWithBlock(blockPos, 0) || player.canInteractWithBlock(blockPos.above(), 0))
            && level.hasChunkAt(blockPos) && ArcadeKioskBlock.isComplete(level, blockPos);
    }

    @Override public void clicked(int slot, int button, ClickType click, Player player) {
        if (stillValid(player)) { super.clicked(slot, button, click, player); }
    }

    @Override public ItemStack quickMoveStack(Player player, int index) {
        if (!stillValid(player) || index < 0 || index >= slots.size() || !slots.get(index).hasItem()) { return ItemStack.EMPTY; }
        Slot slot = slots.get(index);
        ItemStack stack = slot.getItem();
        ItemStack original = stack.copy();
        if (index < 27 ? !moveItemStackTo(stack, 27, 36, false) : !moveItemStackTo(stack, 0, 27, false)) { return ItemStack.EMPTY; }
        if (stack.isEmpty()) { slot.setByPlayer(ItemStack.EMPTY); }
        else { slot.setChanged(); }
        slot.onTake(player, stack);
        return original;
    }

    public void order(ServerPlayer player, ResourceLocation entryId) {
        if (level.isClientSide || player.containerMenu != this || !stillValid(player)) { return; }
        var optional = ArcadeOrderCatalog.find(entryId);
        if (optional.isEmpty()) { setStatus(STATUS_UNAVAILABLE); return; }
        var entry = optional.get();
        List<ItemStack> before = snapshot(player.getInventory());
        List<ItemStack> after = before.stream().map(ItemStack::copy).collect(java.util.stream.Collectors.toCollection(ArrayList::new));
        // Consume a working copy first. No material moves unless every cost can
        // be paid; both packet retries and simultaneous buyers remain ordinary
        // independent, fully paid transactions on the main server thread.
        for (var cost : entry.costs()) {
            int remaining = cost.count();
            for (ItemStack stack : after) {
                if (stack.is(cost.item())) {
                    int taken = Math.min(remaining, stack.getCount());
                    stack.shrink(taken);
                    remaining -= taken;
                    if (remaining == 0) { break; }
                }
            }
            if (remaining != 0) { setStatus(STATUS_MISSING_MATERIALS); return; }
        }
        ItemStack output = entry.output();
        insertOutput(after, output);
        ItemEntity dropped = null;
        if (!output.isEmpty()) {
            dropped = new ItemEntity(level, player.getX(), player.getY() + .4, player.getZ(), output);
            dropped.getPersistentData().putBoolean(OVERFLOW_MARKER, true);
            dropped.setTarget(player.getUUID());
            dropped.setDefaultPickUpDelay();
            // An item-spawn veto must not charge a player for a lost purchase.
            if (!level.addFreshEntity(dropped)) { setStatus(STATUS_UNAVAILABLE); return; }
        }
        // A spawn event can call other mods, so recheck the bound menu and all
        // source stacks before committing its inventory snapshot.
        if (player.containerMenu != this || !stillValid(player) || !sameInventory(player.getInventory(), before)
                || (dropped != null && (dropped.isRemoved() || !ItemStack.matches(dropped.getItem(), entry.output())))) {
            if (dropped != null) { dropped.discard(); }
            setStatus(STATUS_UNAVAILABLE);
            return;
        }
        for (int index = 0; index < 36; index++) { player.getInventory().setItem(index, after.get(index)); }
        player.getInventory().setItem(40, after.get(36));
        player.getInventory().setChanged();
        setStatus(STATUS_ORDERED);
        level.playSound(null, blockPos, SoundEvents.NOTE_BLOCK_CHIME.value(), SoundSource.BLOCKS, .55F, 1.35F);
        player.inventoryMenu.broadcastChanges();
    }

    private void setStatus(int status) { data.set(0, status); broadcastChanges(); }

    private static List<ItemStack> snapshot(Inventory inventory) {
        List<ItemStack> snapshot = new ArrayList<>(37);
        for (int index = 0; index < 36; index++) { snapshot.add(inventory.getItem(index).copy()); }
        snapshot.add(inventory.getItem(40).copy());
        return snapshot;
    }

    private static boolean sameInventory(Inventory inventory, List<ItemStack> snapshot) {
        for (int index = 0; index < 36; index++) {
            if (!ItemStack.matches(inventory.getItem(index), snapshot.get(index))) { return false; }
        }
        return ItemStack.matches(inventory.getItem(40), snapshot.get(36));
    }

    private static void insertOutput(List<ItemStack> inventory, ItemStack output) {
        // Merge first (including an existing offhand stack), then use an empty
        // main slot. Unlike Inventory.add, this never erases creative overflow.
        for (ItemStack slot : inventory) {
            if (!slot.isEmpty() && ItemStack.isSameItemSameComponents(slot, output)) {
                int count = Math.min(output.getCount(), slot.getMaxStackSize() - slot.getCount());
                if (count > 0) { slot.grow(count); output.shrink(count); }
                if (output.isEmpty()) { return; }
            }
        }
        for (int index = 0; index < 36 && !output.isEmpty(); index++) {
            if (inventory.get(index).isEmpty()) { inventory.set(index, output.split(output.getMaxStackSize())); }
        }
    }

    /** Keep a paid ground delivery until a creative buyer actually has room. */
    public static void protectOverflowPickup(ItemEntityPickupEvent.Pre event) {
        if (!event.getPlayer().hasInfiniteMaterials()
                || !event.getItemEntity().getPersistentData().getBoolean(OVERFLOW_MARKER)) { return; }
        ItemStack remaining = event.getItemEntity().getItem().copy();
        insertOutput(snapshot(event.getPlayer().getInventory()), remaining);
        // Vanilla Inventory.add destroys uninsertable creative overflow during
        // automatic pickup. A persistent entity marker scopes this guard to paid
        // kiosk deliveries, including after a save/reload or merged deliveries.
        if (!remaining.isEmpty()) { event.setCanPickup(TriState.FALSE); }
    }
}
