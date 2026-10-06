package local.funpack.custom;

import javax.annotation.Nullable;
import net.minecraft.core.BlockPos;
import net.minecraft.network.RegistryFriendlyByteBuf;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.player.Inventory;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.inventory.AbstractContainerMenu;
import net.minecraft.world.inventory.SimpleContainerData;
import net.minecraft.world.item.ItemStack;

/** The password prompt exposes no machine inventory until the server verifies access. */
public final class GachaponAccessMenu extends AbstractContainerMenu {
    @Nullable private final GachaponBlockEntity machine;
    private final BlockPos blockPos;
    private final boolean setup;
    private final java.util.UUID viewer;
    private final SimpleContainerData data = new SimpleContainerData(1);

    public GachaponAccessMenu(int id, Inventory inventory, RegistryFriendlyByteBuf buffer) {
        super(FunPackCustom.GACHAPON_ACCESS_MENU.get(), id);
        machine = null;
        blockPos = buffer.readBlockPos();
        setup = buffer.readBoolean();
        viewer = inventory.player.getUUID();
        addDataSlots(data);
    }

    GachaponAccessMenu(int id, Inventory inventory, GachaponBlockEntity machine, boolean setup) {
        super(FunPackCustom.GACHAPON_ACCESS_MENU.get(), id);
        this.machine = machine;
        this.blockPos = machine.getBlockPos();
        this.setup = setup;
        this.viewer = inventory.player.getUUID();
        addDataSlots(data);
    }

    public BlockPos getBlockPos() { return blockPos; }
    public boolean isSetup() { return setup; }
    public boolean isSetupMode() { return setup; }
    public int getStatus() { return data.get(0); }

    public void submitPassword(ServerPlayer player, String password) {
        if (machine == null || player.containerMenu != this || !stillValid(player)) { return; }
        if (setup) {
            if (!machine.isOwnerOrCreative(player) || machine.hasPassword()) { data.set(0, 6); }
            else if (!GachaponBlockEntity.validPassword(password)) { data.set(0, 3); }
            else if (machine.setPassword(player, password)) { machine.openOperator(player, false); }
        } else {
            int status = machine.authenticate(player, password);
            data.set(0, status);
            if (status == 0) { machine.openOperator(player, true); }
        }
        broadcastChanges();
    }

    @Override
    public boolean stillValid(Player player) {
        return viewer.equals(player.getUUID()) && (machine == null || machine.canReach(player));
    }

    @Override
    public ItemStack quickMoveStack(Player player, int slot) { return ItemStack.EMPTY; }
}
