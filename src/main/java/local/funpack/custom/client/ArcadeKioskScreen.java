package local.funpack.custom.client;

import java.util.ArrayList;
import java.util.List;
import java.util.UUID;
import java.text.NumberFormat;
import local.funpack.custom.ArcadeKioskMenu;
import local.funpack.custom.ArcadeKioskNetwork;
import local.funpack.custom.ArcadeOrderCatalog;
import local.funpack.custom.ArcadeEconomyConfig;
import local.funpack.custom.ArcadePassData;
import local.funpack.custom.ArcadePassItem;
import local.funpack.custom.ArcadePrizeCatalog;
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
    private static final ResourceLocation PASSES = ResourceLocation.fromNamespaceAndPath("funpackcustom", "passes");
    private static final UUID ZERO_ID = new UUID(0, 0);
    private static final NumberFormat NUMBERS = NumberFormat.getIntegerInstance(java.util.Locale.US);
    private final List<EntryButton> entryButtons = new ArrayList<>();
    private ResourceLocation category;
    private List<ArcadeOrderCatalog.Entry> entries = List.of();
    private List<ArcadePrizeCatalog.Entry> prizes = List.of();
    private List<PassRef> passes = List.of();
    private final List<Button> exchangeButtons = new ArrayList<>();
    private Button targetSelector, sourceSelector, transfer, issue;
    private int targetSlot = -1, sourceSlot = -1, statusRevision;
    private UUID targetId, sourceId;
    private boolean confirmTransfer;
    private boolean hasAnyPass;
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
        prizes = ArcadePrizeCatalog.entries();
        selected = Mth.clamp(selected, 0, Math.max(0, entryCount() - 1));
        scroll = Mth.clamp(scroll, 0, Math.max(0, entryCount() - ROWS));
        entryButtons.clear();
        exchangeButtons.clear();
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
        targetSelector = addRenderableWidget(Button.builder(Component.empty(), button -> cyclePass(false))
            .bounds(leftPos + 11, topPos + 45, 145, 17).build());
        sourceSelector = addRenderableWidget(Button.builder(Component.empty(), button -> cyclePass(true))
            .bounds(leftPos + 164, topPos + 45, 145, 17).build());
        transfer = addRenderableWidget(Button.builder(Component.translatable("kiosk.pass.transfer"), button -> transferSelected())
            .bounds(leftPos + 167, topPos + 104, 138, 17).build());
        issue = addRenderableWidget(Button.builder(Component.translatable("kiosk.pass.issue"), button -> {
            PacketDistributor.sendToServer(new ArcadeKioskNetwork.IssuePassPayload(menu.containerId));
            sentAction();
        }).bounds(leftPos + 95, topPos + 108, 130, 20).build());
        List<ArcadeEconomyConfig.Exchange> rates = ArcadeEconomyConfig.exchangeRates();
        for (int i = 0; i < rates.size(); i++) {
            int index = i;
            exchangeButtons.add(addRenderableWidget(Button.builder(Component.empty(), button -> exchange(index))
                .bounds(leftPos + 110, topPos + 86 + i * 13, 43, 12).build()));
        }
        statusRevision = menu.getStatusRevision();
        refreshPasses();
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
        confirmTransfer = false;
        refreshRows();
        updateOrderButton();
    }

    private ArcadeOrderCatalog.Entry selectedEntry() {
        return isPrizeTab() || isPassTab() || entries.isEmpty() ? null : entries.get(selected);
    }

    private boolean isPrizeTab() { return category.equals(ArcadeOrderCatalog.PRIZES); }
    private boolean isPassTab() { return category.equals(PASSES); }
    private int entryCount() { return isPassTab() ? 0 : isPrizeTab() ? prizes.size() : entries.size(); }
    private Component entryTitle(int index) { return isPrizeTab() ? prizes.get(index).title() : entries.get(index).title(); }
    private ItemStack entryOutput(int index) { return isPrizeTab() ? prizes.get(index).output() : entries.get(index).output(); }

    private void selectEntry(int index) {
        selected = Mth.clamp(index, 0, Math.max(0, entryCount() - 1));
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
            button.visible = !isPassTab() && index < entryCount();
            if (button.visible) {
                button.setMessage(entryTitle(index));
                button.setTooltip(Tooltip.create(entryTitle(index)));
            }
        }
    }

    private void updateOrderButton() {
        if (order == null) return;
        ArcadeOrderCatalog.Entry entry = selectedEntry();
        order.visible = !isPassTab() && entryCount() > 0;
        order.active = cooldown == 0 && minecraft.player != null && (isPrizeTab() ? prizeAffordable()
            : entry != null && ArcadeOrderCatalog.canAfford(minecraft.player, entry));
        order.setTooltip(order.visible && !order.active && cooldown == 0
            ? Tooltip.create(Component.translatable(isPrizeTab() ? target() == null ? "kiosk.pass.no_pass" : "kiosk.prize.missing" : "kiosk.gui.missing")) : null);
        updatePassWidgets();
    }

    private void orderSelected() {
        if (isPrizeTab()) {
            PassRef pass = target();
            if (pass == null || !order.active) return;
            PacketDistributor.sendToServer(new ArcadeKioskNetwork.PrizePayload(menu.containerId,
                prizes.get(selected).id(), pass.slot(), pass.data().id(), pass.data().revision()));
            sentAction();
            return;
        }
        ArcadeOrderCatalog.Entry entry = selectedEntry();
        if (entry == null || !order.active) return;
        PacketDistributor.sendToServer(new ArcadeKioskNetwork.OrderPayload(menu.containerId, entry.id()));
        sentAction();
    }

    @Override
    protected void containerTick() {
        if (cooldown > 0) cooldown--;
        refreshPasses();
        if (statusRevision != menu.getStatusRevision()) {
            statusRevision = menu.getStatusRevision();
            suppressStatus = false;
            confirmTransfer = false;
        }
        updateOrderButton();
    }

    @Override
    public boolean mouseScrolled(double mouseX, double mouseY, double horizontal, double vertical) {
        if (!isPassTab() && isHovering(10, 43, 128, 98, mouseX, mouseY) && entryCount() > ROWS) {
            scroll = Mth.clamp(scroll - (int) Math.signum(vertical), 0, entryCount() - ROWS);
            refreshRows();
            return true;
        }
        return super.mouseScrolled(mouseX, mouseY, horizontal, vertical);
    }

    @Override
    public boolean keyPressed(int keyCode, int scanCode, int modifiers) {
        if (entryCount() > 0) {
            if (keyCode == GLFW.GLFW_KEY_DOWN || keyCode == GLFW.GLFW_KEY_UP) {
                selectEntry(selected + (keyCode == GLFW.GLFW_KEY_DOWN ? 1 : -1));
                return true;
            }
            if (keyCode == GLFW.GLFW_KEY_PAGE_DOWN || keyCode == GLFW.GLFW_KEY_PAGE_UP) {
                selectEntry(selected + (keyCode == GLFW.GLFW_KEY_PAGE_DOWN ? ROWS : -ROWS));
                return true;
            }
            if (keyCode == GLFW.GLFW_KEY_HOME || keyCode == GLFW.GLFW_KEY_END) {
                selectEntry(keyCode == GLFW.GLFW_KEY_HOME ? 0 : entryCount() - 1);
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
        if (isPassTab()) {
            graphics.fill(leftPos + 11, topPos + 43, leftPos + 157, topPos + 141, 0xFFF9FBFB);
            graphics.fill(leftPos + 160, topPos + 43, leftPos + 310, topPos + 141, 0xFFE0E9EB);
        } else if (entryCount() > ROWS) {
            int length = Math.max(12, 95 * ROWS / entryCount());
            int offset = (95 - length) * scroll / (entryCount() - ROWS);
            graphics.fill(leftPos + 133, topPos + 44 + offset, leftPos + 135, topPos + 44 + offset + length, 0xFF4D7A83);
        }
        menu.slots.forEach(slot -> drawSlot(graphics, leftPos + slot.x, topPos + slot.y));
    }

    @Override
    protected void renderLabels(GuiGraphics graphics, int mouseX, int mouseY) {
        graphics.drawString(font, title, 11, 8, INK, false);
        graphics.drawString(font, playerInventoryTitle, inventoryLabelX, inventoryLabelY, INK, false);
        ArcadeOrderCatalog.Entry entry = selectedEntry();
        if (isPassTab()) {
            renderPasses(graphics);
        } else if (isPrizeTab() && !prizes.isEmpty()) {
            renderPrize(graphics);
        } else if (entry == null) {
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
        String idle = isPassTab() ? passes.isEmpty() ? "kiosk.pass.no_pass" : "kiosk.pass.ready"
            : isPrizeTab() ? target() == null ? "kiosk.pass.no_pass" : prizeAffordable() ? "kiosk.gui.ready" : "kiosk.prize.missing"
            : entry == null ? "kiosk.gui.empty" : ArcadeOrderCatalog.canAfford(minecraft.player, entry) ? "kiosk.gui.ready" : "kiosk.gui.missing";
        Component statusMessage = Component.translatable(status == 0 ? idle : "kiosk.gui.status." + status);
        int statusColor = status == 1 || status >= 4 && status <= 6 ? SUCCESS : status > 0 ? ERROR : MUTED;
        graphics.drawWordWrap(font, statusMessage, 12, 173, 57, statusColor);
        graphics.drawWordWrap(font, Component.translatable(isPassTab() ? "kiosk.pass.hint" : isPrizeTab()
            ? "kiosk.prize.hint" : "kiosk.gui.cost_hint"), 252, 162, 57, MUTED);
    }

    @Override
    public void render(GuiGraphics graphics, int mouseX, int mouseY, float partialTick) {
        super.render(graphics, mouseX, mouseY, partialTick);
        renderTooltip(graphics, mouseX, mouseY);
        if (isPassTab()) {
            if (target() != null && isHovering(11, 63, 145, 22, mouseX, mouseY))
                graphics.renderComponentTooltip(font, passTooltip(target(), false), mouseX, mouseY);
            if (source() != null && isHovering(164, 63, 145, 22, mouseX, mouseY))
                graphics.renderComponentTooltip(font, passTooltip(source(), true), mouseX, mouseY);
        } else if (isPrizeTab() && !prizes.isEmpty()) {
            if (isHovering(144, 46, 162, 18, mouseX, mouseY))
                graphics.renderTooltip(font, prizes.get(selected).title(), mouseX, mouseY);
            if (target() != null && isHovering(210, 86, 96, 37, mouseX, mouseY))
                graphics.renderComponentTooltip(font, passTooltip(target(), false), mouseX, mouseY);
        }
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

    private record PassRef(int slot, ItemStack stack, ArcadePassData data) {}

    private PassRef target() { return passes.stream().filter(pass -> pass.slot() == targetSlot).findFirst().orElse(null); }
    private PassRef source() { return passes.stream().filter(pass -> pass.slot() == sourceSlot && pass.slot() != targetSlot).findFirst().orElse(null); }

    private int resolvePass(int slot, UUID id, int avoid) {
        for (PassRef pass : passes) if (pass.slot() == slot && pass.slot() != avoid
            && (pass.data().id().equals(id) || ZERO_ID.equals(id))) return slot;
        if (id != null && !id.equals(ZERO_ID)) for (PassRef pass : passes)
            if (pass.slot() != avoid && pass.data().id().equals(id)) return pass.slot();
        return passes.stream().filter(pass -> pass.slot() != avoid).mapToInt(PassRef::slot).findFirst().orElse(-1);
    }

    private void refreshPasses() {
        if (minecraft.player == null) return;
        List<PassRef> current = new ArrayList<>();
        hasAnyPass = minecraft.player.getOffhandItem().getItem() instanceof ArcadePassItem
            || menu.getCarried().getItem() instanceof ArcadePassItem
            || minecraft.player.inventoryMenu.getCarried().getItem() instanceof ArcadePassItem;
        for (int slot = 0; slot < 36; slot++) {
            ItemStack stack = minecraft.player.getInventory().getItem(slot);
            if (stack.getItem() instanceof ArcadePassItem) hasAnyPass = true;
            ArcadePassData data = ArcadePassItem.data(stack);
            if (ArcadePassItem.isPass(stack) && data != null) current.add(new PassRef(slot, stack, data));
        }
        passes = current;
        int previousTarget = targetSlot, previousSource = sourceSlot;
        targetSlot = resolvePass(targetSlot, targetId, -1);
        sourceSlot = resolvePass(sourceSlot, sourceId, targetSlot);
        UUID nextTarget = target() == null ? null : target().data().id();
        UUID nextSource = source() == null ? null : source().data().id();
        if (previousTarget != targetSlot || previousSource != sourceSlot
                || !java.util.Objects.equals(targetId, nextTarget) || !java.util.Objects.equals(sourceId, nextSource)) confirmTransfer = false;
        targetId = nextTarget; sourceId = nextSource;
    }

    private void cyclePass(boolean chooseSource) {
        List<PassRef> choices = passes.stream().filter(pass -> !chooseSource || pass.slot() != targetSlot).toList();
        if (choices.isEmpty()) return;
        int slot = chooseSource ? sourceSlot : targetSlot;
        int index = 0;
        for (int i = 0; i < choices.size(); i++) if (choices.get(i).slot() == slot) index = (i + 1) % choices.size();
        PassRef chosen = choices.get(index);
        if (chooseSource) { sourceSlot = chosen.slot(); sourceId = chosen.data().id(); }
        else { targetSlot = chosen.slot(); targetId = chosen.data().id(); }
        confirmTransfer = false;
        refreshPasses(); updatePassWidgets();
    }

    private List<Component> passTooltip(PassRef pass, boolean source) {
        return List.of(Component.translatable(source ? "kiosk.pass.source" : "kiosk.pass.target"), pass.stack().getHoverName(),
            ArcadePassItem.designName(pass.data()), Component.translatable("kiosk.pass.id", pass.data().id().toString()),
            Component.translatable("kiosk.pass.slot", pass.slot() + 1),
            Component.translatable("kiosk.pass.credits", NUMBERS.format(pass.data().credits())),
            Component.translatable("kiosk.pass.points", NUMBERS.format(pass.data().prizePoints())));
    }

    private void selector(Button button, PassRef pass, boolean source) {
        String value = pass == null ? Component.translatable("kiosk.pass.none").getString()
            : "#" + (pass.slot() + 1) + " " + pass.data().id().toString().substring(0, 6) + " · " + pass.stack().getHoverName().getString();
        String prefix = source ? "B: " : "A: ";
        int room = button.getWidth() - 12 - font.width(prefix);
        if (font.width(value) > room) value = font.plainSubstrByWidth(value, room - font.width("…")) + "…";
        button.setMessage(Component.literal(prefix + value));
        button.setTooltip(pass == null ? Tooltip.create(Component.translatable("kiosk.pass.no_pass"))
            : Tooltip.create(Component.translatable(source ? "kiosk.pass.source" : "kiosk.pass.target")
                .append("\n").append(pass.stack().getHoverName()).append("\n").append(ArcadePassItem.designName(pass.data()))
                .append("\n").append(Component.translatable("kiosk.pass.id", pass.data().id().toString().substring(0, 8)))
                .append("\n").append(Component.translatable("kiosk.pass.slot", pass.slot() + 1))));
    }

    private void updatePassWidgets() {
        if (targetSelector == null) return;
        boolean tab = isPassTab(), hasPass = !passes.isEmpty();
        targetSelector.visible = (tab && hasPass) || isPrizeTab();
        targetSelector.setPosition(leftPos + (tab ? 11 : 142), topPos + (tab ? 45 : 65));
        targetSelector.setWidth(tab ? 145 : 163);
        targetSelector.active = passes.size() > 1 && cooldown == 0;
        selector(targetSelector, target(), false);
        sourceSelector.visible = tab && hasPass;
        sourceSelector.active = passes.size() > 2 && cooldown == 0;
        selector(sourceSelector, source(), true);
        issue.visible = tab && !hasPass; issue.active = cooldown == 0 && !hasAnyPass;
        issue.setTooltip(hasAnyPass ? Tooltip.create(Component.translatable("kiosk.pass.move_to_inventory")) : null);
        transfer.visible = tab && hasPass;
        PassRef from = source(), to = target();
        transfer.active = cooldown == 0 && from != null && to != null
            && (from.data().credits() > 0 || from.data().prizePoints() > 0);
        transfer.setMessage(Component.translatable(confirmTransfer ? "kiosk.pass.confirm_transfer" : "kiosk.pass.transfer"));
        transfer.setTooltip(Tooltip.create(Component.translatable("kiosk.pass.transfer_hint")));
        List<ArcadeEconomyConfig.Exchange> rates = ArcadeEconomyConfig.exchangeRates();
        for (int i = 0; i < exchangeButtons.size(); i++) {
            var button = exchangeButtons.get(i); var rate = rates.get(i);
            button.visible = tab && hasPass;
            button.active = to != null && cooldown == 0 && ArcadeOrderCatalog.count(minecraft.player, rate.material()) > 0;
            String rateText = "+" + NUMBERS.format(rate.credits());
            if (font.width(rateText) > button.getWidth() - 8) {
                NumberFormat compact = NumberFormat.getCompactNumberInstance(java.util.Locale.US, NumberFormat.Style.SHORT);
                compact.setMaximumFractionDigits(1);
                rateText = "+" + compact.format(rate.credits());
            }
            button.setMessage(Component.literal(rateText));
            button.setTooltip(Tooltip.create(Component.translatable("kiosk.pass.exchange", new ItemStack(rate.material()).getHoverName(), rate.credits())));
        }
    }

    private boolean prizeAffordable() {
        if (prizes.isEmpty() || target() == null) return false;
        int cost = ArcadeEconomyConfig.prizePrice(prizes.get(selected).id());
        return cost > 0 && target().data().prizePoints() >= cost;
    }

    private void exchange(int index) {
        PassRef pass = target();
        if (pass == null || cooldown != 0) return;
        var material = net.minecraft.core.registries.BuiltInRegistries.ITEM.getKey(ArcadeEconomyConfig.exchangeRates().get(index).material());
        PacketDistributor.sendToServer(new ArcadeKioskNetwork.ExchangePayload(menu.containerId, pass.slot(), pass.data().id(), pass.data().revision(), material));
        sentAction();
    }

    private void transferSelected() {
        PassRef from = source(), to = target();
        if (from == null || to == null || !transfer.active) return;
        if (!confirmTransfer) { confirmTransfer = true; updatePassWidgets(); return; }
        PacketDistributor.sendToServer(new ArcadeKioskNetwork.TransferPayload(menu.containerId,
            from.slot(), from.data().id(), from.data().revision(), to.slot(), to.data().id(), to.data().revision()));
        confirmTransfer = false; sentAction();
    }

    private void sentAction() { cooldown = 8; suppressStatus = false; updateOrderButton(); }

    private void fit(GuiGraphics graphics, Component value, int x, int y, int width, int color) {
        float scale = Math.min(1, width / (float)Math.max(1, font.width(value)));
        graphics.pose().pushPose(); graphics.pose().translate(x, y, 0); graphics.pose().scale(scale, scale, 1);
        graphics.drawString(font, value, 0, 0, color, false); graphics.pose().popPose();
    }

    private void balances(GuiGraphics graphics, PassRef pass, int x) {
        if (pass == null) return;
        fit(graphics, Component.translatable("kiosk.pass.credits", NUMBERS.format(pass.data().credits())), x, 65, 139, INK);
        fit(graphics, Component.translatable("kiosk.pass.points", NUMBERS.format(pass.data().prizePoints())), x, 76, 139, TEAL);
    }

    private void renderPasses(GuiGraphics graphics) {
        if (passes.isEmpty()) {
            graphics.drawWordWrap(font, Component.translatable(hasAnyPass ? "kiosk.pass.move_to_inventory" : "kiosk.pass.welcome"), 27, 56, 269, INK);
            return;
        }
        balances(graphics, target(), 14); balances(graphics, source(), 166);
        var rates = ArcadeEconomyConfig.exchangeRates();
        for (int i = 0; i < rates.size(); i++) {
            var rate = rates.get(i); int y = 86 + i * 13;
            item(graphics, new ItemStack(rate.material()), 15, y, 12);
            int owned = ArcadeOrderCatalog.count(minecraft.player, rate.material());
            fit(graphics, Component.translatable("kiosk.pass.trade_count", owned), 32, y + 2, 73, owned > 0 ? MUTED : ERROR);
        }
        if (source() == null) {
            graphics.drawWordWrap(font, Component.translatable("kiosk.pass.need_source"), 166, 68, 138, MUTED);
        } else {
            fit(graphics, Component.translatable("kiosk.pass.direction", sourceSlot + 1, targetSlot + 1), 166, 91, 139, TEAL);
        }
        graphics.drawWordWrap(font, Component.translatable(confirmTransfer ? "kiosk.pass.confirm_hint" : "kiosk.pass.transfer_hint"), 166, 124, 139, MUTED);
    }

    private void renderPrize(GuiGraphics graphics) {
        var prize = prizes.get(selected);
        List<FormattedCharSequence> name = font.split(prize.title(), 162);
        for (int i = 0; i < Math.min(2, name.size()); i++) graphics.drawString(font, name.get(i), 144, 46 + i * 9, INK, false);
        item(graphics, prize.output(), 153, 84, 38);
        int cost = ArcadeEconomyConfig.prizePrice(prize.id());
        graphics.drawString(font, Component.translatable("kiosk.prize.cost"), 211, 86, MUTED, false);
        fit(graphics, Component.literal(NUMBERS.format(cost)), 211, 96, 95, prizeAffordable() ? SUCCESS : ERROR);
        graphics.drawString(font, Component.translatable("kiosk.prize.balance"), 211, 109, MUTED, false);
        fit(graphics, Component.literal(NUMBERS.format(target() == null ? 0 : target().data().prizePoints())), 211, 120, 95, TEAL);
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
            if (index >= entryCount()) return;
            boolean chosen = selected == index;
            graphics.fill(getX(), getY(), getX() + width, getY() + height - 1,
                chosen ? 0xFFC3DFDF : isHoveredOrFocused() ? 0xFFEEF4F5 : 0xFFE0E9EB);
            if (chosen) graphics.fill(getX(), getY(), getX() + 2, getY() + height - 1, 0xFF287B7B);
            graphics.renderItem(entryOutput(index), getX() + 4, getY() + 1);
            String title = entryTitle(index).getString();
            String shown = font.width(title) > 92 ? font.plainSubstrByWidth(title, 83) + "..." : title;
            graphics.drawString(font, shown, getX() + 23, getY() + 6, chosen ? INK : MUTED, false);
        }
    }
}
