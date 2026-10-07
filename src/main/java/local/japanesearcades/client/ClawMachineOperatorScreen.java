package local.japanesearcades.client;

import local.japanesearcades.ClawMachineMenu;
import local.japanesearcades.ClawMachineNetwork;
import net.minecraft.client.gui.GuiGraphics;
import net.minecraft.client.gui.components.Button;
import net.minecraft.client.gui.components.EditBox;
import net.minecraft.client.gui.components.Tooltip;
import net.minecraft.client.gui.screens.inventory.AbstractContainerScreen;
import net.minecraft.network.chat.Component;
import net.minecraft.network.chat.Style;
import net.minecraft.util.FormattedCharSequence;
import net.minecraft.world.entity.player.Inventory;
import net.neoforged.neoforge.network.PacketDistributor;
import org.lwjgl.glfw.GLFW;

/** The prize grid mirrors the cabinet: back row above, front row below. */
public final class ClawMachineOperatorScreen extends AbstractContainerScreen<ClawMachineMenu> {
    private EditBox chance, guarantee, password;
    private Button ramp, savePassword;
    private boolean rampEnabled, edited, syncing;
    private int localStatus;

    public ClawMachineOperatorScreen(ClawMachineMenu menu, Inventory inventory, Component title) {
        super(menu, inventory, title);
        imageWidth = 254; imageHeight = 240;
        inventoryLabelX = 44; inventoryLabelY = 150;
    }
    @Override protected void init() {
        String oldChance = chance == null ? Integer.toString(menu.getBaseWinChance()) : chance.getValue();
        String oldGuarantee = guarantee == null ? Integer.toString(Math.max(1, menu.getGuaranteePlay())) : guarantee.getValue();
        String oldPassword = password == null ? "" : password.getValue();
        if (chance == null) rampEnabled = menu.getGuaranteePlay() > 0;
        super.init();
        chance = numberField(12, 107, 32, 3, "base_chance", oldChance);
        guarantee = numberField(143, 107, 34, 4, "guarantee", oldGuarantee);
        ramp = addRenderableWidget(Button.builder(Component.empty(), button -> {
            rampEnabled = !rampEnabled; edited = true; localStatus = 0; updateRamp();
        }).bounds(leftPos + 52, topPos + 106, 79, 18).build());
        ramp.setTooltip(Tooltip.create(Component.translatable("claw.gui.ramp_hint")));
        addRenderableWidget(Button.builder(Component.translatable("gachapon.gui.save"), button -> save(false))
            .bounds(leftPos + 184, topPos + 106, 60, 18).build());
        password = new EditBox(font, leftPos + 68, topPos + 130, 108, 16, Component.translatable("gachapon.gui.new_password"));
        password.setMaxLength(32);
        password.setFormatter((text, position) -> FormattedCharSequence.forward("*".repeat(text.length()), Style.EMPTY));
        password.setValue(oldPassword); password.setResponder(value -> localStatus = 0);
        addRenderableWidget(password);
        savePassword = addRenderableWidget(Button.builder(Component.translatable("gachapon.gui.set"), button -> save(true))
            .bounds(leftPos + 184, topPos + 128, 60, 18).build());
        updateRamp();
    }
    private EditBox numberField(int x, int y, int width, int length, String key, String value) {
        var field = new EditBox(font, leftPos + x, topPos + y, width, 16, Component.translatable("claw.gui." + key));
        field.setMaxLength(length);
        field.setFilter(text -> text.isEmpty() || text.chars().allMatch(Character::isDigit));
        field.setValue(value);
        field.setResponder(text -> { if (!syncing) edited = true; localStatus = 0; });
        return addRenderableWidget(field);
    }
    private void updateRamp() {
        ramp.setMessage(Component.translatable(rampEnabled ? "claw.gui.ramp_on" : "claw.gui.ramp_off"));
        guarantee.setEditable(rampEnabled);
        password.visible = savePassword.visible = menu.canChangePassword();
    }
    private void save(boolean pin) {
        int base = menu.getBaseWinChance(), nth = menu.getGuaranteePlay();
        String nextPassword = "";
        if (pin) {
            nextPassword = password.getValue();
            if (nextPassword.length() < 4 || nextPassword.length() > 32) { localStatus = 3; return; }
        } else {
            try { base = Integer.parseInt(chance.getValue()); nth = rampEnabled ? Integer.parseInt(guarantee.getValue()) : 0; }
            catch (NumberFormatException error) { localStatus = 7; return; }
            if (base < 0 || base > 100 || nth < 0 || nth > 1000 || rampEnabled && nth == 0) { localStatus = 7; return; }
        }
        PacketDistributor.sendToServer(new ClawMachineNetwork.SettingsPayload(menu.containerId, base, nth, nextPassword));
        localStatus = 0;
        if (pin) password.setValue("");
        setFocused(null);
    }
    @Override protected void containerTick() {
        super.containerTick();
        if (!edited && !chance.isFocused() && !guarantee.isFocused()) {
            syncing = true;
            chance.setValue(Integer.toString(menu.getBaseWinChance()));
            guarantee.setValue(Integer.toString(menu.getGuaranteePlay() == 0 ? 5 : menu.getGuaranteePlay()));
            rampEnabled = menu.getGuaranteePlay() > 0;
            syncing = false;
        }
        updateRamp();
        savePassword.active = password.getValue().length() >= 4;
    }
    @Override public boolean keyPressed(int key, int scanCode, int modifiers) {
        if (key == GLFW.GLFW_KEY_ESCAPE || key == GLFW.GLFW_KEY_TAB) return super.keyPressed(key, scanCode, modifiers);
        if ((chance.isFocused() || guarantee.isFocused() || password.isFocused()) && (key == GLFW.GLFW_KEY_ENTER || key == GLFW.GLFW_KEY_KP_ENTER)) {
            save(password.isFocused()); return true;
        }
        if (chance.isFocused()) return chance.keyPressed(key, scanCode, modifiers);
        if (guarantee.isFocused()) return guarantee.keyPressed(key, scanCode, modifiers);
        if (password.isFocused()) return password.keyPressed(key, scanCode, modifiers);
        return super.keyPressed(key, scanCode, modifiers);
    }
    @Override protected void renderBg(GuiGraphics graphics, float partialTick, int mouseX, int mouseY) {
        GachaponScreen.panel(graphics, leftPos, topPos, imageWidth, imageHeight);
        menu.slots.forEach(slot -> GachaponScreen.slot(graphics, leftPos + slot.x, topPos + slot.y));
    }
    @Override protected void renderLabels(GuiGraphics graphics, int mouseX, int mouseY) {
        graphics.drawString(font, title, 11, 8, GachaponScreen.INK, false);
        label(graphics, "price", 12, 22); label(graphics, "rewards", 85, 22); label(graphics, "collected", 175, 22);
        graphics.drawWordWrap(font, Component.translatable("claw.gui.price_hint"), 11, 54, 63, 0x657080);
        label(graphics, "back", 141, 35); label(graphics, "front", 141, 72);
        graphics.drawString(font, Component.translatable("claw.gui.current_chance", menu.getCurrentWinChance(), menu.getPlaysSinceWin()), 85, 88, 0x3E626F, false);
        label(graphics, "base_chance", 12, 97); label(graphics, "guarantee", 136, 97);
        if (menu.canChangePassword()) label(graphics, "new_password", 12, 133);
        else graphics.drawString(font, Component.translatable("claw.gui.owner_password"), 12, 133, 0x657080, false);
        graphics.drawString(font, playerInventoryTitle, inventoryLabelX, inventoryLabelY, GachaponScreen.INK, false);
        int status = localStatus == 0 ? menu.getStatus() : localStatus;
        if (status != 0) graphics.drawString(font, font.plainSubstrByWidth(statusMessage(status).getString(), 138), 106, 150,
            status == 4 || status == 5 ? 0x287444 : 0xAD303C, false);
    }
    private void label(GuiGraphics graphics, String key, int x, int y) {
        graphics.drawString(font, Component.translatable("claw.gui." + key), x, y, GachaponScreen.INK, false);
    }
    static Component statusMessage(int status) {
        return Component.translatable(status == 7 ? "claw.gui.bad_settings" : status == 9 ? "claw.gui.busy" : "gachapon.gui.status." + status);
    }
    @Override public void render(GuiGraphics graphics, int mouseX, int mouseY, float partialTick) {
        super.render(graphics, mouseX, mouseY, partialTick); renderTooltip(graphics, mouseX, mouseY);
    }
}
