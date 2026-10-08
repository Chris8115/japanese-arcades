package local.japanesearcades.client;

import com.mojang.blaze3d.systems.RenderSystem;
import com.mojang.blaze3d.vertex.ByteBufferBuilder;
import com.mojang.blaze3d.vertex.DefaultVertexFormat;
import com.mojang.blaze3d.vertex.MeshData;
import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.blaze3d.vertex.VertexBuffer;
import com.mojang.blaze3d.vertex.VertexConsumer;
import com.mojang.blaze3d.vertex.VertexFormat;
import com.mojang.blaze3d.vertex.VertexSorting;
import java.lang.reflect.Field;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Map;
import java.util.SequencedMap;
import java.util.Set;
import local.japanesearcades.CustomDisplayBoxData;
import local.japanesearcades.JapaneseArcades;
import net.minecraft.client.Minecraft;
import net.minecraft.client.renderer.LightTexture;
import net.minecraft.client.renderer.MultiBufferSource;
import net.minecraft.client.renderer.RenderType;
import net.minecraft.client.renderer.block.model.ItemOverrides;
import net.minecraft.client.renderer.texture.MissingTextureAtlasSprite;
import net.minecraft.client.renderer.texture.OverlayTexture;
import net.minecraft.client.renderer.texture.TextureAtlasSprite;
import net.minecraft.client.resources.model.BakedModel;
import net.minecraft.core.Direction;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.util.RandomSource;
import net.minecraft.world.item.BlockItem;
import net.minecraft.world.item.ItemStack;
import net.neoforged.api.distmarker.Dist;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.client.event.ClientPlayerNetworkEvent;
import net.neoforged.neoforge.client.event.RegisterRenderBuffersEvent;
import net.neoforged.neoforge.client.event.RenderFrameEvent;
import net.neoforged.neoforge.client.model.data.ModelData;
import org.joml.Matrix3f;
import org.joml.Matrix4f;

/** Retains complete GUI geometry on the GPU without flattening or reducing the model. */
final class CustomDisplayBoxGuiCache {
    private static final int MAX_ENTRIES = 64;
    private static final long MAX_BYTES = 32L * 1024 * 1024;
    private static final int MAX_RUNS = 128;
    private static final Map<Key, Entry> ENTRIES = new LinkedHashMap<>(16, .75F, true);
    private static final Map<Key, Boolean> NATIVE = new LinkedHashMap<>(16, .75F, true);
    // The event's live map also includes buffers appended by listeners which run after us.
    private static SequencedMap<RenderType, ByteBufferBuilder> fixedBuffers;
    private static long uploadedBytes;
    private static boolean builtThisFrame;
    private static boolean warned;
    private static ByteBufferBuilder replayAllocator;
    private static MultiBufferSource.BufferSource replayBuffers;

    private record Key(CustomDisplayBoxData data, Matrix4f linear, Matrix3f normal, boolean shaderTransparency) {}
    private static final class Part {
        private final RenderType type;
        private final VertexBuffer buffer;
        private final ReplayType replay;
        Part(RenderType type, VertexBuffer buffer) {
            this.type = type;
            this.buffer = buffer;
            this.replay = new ReplayType(type, buffer);
        }
    }

    private CustomDisplayBoxGuiCache() {}

    /** No public accessor exists for this map in the pinned NeoForge version. */
    @SuppressWarnings("unchecked")
    static void registerBuffers(RegisterRenderBuffersEvent event) {
        try {
            Field field = RegisterRenderBuffersEvent.class.getDeclaredField("renderBuffers");
            field.setAccessible(true);
            fixedBuffers = (SequencedMap<RenderType, ByteBufferBuilder>) field.get(event);
        } catch (ReflectiveOperationException | RuntimeException unavailable) {
            fixedBuffers = null;
        }
    }

    static void clear() {
        if (!RenderSystem.isOnRenderThread()) {
            RenderSystem.recordRenderCall(CustomDisplayBoxGuiCache::clear);
            return;
        }
        for (Entry entry : ENTRIES.values()) { entry.close(); }
        ENTRIES.clear();
        NATIVE.clear();
        uploadedBytes = 0;
        builtThisFrame = false;
        warned = false;
        if (replayAllocator != null) { replayAllocator.close(); }
        replayAllocator = null;
        replayBuffers = null;
    }

    static boolean render(ItemStack stack, CustomDisplayBoxData data, PoseStack poses,
                          MultiBufferSource buffers, int light, int overlay) {
        Minecraft mc = Minecraft.getInstance();
        // Other renderers can also request GUI transforms for world displays. Only the
        // actual GUI projection and Minecraft's ordinary GUI buffers are supported here.
        if (fixedBuffers == null || stack.hasFoil()
            || light != LightTexture.FULL_BRIGHT || overlay != OverlayTexture.NO_OVERLAY
            || buffers != mc.renderBuffers().bufferSource()
            || buffers.getClass() != MultiBufferSource.BufferSource.class
            || ClawRenderCompatibility.isRenderingShadowPass()
            || RenderSystem.getVertexSorting() != VertexSorting.ORTHOGRAPHIC_Z
            || !poses.last().pose().isFinite() || !poses.last().normal().isFinite()
            || poses.last().pose().m03() != 0 || poses.last().pose().m13() != 0
            || poses.last().pose().m23() != 0 || poses.last().pose().m33() != 1) {
            return false;
        }
        Matrix4f linear = new Matrix4f(poses.last().pose()).setTranslation(0, 0, 0);
        Key key = new Key(data, linear, new Matrix3f(poses.last().normal()), Minecraft.useShaderTransparency());
        Entry entry = ENTRIES.get(key);
        if (entry == null) {
            if (builtThisFrame || NATIVE.containsKey(key)) { return false; }
            builtThisFrame = true;
            try {
                Set<TextureAtlasSprite> sprites = eligibleSprites(data);
                if (sprites == null) { rememberNative(key); return false; }
                PoseStack.Pose caller = poses.last();
                try (Capture capture = new Capture()) {
                    poses.pushPose();
                    poses.last().pose().setTranslation(0, 0, 0);
                    try {
                        CustomDisplayBoxRenderer.draw(data, poses, capture, light, overlay, false);
                    } finally {
                        // A rejected capture can interrupt a nested item or font draw.
                        // Restore the original pose even when it still has pushed children.
                        while (poses.last() != caller) { poses.popPose(); }
                    }
                    entry = capture.finish(sprites);
                }
                ENTRIES.put(key, entry);
                uploadedBytes += entry.bytes;
            } catch (UnsupportedCapture unsupported) {
                rememberNative(key);
                return false;
            } catch (RuntimeException | LinkageError failure) {
                rememberNative(key);
                warn(failure);
                return false;
            }
        }
        if (!entry.markSpritesActive()) { return false; }
        try {
            // Preserve the screen's draw order before switching to our retained buffers.
            mc.renderBuffers().bufferSource().endBatch();
            entry.render(poses.last().pose());
            return true;
        } catch (RuntimeException | LinkageError failure) {
            ENTRIES.remove(key);
            uploadedBytes -= entry.bytes;
            entry.close();
            rememberNative(key);
            warn(failure);
            return false;
        }
    }

    private static void rememberNative(Key key) {
        NATIVE.put(key, Boolean.TRUE);
        while (NATIVE.size() > MAX_ENTRIES) { NATIVE.remove(NATIVE.keySet().iterator().next()); }
    }

    private static void makeRoom(long bytes) {
        while (!ENTRIES.isEmpty() && (ENTRIES.size() >= MAX_ENTRIES || uploadedBytes + bytes > MAX_BYTES)) {
            var oldest = ENTRIES.entrySet().iterator();
            Entry evicted = oldest.next().getValue();
            oldest.remove();
            uploadedBytes -= evicted.bytes;
            evicted.close();
        }
    }

    private static void warn(Throwable failure) {
        if (!warned) {
            warned = true;
            JapaneseArcades.LOGGER.warn("Display box GUI cache unavailable; using the normal item renderer", failure);
        }
    }

    private static Set<TextureAtlasSprite> eligibleSprites(CustomDisplayBoxData data) {
        Set<TextureAtlasSprite> sprites = new LinkedHashSet<>();
        ItemStack retained = data.retainedItem();
        if (!retained.isEmpty() && !collectItemSprites(retained, sprites)) { return null; }
        ItemStack contained = data.containedItem();
        if (!contained.isEmpty() && !ItemStack.isSameItemSameComponents(contained, retained)
            && !collectItemSprites(contained, sprites)) { return null; }
        var mc = Minecraft.getInstance();
        var shell = mc.getModelManager().getModel(CustomDisplayBoxRenderer.SHELL);
        if (shell.isCustomRenderer() || shell.getOverrides() != ItemOverrides.EMPTY) { return null; }
        var state = JapaneseArcades.CUSTOM_DISPLAY_BOX.get().defaultBlockState();
        RandomSource random = RandomSource.create(42);
        for (RenderType layer : shell.getRenderTypes(state, random, ModelData.EMPTY)) {
            for (int side = -1; side < 6; side++) {
                random.setSeed(42);
                for (var quad : shell.getQuads(state, side < 0 ? null : Direction.values()[side], random, ModelData.EMPTY, layer)) {
                    sprites.add(quad.getSprite());
                }
            }
        }
        for (TextureAtlasSprite sprite : sprites) {
            if (sprite.contents().name().equals(MissingTextureAtlasSprite.getLocation())
                || !ClawRenderCompatibility.markSpriteActive(sprite)) { return null; }
        }
        return Set.copyOf(sprites);
    }

    private static boolean collectItemSprites(ItemStack stack, Set<TextureAtlasSprite> sprites) {
        if (!(stack.getItem() instanceof BlockItem) || stack.hasFoil()
            || !BuiltInRegistries.ITEM.getKey(stack.getItem()).getNamespace().equals(JapaneseArcades.MOD_ID)) {
            return false;
        }
        BakedModel model = CabinetInventoryModels.full(Minecraft.getInstance().getItemRenderer()
            .getItemModelShaper().getItemModel(stack));
        if (model.isCustomRenderer() || model.getOverrides() != ItemOverrides.EMPTY) { return false; }
        RandomSource random = RandomSource.create(42);
        for (BakedModel pass : model.getRenderPasses(stack, true)) {
            if (pass.isCustomRenderer() || pass.getOverrides() != ItemOverrides.EMPTY) { return false; }
            for (int side = -1; side < 6; side++) {
                random.setSeed(42);
                for (var quad : pass.getQuads(null, side < 0 ? null : Direction.values()[side], random)) {
                    if (quad.isTinted()) { return false; }
                    sprites.add(quad.getSprite());
                }
            }
        }
        return true;
    }

    private static final class Entry implements AutoCloseable {
        private final List<Part> parts;
        private final Set<TextureAtlasSprite> sprites;
        private final long bytes;
        Entry(List<Part> parts, Set<TextureAtlasSprite> sprites, long bytes) {
            this.parts = parts;
            this.sprites = sprites;
            this.bytes = bytes;
        }
        boolean markSpritesActive() {
            for (TextureAtlasSprite sprite : sprites) {
                if (!ClawRenderCompatibility.markSpriteActive(sprite)) { return false; }
            }
            return true;
        }
        void render(Matrix4f caller) {
            if (replayBuffers == null) {
                replayAllocator = new ByteBufferBuilder(256);
                replayBuffers = MultiBufferSource.immediate(replayAllocator);
            }
            for (Part part : parts) {
                part.replay.x = caller.m30();
                part.replay.y = caller.m31();
                part.replay.z = caller.m32();
                part.replay.failure = null;
                VertexConsumer trigger = replayBuffers.getBuffer(part.replay);
                // The bridge consumes this tiny trigger mesh without drawing it. Going
                // through native endBatch retains rendering-mod GUI shader scopes.
                for (int i = 0; i < 4; i++) { trigger.addVertex(0, 0, 0); }
                replayBuffers.endBatch();
                if (part.replay.failure != null) { throw new IllegalStateException("GUI mesh replay failed", part.replay.failure); }
            }
        }
        @Override public void close() { for (Part part : parts) { part.buffer.close(); } }
    }

    /** Uses native GUI flush scopes, including Iris's non-extended GUI shader path. */
    private static final class ReplayType extends RenderType {
        private final RenderType original;
        private final VertexBuffer retained;
        private float x, y, z;
        private Throwable failure;
        ReplayType(RenderType original, VertexBuffer retained) {
            super("japanesearcades_gui_replay", DefaultVertexFormat.POSITION, VertexFormat.Mode.QUADS,
                256, false, false, () -> {}, () -> {});
            this.original = original;
            this.retained = retained;
        }
        @Override public void draw(MeshData trigger) {
            try {
                trigger.close(); // The trigger vertices are never uploaded or rendered.
                try {
                    original.setupRenderState();
                    try {
                        // Normals already contain the caller's GUI transform. Entity shaders
                        // transform positions, but not normals, with ModelViewMat.
                        Matrix4f view = new Matrix4f(RenderSystem.getModelViewMatrix()).translate(x, y, z);
                        var shader = RenderSystem.getShader();
                        if (shader == null) { throw new UnsupportedCapture(); }
                        retained.bind();
                        retained.drawWithShader(view, RenderSystem.getProjectionMatrix(), shader);
                    } finally {
                        original.clearRenderState();
                    }
                } finally {
                    VertexBuffer.unbind();
                }
            } catch (RuntimeException | LinkageError unavailable) {
                // Let native endBatch leave its rendering-mod scope before falling back.
                failure = unavailable;
            }
        }
    }

    /** Native BufferSource supplies exact shared/fixed ordering and GUI vertex formats. */
    private static final class Capture implements MultiBufferSource, AutoCloseable {
        private final Map<RenderType, CaptureType> types = new HashMap<>();
        private final SequencedMap<RenderType, ByteBufferBuilder> localFixed = new LinkedHashMap<>();
        private final Map<RenderType, ByteBufferBuilder> fixedAllocators = new HashMap<>();
        private final ByteBufferBuilder shared = new ByteBufferBuilder(4096);
        private final MultiBufferSource.BufferSource source = MultiBufferSource.immediateWithBuffers(localFixed, shared);
        private final List<Part> parts = new ArrayList<>();
        private long maximumBytes;
        private long bytes;
        private boolean unsupported;
        private boolean transferred;
        private Throwable failure;

        @Override public VertexConsumer getBuffer(RenderType type) {
            if (unsupported || type.mode() != VertexFormat.Mode.QUADS
                || !(type.format().equals(DefaultVertexFormat.NEW_ENTITY)
                    || type.format().equals(DefaultVertexFormat.POSITION_COLOR_TEX_LIGHTMAP))) {
                throw new UnsupportedCapture();
            }
            CaptureType bridge = types.get(type);
            if (bridge == null) {
                if (types.size() >= MAX_RUNS) { throw new UnsupportedCapture(); }
                bridge = new CaptureType(type);
                types.put(type, bridge);
                if (fixedBuffers.containsKey(type)) {
                    fixedAllocators.put(type, new ByteBufferBuilder(4096));
                    // Only allocate buffers actually used by this box, keeping their
                    // final registered order even if they were requested out of order.
                    localFixed.clear();
                    for (RenderType fixedType : fixedBuffers.keySet()) {
                        ByteBufferBuilder allocator = fixedAllocators.get(fixedType);
                        if (allocator != null) { localFixed.put(types.get(fixedType), allocator); }
                    }
                }
            }
            return new Counted(source.getBuffer(bridge), type.format().getVertexSize());
        }
        Entry finish(Set<TextureAtlasSprite> sprites) {
            source.endBatch();
            if (failure != null) { throw new IllegalStateException("GUI mesh capture failed", failure); }
            if (unsupported || parts.isEmpty()) { throw new UnsupportedCapture(); }
            Entry entry = new Entry(List.copyOf(parts), sprites, bytes);
            transferred = true;
            return entry;
        }
        @Override public void close() {
            if (!transferred) { for (Part part : parts) { part.buffer.close(); } }
            for (ByteBufferBuilder allocator : fixedAllocators.values()) { allocator.close(); }
            shared.close();
        }
        private final class CaptureType extends RenderType {
            private final RenderType original;
            CaptureType(RenderType original) {
                super("japanesearcades_gui_capture", original.format(), original.mode(), 4096,
                    original.affectsCrumbling(), original.sortOnUpload(), () -> {}, () -> {});
                this.original = original;
            }
            @Override public void draw(MeshData mesh) {
                // BufferSource already applied its GUI vertex-format scope and quad sort.
                // Unknown extended formats retain the original renderer instead.
                var state = mesh.drawState();
                long size = mesh.vertexBuffer().remaining() + (long) state.indexCount() * state.indexType().bytes;
                if (unsupported || !state.format().equals(original.format()) || parts.size() >= MAX_RUNS || bytes + size > MAX_BYTES) {
                    mesh.close();
                    unsupported = true;
                    return;
                }
                try {
                    // Upload inside native endBatch as well as drawing there: Iris also
                    // uses this GUI scope when configuring the VAO's vertex attributes.
                    // Include all in-progress parts when reserving the retained budget.
                    makeRoom(bytes + size);
                    VertexBuffer buffer = new VertexBuffer(VertexBuffer.Usage.STATIC);
                    parts.add(new Part(original, buffer));
                    buffer.bind();
                    buffer.upload(mesh); // upload consumes and closes both buffer results.
                    bytes += size;
                } catch (RuntimeException | LinkageError unavailable) {
                    mesh.close();
                    unsupported = true;
                    failure = unavailable;
                } finally {
                    VertexBuffer.unbind();
                }
            }
        }
        private final class Counted implements VertexConsumer {
            private final VertexConsumer delegate;
            private final int vertexSize;
            Counted(VertexConsumer delegate, int vertexSize) { this.delegate = delegate; this.vertexSize = vertexSize; }
            @Override public VertexConsumer addVertex(float x, float y, float z) {
                // Six bytes per vertex covers six 32-bit indices per quad.
                maximumBytes += vertexSize + 6L;
                if (maximumBytes > MAX_BYTES) { throw new UnsupportedCapture(); }
                delegate.addVertex(x, y, z);
                return this;
            }
            @Override public VertexConsumer setColor(int r, int g, int b, int a) { delegate.setColor(r, g, b, a); return this; }
            @Override public VertexConsumer setUv(float u, float v) { delegate.setUv(u, v); return this; }
            @Override public VertexConsumer setUv1(int u, int v) { delegate.setUv1(u, v); return this; }
            @Override public VertexConsumer setUv2(int u, int v) { delegate.setUv2(u, v); return this; }
            @Override public VertexConsumer setNormal(float x, float y, float z) { delegate.setNormal(x, y, z); return this; }
        }
    }

    private static final class UnsupportedCapture extends RuntimeException {
        UnsupportedCapture() { super(null, null, false, false); }
    }

    @EventBusSubscriber(modid = JapaneseArcades.MOD_ID, value = Dist.CLIENT)
    public static final class Events {
        private Events() {}
        @SubscribeEvent public static void frame(RenderFrameEvent.Pre event) { builtThisFrame = false; }
        @SubscribeEvent public static void logout(ClientPlayerNetworkEvent.LoggingOut event) { clear(); }
    }
}
