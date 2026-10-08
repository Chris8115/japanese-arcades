package local.japanesearcades.client;

import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.blaze3d.vertex.VertexConsumer;
import com.mojang.math.Axis;
import local.japanesearcades.ArcadePosterEntity;
import local.japanesearcades.WaccaPosterEntity;
import net.minecraft.client.Minecraft;
import net.minecraft.client.renderer.MultiBufferSource;
import net.minecraft.client.renderer.RenderType;
import net.minecraft.client.renderer.entity.EntityRenderer;
import net.minecraft.client.renderer.entity.EntityRendererProvider;
import net.minecraft.client.renderer.texture.OverlayTexture;
import net.minecraft.client.renderer.texture.TextureAtlasSprite;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.entity.decoration.Painting;

/** A thin framed print using the painting atlas, with no overlapping front faces. */
public final class WaccaPosterRenderer extends EntityRenderer<Painting> {
    private static final float HALF_WIDTH = (float) ArcadePosterEntity.WIDTH / 2F;
    private static final float HALF_HEIGHT = (float) ArcadePosterEntity.HEIGHT / 2F;
    private static final float HALF_DEPTH = .03125F;
    private static final float ART_SCALE = .91F;
    private static final int BLACK = 0xFF000000;
    private static final int WHITE = 0xFFFFFFFF;

    public WaccaPosterRenderer(EntityRendererProvider.Context context) {
        super(context);
    }

    @Override
    public ResourceLocation getTextureLocation(Painting poster) {
        return Minecraft.getInstance().getPaintingTextures().getBackSprite().atlasLocation();
    }

    @Override
    public void render(Painting poster, float yaw, float partialTick, PoseStack poses,
                       MultiBufferSource buffers, int packedLight) {
        var textures = Minecraft.getInstance().getPaintingTextures();
        TextureAtlasSprite art = textures.get(poster.getVariant().value());
        TextureAtlasSprite back = textures.getBackSprite();
        VertexConsumer consumer = buffers.getBuffer(RenderType.entitySolid(back.atlasLocation()));
        poses.pushPose();
        try {
            poses.mulPose(Axis.YP.rotationDegrees(180F - yaw));
            PoseStack.Pose pose = poses.last();
            float x = HALF_WIDTH, y = HALF_HEIGHT, z = HALF_DEPTH;
            float backU = back.getU0(), backV = back.getV0();

            // Back and four outside edges form the original 1/16-block-deep hanging board.
            blackQuad(pose, consumer, backU, backV, packedLight, 0, 0, 1,
                x, y, z, -x, y, z, -x, -y, z, x, -y, z);
            blackQuad(pose, consumer, backU, backV, packedLight, 0, 1, 0,
                x, y, -z, -x, y, -z, -x, y, z, x, y, z);
            blackQuad(pose, consumer, backU, backV, packedLight, 0, -1, 0,
                x, -y, z, -x, -y, z, -x, -y, -z, x, -y, -z);
            blackQuad(pose, consumer, backU, backV, packedLight, 1, 0, 0,
                x, y, z, x, -y, z, x, -y, -z, x, y, -z);
            blackQuad(pose, consumer, backU, backV, packedLight, -1, 0, 0,
                -x, y, -z, -x, -y, -z, -x, -y, z, -x, y, z);

            // WACCA's original supplied image already includes its visible front frame.
            boolean legacy = poster instanceof WaccaPosterEntity;
            float artX = legacy ? x : x * ART_SCALE;
            float artY = legacy ? y : y * ART_SCALE;
            if (!legacy) {
                // These four strips meet the art at their edges; no face sits behind the print.
                frontQuad(pose, consumer, back, BLACK, packedLight, -x, x, artY, y);
                frontQuad(pose, consumer, back, BLACK, packedLight, -x, x, -y, -artY);
                frontQuad(pose, consumer, back, BLACK, packedLight, -x, -artX, -artY, artY);
                frontQuad(pose, consumer, back, BLACK, packedLight, artX, x, -artY, artY);
            }
            frontQuad(pose, consumer, art, WHITE, packedLight, -artX, artX, -artY, artY);
        } finally {
            poses.popPose();
        }
        super.render(poster, yaw, partialTick, poses, buffers, packedLight);
    }

    private static void frontQuad(PoseStack.Pose pose, VertexConsumer consumer, TextureAtlasSprite sprite,
                                  int color, int light, float left, float right, float bottom, float top) {
        vertex(pose, consumer, right, bottom, -HALF_DEPTH, sprite.getU0(), sprite.getV1(), color, light, 0, 0, -1);
        vertex(pose, consumer, left, bottom, -HALF_DEPTH, sprite.getU1(), sprite.getV1(), color, light, 0, 0, -1);
        vertex(pose, consumer, left, top, -HALF_DEPTH, sprite.getU1(), sprite.getV0(), color, light, 0, 0, -1);
        vertex(pose, consumer, right, top, -HALF_DEPTH, sprite.getU0(), sprite.getV0(), color, light, 0, 0, -1);
    }

    private static void blackQuad(PoseStack.Pose pose, VertexConsumer consumer, float u, float v, int light,
                                  float nx, float ny, float nz,
                                  float ax, float ay, float az, float bx, float by, float bz,
                                  float cx, float cy, float cz, float dx, float dy, float dz) {
        vertex(pose, consumer, ax, ay, az, u, v, BLACK, light, nx, ny, nz);
        vertex(pose, consumer, bx, by, bz, u, v, BLACK, light, nx, ny, nz);
        vertex(pose, consumer, cx, cy, cz, u, v, BLACK, light, nx, ny, nz);
        vertex(pose, consumer, dx, dy, dz, u, v, BLACK, light, nx, ny, nz);
    }

    private static void vertex(PoseStack.Pose pose, VertexConsumer consumer, float x, float y, float z,
                               float u, float v, int color, int light, float nx, float ny, float nz) {
        consumer.addVertex(pose, x, y, z).setColor(color).setUv(u, v)
            .setOverlay(OverlayTexture.NO_OVERLAY).setLight(light).setNormal(pose, nx, ny, nz);
    }
}
