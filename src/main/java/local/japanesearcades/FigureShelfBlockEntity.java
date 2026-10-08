package local.japanesearcades;

import java.util.ArrayList;
import java.util.List;
import net.minecraft.core.BlockPos;
import net.minecraft.core.HolderLookup;
import net.minecraft.core.NonNullList;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.Connection;
import net.minecraft.network.chat.Component;
import net.minecraft.network.protocol.game.ClientboundBlockEntityDataPacket;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.Container;
import net.minecraft.world.ContainerHelper;
import net.minecraft.world.MenuProvider;
import net.minecraft.world.entity.player.Inventory;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.inventory.AbstractContainerMenu;
import net.minecraft.world.item.BlockItem;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.Vec3;

/** Item data is persisted verbatim. Only inventory changes send block updates; there is no ticker. */
public final class FigureShelfBlockEntity extends BlockEntity implements MenuProvider {
    private final NonNullList<ItemStack> items;
    // A private adapter deliberately avoids making the block entity a hopper-accessible Container.
    private final Container inventory = new Container() {
        @Override public int getContainerSize() { return size(); }
        @Override public boolean isEmpty() { return items.stream().allMatch(ItemStack::isEmpty); }
        @Override public ItemStack getItem(int slot) { return items.get(slot); }
        @Override public ItemStack removeItem(int slot, int count) {
            ItemStack result = ContainerHelper.removeItem(items, slot, count);
            if (!result.isEmpty()) { setChanged(); }
            return result;
        }
        @Override public ItemStack removeItemNoUpdate(int slot) { return ContainerHelper.takeItem(items, slot); }
        @Override public void setItem(int slot, ItemStack stack) {
            if (!stack.isEmpty() && !accepts(stack)) { return; }
            items.set(slot, stack.isEmpty() ? ItemStack.EMPTY : stack.copyWithCount(1));
            setChanged();
        }
        @Override public int getMaxStackSize() { return 1; }
        @Override public boolean canPlaceItem(int slot, ItemStack stack) { return accepts(stack); }
        @Override public void setChanged() { changed(); }
        @Override public boolean stillValid(Player player) { return canUse(player); }
        @Override public void clearContent() { items.clear(); setChanged(); }
    };

    public FigureShelfBlockEntity(BlockPos pos, BlockState state) {
        super(JapaneseArcades.FIGURE_SHELF_ENTITY.get(), pos, state);
        items = NonNullList.withSize(((FigureShelfBlock) state.getBlock()).rows() * 4, ItemStack.EMPTY);
    }

    public int size() { return items.size(); }
    public int rows() { return size() / 4; }
    /** Read-only display reference. Renderers must not mutate the stored stack. */
    public ItemStack item(int slot) { return slot >= 0 && slot < size() ? items.get(slot) : ItemStack.EMPTY; }
    Container inventory() { return inventory; }

    public static boolean accepts(ItemStack stack) {
        return !stack.isEmpty() && stack.getItem() instanceof BlockItem item
            && (item.getBlock() instanceof MobFigureBlock
                || item.getBlock() == JapaneseArcades.HATSUNE_MIKU_FIGURE.get()
                || item.getBlock() == JapaneseArcades.KASANE_TETO_FIGURE.get());
    }

    boolean canUse(Player player) {
        return level != null && !isRemoved() && !player.isRemoved() && player.level() == level && player.isAlive() && !player.isSpectator()
            && player.mayBuild() && level.getBlockEntity(worldPosition) == this
            && level.getBlockState(worldPosition).getBlock() == getBlockState().getBlock()
            && player.canInteractWithBlock(worldPosition, 0) && level.mayInteract(player, worldPosition);
    }

    public void open(ServerPlayer player) {
        if (canUse(player)) { player.openMenu(this, buffer -> buffer.writeBlockPos(worldPosition).writeVarInt(rows())); }
    }
    @Override public Component getDisplayName() { return getBlockState().getBlock().getName(); }
    @Override public AbstractContainerMenu createMenu(int id, Inventory playerInventory, Player player) {
        return new FigureShelfMenu(id, playerInventory, this);
    }

    private void changed() {
        setChanged();
        if (level != null) { level.sendBlockUpdated(worldPosition, getBlockState(), getBlockState(), 3); }
    }

    void dropContents() {
        if (!(level instanceof ServerLevel server)) { return; }
        List<ItemStack> drops = new ArrayList<>();
        for (ItemStack item : items) { if (!item.isEmpty()) { drops.add(item.copy()); } }
        // Clear before spawn callbacks can re-enter a break, menu click, or neighboring support update.
        items.clear();
        setChanged();
        Vec3 position = Vec3.atCenterOf(worldPosition);
        for (ItemStack drop : drops) {
            if (!ClawMachineRecovery.spawn(server, drop, position, null)) {
                ClawMachineRecovery.enqueue(server, List.of(drop), position, null);
            }
        }
    }

    @Override protected void saveAdditional(CompoundTag tag, HolderLookup.Provider registries) {
        super.saveAdditional(tag, registries);
        ContainerHelper.saveAllItems(tag, items, registries);
    }
    @Override protected void loadAdditional(CompoundTag tag, HolderLookup.Provider registries) {
        super.loadAdditional(tag, registries);
        items.clear();
        ContainerHelper.loadAllItems(tag, items, registries);
    }
    @Override public CompoundTag getUpdateTag(HolderLookup.Provider registries) { return saveWithoutMetadata(registries); }
    @Override public ClientboundBlockEntityDataPacket getUpdatePacket() { return ClientboundBlockEntityDataPacket.create(this); }
    @Override public void handleUpdateTag(CompoundTag tag, HolderLookup.Provider registries) { loadWithComponents(tag, registries); }
    @Override public void onDataPacket(Connection connection, ClientboundBlockEntityDataPacket packet, HolderLookup.Provider registries) {
        handleUpdateTag(packet.getTag(), registries);
    }
}
