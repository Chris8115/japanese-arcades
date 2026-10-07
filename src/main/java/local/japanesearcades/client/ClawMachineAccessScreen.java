package local.japanesearcades.client;

import local.japanesearcades.ClawMachineAccessMenu;
import local.japanesearcades.ClawMachineNetwork;
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

/** Initial owner PIN setup and password-based operator access share the same protected server menu. */
public final class ClawMachineAccessScreen extends AbstractContainerScreen<ClawMachineAccessMenu> {
    private EditBox password;
    private EditBox confirmation;
    private Button submit;
    private int localStatus;
    private int sendCooldown;

    public ClawMachineAccessScreen(ClawMachineAccessMenu menu, Inventory inventory, Component title) {
        super(menu, inventory, title);
        imageWidth = 244;
        imageHeight = menu.isSetup() ? 210 : 174;
    }

    @Override
    protected void init() {
        String oldPassword = password == null ? "" : password.getValue();
        String oldConfirmation = confirmation == null ? "" : confirmation.getValue();
        super.init();
        password = passwordField(topPos + 76, "password");
        password.setValue(oldPassword);
        if (menu.isSetup()) {
            confirmation = passwordField(topPos + 113, "confirm_password");
            confirmation.setValue(oldConfirmation);
        }
        submit = addRenderableWidget(Button.builder(Component.translatable(menu.isSetup()
                ? "gachapon.gui.create_password" : "gachapon.gui.unlock"), button -> submitPassword())
            .bounds(leftPos + 16, topPos + (menu.isSetup() ? 148 : 112), imageWidth - 32, 20).build());
        setInitialFocus(password);
    }

    private EditBox passwordField(int y, String key) {
        EditBox field = new EditBox(font, leftPos + 16, y, imageWidth - 32, 20,
            Component.translatable("gachapon.gui." + key));
        field.setMaxLength(32);
        field.setFormatter((text, position) -> FormattedCharSequence.forward("*".repeat(text.length()), Style.EMPTY));
        field.setResponder(value -> localStatus = 0);
        return addRenderableWidget(field);
    }

    private void submitPassword() {
        if (sendCooldown > 0) return;
        String value = password.getValue();
        if (value.length() < 4 || value.length() > 32) {
            localStatus = 3;
            return;
        }
        if (menu.isSetup() && !value.equals(confirmation.getValue())) {
            localStatus = 8;
            return;
        }
        PacketDistributor.sendToServer(new ClawMachineNetwork.PasswordPayload(menu.containerId, value));
        sendCooldown = 10;
        localStatus = 0;
    }

    @Override
    protected void containerTick() {
        super.containerTick();
        if (sendCooldown > 0) sendCooldown--;
        submit.active = sendCooldown == 0 && password.getValue().length() >= 4;
    }

    @Override
    public boolean keyPressed(int keyCode, int scanCode, int modifiers) {
        if (keyCode == GLFW.GLFW_KEY_ESCAPE || keyCode == GLFW.GLFW_KEY_TAB) {
            return super.keyPressed(keyCode, scanCode, modifiers);
        }
        if (keyCode == GLFW.GLFW_KEY_ENTER || keyCode == GLFW.GLFW_KEY_KP_ENTER) {
            submitPassword();
            return true;
        }
        if (password.isFocused() && password.keyPressed(keyCode, scanCode, modifiers)) return true;
        if (confirmation != null && confirmation.isFocused() && confirmation.keyPressed(keyCode, scanCode, modifiers)) return true;
        // Password letters may match inventory or hotbar bindings and must stay in the field.
        if (password.isFocused() || confirmation != null && confirmation.isFocused()) return false;
        return super.keyPressed(keyCode, scanCode, modifiers);
    }

    @Override
    protected void renderBg(GuiGraphics graphics, float partialTick, int mouseX, int mouseY) {
        GachaponScreen.panel(graphics, leftPos, topPos, imageWidth, imageHeight);
    }

    @Override
    protected void renderLabels(GuiGraphics graphics, int mouseX, int mouseY) {
        graphics.drawString(font, Component.translatable(menu.isSetup()
            ? "claw.gui.setup_title" : "claw.gui.access_title"), 12, 9, GachaponScreen.INK, false);
        graphics.drawWordWrap(font, Component.translatable(menu.isSetup()
            ? "claw.gui.setup_hint" : "claw.gui.access_hint"), 16, 31, imageWidth - 32, 0x526079);
        graphics.drawString(font, Component.translatable("gachapon.gui.password"), 16, 65, GachaponScreen.INK, false);
        if (menu.isSetup()) {
            graphics.drawString(font, Component.translatable("gachapon.gui.confirm_password"), 16, 102, GachaponScreen.INK, false);
        }
        int status = localStatus == 0 ? menu.getStatus() : localStatus;
        if (status != 0) {
            graphics.drawWordWrap(font, ClawMachineOperatorScreen.statusMessage(status), 16,
                menu.isSetup() ? 178 : 142, imageWidth - 32, 0xAD303C);
        }
    }
}
