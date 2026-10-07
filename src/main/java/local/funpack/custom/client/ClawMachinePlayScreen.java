package local.funpack.custom.client;

import java.util.ArrayList;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Locale;
import javax.annotation.Nullable;
import local.funpack.custom.ClawMachineBlock;
import local.funpack.custom.ClawMachineBlockEntity;
import local.funpack.custom.ClawMachineMenu;
import local.funpack.custom.ClawMachineNetwork;
import net.minecraft.client.gui.GuiGraphics;
import net.minecraft.client.gui.components.Button;
import net.minecraft.client.gui.components.Tooltip;
import net.minecraft.client.gui.screens.Screen;
import net.minecraft.client.gui.screens.inventory.MenuAccess;
import net.minecraft.network.chat.Component;
import net.minecraft.world.entity.player.Inventory;
import net.neoforged.neoforge.network.PacketDistributor;
import org.lwjgl.glfw.GLFW;

/** Keeps the cabinet in view; normal screen input holds the camera steady while aiming. */
public final class ClawMachinePlayScreen extends Screen implements MenuAccess<ClawMachineMenu> {
    private final ClawMachineMenu menu;
    private final int imageWidth = 280, imageHeight = 54;
    private int leftPos, topPos;
    private final LinkedHashSet<Integer> heldKeys = new LinkedHashSet<>();
    private final List<Button> movement = new ArrayList<>();
    @Nullable private ClawMachineNetwork.Action mouseDirection;
    private Button drop;
    private int ticks, sequence;
    @Nullable private Boolean previousHideGui;
    private Component feedback = Component.empty();
    private int feedbackTicks;

    public ClawMachinePlayScreen(ClawMachineMenu menu, Inventory inventory, Component title) {
        super(title);
        this.menu = menu;
    }
    @Override public ClawMachineMenu getMenu() { return menu; }
    @Override protected void init() {
        super.init();
        if (previousHideGui == null && minecraft != null) {
            previousHideGui = minecraft.options.hideGui;
            minecraft.options.hideGui = true;
            centerCamera();
        }
        leftPos = (width - imageWidth) / 2;
        topPos = Math.max(4, height - imageHeight - 8);
        movement.clear(); heldKeys.clear(); mouseDirection = null;
        arrow("↑", 94, 4, ClawMachineNetwork.Action.BACK);
        arrow("←", 70, 23, ClawMachineNetwork.Action.LEFT);
        arrow("↓", 94, 23, ClawMachineNetwork.Action.FRONT);
        arrow("→", 118, 23, ClawMachineNetwork.Action.RIGHT);
        drop = addRenderableWidget(Button.builder(Component.translatable("claw.play.drop"), button -> drop())
            .bounds(leftPos + 158, topPos + 20, 58, 20).build());
        drop.setTooltip(Tooltip.create(Component.translatable("claw.play.drop_hint")));
        addRenderableWidget(Button.builder(Component.translatable("claw.play.leave"), button -> onClose())
            .bounds(leftPos + 224, topPos + 20, 46, 20).build());
        setFocused(null);
    }
    private void centerCamera() {
        if (minecraft.level == null || minecraft.player == null) return;
        var state = minecraft.level.getBlockState(menu.getBlockPos());
        if (!(state.getBlock() instanceof ClawMachineBlock)) return;
        var target = ClawMachineBlock.localToWorld(menu.getBlockPos(), state.getValue(ClawMachineBlock.FACING), 24, 29, 16);
        var direction = target.subtract(minecraft.player.getEyePosition());
        float yaw = (float)Math.toDegrees(Math.atan2(-direction.x, direction.z));
        float pitch = (float)-Math.toDegrees(Math.atan2(direction.y, Math.sqrt(direction.x * direction.x + direction.z * direction.z)));
        minecraft.player.setYRot(yaw);
        minecraft.player.setXRot(pitch);
        minecraft.player.yRotO = yaw;
        minecraft.player.xRotO = pitch;
    }
    private void arrow(String glyph, int x, int y, ClawMachineNetwork.Action action) {
        var button = addRenderableWidget(Button.builder(Component.literal(glyph), pressed -> {
            mouseDirection = action;
            send(action);
            setFocused(null);
        }).bounds(leftPos + x, topPos + y, 21, 18).build());
        button.setTooltip(Tooltip.create(Component.translatable("claw.play." + action.name().toLowerCase(Locale.ROOT))));
        movement.add(button);
    }
    private void send(ClawMachineNetwork.Action action) {
        if (minecraft == null || minecraft.getConnection() == null) return;
        PacketDistributor.sendToServer(new ClawMachineNetwork.ActionPayload(menu.containerId, menu.getBlockPos(),
            menu.getSessionId(), sequence++, action));
    }
    private boolean aiming() { return menu.getPhase() == ClawMachineBlockEntity.Phase.AIMING; }
    private void drop() {
        if (!aiming()) return;
        heldKeys.clear(); mouseDirection = null;
        send(ClawMachineNetwork.Action.DROP);
    }
    @Override public void tick() {
        super.tick();
        if (minecraft == null || minecraft.player == null) return;
        if (!minecraft.player.isAlive() || minecraft.player.isRemoved()) {
            minecraft.player.closeContainer();
            return;
        }
        ticks++;
        if (feedbackTicks > 0) feedbackTicks--;
        boolean aiming = aiming();
        movement.forEach(button -> button.active = aiming);
        drop.active = aiming;
        if (ticks % 10 == 0) send(ClawMachineNetwork.Action.HEARTBEAT);
        if (!aiming) { heldKeys.clear(); mouseDirection = null; return; }
        ClawMachineNetwork.Action direction = mouseDirection;
        if (direction == null) for (int key : heldKeys) direction = keyAction(key);
        if (direction != null && ticks % 2 == 0) send(direction);
    }
    @Nullable private static ClawMachineNetwork.Action keyAction(int key) {
        return switch (key) {
            case GLFW.GLFW_KEY_A, GLFW.GLFW_KEY_LEFT -> ClawMachineNetwork.Action.LEFT;
            case GLFW.GLFW_KEY_D, GLFW.GLFW_KEY_RIGHT -> ClawMachineNetwork.Action.RIGHT;
            case GLFW.GLFW_KEY_W, GLFW.GLFW_KEY_UP -> ClawMachineNetwork.Action.BACK;
            case GLFW.GLFW_KEY_S, GLFW.GLFW_KEY_DOWN -> ClawMachineNetwork.Action.FRONT;
            default -> null;
        };
    }
    @Override public boolean keyPressed(int key, int scanCode, int modifiers) {
        if (key == GLFW.GLFW_KEY_ESCAPE) { onClose(); return true; }
        var action = keyAction(key);
        if (action != null) {
            if (aiming() && heldKeys.add(key)) send(action);
            return true;
        }
        if (key == GLFW.GLFW_KEY_SPACE || key == GLFW.GLFW_KEY_ENTER || key == GLFW.GLFW_KEY_KP_ENTER) { drop(); return true; }
        return true;
    }
    @Override public boolean keyReleased(int key, int scanCode, int modifiers) {
        heldKeys.remove(key);
        return keyAction(key) != null || super.keyReleased(key, scanCode, modifiers);
    }
    @Override public boolean mouseReleased(double x, double y, int button) {
        mouseDirection = null;
        return super.mouseReleased(x, y, button);
    }
    @Override public void onClose() {
        heldKeys.clear(); mouseDirection = null;
        send(ClawMachineNetwork.Action.EXIT);
        if (minecraft != null && minecraft.player != null) minecraft.player.closeContainer();
        super.onClose();
    }
    @Override public boolean isPauseScreen() { return false; }
    public void showFeedback(Component message) {
        feedback = message.copy();
        feedbackTicks = 60;
    }
    @Override public void removed() {
        if (previousHideGui != null && minecraft != null) minecraft.options.hideGui = previousHideGui;
        if (minecraft != null && minecraft.player != null) menu.removed(minecraft.player);
        super.removed();
    }
    @Override public void renderBackground(GuiGraphics graphics, int mouseX, int mouseY, float partialTick) {
        // Keep the world visible without the usual screen blur and dim layer.
        renderBg(graphics, partialTick, mouseX, mouseY);
    }
    private void renderBg(GuiGraphics graphics, float partialTick, int mouseX, int mouseY) {
        graphics.fill(leftPos, topPos, leftPos + imageWidth, topPos + imageHeight, 0xBE17212D);
        graphics.fill(leftPos, topPos, leftPos + imageWidth, topPos + 1, 0xA88BBDCB);
        if (feedbackTicks > 0) graphics.fill(leftPos, topPos - feedbackHeight() - 4, leftPos + imageWidth, topPos - 4, 0xDA17212D);
    }
    private int feedbackHeight() { return font.split(feedback, imageWidth - 20).size() * font.lineHeight + 8; }
    private void renderLabels(GuiGraphics graphics, int mouseX, int mouseY) {
        graphics.drawString(font, Component.translatable("claw.play.price"), 10, 7, 0xFFFFFF, false);
        var price = menu.getPrice();
        if (!price.isEmpty()) {
            graphics.renderItem(price, 10, 21);
            graphics.drawString(font, Component.literal("× " + price.getCount()), 30, 25, 0xFFFFFF, false);
        } else graphics.drawWordWrap(font, Component.translatable("claw.play.no_price"), 9, 21, 55, 0xE9B9A9);
        graphics.drawString(font, Component.translatable("claw.phase." + menu.getPhase().name().toLowerCase(Locale.ROOT)), 158, 7, 0xC7E8EC, false);
        graphics.drawCenteredString(font, Component.translatable("claw.play.keys"), imageWidth / 2, 44, 0xD1DBE0);
        if (feedbackTicks > 0) graphics.drawWordWrap(font, feedback, 10, -feedbackHeight(), imageWidth - 20, 0xFFFFFF);
    }
    @Override public void render(GuiGraphics graphics, int mouseX, int mouseY, float partialTick) {
        super.render(graphics, mouseX, mouseY, partialTick);
        graphics.pose().pushPose();
        graphics.pose().translate(leftPos, topPos, 0);
        renderLabels(graphics, mouseX, mouseY);
        graphics.pose().popPose();
        if (!menu.getPrice().isEmpty() && mouseX >= leftPos + 8 && mouseX <= leftPos + 64
            && mouseY >= topPos + 19 && mouseY <= topPos + 39)
            graphics.renderTooltip(font, menu.getPrice(), mouseX, mouseY);
    }
}
