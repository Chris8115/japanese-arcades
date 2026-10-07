package local.japanesearcades.client;

import com.mojang.blaze3d.vertex.DefaultVertexFormat;
import com.mojang.blaze3d.vertex.VertexConsumer;
import com.mojang.blaze3d.vertex.VertexFormat;
import java.lang.invoke.MethodHandle;
import java.lang.invoke.MethodHandles;
import java.lang.invoke.MethodType;
import net.minecraft.client.renderer.texture.TextureAtlasSprite;
import net.neoforged.fml.ModList;

/** Optional rendering hooks; neither Iris nor Sodium is a required dependency. */
final class ClawRenderCompatibility {
    private static final boolean IRIS_PRESENT = ModList.get().isLoaded("iris");
    private static final boolean SODIUM_PRESENT = ModList.get().isLoaded("sodium");
    private static volatile MethodHandle shadowPass = resolveShadowPass();
    private static volatile MethodHandle spriteActive = resolveSpriteActive();
    private static volatile MethodHandle bulkWriter = resolveBulkWriter();

    private ClawRenderCompatibility() {}

    static boolean hasSodium() { return SODIUM_PRESENT; }

    /**
     * Matches Sodium's item-renderer fast-path check for this actual consumer and the entity
     * vertex format. Iris can disable intrinsics per consumer even when Sodium is installed.
     * A missing or failing optional hook returns false so callers use primitive replay.
     */
    static boolean supportsBulkWriting(VertexConsumer consumer) {
        MethodHandle hook = bulkWriter;
        if (hook == null || consumer == null) { return false; }
        try {
            return (Object) hook.invokeExact(consumer) != null;
        } catch (Throwable failure) {
            rethrowFatal(failure);
            bulkWriter = null;
            return false;
        }
    }

    /** An unavailable Iris hook conservatively disables camera-facing culling. */
    static boolean isRenderingShadowPass() {
        if (!IRIS_PRESENT) { return false; }
        MethodHandle hook = shadowPass;
        if (hook == null) { return true; }
        try {
            return (boolean) hook.invokeExact();
        } catch (Throwable failure) {
            rethrowFatal(failure);
            shadowPass = null;
            return true;
        }
    }

    /**
     * Marks a sprite used this frame so Sodium keeps its animation running. Returns false
     * when Sodium is present but its hook is unavailable; callers must then render animated
     * items through the native item renderer. Without Sodium, no marking is required.
     */
    static boolean markSpriteActive(TextureAtlasSprite sprite) {
        if (!SODIUM_PRESENT) { return true; }
        MethodHandle hook = spriteActive;
        if (hook == null || sprite == null) { return false; }
        try {
            hook.invokeExact(sprite);
            return true;
        } catch (Throwable failure) {
            rethrowFatal(failure);
            spriteActive = null;
            return false;
        }
    }

    private static MethodHandle resolveShadowPass() {
        if (!IRIS_PRESENT) { return null; }
        try {
            Class<?> api = Class.forName("net.irisshaders.iris.api.v0.IrisApi", true,
                ClawRenderCompatibility.class.getClassLoader());
            Object instance = api.getMethod("getInstance").invoke(null);
            return MethodHandles.publicLookup().unreflect(api.getMethod("isRenderingShadowPass"))
                .bindTo(instance);
        } catch (ReflectiveOperationException | RuntimeException | LinkageError unavailable) {
            return null;
        }
    }

    private static MethodHandle resolveSpriteActive() {
        if (!SODIUM_PRESENT) { return null; }
        try {
            Class<?> api = Class.forName("net.caffeinemc.mods.sodium.api.texture.SpriteUtil", true,
                ClawRenderCompatibility.class.getClassLoader());
            Object instance = api.getField("INSTANCE").get(null);
            return MethodHandles.publicLookup().unreflect(api.getMethod("markSpriteActive", TextureAtlasSprite.class))
                .bindTo(instance);
        } catch (ReflectiveOperationException | RuntimeException | LinkageError unavailable) {
            return null;
        }
    }

    private static MethodHandle resolveBulkWriter() {
        if (!SODIUM_PRESENT) { return null; }
        try {
            Class<?> api = Class.forName("net.caffeinemc.mods.sodium.api.vertex.buffer.VertexBufferWriter", true,
                ClawRenderCompatibility.class.getClassLoader());
            MethodHandle hook = MethodHandles.publicLookup().unreflect(
                api.getMethod("tryOf", VertexConsumer.class, VertexFormat.class));
            // Sodium's EntityVertex.FORMAT is DefaultVertexFormat.NEW_ENTITY. Bind it once,
            // retaining the format-specific canUseIntrinsics check without a logging hook.
            return MethodHandles.insertArguments(hook, 1, DefaultVertexFormat.NEW_ENTITY)
                .asType(MethodType.methodType(Object.class, VertexConsumer.class));
        } catch (ReflectiveOperationException | RuntimeException | LinkageError unavailable) {
            return null;
        }
    }

    private static void rethrowFatal(Throwable failure) {
        if (failure instanceof VirtualMachineError fatal) { throw fatal; }
        if (failure instanceof ThreadDeath death) { throw death; }
    }
}
