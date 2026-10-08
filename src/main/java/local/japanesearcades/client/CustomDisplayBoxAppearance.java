package local.japanesearcades.client;

import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.blaze3d.vertex.VertexConsumer;
import java.util.LinkedHashMap;
import java.util.Map;
import java.util.PriorityQueue;
import java.util.Comparator;
import net.minecraft.client.Minecraft;
import net.minecraft.client.renderer.block.model.BakedQuad;
import net.minecraft.client.renderer.texture.TextureAtlasSprite;
import net.minecraft.core.component.DataComponents;
import net.minecraft.util.Mth;
import net.minecraft.world.item.ItemDisplayContext;
import net.minecraft.world.item.ItemStack;
import org.joml.Vector3f;

/** Bounded, resource-reload-aware analysis of the item's pixels and display bounds. */
final class CustomDisplayBoxAppearance {
    private static final int LIMIT = 256;
    private static final Map<Key, Appearance> CACHE = new LinkedHashMap<>(16, .75F, true);
    private static final Appearance EMPTY = new Appearance(0x73C8CC, 1, 0, 0, 0);
    record Appearance(int color, float scale, float x, float y, float z) {}
    private record Key(ItemStack stack, boolean straightOn) {
        @Override public int hashCode() { return 31 * ItemStack.hashItemAndComponents(stack) + Boolean.hashCode(straightOn); }
        @Override public boolean equals(Object other) {
            return other instanceof Key key && straightOn == key.straightOn && ItemStack.isSameItemSameComponents(stack, key.stack);
        }
    }
    static void clear() { CACHE.clear(); }
    static Appearance of(ItemStack stack) {
        return of(stack, false);
    }
    static Appearance of(ItemStack stack, boolean straightOn) {
        if (stack.isEmpty()) { return EMPTY; }
        Appearance found = CACHE.get(new Key(stack, straightOn));
        if (found != null) { return found; }
        Minecraft mc = Minecraft.getInstance();
        var renderer = mc.getItemRenderer();
        var model = CabinetInventoryModels.full(renderer.getModel(stack, mc.level, mc.player, 0));
        Capture capture = new Capture();
        // Custom renderers can change GL state or recurse. Their particle sprite provides a
        // stable fallback color; the ordinary native renderer still displays the actual item.
        if (!model.isCustomRenderer()) {
            ItemStack analyzed = stack.copy();
            // The fake analysis buffer is shared across layers. Do not combine it with
            // itself through a glint VertexMultiConsumer; glint is not packaging color.
            analyzed.set(DataComponents.ENCHANTMENT_GLINT_OVERRIDE, false);
            renderer.render(analyzed, straightOn ? ItemDisplayContext.NONE : ItemDisplayContext.GUI,
                false, new PoseStack(), ignored -> capture, 0, 0, model);
        }
        if (capture.surfaces.isEmpty()) { capture.sample(model.getParticleIcon(), 0, 1, 0, 1, 1, 1, 1, 1); }
        found = capture.finish();
        // Orientation changes the fit, never the packaging's identity or color.
        if (straightOn) { found = new Appearance(of(stack).color(), found.scale(), found.x(), found.y(), found.z()); }
        if (CACHE.size() >= LIMIT) { CACHE.remove(CACHE.keySet().iterator().next()); }
        CACHE.put(new Key(stack.copyWithCount(1), straightOn), found);
        return found;
    }

    private static final class Capture implements VertexConsumer {
        private final double[] weights = new double[4096], red = new double[4096], green = new double[4096], blue = new double[4096];
        private float minX = Float.POSITIVE_INFINITY, minY = minX, minZ = minX;
        private float maxX = Float.NEGATIVE_INFINITY, maxY = maxX, maxZ = maxX;
        private record Surface(TextureAtlasSprite sprite, float u0, float u1, float v0, float v1,
                               float r, float g, float b, float area) {}
        private final PriorityQueue<Surface> surfaces = new PriorityQueue<>(Comparator.comparingDouble(Surface::area));
        private final Vector3f p0 = new Vector3f(), p1 = new Vector3f(), p2 = new Vector3f();
        @Override public void putBulkData(PoseStack.Pose pose, BakedQuad quad, float r, float g, float b,
                                         float a, int light, int overlay, boolean readColor) {
            int[] vertices = quad.getVertices();
            position(vertices, 0, pose, p0); position(vertices, 1, pose, p1); position(vertices, 2, pose, p2);
            p1.sub(p0); p2.sub(p0); p1.cross(p2);
            // Weight the visible GUI surface area, not the number of tiny extruded edge
            // quads. Keep the largest surfaces across the complete model, regardless of order.
            float area = Math.abs(p1.z) + p1.length() * .05F;
            if (area > .000001F && (surfaces.size() < 192 || area > surfaces.peek().area)) {
                TextureAtlasSprite sprite = quad.getSprite();
                float u0 = 1, v0 = 1, u1 = 0, v1 = 0;
                float vr = 0, vg = 0, vb = 0, va = 0;
                for (int n = 0; n < 4; n++) {
                    float u = (Float.intBitsToFloat(vertices[n * 8 + 4]) - sprite.getU0()) / (sprite.getU1() - sprite.getU0());
                    float v = (Float.intBitsToFloat(vertices[n * 8 + 5]) - sprite.getV0()) / (sprite.getV1() - sprite.getV0());
                    u0 = Math.min(u0, u); u1 = Math.max(u1, u); v0 = Math.min(v0, v); v1 = Math.max(v1, v);
                    int baked = vertices[n * 8 + 3];
                    vr += (baked & 255) / 1020F; vg += (baked >> 8 & 255) / 1020F;
                    vb += (baked >> 16 & 255) / 1020F; va += (baked >>> 24) / 1020F;
                }
                if (!readColor || va * a >= .5F) {
                    if (surfaces.size() == 192) { surfaces.poll(); }
                    surfaces.add(new Surface(sprite, u0, u1, v0, v1, r * (readColor ? vr : 1),
                        g * (readColor ? vg : 1), b * (readColor ? vb : 1), area));
                }
            }
            VertexConsumer.super.putBulkData(pose, quad, r, g, b, a, light, overlay, readColor);
        }
        private static void position(int[] vertices, int index, PoseStack.Pose pose, Vector3f out) {
            int n = index * 8;
            pose.pose().transformPosition(Float.intBitsToFloat(vertices[n]), Float.intBitsToFloat(vertices[n + 1]),
                Float.intBitsToFloat(vertices[n + 2]), out);
        }
        void sample(TextureAtlasSprite sprite, float u0, float u1, float v0, float v1, float tr, float tg, float tb, float area) {
            int width = sprite.contents().width(), height = sprite.contents().height();
            for (int y = 0; y < 12; y++) { for (int x = 0; x < 12; x++) {
                int px = Mth.clamp((int)((u0 + (u1 - u0) * (x + .5F) / 12) * width), 0, width - 1);
                int py = Mth.clamp((int)((v0 + (v1 - v0) * (y + .5F) / 12) * height), 0, height - 1);
                int abgr = sprite.getPixelRGBA(0, px, py);
                if ((abgr >>> 24) < 128) { continue; }
                int r = Mth.clamp((int)((abgr & 255) * tr), 0, 255);
                int g = Mth.clamp((int)((abgr >> 8 & 255) * tg), 0, 255);
                int b = Mth.clamp((int)((abgr >> 16 & 255) * tb), 0, 255);
                int max = Math.max(r, Math.max(g, b)), min = Math.min(r, Math.min(g, b));
                // Downweight neutral outlines/highlights so a diamond's cyan, for example,
                // wins over its black edging. Neutral-only items still receive neutral boxes.
                double brightness = max / 255.0;
                double weight = (max < 35 ? .04 : (max - min < 20 ? .18 : 1.0))
                    * Math.max(.03, brightness * brightness) * area;
                int bin = (r >> 4) << 8 | (g >> 4) << 4 | b >> 4;
                weights[bin] += weight; red[bin] += r * weight; green[bin] += g * weight; blue[bin] += b * weight;
            } }
        }
        Appearance finish() {
            for (Surface surface : surfaces) {
                sample(surface.sprite, surface.u0, surface.u1, surface.v0, surface.v1, surface.r, surface.g, surface.b, surface.area);
            }
            int winner = -1;
            for (int n = 0; n < weights.length; n++) { if (weights[n] > 0 && (winner < 0 || weights[n] > weights[winner])) { winner = n; } }
            int color = EMPTY.color;
            if (winner >= 0) {
                int r = (int)(red[winner] / weights[winner]), g = (int)(green[winner] / weights[winner]), b = (int)(blue[winner] / weights[winner]);
                // Lift only very dark colors enough for the printed accent to stay legible.
                int max = Math.max(r, Math.max(g, b));
                if (max < 65) { r += 65 - max; g += 65 - max; b += 65 - max; }
                color = r << 16 | g << 8 | b;
            }
            if (!Float.isFinite(minX)) { return new Appearance(color, .42F, 0, 0, 0); }
            float scale = Math.min(.50F / Math.max(.001F, maxX - minX),
                Math.min(.57F / Math.max(.001F, maxY - minY), .38F / Math.max(.001F, maxZ - minZ)));
            return new Appearance(color, Math.min(scale, 3), (minX + maxX) / 2, (minY + maxY) / 2, (minZ + maxZ) / 2);
        }
        @Override public VertexConsumer addVertex(float x, float y, float z) {
            if (Float.isFinite(x) && Float.isFinite(y) && Float.isFinite(z)) {
                minX = Math.min(minX, x); minY = Math.min(minY, y); minZ = Math.min(minZ, z);
                maxX = Math.max(maxX, x); maxY = Math.max(maxY, y); maxZ = Math.max(maxZ, z);
            }
            return this;
        }
        @Override public VertexConsumer setColor(int r, int g, int b, int a) { return this; }
        @Override public VertexConsumer setUv(float u, float v) { return this; }
        @Override public VertexConsumer setUv1(int u, int v) { return this; }
        @Override public VertexConsumer setUv2(int u, int v) { return this; }
        @Override public VertexConsumer setNormal(float x, float y, float z) { return this; }
    }
}
