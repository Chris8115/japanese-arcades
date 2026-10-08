package local.japanesearcades.client;

import local.japanesearcades.FigureShelfMenu;
import net.minecraft.client.gui.GuiGraphics;
import net.minecraft.client.gui.screens.inventory.AbstractContainerScreen;
import net.minecraft.network.chat.Component;
import net.minecraft.world.entity.player.Inventory;

/** The slot arrangement matches the shelf as seen from its front. */
public final class FigureShelfScreen extends AbstractContainerScreen<FigureShelfMenu> {
    public FigureShelfScreen(FigureShelfMenu menu, Inventory inventory, Component title) {
        super(menu, inventory, title);
        imageWidth = 176;
        imageHeight = 166;
        inventoryLabelY = 74;
    }

    @Override protected void renderBg(GuiGraphics graphics, float partialTick, int mouseX, int mouseY) {
        int x = leftPos, y = topPos;
        graphics.fill(x, y, x + imageWidth, y + imageHeight, 0xFF3C3630);
        graphics.fill(x + 2, y + 2, x + imageWidth - 2, y + imageHeight - 2, 0xFFF1EDE4);
        graphics.fill(x + 2, y + 2, x + imageWidth - 2, y + 5, 0xFF287B7B);
        graphics.fill(x + 6, y + 24, x + 170, y + 69, 0xFFE1DBCE);
        for (int row = 0; row < menu.rows(); row++) {
            int sy = y + 30 + row * 18;
            graphics.fill(x + 51, sy + 16, x + 125, sy + 18, 0xFF806447);
        }
        for (var slot : menu.slots) {
            int sx = x + slot.x, sy = y + slot.y;
            graphics.fill(sx - 1, sy - 1, sx + 17, sy + 17, 0xFF71685D);
            graphics.fill(sx, sy, sx + 17, sy + 17, 0xFFFFFFFF);
            graphics.fill(sx, sy, sx + 16, sy + 16, 0xFFBEB9AD);
        }
    }

    @Override protected void renderLabels(GuiGraphics graphics, int mouseX, int mouseY) {
        graphics.drawString(font, title, 8, 10, 0x3C3630, false);
        if (menu.rows() == 2) {
            graphics.drawString(font, Component.translatable("shelf.gui.upper"), 12, 34, 0x675A49, false);
            graphics.drawString(font, Component.translatable("shelf.gui.lower"), 12, 52, 0x675A49, false);
        } else {
            graphics.drawString(font, Component.translatable("shelf.gui.display"), 10, 34, 0x675A49, false);
            graphics.drawCenteredString(font, Component.translatable("shelf.gui.hint"), 88, 55, 0x675A49);
        }
        graphics.drawString(font, playerInventoryTitle, inventoryLabelX, inventoryLabelY, 0x3C3630, false);
    }

    @Override public void render(GuiGraphics graphics, int mouseX, int mouseY, float partialTick) {
        super.render(graphics, mouseX, mouseY, partialTick);
        renderTooltip(graphics, mouseX, mouseY);
    }
}
