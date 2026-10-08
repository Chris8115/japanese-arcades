package local.japanesearcades.client;

import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.blaze3d.vertex.VertexConsumer;
import com.mojang.math.Axis;
import java.util.IdentityHashMap;
import java.util.Map;
import local.japanesearcades.FigureShelfBlock;
import local.japanesearcades.FigureShelfBlockEntity;
import net.minecraft.client.Minecraft;
import net.minecraft.client.renderer.MultiBufferSource;
import net.minecraft.client.renderer.blockentity.BlockEntityRenderer;
import net.minecraft.client.renderer.blockentity.BlockEntityRendererProvider;
import net.minecraft.client.resources.model.BakedModel;
import net.minecraft.core.component.DataComponents;
import net.minecraft.world.item.ItemDisplayContext;
import net.minecraft.world.item.ItemStack;

/** Static furniture is chunk-baked. Only the occupied miniature slots are drawn here. */
public final class FigureShelfRenderer implements BlockEntityRenderer<FigureShelfBlockEntity> {
    private static final Map<BakedModel, Fit> FITS = new IdentityHashMap<>();
    private record Fit(float scale, float centerX, float bottom, float centerZ) {}

    public FigureShelfRenderer(BlockEntityRendererProvider.Context context) {}
    static void clear() { FITS.clear(); }
    @Override public int getViewDistance() { return 24; }

    @Override public void render(FigureShelfBlockEntity shelf, float partialTick, PoseStack pose,
                                 MultiBufferSource buffers, int light, int overlay) {
        Minecraft mc = Minecraft.getInstance();
        pose.pushPose();
        pose.translate(.5, 0, .5);
        pose.mulPose(Axis.YP.rotationDegrees(switch (shelf.getBlockState().getValue(FigureShelfBlock.FACING)) {
            case SOUTH -> 180; case EAST -> -90; case WEST -> 90; default -> 0;
        }));
        pose.translate(-.5, 0, -.5);
        for (int slot = 0; slot < shelf.size(); slot++) {
            ItemStack stack = shelf.item(slot);
            if (stack.isEmpty()) continue;
            BakedModel model = CabinetInventoryModels.full(mc.getItemRenderer().getModel(stack, mc.level, null, 0));
            Fit fit = FITS.computeIfAbsent(model, key -> measure(stack, key));
            pose.pushPose();
            // Looking into a north-facing shelf, +X is on the viewer's left.
            double surface = shelf.rows() == 2 ? (1 + (slot / 4) * 8) / 16.0 : 3 / 16.0;
            pose.translate((13.5 - (slot % 4) * (11.0 / 3)) / 16.0, surface + .001,
                shelf.rows() == 2 ? 10.5 / 16.0 : 11.5 / 16.0);
            pose.scale(fit.scale(), fit.scale(), fit.scale());
            pose.translate(-fit.centerX(), -fit.bottom(), -fit.centerZ());
            if (!DisplayItemMeshes.INSTANCE.render(stack, pose, buffers, light, overlay, true, ItemDisplayContext.NONE)) {
                CabinetInventoryModels.renderFull(stack, ItemDisplayContext.NONE, light, overlay, pose, buffers, mc.level, 0);
            }
            pose.popPose();
        }
        pose.popPose();
    }

    private static Fit measure(ItemStack stack, BakedModel model) {
        Bounds bounds = new Bounds();
        if (!model.isCustomRenderer()) {
            ItemStack sample = stack.copyWithCount(1);
            sample.set(DataComponents.ENCHANTMENT_GLINT_OVERRIDE, false);
            Minecraft.getInstance().getItemRenderer().render(sample, ItemDisplayContext.NONE, false,
                new PoseStack(), ignored -> bounds, 0, 0, model);
        }
        if (!Float.isFinite(bounds.minX)) return new Fit(.2F, 0, -.5F, 0);
        // Preserve proportions. Every model, including wings/tails and packaging, fits
        // a 3.15 x 5.7 x 6 model-unit cell without touching its neighbors or the roof.
        float scale = Math.min(.6F, Math.min(3.15F / 16 / Math.max(.001F, bounds.maxX - bounds.minX),
            Math.min(5.7F / 16 / Math.max(.001F, bounds.maxY - bounds.minY),
                6F / 16 / Math.max(.001F, bounds.maxZ - bounds.minZ))));
        return new Fit(scale, (bounds.minX + bounds.maxX) / 2, bounds.minY, (bounds.minZ + bounds.maxZ) / 2);
    }

    /** The native item transform is measured once per baked model, then shared by all shelves. */
    private static final class Bounds implements VertexConsumer {
        private float minX = Float.POSITIVE_INFINITY, minY = minX, minZ = minX;
        private float maxX = Float.NEGATIVE_INFINITY, maxY = maxX, maxZ = maxX;
        @Override public VertexConsumer addVertex(float x, float y, float z) {
            minX = Math.min(minX, x); minY = Math.min(minY, y); minZ = Math.min(minZ, z);
            maxX = Math.max(maxX, x); maxY = Math.max(maxY, y); maxZ = Math.max(maxZ, z);
            return this;
        }
        @Override public VertexConsumer setColor(int r, int g, int b, int a) { return this; }
        @Override public VertexConsumer setUv(float u, float v) { return this; }
        @Override public VertexConsumer setUv1(int u, int v) { return this; }
        @Override public VertexConsumer setUv2(int u, int v) { return this; }
        @Override public VertexConsumer setNormal(float x, float y, float z) { return this; }
    }
}
