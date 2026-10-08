package probe;

import com.mojang.blaze3d.pipeline.TextureTarget;
import com.mojang.blaze3d.platform.Lighting;
import com.mojang.blaze3d.platform.NativeImage;
import com.mojang.blaze3d.systems.RenderSystem;
import com.mojang.blaze3d.vertex.ByteBufferBuilder;
import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.blaze3d.vertex.VertexSorting;
import java.nio.file.Files;
import java.nio.file.Path;

import net.minecraft.client.Minecraft;
import net.minecraft.client.renderer.LightTexture;
import net.minecraft.client.renderer.MultiBufferSource;
import net.minecraft.client.renderer.texture.OverlayTexture;
import net.minecraft.world.item.ItemDisplayContext;
import net.minecraft.core.Direction;
import net.minecraft.util.RandomSource;
import net.neoforged.neoforge.client.ClientHooks;
import org.joml.Vector4f;
import net.minecraft.world.item.ItemStack;
import org.joml.Matrix4f;

/** Offline native asset capture only. Invoke once outside benchmark samples. */
public final class InventoryIconBake {
    private InventoryIconBake() {}

    public static void capture(ItemStack stack, Path destination) throws Exception {
        RenderSystem.assertOnRenderThread();
        final int size = 256;
        var mc = Minecraft.getInstance();

        var model = mc.getItemRenderer().getModel(stack, mc.level, mc.player, 0);
        try {
            var unwrap = Class.forName("local.japanesearcades.client.CabinetInventoryModels").getMethod("full", net.minecraft.client.resources.model.BakedModel.class);
            model = (net.minecraft.client.resources.model.BakedModel) unwrap.invoke(null, model);
        } catch (ClassNotFoundException absent) { /* Baseline build predates snapshot wrappers. */ }
        // Measure actual baked vertices after the existing native GUI transform.
        // Preserve its viewing angle and original framing without auto-fit.
        var measuredPose = new PoseStack();
        var measuredModel = ClientHooks.handleCameraTransforms(measuredPose, model, ItemDisplayContext.GUI, false);
        measuredPose.translate(-.5F,-.5F,-.5F);
        float minModelX=Float.POSITIVE_INFINITY,minModelY=Float.POSITIVE_INFINITY;
        float maxModelX=Float.NEGATIVE_INFINITY,maxModelY=Float.NEGATIVE_INFINITY;
        var random=RandomSource.create(42);
        int capturedQuads=0;
        for(var pass:measuredModel.getRenderPasses(stack,true)) for(int side=-1;side<6;side++) {
            random.setSeed(42);
            for(var quad:pass.getQuads(null,side<0?null:Direction.values()[side],random)) {
                capturedQuads++;
                int[] vertices=quad.getVertices();int stride=vertices.length/4;
                for(int i=0;i<4;i++) {
                    var v=new Vector4f(Float.intBitsToFloat(vertices[i*stride]),Float.intBitsToFloat(vertices[i*stride+1]),Float.intBitsToFloat(vertices[i*stride+2]),1);
                    measuredPose.last().pose().transform(v);
                    minModelX=Math.min(minModelX,v.x);maxModelX=Math.max(maxModelX,v.x);
                    minModelY=Math.min(minModelY,v.y);maxModelY=Math.max(maxModelY,v.y);
                }
            }
        }
        if(capturedQuads<100) throw new IllegalStateException("Icon bake must use the original full cabinet model, got "+capturedQuads+" quads");
        float fit=size/1.5F;
        System.out.println("INVENTORY ICON FRAME quads="+capturedQuads+" bounds="+minModelX+","+minModelY+".."+maxModelX+","+maxModelY+" scale="+fit);
        var oldProjection = new Matrix4f(RenderSystem.getProjectionMatrix());
        var oldSorting = RenderSystem.getVertexSorting();
        var oldColor = RenderSystem.getShaderColor().clone();
        var modelView = RenderSystem.getModelViewStack();
        var target = new TextureTarget(size, size, true, Minecraft.ON_OSX);
        mc.renderBuffers().bufferSource().endBatch();
        modelView.pushMatrix();
        try (var allocator = new ByteBufferBuilder(262144)) {
            target.setClearColor(0, 0, 0, 0);
            target.clear(Minecraft.ON_OSX);
            target.bindWrite(true);
            RenderSystem.setProjectionMatrix(new Matrix4f().setOrtho(0, size, size, 0, 1000, 21000), VertexSorting.ORTHOGRAPHIC_Z);
            modelView.identity().translate(0, 0, -11000);
            RenderSystem.applyModelViewMatrix();
            RenderSystem.setShaderColor(1, 1, 1, 1);
            RenderSystem.enableDepthTest();
            RenderSystem.depthMask(true);
            RenderSystem.disableScissor();
            RenderSystem.defaultBlendFunc();
            Lighting.setupFor3DItems();
            if (!model.usesBlockLight()) Lighting.setupForFlatItems();
            var pose = new PoseStack();
            // Native GUI viewing angle and lighting, exact native framing in a fixed 24-GUI-pixel canvas, scaled back by a 1.5-unit GUI quad.
            pose.translate(size / 2F, size / 2F, 150);
            pose.scale(fit, -fit, fit);
            var buffer = MultiBufferSource.immediate(allocator);
            mc.getItemRenderer().render(stack, ItemDisplayContext.GUI, false, pose, buffer,
                LightTexture.FULL_BRIGHT, OverlayTexture.NO_OVERLAY, model);
            buffer.endBatch();
            RenderSystem.bindTexture(target.getColorTextureId());
            try (var image = new NativeImage(size, size, false)) {
                // Screenshot.takeScreenshot uses removeAlpha=true; preserve real transparency.
                image.downloadTexture(0, false);
                image.flipY();
                int minX=size, minY=size, maxX=-1, maxY=-1, opaque=0, transparent=0;
                for (int y=0;y<size;y++) for (int x=0;x<size;x++) {
                    int alpha=image.getPixelRGBA(x,y)>>>24;
                    if(alpha==0) transparent++;
                    else { opaque++;minX=Math.min(minX,x);maxX=Math.max(maxX,x);minY=Math.min(minY,y);maxY=Math.max(maxY,y); }
                }
                if(opaque<128 || transparent<128) throw new IllegalStateException("Invalid icon alpha: filled="+opaque+", clear="+transparent);
                if(minX==0||minY==0||maxX==size-1||maxY==size-1) throw new IllegalStateException("GUI capture clips: "+destination+" "+minX+","+minY+".."+maxX+","+maxY);
                Files.createDirectories(destination.toAbsolutePath().getParent());
                image.writeToFile(destination);
                System.out.println("INVENTORY ICON BAKE " + destination.toAbsolutePath() + " 256x256 RGBA; occupied="+opaque+", clear="+transparent+", bounds="+minX+","+minY+".."+maxX+","+maxY);
            }
        } finally {
            target.unbindWrite();
            modelView.popMatrix();
            RenderSystem.applyModelViewMatrix();
            RenderSystem.setProjectionMatrix(oldProjection, oldSorting);
            RenderSystem.setShaderColor(oldColor[0], oldColor[1], oldColor[2], oldColor[3]);
            Lighting.setupFor3DItems();
            mc.getMainRenderTarget().bindWrite(true);
            target.destroyBuffers();
        }
    }
}
