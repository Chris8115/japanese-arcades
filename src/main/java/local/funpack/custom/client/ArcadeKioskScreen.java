package local.funpack.custom.client;

import java.util.ArrayList;
import java.util.List;
import local.funpack.custom.ArcadeKioskMenu;
import local.funpack.custom.ArcadeKioskNetwork;
import local.funpack.custom.ArcadeOrderCatalog;
import net.minecraft.client.gui.GuiGraphics;
import net.minecraft.client.gui.components.Button;
import net.minecraft.client.gui.components.Tooltip;
import net.minecraft.client.gui.screens.inventory.AbstractContainerScreen;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.util.FormattedCharSequence;
import net.minecraft.util.Mth;
import net.minecraft.world.entity.player.Inventory;
import net.minecraft.world.item.ItemStack;
import net.neoforged.neoforge.network.PacketDistributor;
import org.lwjgl.glfw.GLFW;

/** A browsable catalogue with visible material costs and one explicit purchase action. */
public final class ArcadeKioskScreen extends AbstractContainerScreen<ArcadeKioskMenu> {
    private static final int INK = 0x22394D;
    private static final int TEAL = 0x287B7B;
    private static final int MUTED = 0x647680;
    private static final int SUCCESS = 0x24734A;
    private static final int ERROR = 0xAF3744;
    private static final int ROWS = 5;
    private static final int ROW_HEIGHT = 19;
    private final List<EntryButton> entryButtons = new ArrayList<>();
    private ResourceLocation category;
    private List<ArcadeOrderCatalog.Entry> entries = List.of();
    private int selected;
    private int scroll;
    private int cooldown;
    private boolean suppressStatus;
    private Button order;

    public ArcadeKioskScreen(ArcadeKioskMenu menu, Inventory inventory, Component title) {
        super(menu, inventory, title);
        imageWidth = 320;
        imageHeight = 236;
        inventoryLabelX = 79;
        inventoryLabelY = 144;
        category = ArcadeOrderCatalog.categories().getFirst().id();
    }

    @Override
    protected void init() {
        super.init();
        entries = ArcadeOrderCatalog.entries(category);
        selected = Mth.clamp(selected, 0, Math.max(0, entries.size() - 1));
        scroll = Mth.clamp(scroll, 0, Math.max(0, entries.size() - ROWS));
        entryButtons.clear();
        List<ArcadeOrderCatalog.Category> categories = ArcadeOrderCatalog.categories();
        int tabWidth = Math.min(110, 298 / Math.max(1, categories.size()));
        for (int i = 0; i < categories.size(); i++) {
            ArcadeOrderCatalog.Category tab = categories.get(i);
            addRenderableWidget(new CategoryButton(leftPos + 11 + i * tabWidth, topPos + 24, tabWidth - 3, 17, tab));
        }
        for (int row = 0; row < ROWS; row++) {
            EntryButton button = new EntryButton(leftPos + 11, topPos + 44 + row * ROW_HEIGHT, row);
            entryButtons.add(addRenderableWidget(button));
        }
        order = addRenderableWidget(Button.builder(Component.translatable("kiosk.gui.order"), button -> orderSelected())
            .bounds(leftPos + 142, topPos + 124, 62, 17).build());
        refreshRows();
        updateOrderButton();
    }

    private void chooseCategory(ResourceLocation next) {
        if (category.equals(next)) return;
        category = next;
        entries = ArcadeOrderCatalog.entries(category);
        selected = 0;
        scroll = 0;
        suppressStatus = true;
        refreshRows();
        updateOrderButton();
    }

    private ArcadeOrderCatalog.Entry selectedEntry() {
        return entries.isEmpty() ? null : entries.get(selected);
    }

    private void selectEntry(int index) {
        selected = Mth.clamp(index, 0, Math.max(0, entries.size() - 1));
        if (selected < scroll) scroll = selected;
        if (selected >= scroll + ROWS) scroll = selected - ROWS + 1;
        suppressStatus = true;
        refreshRows();
        updateOrderButton();
    }

    private void refreshRows() {
        for (int row = 0; row < entryButtons.size(); row++) {
            EntryButton button = entryButtons.get(row);
            int index = scroll + row;
            button.visible = index < entries.size();
            if (button.visible) {
                button.setMessage(entries.get(index).title());
                button.setTooltip(Tooltip.create(entries.get(index).title()));
            }
        }
    }

    private void updateOrderButton() {
        ArcadeOrderCatalog.Entry entry = selectedEntry();
        order.visible = entry != null;
        order.active = entry != null && minecraft.player != null && cooldown == 0
            && ArcadeOrderCatalog.canAfford(minecraft.player, entry);
        order.setTooltip(entry != null && !order.active && cooldown == 0
            ? Tooltip.create(Component.translatable("kiosk.gui.missing")) : null);
    }

    private void orderSelected() {
        ArcadeOrderCatalog.Entry entry = selectedEntry();
        if (entry == null || !order.active) return;
        PacketDistributor.sendToServer(new ArcadeKioskNetwork.OrderPayload(menu.containerId, entry.id()));
        cooldown = 8;
        suppressStatus = false;
        updateOrderButton();
    }

    @Override
    protected void containerTick() {
        if (cooldown > 0) cooldown--;
        updateOrderButton();
    }

    @Override
    public boolean mouseScrolled(double mouseX, double mouseY, double horizontal, double vertical) {
        if (isHovering(10, 43, 128, 98, mouseX, mouseY) && entries.size() > ROWS) {
            scroll = Mth.clamp(scroll - (int) Math.signum(vertical), 0, entries.size() - ROWS);
            refreshRows();
            return true;
        }
        return super.mouseScrolled(mouseX, mouseY, horizontal, vertical);
    }

    @Override
    public boolean keyPressed(int keyCode, int scanCode, int modifiers) {
        if (!entries.isEmpty()) {
            if (keyCode == GLFW.GLFW_KEY_DOWN || keyCode == GLFW.GLFW_KEY_UP) {
                selectEntry(selected + (keyCode == GLFW.GLFW_KEY_DOWN ? 1 : -1));
                return true;
            }
            if (keyCode == GLFW.GLFW_KEY_PAGE_DOWN || keyCode == GLFW.GLFW_KEY_PAGE_UP) {
                selectEntry(selected + (keyCode == GLFW.GLFW_KEY_PAGE_DOWN ? ROWS : -ROWS));
                return true;
            }
            if (keyCode == GLFW.GLFW_KEY_HOME || keyCode == GLFW.GLFW_KEY_END) {
                selectEntry(keyCode == GLFW.GLFW_KEY_HOME ? 0 : entries.size() - 1);
                return true;
            }
        }
        return super.keyPressed(keyCode, scanCode, modifiers);
    }

    @Override
    protected void renderBg(GuiGraphics graphics, float partialTick, int mouseX, int mouseY) {
        graphics.fill(leftPos - 1, topPos - 1, leftPos + imageWidth + 1, topPos + imageHeight + 1, 0xFF233849);
        graphics.fill(leftPos, topPos, leftPos + imageWidth, topPos + imageHeight, 0xFFE9EFF0);
        graphics.fill(leftPos, topPos, leftPos + imageWidth, topPos + 21, 0xFFFDFEFE);
        graphics.fill(leftPos, topPos, leftPos + imageWidth, topPos + 2, 0xFFBA3441);
        graphics.fill(leftPos + 139, topPos + 43, leftPos + 310, topPos + 142, 0xFFF9FBFB);
        graphics.fill(leftPos + 11, topPos + 43, leftPos + 136, topPos + 140, 0xFFDDE6E8);
        graphics.fill(leftPos + 11, topPos + 142, leftPos + 309, topPos + 143, 0xFFC4D2D6);
        if (entries.size() > ROWS) {
            int length = Math.max(12, 95 * ROWS / entries.size());
            int offset = (95 - length) * scroll / (entries.size() - ROWS);
            graphics.fill(leftPos + 133, topPos + 44 + offset, leftPos + 135, topPos + 44 + offset + length, 0xFF4D7A83);
        }
        menu.slots.forEach(slot -> drawSlot(graphics, leftPos + slot.x, topPos + slot.y));
    }

    @Override
    protected void renderLabels(GuiGraphics graphics, int mouseX, int mouseY) {
        graphics.drawString(font, title, 11, 8, INK, false);
        graphics.drawString(font, playerInventoryTitle, inventoryLabelX, inventoryLabelY, INK, false);
        ArcadeOrderCatalog.Entry entry = selectedEntry();
        if (entry == null) {
            graphics.drawWordWrap(font, Component.translatable("kiosk.gui.empty"), 20, 61, 106, MUTED);
            graphics.drawWordWrap(font, Component.translatable("kiosk.gui.empty_hint"), 153, 69, 144, MUTED);
        } else {
            List<FormattedCharSequence> name = font.split(entry.title(), 162);
            for (int i = 0; i < Math.min(2, name.size()); i++) {
                graphics.drawString(font, name.get(i), 144, 46 + i * 9, INK, false);
            }
            item(graphics, entry.output(), 146, 70, 52);
            graphics.drawString(font, Component.translatable("kiosk.gui.need_have"), 216, 65, MUTED, false);
            for (int i = 0; i < entry.costs().size(); i++) {
                ArcadeOrderCatalog.Cost cost = entry.costs().get(i);
                int owned = ArcadeOrderCatalog.count(minecraft.player, cost.item());
                int y = 75 + i * 13;
                item(graphics, cost.stack(), 213, y, 12);
                String counts = cost.count() + " / " + owned;
                graphics.drawString(font, counts, 230, y + 2, owned >= cost.count() ? SUCCESS : ERROR, false);
            }
        }
        graphics.drawString(font, Component.translatable("kiosk.gui.status"), 12, 158, INK, false);
        int status = suppressStatus ? 0 : menu.getStatus();
        Component statusMessage = Component.translatable(status == 0
            ? entry == null ? "kiosk.gui.empty" : ArcadeOrderCatalog.canAfford(minecraft.player, entry)
                ? "kiosk.gui.ready" : "kiosk.gui.missing"
            : "kiosk.gui.status." + status);
        int statusColor = status == 1 ? SUCCESS : status == 2 || status == 3 ? ERROR : MUTED;
        graphics.drawWordWrap(font, statusMessage, 12, 173, 57, statusColor);
        graphics.drawWordWrap(font, Component.translatable("kiosk.gui.cost_hint"), 252, 162, 57, MUTED);
    }

    @Override
    public void render(GuiGraphics graphics, int mouseX, int mouseY, float partialTick) {
        super.render(graphics, mouseX, mouseY, partialTick);
        renderTooltip(graphics, mouseX, mouseY);
        ArcadeOrderCatalog.Entry entry = selectedEntry();
        if (entry != null) {
            if (isHovering(144, 46, 162, 18, mouseX, mouseY)) {
                graphics.renderTooltip(font, entry.title(), mouseX, mouseY);
            }
            for (int i = 0; i < entry.costs().size(); i++) {
                if (isHovering(211, 74 + i * 13, 96, 13, mouseX, mouseY)) {
                    ArcadeOrderCatalog.Cost cost = entry.costs().get(i);
                    graphics.renderComponentTooltip(font, List.of(cost.stack().getHoverName(),
                        Component.translatable("kiosk.gui.need", cost.count()),
                        Component.translatable("kiosk.gui.have", ArcadeOrderCatalog.count(minecraft.player, cost.item()))), mouseX, mouseY);
                }
            }
        }
    }

    private void item(GuiGraphics graphics, ItemStack stack, int x, int y, int size) {
        graphics.pose().pushPose();
        graphics.pose().translate(x, y, 0);
        float scale = size / 16F;
        graphics.pose().scale(scale, scale, 1);
        graphics.renderItem(stack, 0, 0);
        graphics.pose().popPose();
    }

    private static void drawSlot(GuiGraphics graphics, int x, int y) {
        graphics.fill(x - 1, y - 1, x + 17, y + 17, 0xFF82969F);
        graphics.fill(x, y, x + 17, y + 17, 0xFFFFFFFF);
        graphics.fill(x, y, x + 16, y + 16, 0xFFC9D6DB);
    }

    private final class CategoryButton extends Button {
        private final ArcadeOrderCatalog.Category tab;

        private CategoryButton(int x, int y, int width, int height, ArcadeOrderCatalog.Category tab) {
            super(x, y, width, height, tab.title(), button -> chooseCategory(tab.id()), DEFAULT_NARRATION);
            this.tab = tab;
            setTooltip(Tooltip.create(tab.title()));
        }

        @Override
        protected void renderWidget(GuiGraphics graphics, int mouseX, int mouseY, float partialTick) {
            boolean chosen = category.equals(tab.id());
            int background = chosen ? 0xFF287B7B : isHoveredOrFocused() ? 0xFFD2E2E5 : 0xFFE3EAEC;
            graphics.fill(getX(), getY(), getX() + width, getY() + height, background);
            if (chosen) graphics.fill(getX(), getY() + height - 2, getX() + width, getY() + height, 0xFF1D535E);
            String name = font.plainSubstrByWidth(tab.title().getString(), width - 10);
            graphics.drawString(font, name, getX() + (width - font.width(name)) / 2, getY() + 5, chosen ? 0xFFFFFF : INK, false);
        }
    }

    private final class EntryButton extends Button {
        private final int row;

        private EntryButton(int x, int y, int row) {
            super(x, y, 120, ROW_HEIGHT, Component.empty(), button -> selectEntry(scroll + row), DEFAULT_NARRATION);
            this.row = row;
        }

        @Override
        protected void renderWidget(GuiGraphics graphics, int mouseX, int mouseY, float partialTick) {
            int index = scroll + row;
            if (index >= entries.size()) return;
            ArcadeOrderCatalog.Entry entry = entries.get(index);
            boolean chosen = selected == index;
            graphics.fill(getX(), getY(), getX() + width, getY() + height - 1,
                chosen ? 0xFFC3DFDF : isHoveredOrFocused() ? 0xFFEEF4F5 : 0xFFE0E9EB);
            if (chosen) graphics.fill(getX(), getY(), getX() + 2, getY() + height - 1, 0xFF287B7B);
            graphics.renderItem(entry.output(), getX() + 4, getY() + 1);
            String title = entry.title().getString();
            String shown = font.width(title) > 92 ? font.plainSubstrByWidth(title, 83) + "..." : title;
            graphics.drawString(font, shown, getX() + 23, getY() + 6, chosen ? INK : MUTED, false);
        }
    }
}
