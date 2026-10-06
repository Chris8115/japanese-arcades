package local.funpack.custom;

import javax.annotation.Nullable;
import net.minecraft.core.BlockPos;
import net.minecraft.network.RegistryFriendlyByteBuf;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.Container;
import net.minecraft.world.SimpleContainer;
import net.minecraft.world.entity.player.Inventory;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.inventory.AbstractContainerMenu;
import net.minecraft.world.inventory.ClickType;
import net.minecraft.world.inventory.ContainerData;
import net.minecraft.world.inventory.SimpleContainerData;
import net.minecraft.world.inventory.Slot;
import net.minecraft.world.item.ItemStack;

/** Access is a short-lived server menu session, never a client-provided permission flag. */
public final class GachaponMenu extends AbstractContainerMenu {
    @Nullable private final GachaponBlockEntity machine;
    private final BlockPos blockPos;
    private final ContainerData data;
    private final boolean authenticated;
    private final int passwordRevision;
    private final java.util.UUID viewer;

    public GachaponMenu(int id, Inventory playerInventory, RegistryFriendlyByteBuf buffer) {
        this(id, playerInventory, buffer.readBlockPos(), buffer.readBoolean());
    }

    private GachaponMenu(int id, Inventory playerInventory, BlockPos pos, boolean canChangePassword) {
        super(FunPackCustom.GACHAPON_MENU.get(), id);
        machine = null;
        blockPos = pos;
        viewer = playerInventory.player.getUUID();
        authenticated = false;
        passwordRevision = 0;
        data = new SimpleContainerData(3);
        data.set(0, 1);
        data.set(1, canChangePassword ? 1 : 0);
        addSlots(new SimpleContainer(GachaponBlockEntity.INVENTORY_SIZE), playerInventory);
        addDataSlots(data);
    }

    GachaponMenu(int id, Inventory playerInventory, GachaponBlockEntity machine, boolean authenticated) {
        super(FunPackCustom.GACHAPON_MENU.get(), id);
        this.machine = machine;
        this.blockPos = machine.getBlockPos();
        this.authenticated = authenticated;
        this.passwordRevision = machine.passwordRevision();
        this.viewer = playerInventory.player.getUUID();
        data = new ContainerData() {
            private int status;
            @Override public int get(int index) {
                return switch (index) {
                    case 0 -> machine.getDispenseAmount();
                    case 1 -> machine.isOwnerOrCreative(playerInventory.player) ? 1 : 0;
                    case 2 -> status;
                    default -> 0;
                };
            }
            @Override public void set(int index, int value) { if (index == 2) { status = value; } }
            @Override public int getCount() { return 3; }
        };
        addSlots(machine.operatorInventory(), playerInventory);
        addDataSlots(data);
    }

    private void addSlots(Container contents, Inventory playerInventory) {
        addSlot(new Slot(contents, GachaponBlockEntity.PRICE_SLOT, 20, 35));
        for (int row = 0; row < 3; row++) {
            for (int column = 0; column < 3; column++) {
                addSlot(new Slot(contents, GachaponBlockEntity.REWARD_START + row * 3 + column, 82 + column * 18, 35 + row * 18));
            }
        }
        for (int row = 0; row < 3; row++) {
            for (int column = 0; column < 3; column++) {
                addSlot(new Slot(contents, GachaponBlockEntity.PAYMENT_START + row * 3 + column, 158 + column * 18, 35 + row * 18) {
                    @Override public boolean mayPlace(ItemStack stack) { return false; }
                });
            }
        }
        for (int row = 0; row < 3; row++) {
            for (int column = 0; column < 9; column++) { addSlot(new Slot(playerInventory, column + row * 9 + 9, 35 + column * 18, 151 + row * 18)); }
        }
        for (int column = 0; column < 9; column++) { addSlot(new Slot(playerInventory, column, 35 + column * 18, 209)); }
    }

    public BlockPos getBlockPos() { return blockPos; }
    public int getDispenseAmount() { return data.get(0); }
    public boolean canChangePassword() { return data.get(1) != 0; }
    public int getStatus() { return data.get(2); }

    @Override
    public boolean stillValid(Player player) {
        if (!viewer.equals(player.getUUID())) { return false; }
        return machine == null || (machine.canReach(player) && (machine.isOwnerOrCreative(player)
            || (authenticated && machine.passwordRevision() == passwordRevision)));
    }

    @Override
    public void clicked(int slot, int button, ClickType click, Player player) {
        if (stillValid(player)) { super.clicked(slot, button, click, player); }
    }

    public void applySettings(ServerPlayer player, int amount, String newPassword) {
        if (machine == null || player.containerMenu != this || !stillValid(player)) { return; }
        if (amount < 1 || amount > 64) { data.set(2, 7); return; }
        if (!newPassword.isEmpty()) {
            if (!machine.isOwnerOrCreative(player)) { data.set(2, 6); return; }
            if (!GachaponBlockEntity.validPassword(newPassword)) { data.set(2, 3); return; }
            machine.setPassword(player, newPassword);
            data.set(2, 4);
        } else { data.set(2, 5); }
        machine.setDispenseAmount(amount);
        broadcastChanges();
    }

    public void changePassword(ServerPlayer player, String password) { applySettings(player, getDispenseAmount(), password); }
    public void updateDispenseAmount(ServerPlayer player, int amount) { applySettings(player, amount, ""); }

    @Override
    public ItemStack quickMoveStack(Player player, int index) {
        if (!stillValid(player) || index < 0 || index >= slots.size()) { return ItemStack.EMPTY; }
        Slot slot = slots.get(index);
        if (!slot.hasItem()) { return ItemStack.EMPTY; }
        ItemStack original = slot.getItem();
        ItemStack copy = original.copy();
        int machineSlots = GachaponBlockEntity.INVENTORY_SIZE;
        if (index < machineSlots) {
            if (!moveItemStackTo(original, machineSlots, slots.size(), true)) { return ItemStack.EMPTY; }
        } else if (!moveItemStackTo(original, GachaponBlockEntity.REWARD_START, GachaponBlockEntity.PAYMENT_START, false)) {
            return ItemStack.EMPTY;
        }
        if (original.isEmpty()) { slot.setByPlayer(ItemStack.EMPTY); }
        else { slot.setChanged(); }
        slot.onTake(player, original);
        return copy;
    }
}
