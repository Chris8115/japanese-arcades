package local.funpack.custom;

import java.util.UUID;
import javax.annotation.Nullable;
import net.minecraft.core.BlockPos;
import net.minecraft.network.RegistryFriendlyByteBuf;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.SimpleMenuProvider;
import net.minecraft.world.entity.player.Inventory;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.inventory.AbstractContainerMenu;
import net.minecraft.world.inventory.SimpleContainerData;
import net.minecraft.world.item.ItemStack;

/** No machine contents are synchronized until operator access has been verified. */
public final class ClawMachineAccessMenu extends AbstractContainerMenu {
    @Nullable private final ClawMachineBlockEntity machine;
    private final BlockPos blockPos;
    private final boolean setup;
    private final UUID viewer;
    private final SimpleContainerData data = new SimpleContainerData(1);

    public ClawMachineAccessMenu(int id, Inventory inventory, RegistryFriendlyByteBuf buffer) {
        super(FunPackCustom.CLAW_MACHINE_ACCESS_MENU.get(), id);
        machine = null;
        blockPos = buffer.readBlockPos(); setup = buffer.readBoolean(); viewer = inventory.player.getUUID();
        addDataSlots(data);
    }
    ClawMachineAccessMenu(int id, Inventory inventory, ClawMachineBlockEntity machine, boolean setup) {
        super(FunPackCustom.CLAW_MACHINE_ACCESS_MENU.get(), id);
        this.machine = machine; blockPos = machine.getBlockPos(); this.setup = setup; viewer = inventory.player.getUUID();
        addDataSlots(data);
    }
    public static void open(ServerPlayer player, ClawMachineBlockEntity machine, boolean setup) {
        if (!machine.canReach(player)) return;
        boolean initial = setup && machine.isOwnerOrCreative(player) && !machine.hasPassword();
        player.openMenu(new SimpleMenuProvider((id, inv, viewer) -> new ClawMachineAccessMenu(id, inv, machine, initial),
            Component.translatable(initial ? "claw.gui.setup_title" : "claw.gui.access_title")),
            buffer -> { buffer.writeBlockPos(machine.getBlockPos()); buffer.writeBoolean(initial); });
    }
    public BlockPos getBlockPos() { return blockPos; }
    public boolean isSetup() { return setup; }
    public int getStatus() { return data.get(0); }
    public void submitPassword(ServerPlayer player, String password) {
        if (machine == null || player.containerMenu != this || !stillValid(player)) return;
        if (setup) {
            if (!machine.isOwnerOrCreative(player) || machine.hasPassword()) { data.set(0, 6); return; }
            if (!ClawMachineBlockEntity.validPassword(password)) { data.set(0, 3); return; }
            if (!machine.setPassword(player, password)) { data.set(0, 6); return; }
            if (!ClawMachineMenu.openOperator(player, machine, false)) data.set(0, 9);
        } else {
            int status = machine.authenticate(player, password);
            data.set(0, status);
            if (status == 0 && !ClawMachineMenu.openOperator(player, machine, true)) data.set(0, 9);
        }
        broadcastChanges();
    }
    @Override public boolean stillValid(Player player) {
        return viewer.equals(player.getUUID()) && (machine == null || machine.canReach(player));
    }
    @Override public ItemStack quickMoveStack(Player player, int slot) { return ItemStack.EMPTY; }
}
