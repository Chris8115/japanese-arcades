package local.japanesearcades;

import java.util.UUID;
import javax.annotation.Nullable;
import net.minecraft.core.BlockPos;
import net.minecraft.network.RegistryFriendlyByteBuf;
import net.minecraft.world.Container;
import net.minecraft.world.SimpleContainer;
import net.minecraft.world.entity.player.Inventory;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.inventory.AbstractContainerMenu;
import net.minecraft.world.inventory.ClickType;
import net.minecraft.world.inventory.Slot;
import net.minecraft.world.item.ItemStack;

/** Uses vanilla inventory transactions; each display cell holds exactly one collectible. */
public final class FigureShelfMenu extends AbstractContainerMenu {
    @Nullable private final FigureShelfBlockEntity shelf;
    private final BlockPos blockPos;
    private final int rows;
    private final UUID viewer;

    public FigureShelfMenu(int id, Inventory playerInventory, RegistryFriendlyByteBuf buffer) {
        this(id, playerInventory, buffer.readBlockPos(), buffer.readVarInt());
    }
    private FigureShelfMenu(int id, Inventory playerInventory, BlockPos pos, int rows) {
        super(JapaneseArcades.FIGURE_SHELF_MENU.get(), id);
        if (rows < 1 || rows > 2) { throw new IllegalArgumentException("Invalid shelf row count"); }
        this.shelf = null;
        this.blockPos = pos;
        this.rows = rows;
        this.viewer = playerInventory.player.getUUID();
        addSlots(new SimpleContainer(rows * 4), playerInventory);
    }
    FigureShelfMenu(int id, Inventory playerInventory, FigureShelfBlockEntity shelf) {
        super(JapaneseArcades.FIGURE_SHELF_MENU.get(), id);
        this.shelf = shelf;
        this.blockPos = shelf.getBlockPos();
        this.rows = shelf.rows();
        this.viewer = playerInventory.player.getUUID();
        addSlots(shelf.inventory(), playerInventory);
    }

    private void addSlots(Container contents, Inventory playerInventory) {
        for (int row = 0; row < rows; row++) {
            for (int column = 0; column < 4; column++) {
                addSlot(new Slot(contents, row * 4 + column, 53 + column * 18, 30 + (rows - row - 1) * 18) {
                    @Override public boolean mayPlace(ItemStack stack) { return FigureShelfBlockEntity.accepts(stack); }
                    @Override public int getMaxStackSize() { return 1; }
                    @Override public int getMaxStackSize(ItemStack stack) { return 1; }
                });
            }
        }
        for (int row = 0; row < 3; row++) {
            for (int column = 0; column < 9; column++) {
                addSlot(new Slot(playerInventory, column + row * 9 + 9, 8 + column * 18, 84 + row * 18));
            }
        }
        for (int column = 0; column < 9; column++) { addSlot(new Slot(playerInventory, column, 8 + column * 18, 142)); }
    }

    public int rows() { return rows; }
    public int shelfSize() { return rows * 4; }
    public BlockPos getBlockPos() { return blockPos; }
    @Override public boolean stillValid(Player player) {
        return viewer.equals(player.getUUID()) && (shelf == null || shelf.canUse(player));
    }
    @Override public void clicked(int slot, int button, ClickType click, Player player) {
        if (stillValid(player)) { super.clicked(slot, button, click, player); }
    }
    @Override public ItemStack quickMoveStack(Player player, int index) {
        if (!stillValid(player) || index < 0 || index >= slots.size()) { return ItemStack.EMPTY; }
        Slot slot = slots.get(index);
        if (!slot.hasItem()) { return ItemStack.EMPTY; }
        ItemStack stack = slot.getItem();
        ItemStack original = stack.copy();
        if (index < shelfSize()) {
            if (!moveItemStackTo(stack, shelfSize(), slots.size(), true)) { return ItemStack.EMPTY; }
        } else {
            if (!FigureShelfBlockEntity.accepts(stack)) { return ItemStack.EMPTY; }
            boolean moved = false;
            // Vanilla stops after the first empty slot. Fill each one-item cell in this transaction.
            for (int target = 0; target < shelfSize() && !stack.isEmpty(); target++) {
                moved |= moveItemStackTo(stack, target, target + 1, false);
            }
            if (!moved) { return ItemStack.EMPTY; }
        }
        if (stack.isEmpty()) { slot.setByPlayer(ItemStack.EMPTY); }
        else { slot.setChanged(); }
        slot.onTake(player, stack);
        return original;
    }
}
