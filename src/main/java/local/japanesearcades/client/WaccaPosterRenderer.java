package local.japanesearcades.client;

import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.blaze3d.vertex.VertexConsumer;
import local.japanesearcades.WaccaPosterEntity;
import net.minecraft.client.renderer.MultiBufferSource;
import net.minecraft.client.renderer.RenderType;
import net.minecraft.client.renderer.entity.EntityRendererProvider;
import net.minecraft.client.renderer.entity.PaintingRenderer;
import net.minecraft.world.entity.decoration.Painting;

/** Keeps vanilla painting rendering while fitting the print's fractional block height. */
public final class WaccaPosterRenderer extends PaintingRenderer {
    public WaccaPosterRenderer(EntityRendererProvider.Context context) {
        super(context);
    }

    @Override
    public void render(Painting poster, float yaw, float partialTick, PoseStack poses,
                       MultiBufferSource buffers, int packedLight) {
        poses.pushPose();
        try {
            poses.scale(1.0F, (float)(WaccaPosterEntity.HEIGHT / poster.getVariant().value().height()), 1.0F);
            RenderType paintingLayer = RenderType.entitySolid(getTextureLocation(poster));
            MultiBufferSource posterBuffers = layer -> layer == paintingLayer
                ? new BlackBackingConsumer(buffers.getBuffer(layer)) : buffers.getBuffer(layer);
            super.render(poster, yaw, partialTick, poses, posterBuffers, packedLight);
        } finally {
            poses.popPose();
        }
    }

    /** Vanilla supplies local face normals last; defer color until that face is known. */
    private static final class BlackBackingConsumer implements VertexConsumer {
        private final VertexConsumer delegate;
        private int red = 255, green = 255, blue = 255, alpha = 255;

        private BlackBackingConsumer(VertexConsumer delegate) { this.delegate = delegate; }

        @Override public VertexConsumer addVertex(float x, float y, float z) {
            delegate.addVertex(x, y, z);
            return this;
        }
        @Override public VertexConsumer setColor(int red, int green, int blue, int alpha) {
            this.red = red; this.green = green; this.blue = blue; this.alpha = alpha;
            return this;
        }
        @Override public VertexConsumer setUv(float u, float v) { delegate.setUv(u, v); return this; }
        @Override public VertexConsumer setUv1(int u, int v) { delegate.setUv1(u, v); return this; }
        @Override public VertexConsumer setUv2(int u, int v) { delegate.setUv2(u, v); return this; }

        @Override public VertexConsumer setNormal(PoseStack.Pose pose, float x, float y, float z) {
            // The print faces local -Z. Only this poster's other faces receive black.
            delegate.setColor(z < 0 ? red : 0, z < 0 ? green : 0, z < 0 ? blue : 0, alpha);
            delegate.setNormal(pose, x, y, z);
            return this;
        }
        @Override public VertexConsumer setNormal(float x, float y, float z) {
            delegate.setColor(red, green, blue, alpha);
            delegate.setNormal(x, y, z);
            return this;
        }
    }
}
