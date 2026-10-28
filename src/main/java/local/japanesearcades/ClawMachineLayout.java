package local.japanesearcades;

import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;

/** Shared footprint, stock indexing and model-space crane geometry. */
public enum ClawMachineLayout {
    LARGE(3, 3, 5, 8, 40, 20.5F, 36.5F, 41.8F, 1, 18, 7, 8, 19.2F, 16.1F, 26),
    COMPACT(2, 2, 4, 6, 26, 13.5F, 23, 28.1F, .85F, 11, 5, 5, 11.2F, 8.65F, 16.5F);

    private final int width, height, columns;
    private final float minX, maxX, prizeY, homeY, railY, clawScale, bedY, chuteY, deliveryY, priceX, priceY, countX;
    ClawMachineLayout(int width, int height, int columns, float minX, float maxX, float prizeY,
            float homeY, float railY, float clawScale, float bedY, float chuteY, float deliveryY,
            float priceX, float priceY, float countX) {
        this.width = width; this.height = height; this.columns = columns;
        this.minX = minX; this.maxX = maxX; this.prizeY = prizeY; this.homeY = homeY; this.railY = railY;
        this.clawScale = clawScale; this.bedY = bedY; this.chuteY = chuteY; this.deliveryY = deliveryY;
        this.priceX = priceX; this.priceY = priceY; this.countX = countX;
    }
    public int width() { return width; }
    public int depth() { return 2; }
    public int height() { return height; }
    public int floorPartCount() { return width * depth(); }
    public int partCount() { return floorPartCount() * height; }
    public float modelWidth() { return width * 16; }
    public float modelDepth() { return depth() * 16; }
    public float modelHeight() { return height * 16; }
    public int columns() { return columns; }
    public int rows() { return 3; }
    public int rewardCount() { return columns * rows(); }
    public int inventorySize() { return 19 + (columns - 3) * rows(); }

    /** Old price/reward/cash slot IDs never move; additional prize columns are appended. */
    public int rewardSlot(int displayIndex) {
        if (displayIndex < 0 || displayIndex >= rewardCount()) throw new IndexOutOfBoundsException(displayIndex);
        int row = displayIndex / columns, column = displayIndex % columns;
        return column < 3 ? 1 + row * 3 + column : 19 + row * (columns - 3) + column - 3;
    }
    public int migrateLegacyDisplaySlot(int slot) {
        int old = Math.clamp(slot, 0, 8);
        return old / 3 * columns + old % 3;
    }
    /** Preserve positions along the old source-to-chute path while adding columns at its right. */
    public float migrateLegacyX(float x) { return 1 - (1 - x) * 2 / (columns - 1); }
    public float slotX(int slot) { return 1 - (slot % columns) / (float) (columns - 1); }
    public float slotZ(int slot) { return 1 - (slot / columns) / (float) (rows() - 1); }
    public int selectedSlot(float x, float z) {
        return (rows() - 1 - Math.round(Math.clamp(z, 0, 1) * (rows() - 1))) * columns
            + columns - 1 - Math.round(Math.clamp(x, 0, 1) * (columns - 1));
    }
    public BlockPos partPosition(BlockPos anchor, Direction facing, int part) {
        return anchor.relative(facing.getClockWise(), part % width)
            .relative(facing.getOpposite(), (part / width) % depth()).above(part / floorPartCount());
    }
    public BlockPos anchor(BlockPos pos, Direction facing, int part) {
        return pos.relative(facing.getClockWise(), -(part % width))
            .relative(facing.getOpposite(), -((part / width) % depth())).below(part / floorPartCount());
    }
    public int mirroredPart(int part) { return part - part % width + width - 1 - part % width; }

    public float modelX(float x) { return minX + (maxX - minX) * x; }
    public float modelY(float y) { return homeY - (homeY - prizeY) * y; }
    public float modelZ(float z) { return (this == COMPACT ? 9 : 8) + 16 * z; }
    public float prizeY() { return prizeY; }
    public float prizeSize() { return 4.6F; }
    public float prizeDepth() { return 3.4F; }
    public float bedY() { return bedY; }
    public float padY() { return bedY + .18F; }
    public float railY() { return railY; }
    public float cableTopY() { return railY - .4F; }
    public float clawScale() { return clawScale; }
    public float railMinX() { return this == LARGE ? 3 : 2; }
    public float railMaxX() { return width * 16 - railMinX(); }
    public float chuteX() { return maxX; }
    public float chuteY() { return chuteY; }
    public float chuteZ() { return -4; }
    public float chuteAimX() { return 1; }
    public float chuteAimZ() { return this == COMPACT ? -.3375F : -.3125F; }
    public float deliveryProgress() { return (homeY - deliveryY) / (homeY - prizeY); }
    public float priceX() { return priceX; }
    public float priceY() { return priceY; }
    public float priceZ() { return this == COMPACT ? .20F : .06F; }
    public float countX() { return countX; }
    public float countY() { return priceY; }
    public float countZ() { return this == COMPACT ? .20F : .075F; }
}
