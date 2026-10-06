package local.funpack.custom.client;

import local.funpack.custom.GachaponMenu;
import local.funpack.custom.GachaponNetwork;
import net.minecraft.client.gui.GuiGraphics;
import net.minecraft.client.gui.components.Button;
import net.minecraft.client.gui.components.EditBox;
import net.minecraft.client.gui.screens.inventory.AbstractContainerScreen;
import net.minecraft.network.chat.Component;
import net.minecraft.network.chat.Style;
import net.minecraft.util.FormattedCharSequence;
import net.minecraft.world.entity.player.Inventory;
import net.neoforged.neoforge.network.PacketDistributor;
import org.lwjgl.glfw.GLFW;

/** Operator inventory: independent prize stock, collected payments, and a price template. */
public final class GachaponScreen extends AbstractContainerScreen<GachaponMenu> {
    static final int INK = 0x243B69;
    private EditBox amount;
    private EditBox password;
    private Button saveAmount;
    private Button savePassword;
    private boolean amountEdited;
    private boolean syncingAmount;
    private int localStatus;

    public GachaponScreen(GachaponMenu menu, Inventory inventory, Component title) {
        super(menu, inventory, title);
        imageWidth = 230;
        imageHeight = 233;
        inventoryLabelX = 35;
        inventoryLabelY = 140;
    }

    @Override
    protected void init() {
        String oldAmount = amount == null ? Integer.toString(menu.getDispenseAmount()) : amount.getValue();
        String oldPassword = password == null ? "" : password.getValue();
        super.init();
        amount = new EditBox(font, leftPos + 13, topPos + 104, 34, 18,
            Component.translatable("gachapon.gui.dispense"));
        amount.setMaxLength(2);
        amount.setFilter(value -> value.isEmpty() || value.chars().allMatch(Character::isDigit));
        amount.setValue(oldAmount);
        amount.setResponder(value -> {
            if (!syncingAmount) amountEdited = true;
            localStatus = 0;
        });
        addRenderableWidget(amount);
        saveAmount = addRenderableWidget(Button.builder(Component.translatable("gachapon.gui.save"), b -> save(false))
            .bounds(leftPos + 51, topPos + 103, 44, 20).build());
        password = new EditBox(font, leftPos + 106, topPos + 104, 69, 18,
            Component.translatable("gachapon.gui.new_password"));
        password.setMaxLength(32);
        password.setFormatter((text, position) -> FormattedCharSequence.forward("*".repeat(text.length()), Style.EMPTY));
        password.setValue(oldPassword);
        password.setResponder(value -> localStatus = 0);
        addRenderableWidget(password);
        savePassword = addRenderableWidget(Button.builder(Component.translatable("gachapon.gui.set"), b -> save(true))
            .bounds(leftPos + 179, topPos + 103, 39, 20).build());
        updatePasswordPermission();
    }

    private void updatePasswordPermission() {
        password.visible = menu.canChangePassword();
        savePassword.visible = menu.canChangePassword();
    }

    private void save(boolean changingPassword) {
        int value;
        try {
            value = Integer.parseInt(amount.getValue());
        } catch (NumberFormatException exception) {
            localStatus = 7;
            return;
        }
        if (value < 1 || value > 64) {
            localStatus = 7;
            return;
        }
        String nextPassword = changingPassword ? password.getValue() : "";
        if (changingPassword && (nextPassword.length() < 4 || nextPassword.length() > 32)) {
            localStatus = 3;
            return;
        }
        PacketDistributor.sendToServer(new GachaponNetwork.SettingsPayload(menu.containerId, value, nextPassword));
        localStatus = 0;
        if (changingPassword) password.setValue("");
        setFocused(null);
    }

    @Override
    protected void containerTick() {
        super.containerTick();
        updatePasswordPermission();
        if (!amountEdited && !amount.isFocused()
            && !amount.getValue().equals(Integer.toString(menu.getDispenseAmount()))) {
            syncingAmount = true;
            amount.setValue(Integer.toString(menu.getDispenseAmount()));
            syncingAmount = false;
        }
        saveAmount.active = !amount.getValue().isEmpty();
        savePassword.active = password.getValue().length() >= 4;
    }

    @Override
    public boolean keyPressed(int keyCode, int scanCode, int modifiers) {
        if (keyCode == GLFW.GLFW_KEY_ESCAPE || keyCode == GLFW.GLFW_KEY_TAB) {
            return super.keyPressed(keyCode, scanCode, modifiers);
        }
        if ((amount.isFocused() || password.isFocused())
            && (keyCode == GLFW.GLFW_KEY_ENTER || keyCode == GLFW.GLFW_KEY_KP_ENTER)) {
            save(password.isFocused());
            return true;
        }
        if (amount.isFocused() && amount.keyPressed(keyCode, scanCode, modifiers)) return true;
        if (password.isFocused() && password.keyPressed(keyCode, scanCode, modifiers)) return true;
        // Typing inventory/hotbar bindings into a field must not move stacks or close this screen.
        if (amount.isFocused() || password.isFocused()) return false;
        return super.keyPressed(keyCode, scanCode, modifiers);
    }

    @Override
    protected void renderBg(GuiGraphics graphics, float partialTick, int mouseX, int mouseY) {
        panel(graphics, leftPos, topPos, imageWidth, imageHeight);
        graphics.fill(leftPos + 9, topPos + 89, leftPos + imageWidth - 9, topPos + 90, 0xFFD2D7E0);
        menu.slots.forEach(slot -> slot(graphics, leftPos + slot.x, topPos + slot.y));
    }

    @Override
    protected void renderLabels(GuiGraphics graphics, int mouseX, int mouseY) {
        graphics.drawString(font, title, 11, 9, INK, false);
        label(graphics, "price", 12, 24);
        label(graphics, "rewards", 81, 24);
        label(graphics, "collected", 157, 24);
        graphics.drawWordWrap(font, Component.translatable("gachapon.gui.price_hint"), 11, 56, 60, 0x667085);
        label(graphics, "dispense", 13, 94);
        if (menu.canChangePassword()) label(graphics, "new_password", 106, 94);
        else graphics.drawWordWrap(font, Component.translatable("gachapon.gui.owner_password"), 105, 98, 114, 0x667085);
        int status = localStatus != 0 ? localStatus : menu.getStatus();
        if (status != 0) {
            graphics.drawString(font, statusMessage(status), 12, 128, status == 4 || status == 5 ? 0x287444 : 0xAD303C, false);
        }
        graphics.drawString(font, playerInventoryTitle, inventoryLabelX, inventoryLabelY, INK, false);
    }

    @Override
    public void render(GuiGraphics graphics, int mouseX, int mouseY, float partialTick) {
        super.render(graphics, mouseX, mouseY, partialTick);
        renderTooltip(graphics, mouseX, mouseY);
    }

    private void label(GuiGraphics graphics, String key, int x, int y) {
        graphics.drawString(font, Component.translatable("gachapon.gui." + key), x, y, INK, false);
    }

    static Component statusMessage(int status) {
        return Component.translatable("gachapon.gui.status." + status);
    }

    static void panel(GuiGraphics graphics, int x, int y, int width, int height) {
        graphics.fill(x - 1, y - 1, x + width + 1, y + height + 1, 0xFF172C50);
        graphics.fill(x, y, x + width, y + height, 0xFFEBEDF2);
        graphics.fill(x + 1, y + 1, x + width - 1, y + 20, 0xFFF8F9FC);
        graphics.fill(x + 1, y + 20, x + width - 1, y + 21, 0xFFD4B83E);
    }

    static void slot(GuiGraphics graphics, int x, int y) {
        graphics.fill(x - 1, y - 1, x + 17, y + 17, 0xFF8692A6);
        graphics.fill(x, y, x + 17, y + 17, 0xFFFFFFFF);
        graphics.fill(x, y, x + 16, y + 16, 0xFFC4CBD7);
    }
}
