package local.japanesearcades.client;

import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.blaze3d.vertex.VertexConsumer;
import com.mojang.blaze3d.systems.RenderSystem;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import local.japanesearcades.JapaneseArcades;
import net.minecraft.client.Minecraft;
import net.minecraft.client.renderer.MultiBufferSource;
import net.minecraft.client.renderer.RenderType;
import net.minecraft.client.renderer.Sheets;
import net.minecraft.client.renderer.block.model.ItemOverrides;
import net.minecraft.client.renderer.block.model.BakedQuad;
import net.minecraft.client.renderer.entity.ItemRenderer;
import net.minecraft.client.renderer.texture.TextureAtlasSprite;
import net.minecraft.client.resources.model.BakedModel;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.Direction;
import net.minecraft.util.RandomSource;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.item.BlockItem;
import net.minecraft.world.item.ItemDisplayContext;
import net.minecraft.world.item.ItemStack;
import net.neoforged.neoforge.client.NeoForgeRenderTypes;
import net.neoforged.neoforge.client.model.BakedModelWrapper;
import org.joml.Matrix4f;
import org.joml.Vector3f;

/** Reuses the detailed arcade prize meshes without rebuilding their quads every frame. */
final class DisplayItemMeshes {
    static final DisplayItemMeshes INSTANCE = new DisplayItemMeshes();
    // Roughly 40 MiB of vertex data and quad references, shared across all display
    // renderers rather than duplicated per machine type. Cleared after every model bake.
    private static final int MAX_VERTICES = 800_000;
    private record ModelKey(BakedModel model, ItemDisplayContext context) {}
    private final Map<ModelKey, Mesh> meshes = new LinkedHashMap<>(16, .75F, true);
    private final java.util.Set<ModelKey> nativeModels = new java.util.HashSet<>();
    private int vertices;

    private DisplayItemMeshes() {}

    void clear() {
        meshes.clear();
        nativeModels.clear();
        vertices = 0;
    }

    boolean render(ItemStack stack, PoseStack pose, MultiBufferSource buffers, int light, int overlay) {
        return render(stack, pose, buffers, light, overlay, true);
    }

    boolean render(ItemStack stack, PoseStack pose, MultiBufferSource buffers, int light, int overlay, boolean cullFromEye) {
        return render(stack, pose, buffers, light, overlay, cullFromEye, ItemDisplayContext.GUI);
    }

    boolean render(ItemStack stack, PoseStack pose, MultiBufferSource buffers, int light, int overlay,
                   boolean cullFromEye, ItemDisplayContext context) {
        // Only our static block items are eligible. Vanilla/modded dynamic models, custom
        // renderers, item overrides and enchanted items retain their normal rendering path.
        if (!(stack.getItem() instanceof BlockItem) || stack.hasFoil()
            || !BuiltInRegistries.ITEM.getKey(stack.getItem()).getNamespace().equals(JapaneseArcades.MOD_ID)) {
            return false;
        }
        ItemRenderer renderer = Minecraft.getInstance().getItemRenderer();
        BakedModel model = renderer.getItemModelShaper().getItemModel(stack);
        ModelKey key = new ModelKey(model, context);
        if (model.isCustomRenderer() || model.getOverrides() != ItemOverrides.EMPTY || nativeModels.contains(key)) { return false; }
        Mesh mesh = meshes.get(key);
        if (mesh == null) {
            Capture capture = new Capture();
            // Capture the requested transform and render passes as ItemRenderer. Light is zero
            // here so baked emission can be combined with the current world light on replay.
            renderer.render(stack, context, false, new PoseStack(), capture, 0, 0, model);
            if (!capture.supported()) { nativeModels.add(key); return false; }
            mesh = capture.finish(model);
            if (mesh.vertices > MAX_VERTICES) { nativeModels.add(key); return false; }
            while (vertices + mesh.vertices > MAX_VERTICES && !meshes.isEmpty()) {
                var oldest = meshes.entrySet().iterator();
                vertices -= oldest.next().getValue().vertices;
                oldest.remove();
            }
            meshes.put(key, mesh);
            vertices += mesh.vertices;
        }
        if (!mesh.markSpritesActive()) { return false; }
        mesh.render(stack, pose, buffers, light, overlay, cullFromEye);
        return true;
    }

    private record Mesh(List<Part> parts, int vertices) {
        boolean markSpritesActive() {
            for (Part part : parts) {
                for (TextureAtlasSprite sprite : part.sprites) {
                    if (!ClawRenderCompatibility.markSpriteActive(sprite)) { return false; }
                }
            }
            return true;
        }
        void render(ItemStack stack, PoseStack poses, MultiBufferSource buffers, int light, int overlay, boolean cullFromEye) {
            PoseStack.Pose pose = poses.last();
            Vector3f position = new Vector3f(), normal = new Vector3f();
            Matrix4f view = new Matrix4f(RenderSystem.getModelViewMatrix()).mul(pose.pose());
            float winding = Math.signum(view.determinant3x3());
            Vector3f eye = view.invert().transformPosition(0, 0, 0, new Vector3f());
            // Shadow maps use a light projection, not the eye. Keep their complete geometry.
            boolean cull = cullFromEye && !ClawRenderCompatibility.isRenderingShadowPass();
            for (Part part : parts) {
                VertexConsumer out = buffers.getBuffer(part.type);
                float[] data = part.data;
                int[] colors = part.colors, emission = part.emission;
                if (ClawRenderCompatibility.supportsBulkWriting(out)) {
                    // Preserve Sodium's bulk quad writer instead of replacing it with a slower
                    // per-vertex Java loop. Iris's extended-format buffers can reject this
                    // fast path, in which case the cached primitive replay below is faster.
                    part.visible.clear();
                    for (int q = 0; q < part.quads.size(); q++) {
                        if (!cull || part.visibleFrom(q, eye, winding)) { part.visible.add(part.quads.get(q)); }
                    }
                    poses.pushPose();
                    poses.mulPose(part.transform);
                    Minecraft.getInstance().getItemRenderer().renderModelLists(part.filteredModel, stack,
                        light, overlay, poses, out);
                    poses.popPose();
                    continue;
                }
                for (int i = 0, vertex = 0; i < data.length; i += 8, vertex++) {
                    if (vertex % 4 == 0 && cull && !part.visibleFrom(vertex / 4, eye, winding)) {
                        i += 24; vertex += 3; continue;
                    }
                    pose.pose().transformPosition(data[i], data[i + 1], data[i + 2], position);
                    // NeoForge transforms explicit baked normals without normalizing them.
                    // Keep that distinction under the prize's nonuniform scale, otherwise
                    // cached models become brighter than the original item rendering.
                    int bakedNormal = part.quads.get(vertex / 4).getVertices()[(vertex % 4) * 8 + 7];
                    if ((bakedNormal & 0x00ffffff) != 0) {
                        pose.normal().transform(data[i + 5], data[i + 6], data[i + 7], normal);
                    } else {
                        pose.transformNormal(data[i + 5], data[i + 6], data[i + 7], normal);
                    }
                    int lit = Math.max(light & 0xffff, emission[vertex] & 0xffff)
                        | Math.max(light >>> 16, emission[vertex] >>> 16) << 16;
                    // Use the supplied consumer, including Sodium/Iris wrappers, rather than
                    // drawing a private VBO outside Minecraft's lighting/transparency pipeline.
                    out.addVertex(position.x, position.y, position.z, colors[vertex], data[i + 3], data[i + 4],
                        overlay, lit, normal.x, normal.y, normal.z);
                }
            }
        }
    }

    private record Part(RenderType type, float[] data, int[] colors, int[] emission,
                        float[] planes, List<BakedQuad> quads, Matrix4f transform,
                        List<BakedQuad> visible, List<TextureAtlasSprite> sprites, BakedModel filteredModel) {
        boolean visibleFrom(int q, Vector3f eye, float winding) {
            if (planes == null) { return true; }
            int p = q * 4;
            return winding * (planes[p] * eye.x + planes[p + 1] * eye.y + planes[p + 2] * eye.z - planes[p + 3]) >= -.00001F;
        }
    }

    /** Retains the native renderModelLists call site that Sodium accelerates. */
    private static final class FilteredModel extends BakedModelWrapper<BakedModel> {
        private final List<BakedQuad> visible;
        FilteredModel(BakedModel original, List<BakedQuad> visible) { super(original); this.visible = visible; }
        @Override public List<BakedQuad> getQuads(BlockState state, Direction side, RandomSource random) {
            return side == null ? visible : List.of();
        }
    }

    private static final class Capture implements MultiBufferSource {
        private final Map<RenderType, Collector> parts = new LinkedHashMap<>();
        @Override public VertexConsumer getBuffer(RenderType type) {
            return parts.computeIfAbsent(type, ignored -> new Collector());
        }
        boolean supported() {
            return !parts.isEmpty() && parts.values().stream().allMatch(c -> c.supported
                && c.transform != null && c.size == c.quads.size() * 4);
        }
        Mesh finish(BakedModel original) {
            List<Part> result = new ArrayList<>();
            int count = 0;
            for (var entry : parts.entrySet()) {
                Collector c = entry.getValue();
                RenderType type = entry.getKey();
                // These exact native passes all enable back-face culling. Never cull a
                // double-sided or unknown pass; preserve the same visible surface set.
                boolean culled = type == NeoForgeRenderTypes.ITEM_LAYERED_SOLID.get()
                    || type == NeoForgeRenderTypes.ITEM_LAYERED_CUTOUT.get()
                    || type == NeoForgeRenderTypes.ITEM_LAYERED_CUTOUT_MIPPED.get()
                    || type == NeoForgeRenderTypes.ITEM_LAYERED_TRANSLUCENT.get()
                    || type == Sheets.cutoutBlockSheet();
                float[] planes = culled ? new float[c.size] : null;
                if (planes != null) {
                    Vector3f edge = new Vector3f(), normal = new Vector3f();
                    for (int q = 0; q < c.size / 4; q++) {
                        int i = q * 32, p = q * 4;
                        edge.set(c.data[i + 8] - c.data[i], c.data[i + 9] - c.data[i + 1], c.data[i + 10] - c.data[i + 2]);
                        normal.set(c.data[i + 16] - c.data[i], c.data[i + 17] - c.data[i + 1], c.data[i + 18] - c.data[i + 2]);
                        edge.cross(normal, normal);
                        if (normal.lengthSquared() < 1e-16F) { continue; }
                        normal.normalize();
                        float distance = normal.x * c.data[i] + normal.y * c.data[i + 1] + normal.z * c.data[i + 2];
                        float fourth = normal.x * c.data[i + 24] + normal.y * c.data[i + 25] + normal.z * c.data[i + 26];
                        if (Math.abs(fourth - distance) > .00001F) { continue; }
                        planes[p] = normal.x; planes[p + 1] = normal.y; planes[p + 2] = normal.z; planes[p + 3] = distance;
                    }
                }
                List<BakedQuad> visible = new ArrayList<>(c.quads.size());
                result.add(new Part(type, Arrays.copyOf(c.data, c.size * 8),
                    Arrays.copyOf(c.colors, c.size), Arrays.copyOf(c.emission, c.size), planes,
                    List.copyOf(c.quads), c.transform, visible, List.copyOf(c.sprites), new FilteredModel(original, visible)));
                count += c.size;
            }
            return new Mesh(List.copyOf(result), count);
        }
    }

    private static final class Collector implements VertexConsumer {
        private final List<BakedQuad> quads = new ArrayList<>();
        private final java.util.Set<TextureAtlasSprite> sprites = new java.util.HashSet<>();
        private Matrix4f transform;
        private boolean supported = true;
        private float[] data = new float[8192];
        private int[] colors = new int[1024], emission = new int[1024];
        private int size;
        @Override public void putBulkData(PoseStack.Pose pose, BakedQuad quad, float r, float g, float b,
                                          float a, int light, int overlay, boolean readColor) {
            quads.add(quad);
            sprites.add(quad.getSprite());
            if (transform == null) { transform = new Matrix4f(pose.pose()); }
            // Resource packs may replace a static model with tinted/component-dependent
            // geometry or custom per-quad transforms. Leave those to the native renderer.
            if (quad.isTinted() || !transform.equals(pose.pose())) { supported = false; }
            VertexConsumer.super.putBulkData(pose, quad, r, g, b, a, light, overlay, readColor);
        }
        @Override public VertexConsumer addVertex(float x, float y, float z) {
            if (size == colors.length) {
                colors = Arrays.copyOf(colors, colors.length * 2);
                emission = Arrays.copyOf(emission, emission.length * 2);
                data = Arrays.copyOf(data, data.length * 2);
            }
            int offset = size++ * 8;
            data[offset] = x; data[offset + 1] = y; data[offset + 2] = z;
            return this;
        }
        @Override public VertexConsumer setColor(int r, int g, int b, int a) {
            colors[size - 1] = a << 24 | r << 16 | g << 8 | b;
            return this;
        }
        @Override public VertexConsumer setUv(float u, float v) {
            int offset = (size - 1) * 8;
            data[offset + 3] = u; data[offset + 4] = v;
            return this;
        }
        @Override public VertexConsumer setUv1(int u, int v) { return this; }
        @Override public VertexConsumer setUv2(int u, int v) {
            emission[size - 1] = u | v << 16;
            return this;
        }
        @Override public VertexConsumer setNormal(float x, float y, float z) {
            int offset = (size - 1) * 8;
            data[offset + 5] = x; data[offset + 6] = y; data[offset + 7] = z;
            return this;
        }
    }
}
