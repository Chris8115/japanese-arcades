package local.japanesearcades.client;

import java.text.NumberFormat;
import java.util.ArrayList;
import java.util.List;
import java.util.Locale;
import java.util.HashMap;
import java.util.Map;
import local.japanesearcades.ArcadeKioskMenu;
import local.japanesearcades.ArcadePassData;
import local.japanesearcades.ArcadePassItem;
import local.japanesearcades.MobFigureBlock;
import local.japanesearcades.ArcadePrizeCatalog;
import local.japanesearcades.ArcadePrizeCatalog.Category;
import local.japanesearcades.ArcadePrizeCatalog.Offer;
import local.japanesearcades.ArcadePrizeCatalog.Sort;
import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.Font;
import net.minecraft.client.gui.GuiGraphics;
import net.minecraft.client.gui.components.Button;
import net.minecraft.client.gui.components.EditBox;
import net.minecraft.client.gui.components.Tooltip;
import net.minecraft.client.gui.screens.Screen;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.util.Mth;
import net.minecraft.world.item.BlockItem;
import org.lwjgl.glfw.GLFW;

/** Paged, cached browsing. Only the current page and selected preview submit item models. */
final class ArcadeRewardBrowser {
    private static final int INK = 0x22394D, MUTED = 0x647680, TEAL = 0x287B7B;
    private static final int SUCCESS = 0x24734A, ERROR = 0xAF3744;
    private static final NumberFormat NUMBERS = NumberFormat.getIntegerInstance(Locale.US);
    private final ArcadeKioskScreen screen;
    private final ArcadeKioskMenu menu;
    private final Font font = Minecraft.getInstance().font;
    private final List<RewardTile> tiles = new ArrayList<>();
    private List<Offer> catalog = List.of(), offers = List.of();
    private final Map<ResourceLocation, Component> shortNames = new HashMap<>();
    private Category category = Category.ALL;
    private Sort sort = Sort.NAME;
    private String query = "";
    private boolean affordableOnly, inventoryOpen;
    private long observedPoints = Long.MIN_VALUE;
    private ResourceLocation selectedId;
    private int page, columns, rows, pageSize;
    private int x, y, width, height, gridWidth, cellWidth, cellHeight, detailX;
    private EditBox search;
    private Button previous, next, inventory, redeem, sortButton, affordable, clear, reset;

    ArcadeRewardBrowser(ArcadeKioskScreen screen) {
        this.screen = screen;
        this.menu = screen.getMenu();
    }

    void init(int x, int y, int width, int height) {
        this.x = x; this.y = y; this.width = width; this.height = height;
        gridWidth = width - 154;
        detailX = x + width - 136;
        columns = Math.max(3, gridWidth / 46);
        rows = Math.max(2, (height - 138) / 46);
        pageSize = columns * rows;
        cellWidth = gridWidth / columns;
        cellHeight = (height - 140) / rows;
        tiles.clear();
        // init also runs after language/resource reloads and resolution changes.
        snapshotCatalog();
        Category[] groups = Category.values();
        int tabWidth = (width - 20) / groups.length;
        for (int i = 0; i < groups.length; i++) {
            screen.addBrowserWidget(new GroupButton(x + 10 + i * tabWidth, y + 46, tabWidth - 2, groups[i]));
        }
        search = screen.addBrowserWidget(new EditBox(font, x + 11, y + 68, width - 44, 18,
            Component.translatable("kiosk.prize.search")));
        search.setMaxLength(80);
        search.setHint(Component.translatable("kiosk.prize.search"));
        search.setValue(query);
        search.setResponder(value -> { query = value; filter(true); });
        clear = button("kiosk.prize.clear", x + width - 29, y + 68, 18, b -> search.setValue(""));
        clear.setMessage(Component.literal("×"));
        clear.setTooltip(Tooltip.create(Component.translatable("kiosk.prize.clear")));
        sortButton = button("kiosk.prize.sort.name", x + 10, y + 90, 116, b -> {
            sort = Sort.values()[(sort.ordinal() + 1) % Sort.values().length];
            filter(true);
        });
        affordable = button("kiosk.prize.affordable", x + 130, y + 90, 94, b -> {
            affordableOnly = !affordableOnly; filter(true);
        });
        for (int i = 0; i < pageSize; i++) {
            RewardTile tile = new RewardTile(x + 10 + i % columns * cellWidth,
                y + 112 + i / columns * cellHeight, i);
            tiles.add(screen.addBrowserWidget(tile));
        }
        inventory = button("kiosk.prize.inventory", x + 10, y + height - 25, 72, b -> {
            inventoryOpen = !inventoryOpen;
            menu.setClientInventoryVisible(inventoryOpen);
            updateWidgets();
        });
        previous = button("kiosk.prize.previous", x + 88, y + height - 25, 18, b -> changePage(page - 1));
        previous.setMessage(Component.literal("<"));
        previous.setTooltip(Tooltip.create(Component.translatable("kiosk.prize.previous")));
        next = button("kiosk.prize.next", x + 10 + gridWidth - 18, y + height - 25, 18, b -> changePage(page + 1));
        next.setMessage(Component.literal(">"));
        next.setTooltip(Tooltip.create(Component.translatable("kiosk.prize.next")));
        redeem = button("kiosk.prize.redeem", detailX + 6, y + height - 25, 114, b -> {
            Offer selected = selected();
            if (selected != null) screen.redeemPrize(selected.entry().id());
        });
        reset = button("kiosk.prize.reset", x + 18, y + 176, gridWidth - 16, b -> {
            category = Category.ALL; affordableOnly = false; sort = Sort.NAME;
            query = ""; search.setValue(""); filter(true);
        });
        menu.layoutClientSlots(10 + (gridWidth - 162) / 2, 130, inventoryOpen,
            17, 48, width - 129, 114);
        menu.setPassSlotVisibility(false, true);
        filter(false);
    }

    private Button button(String key, int x, int y, int width, Button.OnPress action) {
        return screen.addBrowserWidget(Button.builder(Component.translatable(key), action).bounds(x, y, width, 18).build());
    }

    private ArcadePassData pass() { return ArcadePassItem.data(menu.getTargetPass()); }
    private long points() { ArcadePassData pass = pass(); return pass == null ? -1 : pass.prizePoints(); }
    private int pageCount() { return Math.max(1, (offers.size() + pageSize - 1) / pageSize); }
    private Offer selected() {
        return selectedId == null ? null : offers.stream().filter(o -> o.entry().id().equals(selectedId)).findFirst().orElse(null);
    }

    private void snapshotCatalog() {
        catalog = ArcadePrizeCatalog.snapshot();
        shortNames.clear();
        for (Offer offer : catalog) {
            Component name = offer.output().getItem() instanceof BlockItem item && item.getBlock() instanceof MobFigureBlock figure
                ? Component.translatable("entity.minecraft." + figure.mob()) : offer.title();
            shortNames.put(offer.entry().id(), name);
        }
    }

    private void filter(boolean resetPage) {
        observedPoints = points();
        offers = ArcadePrizeCatalog.browse(catalog, category, query, sort, observedPoints, affordableOnly);
        page = resetPage ? 0 : Mth.clamp(page, 0, pageCount() - 1);
        if (resetPage || selected() == null) selectedId = offers.isEmpty() ? null : offers.get(page * pageSize).entry().id();
        else {
            // A resize or changed price/balance can move the retained selection to another page.
            for (int i = 0; i < offers.size(); i++) {
                if (offers.get(i).entry().id().equals(selectedId)) { page = i / pageSize; break; }
            }
        }
        if (resetPage) screen.browserSelectionChanged();
        updateWidgets();
    }

    private void select(int index) {
        if (offers.isEmpty()) return;
        index = Mth.clamp(index, 0, offers.size() - 1);
        selectedId = offers.get(index).entry().id();
        page = index / pageSize;
        screen.browserSelectionChanged();
        updateWidgets();
        screen.setFocused(tiles.get(index % pageSize));
    }

    private void changePage(int newPage) {
        if (!inventoryOpen) select(Mth.clamp(newPage, 0, pageCount() - 1) * pageSize);
    }

    void tick() {
        if (ArcadePrizeCatalog.pricesChanged(catalog)) {
            snapshotCatalog(); filter(false);
        } else if (points() != observedPoints) {
            observedPoints = points();
            if (affordableOnly) filter(false);
        }
        updateWidgets();
    }

    private void updateWidgets() {
        for (int i = 0; i < tiles.size(); i++) {
            RewardTile tile = tiles.get(i);
            int index = page * pageSize + i;
            tile.visible = !inventoryOpen && index < offers.size();
            if (tile.visible) {
                Offer offer = offers.get(index);
                tile.setMessage(Component.translatable("kiosk.prize.offer", offer.title(), price(offer)));
            }
        }
        if (redeem == null) return;
        Offer selected = selected();
        redeem.active = selected != null && points() >= selected.price() && selected.price() > 0 && !screen.purchaseCoolingDown();
        redeem.setTooltip(redeem.active ? null : Tooltip.create(Component.translatable(pass() == null
            ? "kiosk.prize.insert_hint" : selected == null ? "kiosk.prize.choose" : "kiosk.prize.missing")));
        inventory.setMessage(Component.translatable(inventoryOpen ? "kiosk.prize.browse" : pass() == null
            ? "kiosk.prize.insert_pass" : "kiosk.prize.inventory"));
        inventory.setTooltip(Tooltip.create(Component.translatable("kiosk.prize.inventory_hint")));
        previous.visible = next.visible = !inventoryOpen;
        previous.active = page > 0;
        next.active = page + 1 < pageCount();
        sortButton.setMessage(sort.title());
        sortButton.setTooltip(Tooltip.create(sort.title()));
        affordable.setMessage(Component.literal(affordableOnly ? "[x] " : "[ ] ")
            .append(Component.translatable("kiosk.prize.affordable")));
        affordable.setTooltip(Tooltip.create(Component.translatable("kiosk.prize.affordable_hint")));
        clear.active = !query.isEmpty();
        reset.visible = !inventoryOpen && offers.isEmpty();
    }

    void renderBackground(GuiGraphics graphics) {
        graphics.drawString(font, Component.translatable("kiosk.prize.title"), x + 11, y + 8, INK, false);
        int status = screen.browserStatus();
        Component heading = status > 0 ? Component.translatable("kiosk.gui.status." + status)
            : Component.translatable("kiosk.prize.total", catalog.size());
        fit(graphics, heading, x + 134, y + 8, width - 145, status == 1 ? SUCCESS : status > 1 ? ERROR : MUTED, true);
        graphics.fill(x + 10, y + 111, x + 10 + gridWidth, y + height - 29, 0xFFDDE6E8);
        graphics.fill(detailX, y + 111, x + width - 10, y + height - 5, 0xFFF9FBFB);
        fit(graphics, Component.translatable("kiosk.prize.results", offers.size()), x + 229, y + 95, width - 239, MUTED, true);
        if (inventoryOpen) {
            graphics.drawString(font, Component.translatable("container.inventory"), x + 16, y + 116, INK, false);
            if (height >= 275) graphics.drawWordWrap(font, Component.translatable("kiosk.prize.inventory_hint"),
                x + 18, y + 217, gridWidth - 16, MUTED);
        } else if (offers.isEmpty()) {
            graphics.drawWordWrap(font, Component.translatable("kiosk.prize.no_results"), x + 19, y + 126, gridWidth - 18, INK);
            graphics.drawWordWrap(font, Component.translatable(affordableOnly && pass() == null
                ? "kiosk.prize.insert_hint" : "kiosk.prize.no_results_hint"), x + 19, y + 145, gridWidth - 18, MUTED);
        } else {
            Component pages = Component.translatable("kiosk.prize.page", page + 1, pageCount());
            int start = x + 108, available = x + 10 + gridWidth - 20 - start;
            fit(graphics, pages, start, y + height - 19, available, MUTED, false);
        }
        graphics.fill(detailX + 4, y + 112, detailX + 122, y + 136, 0xFFE0E9EB);
        graphics.drawString(font, Component.translatable(pass() == null ? "kiosk.prize.pass" : "kiosk.prize.balance"), detailX + 30, y + 114, MUTED, false);
        fit(graphics, pass() == null ? Component.translatable("kiosk.pass.insert") : Component.literal(NUMBERS.format(points())),
            detailX + 30, y + 125, 88, TEAL, false);
        Offer offer = selected();
        if (offer != null) {
            var lines = font.split(offer.title(), 114);
            for (int i = 0; i < Math.min(2, lines.size()); i++) graphics.drawString(font, lines.get(i), detailX + 6, y + 143 + i * 10, INK, false);
            boolean compact = height < 280;
            int size = compact ? 34 : Math.min(72, height - 232);
            int iconX = compact ? detailX + 7 : detailX + (126 - size) / 2;
            int iconY = compact ? y + height - 67 : y + 167;
            graphics.pose().pushPose();
            graphics.pose().translate(iconX, iconY, 0);
            graphics.pose().scale(size / 16F, size / 16F, 1);
            graphics.renderItem(offer.output(), 0, 0);
            graphics.pose().popPose();
            int priceX = compact ? detailX + 48 : detailX + 8;
            int priceY = y + height - 57;
            graphics.drawString(font, Component.translatable("kiosk.prize.cost"), priceX, priceY, MUTED, false);
            fit(graphics, price(offer), priceX, priceY + 12, compact ? 73 : 108, points() >= offer.price() && offer.price() > 0 ? SUCCESS : ERROR, false);
        } else graphics.drawWordWrap(font, Component.translatable("kiosk.prize.choose"), detailX + 8, y + 146, 108, MUTED);
        menu.slots.stream().filter(slot -> slot.isActive()).forEach(slot -> drawSlot(graphics, x + slot.x, y + slot.y));
    }

    void renderTooltips(GuiGraphics graphics, int mouseX, int mouseY) {
        for (RewardTile tile : tiles) {
            if (tile.visible && tile.isMouseOver(mouseX, mouseY)) {
                tooltip(graphics, offers.get(page * pageSize + tile.offset), mouseX, mouseY);
                return;
            }
        }
        Offer offer = selected();
        if (offer != null && inside(mouseX, mouseY, detailX + 4, y + 141, 118, height - 171)) tooltip(graphics, offer, mouseX, mouseY);
        if (inside(mouseX, mouseY, detailX + 29, y + 112, 92, 24)) {
            graphics.renderTooltip(font, pass() == null ? Component.translatable("kiosk.prize.insert_hint") : menu.getTargetPass().getHoverName(), mouseX, mouseY);
        }
    }

    private void tooltip(GuiGraphics graphics, Offer offer, int x, int y) {
        graphics.renderComponentTooltip(font, List.of(offer.title(), offer.entry().category().title(),
            Component.translatable("kiosk.prize.tooltip_cost", price(offer))), x, y);
    }

    boolean mouseScrolled(double mouseX, double mouseY, double vertical) {
        if (!inventoryOpen && inside(mouseX, mouseY, x + 10, y + 111, gridWidth, height - 138)) {
            if (vertical != 0) changePage(page - (int) Math.signum(vertical));
            return true;
        }
        return false;
    }

    boolean keyPressed(int keyCode, int scanCode, int modifiers) {
        if (keyCode == GLFW.GLFW_KEY_F && Screen.hasControlDown()) {
            screen.setFocused(search); search.setFocused(true); search.moveCursorToEnd(false); search.setHighlightPos(0); return true;
        }
        if (search.isFocused()) {
            if (keyCode == GLFW.GLFW_KEY_TAB) return false;
            if (keyCode == GLFW.GLFW_KEY_ESCAPE) { screen.setFocused(null); search.setFocused(false); }
            else search.keyPressed(keyCode, scanCode, modifiers);
            // Typed E, number keys and drop bindings must never act on the container.
            return true;
        }
        if (inventoryOpen || offers.isEmpty()) return false;
        boolean arrow = keyCode == GLFW.GLFW_KEY_LEFT || keyCode == GLFW.GLFW_KEY_RIGHT
            || keyCode == GLFW.GLFW_KEY_UP || keyCode == GLFW.GLFW_KEY_DOWN;
        if (arrow && screen.getFocused() != null && !(screen.getFocused() instanceof RewardTile)) return false;
        int selected = 0;
        for (int i = 0; i < offers.size(); i++) if (offers.get(i).entry().id().equals(selectedId)) { selected = i; break; }
        int index = switch (keyCode) {
            case GLFW.GLFW_KEY_RIGHT -> selected + 1;
            case GLFW.GLFW_KEY_LEFT -> selected - 1;
            case GLFW.GLFW_KEY_DOWN -> selected + columns;
            case GLFW.GLFW_KEY_UP -> selected - columns;
            case GLFW.GLFW_KEY_PAGE_DOWN -> selected + pageSize;
            case GLFW.GLFW_KEY_PAGE_UP -> selected - pageSize;
            case GLFW.GLFW_KEY_HOME -> 0;
            case GLFW.GLFW_KEY_END -> offers.size() - 1;
            default -> Integer.MIN_VALUE;
        };
        if (index != Integer.MIN_VALUE) {
            select(index); return true;
        }
        return false;
    }

    private Component price(Offer offer) { return offer.price() > 0 ? Component.literal(NUMBERS.format(offer.price())) : Component.literal("—"); }
    private static boolean inside(double mx, double my, int x, int y, int w, int h) { return mx >= x && mx < x + w && my >= y && my < y + h; }
    private void fit(GuiGraphics g, Component text, int x, int y, int width, int color, boolean right) {
        String full = text.getString();
        String shown = font.width(full) <= width ? full : font.plainSubstrByWidth(full, Math.max(0, width - font.width("…"))) + "…";
        g.drawString(font, shown, right ? x + width - font.width(shown) : x, y, color, false);
    }
    private static void drawSlot(GuiGraphics g, int x, int y) {
        g.fill(x - 1, y - 1, x + 17, y + 17, 0xFF82969F);
        g.fill(x, y, x + 17, y + 17, 0xFFFFFFFF);
        g.fill(x, y, x + 16, y + 16, 0xFFC9D6DB);
    }

    private final class GroupButton extends Button {
        private final Category group;
        GroupButton(int x, int y, int width, Category group) {
            super(x, y, width, 17, group.title(), b -> { category = group; filter(true); }, DEFAULT_NARRATION);
            this.group = group;
            long count = catalog.stream().filter(o -> group == Category.ALL || o.entry().category() == group).count();
            setTooltip(Tooltip.create(Component.translatable("kiosk.prize.group_count", group.title(), count)));
        }
        @Override protected void renderWidget(GuiGraphics g, int mx, int my, float tick) {
            boolean chosen = category == group;
            g.fill(getX(), getY(), getX() + width, getY() + height, chosen ? 0xFF287B7B : isHoveredOrFocused() ? 0xFFD2E2E5 : 0xFFE0E9EB);
            Component shortTitle = Component.translatable("kiosk.prize.category." + group.id() + ".short");
            // Keep every category legible at the minimum GUI size; full labels are narrated/tooltiped.
            float scale = Math.min(1, (width - 5F) / Math.max(1, font.width(shortTitle)));
            g.pose().pushPose();
            g.pose().translate(getX() + (width - font.width(shortTitle) * scale) / 2, getY() + 5, 0);
            g.pose().scale(scale, scale, 1);
            g.drawString(font, shortTitle, 0, 0, chosen ? 0xFFFFFF : INK, false);
            g.pose().popPose();
        }
    }

    private final class RewardTile extends Button {
        private final int offset;
        RewardTile(int x, int y, int offset) {
            super(x, y, cellWidth - 2, cellHeight - 2, Component.empty(), b -> select(page * pageSize + offset), DEFAULT_NARRATION);
            this.offset = offset;
        }
        @Override protected void renderWidget(GuiGraphics g, int mx, int my, float tick) {
            int index = page * pageSize + offset;
            if (index >= offers.size()) return;
            Offer offer = offers.get(index);
            boolean chosen = offer.entry().id().equals(selectedId);
            g.fill(getX(), getY(), getX() + width, getY() + height, chosen ? 0xFF287B7B : isHoveredOrFocused() ? 0xFFFDFEFE : 0xFFEAF0F1);
            if (chosen || isFocused()) {
                g.renderOutline(getX(), getY(), width, height, chosen ? 0xFF1D535E : 0xFF287B7B);
            }
            int iconSize = height < 50 ? 20 : 26;
            g.pose().pushPose();
            g.pose().translate(getX() + (width - iconSize) / 2F, getY() + 2, 0);
            g.pose().scale(iconSize / 16F, iconSize / 16F, 1);
            g.renderItem(offer.output(), 0, 0);
            g.pose().popPose();
            fit(g, shortNames.get(offer.entry().id()), getX() + 3, getY() + height - 22, width - 6, chosen ? 0xFFFFFF : INK, false);
            Component price = price(offer);
            String amount = price.getString();
            fit(g, price, getX() + Math.max(3, (width - font.width(amount)) / 2), getY() + height - 11, width - 6,
                chosen ? 0xFFFFFF : points() >= offer.price() && offer.price() > 0 ? SUCCESS : MUTED, false);
        }
    }
}
