package local.japanesearcades.client;

import java.util.Map;
import java.util.WeakHashMap;
import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.blaze3d.vertex.VertexConsumer;
import com.mojang.math.Axis;
import local.japanesearcades.ClawMachineBlock;
import local.japanesearcades.ClawMachineBlockEntity;
import local.japanesearcades.ClawMachineLayout;
import local.japanesearcades.JapaneseArcades;
import net.minecraft.client.gui.Font;
import net.minecraft.client.renderer.MultiBufferSource;
import net.minecraft.client.renderer.RenderType;
import net.minecraft.client.renderer.blockentity.BlockEntityRenderer;
import net.minecraft.client.renderer.blockentity.BlockEntityRendererProvider;
import net.minecraft.core.Direction;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.item.ItemDisplayContext;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;
import org.joml.Quaternionf;
import org.joml.Vector3f;

/** Live stock, independent falling prizes and a three-finger gantry driven by server poses. */
public final class ClawMachineRenderer implements BlockEntityRenderer<ClawMachineBlockEntity> {
    private static final ResourceLocation METAL = ResourceLocation.fromNamespaceAndPath(
        JapaneseArcades.MOD_ID, "textures/entity/claw_machine.png");
    private static final int SILVER = 0xBCCDD6, DARK = 0x263B4B, CYAN = 0x59ECF4;
    private static final int PINK = 0xEEA1CC, RUBBER = 0x26313A;
    private final Font font;
    private final DisplayItemMeshes prizeMeshes = DisplayItemMeshes.INSTANCE;
    private final Map<ClawMachineBlockEntity, Sample> samples = new WeakHashMap<>();

    public ClawMachineRenderer(BlockEntityRendererProvider.Context context) { font = context.getFont(); }

    @Override
    public void render(ClawMachineBlockEntity machine, float partialTick, PoseStack pose,
                       MultiBufferSource buffers, int light, int overlay) {
        Direction facing = machine.getBlockState().getValue(ClawMachineBlock.FACING);
        pose.pushPose();
        pose.translate(.5, 0, .5);
        pose.mulPose(Axis.YP.rotationDegrees(switch (facing) {
            case EAST -> -90; case SOUTH -> 180; case WEST -> 90; default -> 0;
        }));
        pose.translate(-.5, 0, -.5);
        pose.scale(1F / 16, 1F / 16, 1F / 16);

        ClawMachineLayout layout = machine.layout();
        for (int slot = 0; slot < layout.rewardCount(); slot++) {
            ItemStack reward = machine.rewardDisplayReference(slot);
            if (!reward.isEmpty()) {
                float x = layout.modelX(layout.slotX(slot));
                float z = layout.modelZ(layout.slotZ(slot));
                prize(reward, x, layout.padY() + .02F, z,
                    layout, machine, pose, buffers, light, overlay, slot);
            }
        }

        float[] state = interpolated(machine, partialTick);
        float x = layout.modelX(state[0]), y = layout.modelY(state[1]), z = layout.modelZ(state[2]);
        VertexConsumer metal = buffers.getBuffer(RenderType.entityCutoutNoCull(METAL));
        if (machine.getPhase() == ClawMachineBlockEntity.Phase.AIMING) {
            // Match the server's nearest-cell drop selection rather than the delayed cosmetic
            // claw interpolation, so the player can see the exact target before pressing Drop.
            int selected = layout.selectedSlot(machine.getClawX(), machine.getClawZ());
            float selectedX = layout.modelX(layout.slotX(selected));
            float selectedZ = layout.modelZ(layout.slotZ(selected));
            float padY = layout.padY() + .02F;
            float halfWidth = layout == ClawMachineLayout.COMPACT ? 2.8F : 3.25F;
            box(pose, metal, selectedX - halfWidth, padY, selectedZ - 3.15F,
                selectedX + halfWidth, padY + .08F, selectedZ - 2.97F, CYAN, 0xF000F0, overlay);
            box(pose, metal, selectedX - halfWidth, padY, selectedZ + 2.97F,
                selectedX + halfWidth, padY + .08F, selectedZ + 3.15F, CYAN, 0xF000F0, overlay);
            box(pose, metal, selectedX - halfWidth, padY, selectedZ - 2.97F,
                selectedX - halfWidth + .18F, padY + .08F, selectedZ + 2.97F, CYAN, 0xF000F0, overlay);
            box(pose, metal, selectedX + halfWidth - .18F, padY, selectedZ - 2.97F,
                selectedX + halfWidth, padY + .08F, selectedZ + 2.97F, CYAN, 0xF000F0, overlay);
        }
        float hardware = layout.clawScale(), railY = layout.railY();
        box(pose, metal, layout.railMinX(), railY, z - .32F * hardware,
            layout.railMaxX(), railY + .45F * hardware, z + .32F * hardware, SILVER, light, overlay);
        box(pose, metal, x - 2 * hardware, railY - 1.2F * hardware, z - 1.25F * hardware,
            x + 2 * hardware, railY + .65F * hardware, z + 1.25F * hardware, DARK, light, overlay);
        box(pose, metal, x - 1.7F * hardware, railY - .95F * hardware, z - 1.35F * hardware,
            x + 1.7F * hardware, railY, z - 1.23F * hardware, CYAN, 0xF000F0, overlay);
        box(pose, metal, x - .10F * hardware, y + 3.45F * hardware, z - .10F * hardware,
            x + .10F * hardware, layout.cableTopY(), z + .10F * hardware, RUBBER, light, overlay);
        pose.pushPose();
        pose.translate(x, y, z);
        pose.scale(hardware, hardware, hardware);
        box(pose, metal, -1.45F, 2, -1.45F, 1.45F, 3.5F, 1.45F, SILVER, light, overlay);
        box(pose, metal, -1.5F, 2.6F, -1.5F, 1.5F, 2.95F, 1.5F, PINK, light, overlay);
        float grip = Math.max(0, Math.min(1, state[3]));
        for (int finger = 0; finger < 3; finger++) {
            double angle = Math.toRadians(90 + 120 * finger);
            float dx = (float) Math.cos(angle), dz = (float) Math.sin(angle);
            float elbow = 3.1F - 1.1F * grip, tip = 2.9F - 2.15F * grip;
            rod(pose, metal, dx * .95F, 2.1F, dz * .95F,
                dx * elbow, .45F, dz * elbow, .19F, SILVER, light, overlay);
            rod(pose, metal, dx * elbow, .45F, dz * elbow,
                dx * tip, -1.3F, dz * tip, .19F, SILVER, light, overlay);
            rod(pose, metal, dx * tip, -1.3F, dz * tip,
                dx * (tip - .45F), -1.45F, dz * (tip - .45F), .25F, RUBBER, light, overlay);
        }
        pose.popPose();

        ItemStack held = machine.heldDisplayReference();
        if (!held.isEmpty()) {
            // The full reserved stack travels together. Slipping uses a separate server pose,
            // leaving the released claw overhead while the prize falls to its new stock cell.
            prize(held, layout.modelX(state[4]), layout.padY() + .02F + layout.modelY(state[5]) - layout.prizeY(),
                layout.modelZ(state[6]), layout, machine, pose, buffers, light, overlay, 19);
        }
        ItemStack price = machine.priceDisplayReference();
        if (!price.isEmpty()) {
            icon(price, layout.priceX(), layout.priceY(), layout.priceZ(), 1.75F, .15F,
                machine, pose, buffers, light, overlay, 23);
        }
        // Keep labels together: switching to the font between each stocked item flushes
        // Minecraft's shared item buffer, uploading/drawing every cabinet separately.
        for (int slot = 0; slot < layout.rewardCount(); slot++) {
            prizeCount(machine.rewardDisplayReference(slot), layout.modelX(layout.slotX(slot)), layout.prizeY(),
                layout.modelZ(layout.slotZ(slot)), pose, buffers, light);
        }
        prizeCount(held, layout.modelX(state[4]), layout.modelY(state[5]), layout.modelZ(state[6]), pose, buffers, light);
        if (!price.isEmpty()) {
            text(Component.literal(price.getCount() + " X"), layout.countX(), layout.countY(), layout.countZ(),
                .16F, 0x173849, pose, buffers, 0xF000F0);
        }
        pose.popPose();
    }

    private float[] interpolated(ClawMachineBlockEntity machine, float partialTick) {
        float[] target = { machine.getClawX(), machine.getClawY(), machine.getClawZ(), machine.getGrip(),
            machine.getHeldX(), machine.getHeldY(), machine.getHeldZ() };
        double now = (machine.getLevel() == null ? 0 : machine.getLevel().getGameTime()) + partialTick;
        Sample sample = samples.get(machine);
        if (sample == null) {
            sample = new Sample(target.clone(), target, now);
            samples.put(machine, sample);
        } else if (!java.util.Arrays.equals(target, sample.to)) {
            sample = new Sample(sample.at(now), target, now);
            samples.put(machine, sample);
        }
        return sample.at(now);
    }

    private record Sample(float[] from, float[] to, double receivedAt) {
        float[] at(double now) {
            float t = (float) Math.max(0, Math.min(1, (now - receivedAt) / 2));
            float[] result = new float[to.length];
            for (int i = 0; i < result.length; i++) { result[i] = from[i] + (to[i] - from[i]) * t; }
            return result;
        }
    }

    private void prizeCount(ItemStack stack, float x, float y, float z,
                            PoseStack pose, MultiBufferSource buffers, int light) {
        if (stack.getCount() > 1) {
            text(Component.literal("x" + stack.getCount()), x, y - 1.8F, z - 2.4F,
                .12F, 0x173849, pose, buffers, light);
        }
    }

    private void prize(ItemStack stack, float x, float floor, float z, ClawMachineLayout layout,
                       ClawMachineBlockEntity machine, PoseStack pose, MultiBufferSource buffers,
                       int light, int overlay, int seed) {
        DisplayItemMeshes.Bounds bounds = prizeMeshes.bounds(stack, ItemDisplayContext.GUI);
        if (bounds == null || !Float.isFinite(bounds.minX()) || !Float.isFinite(bounds.maxX())
            || !Float.isFinite(bounds.minY()) || !Float.isFinite(bounds.maxY())
            || !Float.isFinite(bounds.minZ()) || !Float.isFinite(bounds.maxZ())) {
            // Dynamic, enchanted and third-party models retain native rendering. Their
            // custom renderer may draw beyond ordinary baked bounds, so do not cache a fit.
            icon(stack, x, floor + layout.prizeY() - layout.padY() - .02F, z,
                layout.prizeSize(), layout.prizeDepth(), machine, pose, buffers, light, overlay, seed);
            return;
        }
        float scale = Math.min(layout.prizeSize() / Math.max(.001F, bounds.maxX() - bounds.minX()),
            Math.min(layout.prizeSize() / Math.max(.001F, bounds.maxY() - bounds.minY()),
                layout.prizeDepth() / Math.max(.001F, bounds.maxZ() - bounds.minZ())));
        pose.pushPose();
        pose.translate(x, floor, z);
        pose.mulPose(Axis.YP.rotationDegrees(180));
        pose.scale(scale, scale, scale);
        pose.translate(-(bounds.minX() + bounds.maxX()) / 2, -bounds.minY(),
            -(bounds.minZ() + bounds.maxZ()) / 2);
        if (!prizeMeshes.render(stack, pose, buffers, light, overlay)) {
            CabinetInventoryModels.renderFull(stack, ItemDisplayContext.GUI,
                light, overlay, pose, buffers, machine.getLevel(), seed);
        }
        pose.popPose();
    }

    private void icon(ItemStack stack, float x, float y, float z, float size, float depth,
                      ClawMachineBlockEntity machine, PoseStack pose, MultiBufferSource buffers,
                      int light, int overlay, int seed) {
        pose.pushPose();
        pose.translate(x, y, z);
        pose.mulPose(Axis.YP.rotationDegrees(180));
        pose.scale(size, size, depth);
        if (!prizeMeshes.render(stack, pose, buffers, light, overlay)) {
            CabinetInventoryModels.renderFull(stack, ItemDisplayContext.GUI,
                light, overlay, pose, buffers, machine.getLevel(), seed);
        }
        pose.popPose();
    }

    private void text(Component value, float x, float y, float z, float scale, int color,
                      PoseStack pose, MultiBufferSource buffers, int light) {
        pose.pushPose();
        pose.translate(x, y, z);
        pose.mulPose(Axis.YP.rotationDegrees(180));
        pose.scale(scale, -scale, scale);
        font.drawInBatch(value, -font.width(value) / 2F, -font.lineHeight / 2F, color,
            false, pose.last().pose(), buffers, Font.DisplayMode.NORMAL, 0, light);
        pose.popPose();
    }

    private static void rod(PoseStack pose, VertexConsumer vertices, float x0, float y0, float z0,
                            float x1, float y1, float z1, float radius, int color, int light, int overlay) {
        Vector3f direction = new Vector3f(x1 - x0, y1 - y0, z1 - z0);
        float length = direction.length();
        if (length < .001F) { return; }
        pose.pushPose();
        pose.translate(x0, y0, z0);
        pose.mulPose(new Quaternionf().rotationTo(new Vector3f(0, 1, 0), direction.normalize()));
        box(pose, vertices, -radius, 0, -radius, radius, length, radius, color, light, overlay);
        pose.popPose();
    }

    private static void box(PoseStack pose, VertexConsumer out, float x0, float y0, float z0,
                            float x1, float y1, float z1, int color, int light, int overlay) {
        // The gantry draws 15+ boxes per frame. Emit the same vertices directly;
        // rebuilding 23 coordinate/index/normal arrays per box creates avoidable GC.
        face(pose, out, color, light, overlay, 0,0,-1, x0,y1,z0, x1,y1,z0, x1,y0,z0, x0,y0,z0);
        face(pose, out, color, light, overlay, 0,0,1, x1,y1,z1, x0,y1,z1, x0,y0,z1, x1,y0,z1);
        face(pose, out, color, light, overlay, 1,0,0, x1,y1,z0, x1,y1,z1, x1,y0,z1, x1,y0,z0);
        face(pose, out, color, light, overlay, -1,0,0, x0,y1,z1, x0,y1,z0, x0,y0,z0, x0,y0,z1);
        face(pose, out, color, light, overlay, 0,1,0, x0,y1,z1, x1,y1,z1, x1,y1,z0, x0,y1,z0);
        face(pose, out, color, light, overlay, 0,-1,0, x0,y0,z0, x1,y0,z0, x1,y0,z1, x0,y0,z1);
    }

    private static void face(PoseStack pose, VertexConsumer out, int color, int light, int overlay,
                             float nx, float ny, float nz,
                             float ax, float ay, float az, float bx, float by, float bz,
                             float cx, float cy, float cz, float dx, float dy, float dz) {
        int red = color >> 16 & 255, green = color >> 8 & 255, blue = color & 255;
        out.addVertex(pose.last(), ax, ay, az).setColor(red, green, blue, 255).setUv(0, 0)
            .setOverlay(overlay).setLight(light).setNormal(pose.last(), nx, ny, nz);
        out.addVertex(pose.last(), bx, by, bz).setColor(red, green, blue, 255).setUv(1, 0)
            .setOverlay(overlay).setLight(light).setNormal(pose.last(), nx, ny, nz);
        out.addVertex(pose.last(), cx, cy, cz).setColor(red, green, blue, 255).setUv(1, 1)
            .setOverlay(overlay).setLight(light).setNormal(pose.last(), nx, ny, nz);
        out.addVertex(pose.last(), dx, dy, dz).setColor(red, green, blue, 255).setUv(0, 1)
            .setOverlay(overlay).setLight(light).setNormal(pose.last(), nx, ny, nz);
    }

    @Override
    public AABB getRenderBoundingBox(ClawMachineBlockEntity machine) {
        Direction facing = machine.getBlockState().getValue(ClawMachineBlock.FACING);
        ClawMachineLayout layout = machine.layout();
        Vec3 a = ClawMachineBlock.localToWorld(machine.getBlockPos(), facing, 0, 0, -2);
        Vec3 b = ClawMachineBlock.localToWorld(machine.getBlockPos(), facing,
            layout.modelWidth(), layout.modelHeight(), layout.modelDepth());
        return new AABB(a, b).inflate(.125);
    }

    @Override public int getViewDistance() { return 96; }
}
