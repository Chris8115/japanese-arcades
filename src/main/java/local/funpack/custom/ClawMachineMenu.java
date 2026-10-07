package local.funpack.custom;

import java.util.UUID;
import javax.annotation.Nullable;
import net.minecraft.core.BlockPos;
import net.minecraft.network.RegistryFriendlyByteBuf;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.Container;
import net.minecraft.world.SimpleContainer;
import net.minecraft.world.SimpleMenuProvider;
import net.minecraft.world.entity.player.Inventory;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.inventory.AbstractContainerMenu;
import net.minecraft.world.inventory.ClickType;
import net.minecraft.world.inventory.ContainerData;
import net.minecraft.world.inventory.SimpleContainerData;
import net.minecraft.world.inventory.Slot;
import net.minecraft.world.inventory.MenuType;
import net.minecraft.world.item.ItemStack;

/** The active server menu binds every control packet to one viewer, machine and session. */
public final class ClawMachineMenu extends AbstractContainerMenu {
    private static final UUID NO_SESSION = new UUID(0, 0);
    private static final int DATA_COUNT = 7;
    @Nullable private final ClawMachineBlockEntity machine;
    private final BlockPos blockPos;
    private final UUID viewer, sessionId;
    private final boolean operator, authenticated;
    private final int passwordRevision;
    private final ContainerData data;

    public ClawMachineMenu(int id, Inventory inventory, RegistryFriendlyByteBuf buffer) {
        this(FunPackCustom.CLAW_MACHINE_MENU.get(), id, inventory, buffer);
    }

    public static ClawMachineMenu playFromNetwork(int id, Inventory inventory, RegistryFriendlyByteBuf buffer) {
        return new ClawMachineMenu(FunPackCustom.CLAW_MACHINE_PLAY_MENU.get(), id, inventory, buffer);
    }

    private ClawMachineMenu(MenuType<ClawMachineMenu> type, int id, Inventory inventory, RegistryFriendlyByteBuf buffer) {
        super(type, id);
        machine = null;
        blockPos = buffer.readBlockPos();
        operator = buffer.readBoolean();
        boolean changePassword = buffer.readBoolean();
        sessionId = buffer.readUUID();
        viewer = inventory.player.getUUID();
        authenticated = false;
        passwordRevision = 0;
        data = new SimpleContainerData(DATA_COUNT);
        data.set(0, changePassword ? 1 : 0);
        addSlots(new SimpleContainer(ClawMachineBlockEntity.INVENTORY_SIZE), inventory);
        addDataSlots(data);
    }

    ClawMachineMenu(int id, Inventory inventory, ClawMachineBlockEntity machine, boolean operator, boolean authenticated) {
        super(operator ? FunPackCustom.CLAW_MACHINE_MENU.get() : FunPackCustom.CLAW_MACHINE_PLAY_MENU.get(), id);
        this.machine = machine;
        this.blockPos = machine.getBlockPos();
        this.operator = operator;
        this.authenticated = authenticated;
        this.passwordRevision = machine.passwordRevision();
        this.viewer = inventory.player.getUUID();
        this.sessionId = operator || machine.getSessionId() == null ? NO_SESSION : machine.getSessionId();
        data = new ContainerData() {
            private int status;
            @Override public int get(int index) {
                return switch (index) {
                    case 0 -> operator && machine.isOwnerOrCreative(inventory.player) ? 1 : 0;
                    case 1 -> status;
                    case 2 -> operator ? machine.getBaseWinChance() : 0;
                    case 3 -> operator ? machine.getGuaranteePlay() : 0;
                    case 4 -> operator ? Math.min(32767, machine.getPlaysSinceWin()) : 0;
                    case 5 -> operator ? Math.round(machine.getCurrentWinChance()) : 0;
                    case 6 -> machine.getPhase().ordinal();
                    default -> 0;
                };
            }
            @Override public void set(int index, int value) { if (index == 1) status = value; }
            @Override public int getCount() { return DATA_COUNT; }
        };
        if (operator) addSlots(machine.operatorInventory(), inventory);
        else {
            var price = new SimpleContainer(ClawMachineBlockEntity.INVENTORY_SIZE);
            price.setItem(ClawMachineBlockEntity.PRICE_SLOT, machine.getPrice().copy());
            addSlots(price, inventory);
        }
        addDataSlots(data);
    }

    public static boolean openPlay(ServerPlayer player, ClawMachineBlockEntity machine) {
        if (!machine.startSession(player)) return false;
        UUID session = machine.getSessionId();
        if (session == null) return false;
        var opened = player.openMenu(new SimpleMenuProvider((id, inv, viewer) ->
            new ClawMachineMenu(id, inv, machine, false, false), Component.translatable("claw.gui.play_title")),
            buffer -> { buffer.writeBlockPos(machine.getBlockPos()); buffer.writeBoolean(false); buffer.writeBoolean(false); buffer.writeUUID(session); });
        if (opened.isEmpty()) { machine.cancelSession(player); return false; }
        return true;
    }

    public static boolean openOperator(ServerPlayer player, ClawMachineBlockEntity machine, boolean authenticated) {
        if (!machine.canReach(player) || (!authenticated && !machine.isOwnerOrCreative(player))
            || !machine.acquireOperator(player)) return false;
        var opened = player.openMenu(new SimpleMenuProvider((id, inv, viewer) ->
            new ClawMachineMenu(id, inv, machine, true, authenticated), Component.translatable("claw.gui.operator_title")),
            buffer -> { buffer.writeBlockPos(machine.getBlockPos()); buffer.writeBoolean(true); buffer.writeBoolean(machine.isOwnerOrCreative(player)); buffer.writeUUID(NO_SESSION); });
        if (opened.isEmpty()) { machine.releaseOperator(player); return false; }
        return true;
    }

    private void addSlots(Container contents, Inventory inventory) {
        addSlot(new Slot(contents, ClawMachineBlockEntity.PRICE_SLOT, 20, 32) {
            @Override public boolean isActive() { return operator; }
            @Override public boolean mayPlace(ItemStack stack) { return operator; }
            @Override public boolean mayPickup(Player player) { return operator && stillValid(player); }
        });
        if (!operator) return;
        for (int row = 0; row < 3; row++) for (int column = 0; column < 3; column++)
            addSlot(new Slot(contents, ClawMachineBlockEntity.REWARD_START + row * 3 + column, 85 + column * 18, 32 + row * 18));
        for (int row = 0; row < 3; row++) for (int column = 0; column < 3; column++)
            addSlot(new Slot(contents, ClawMachineBlockEntity.PAYMENT_START + row * 3 + column, 175 + column * 18, 32 + row * 18) {
                @Override public boolean mayPlace(ItemStack stack) { return false; }
            });
        for (int row = 0; row < 3; row++) for (int column = 0; column < 9; column++)
            addSlot(new Slot(inventory, 9 + row * 9 + column, 44 + column * 18, 162 + row * 18));
        for (int column = 0; column < 9; column++) addSlot(new Slot(inventory, column, 44 + column * 18, 220));
    }

    public boolean isOperator() { return operator; }
    public BlockPos getBlockPos() { return blockPos; }
    public UUID getSessionId() { return sessionId; }
    public ItemStack getPrice() { return getSlot(0).getItem(); }
    public boolean canChangePassword() { return data.get(0) != 0; }
    public int getStatus() { return data.get(1); }
    public int getBaseWinChance() { return data.get(2); }
    public int getGuaranteePlay() { return data.get(3); }
    public int getPlaysSinceWin() { return data.get(4); }
    public int getCurrentWinChance() { return data.get(5); }
    public ClawMachineBlockEntity.Phase getPhase() {
        var phases = ClawMachineBlockEntity.Phase.values();
        return phases[Math.max(0, Math.min(phases.length - 1, data.get(6)))];
    }

    @Override public boolean stillValid(Player player) {
        if (!viewer.equals(player.getUUID())) return false;
        if (machine == null) return true;
        if (!machine.canReach(player)) return false;
        if (operator) return machine.canOperate(player) && (machine.isOwnerOrCreative(player)
            || authenticated && machine.passwordRevision() == passwordRevision);
        return machine.hasSession(player) && sessionId.equals(machine.getSessionId());
    }

    public void action(ServerPlayer player, BlockPos anchor, UUID session, int sequence, ClawMachineNetwork.Action action) {
        if (operator || machine == null || player.containerMenu != this || !blockPos.equals(anchor)
            || !sessionId.equals(session) || !stillValid(player) || sequence < 0) return;
        machine.handleAction(player, session, sequence, action.ordinal());
    }

    public void applySettings(ServerPlayer player, int base, int guarantee, String password) {
        if (!operator || machine == null || player.containerMenu != this || !stillValid(player)) return;
        if (base < 0 || base > 100 || guarantee < 0 || guarantee > 1000) { data.set(1, 7); return; }
        if (!password.isEmpty()) {
            if (!machine.isOwnerOrCreative(player)) { data.set(1, 6); return; }
            if (!ClawMachineBlockEntity.validPassword(password)) { data.set(1, 3); return; }
        }
        if (!machine.setWinSettings(player, base, guarantee)) { data.set(1, 6); return; }
        if (!password.isEmpty()) {
            if (!machine.setPassword(player, password)) { data.set(1, 6); return; }
            data.set(1, 4);
        } else data.set(1, 5);
        broadcastChanges();
    }

    @Override public void clicked(int slot, int button, ClickType click, Player player) {
        if (operator && player.containerMenu == this && stillValid(player)) super.clicked(slot, button, click, player);
    }
    @Override public ItemStack quickMoveStack(Player player, int index) {
        if (!operator || player.containerMenu != this || !stillValid(player) || index < 0 || index >= slots.size()) return ItemStack.EMPTY;
        Slot slot = slots.get(index);
        if (!slot.hasItem()) return ItemStack.EMPTY;
        ItemStack original = slot.getItem(), copy = original.copy();
        if (index < ClawMachineBlockEntity.INVENTORY_SIZE) {
            if (!moveItemStackTo(original, ClawMachineBlockEntity.INVENTORY_SIZE, slots.size(), true)) return ItemStack.EMPTY;
        } else if (!moveItemStackTo(original, ClawMachineBlockEntity.REWARD_START, ClawMachineBlockEntity.PAYMENT_START, false)) return ItemStack.EMPTY;
        if (original.isEmpty()) slot.setByPlayer(ItemStack.EMPTY); else slot.setChanged();
        slot.onTake(player, original);
        return copy;
    }
    @Override public void removed(Player player) {
        super.removed(player);
        if (machine != null) {
            if (operator) machine.releaseOperator(player);
            else if (sessionId.equals(machine.getSessionId())) machine.cancelSession(player);
        }
    }
}
