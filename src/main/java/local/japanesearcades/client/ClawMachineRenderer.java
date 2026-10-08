package local.japanesearcades.client;

import java.util.Map;
import java.util.WeakHashMap;
import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.blaze3d.vertex.VertexConsumer;
import com.mojang.math.Axis;
import local.japanesearcades.ClawMachineBlock;
import local.japanesearcades.ClawMachineBlockEntity;
import local.japanesearcades.JapaneseArcades;
import net.minecraft.client.Minecraft;
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

        ItemStack[] stock = new ItemStack[9];
        for (int slot = 0; slot < 9; slot++) {
            ItemStack reward = machine.getRewardDisplay(slot);
            stock[slot] = reward;
            if (!reward.isEmpty()) {
                float x = modelX(ClawMachineBlockEntity.slotX(slot));
                float z = modelZ(ClawMachineBlockEntity.slotZ(slot));
                icon(reward, x, 20.5F, z, 4.6F, 3.4F, machine, pose, buffers, light, overlay, slot);
            }
        }

        float[] state = interpolated(machine, partialTick);
        float x = modelX(state[0]), y = modelY(state[1]), z = modelZ(state[2]);
        VertexConsumer metal = buffers.getBuffer(RenderType.entityCutoutNoCull(METAL));
        if (machine.getPhase() == ClawMachineBlockEntity.Phase.AIMING) {
            // Match the server's nearest-cell drop selection rather than the delayed cosmetic
            // claw interpolation, so the player can see the exact target before pressing Drop.
            float selectedX = modelX(Math.max(0, Math.min(2, Math.round(machine.getClawX() * 2))) * .5F);
            float selectedZ = modelZ(Math.max(0, Math.min(2, Math.round(machine.getClawZ() * 2))) * .5F);
            box(pose, metal, selectedX - 3.25F, 18.2F, selectedZ - 3.15F,
                selectedX + 3.25F, 18.28F, selectedZ - 2.97F, CYAN, 0xF000F0, overlay);
            box(pose, metal, selectedX - 3.25F, 18.2F, selectedZ + 2.97F,
                selectedX + 3.25F, 18.28F, selectedZ + 3.15F, CYAN, 0xF000F0, overlay);
            box(pose, metal, selectedX - 3.25F, 18.2F, selectedZ - 2.97F,
                selectedX - 3.07F, 18.28F, selectedZ + 2.97F, CYAN, 0xF000F0, overlay);
            box(pose, metal, selectedX + 3.07F, 18.2F, selectedZ - 2.97F,
                selectedX + 3.25F, 18.28F, selectedZ + 2.97F, CYAN, 0xF000F0, overlay);
        }
        box(pose, metal, 3, 41.8F, z - .32F, 45, 42.25F, z + .32F, SILVER, light, overlay);
        box(pose, metal, x - 2, 40.6F, z - 1.25F, x + 2, 42.65F, z + 1.25F, DARK, light, overlay);
        box(pose, metal, x - 1.7F, 40.85F, z - 1.35F, x + 1.7F, 41.8F, z - 1.23F, CYAN, 0xF000F0, overlay);
        box(pose, metal, x - .10F, y + 3.45F, z - .10F, x + .10F, 41.4F, z + .10F, RUBBER, light, overlay);
        box(pose, metal, x - 1.45F, y + 2, z - 1.45F, x + 1.45F, y + 3.5F, z + 1.45F, SILVER, light, overlay);
        box(pose, metal, x - 1.5F, y + 2.6F, z - 1.5F, x + 1.5F, y + 2.95F, z + 1.5F, PINK, light, overlay);
        float grip = Math.max(0, Math.min(1, state[3]));
        for (int finger = 0; finger < 3; finger++) {
            double angle = Math.toRadians(90 + 120 * finger);
            float dx = (float) Math.cos(angle), dz = (float) Math.sin(angle);
            float elbow = 3.1F - 1.1F * grip, tip = 2.9F - 2.15F * grip;
            rod(pose, metal, x + dx * .95F, y + 2.1F, z + dz * .95F,
                x + dx * elbow, y + .45F, z + dz * elbow, .19F, SILVER, light, overlay);
            rod(pose, metal, x + dx * elbow, y + .45F, z + dz * elbow,
                x + dx * tip, y - 1.3F, z + dz * tip, .19F, SILVER, light, overlay);
            rod(pose, metal, x + dx * tip, y - 1.3F, z + dz * tip,
                x + dx * (tip - .45F), y - 1.45F, z + dz * (tip - .45F), .25F, RUBBER, light, overlay);
        }

        ItemStack held = machine.getHeldDisplay();
        if (!held.isEmpty()) {
            // The full reserved stack travels together. Slipping uses a separate server pose,
            // leaving the released claw overhead while the prize falls to its new stock cell.
            icon(held, modelX(state[4]), modelY(state[5]), modelZ(state[6]),
                4.6F, 3.4F, machine, pose, buffers, light, overlay, 19);
        }
        ItemStack price = machine.getPrice();
        if (!price.isEmpty()) {
            icon(price, 19.2F, 16.1F, .06F, 1.75F, .15F, machine, pose, buffers, light, overlay, 23);
        }
        // Keep labels together: switching to the font between each stocked item flushes
        // Minecraft's shared item buffer, uploading/drawing every cabinet separately.
        for (int slot = 0; slot < stock.length; slot++) {
            prizeCount(stock[slot], modelX(ClawMachineBlockEntity.slotX(slot)), 20.5F,
                modelZ(ClawMachineBlockEntity.slotZ(slot)), pose, buffers, light);
        }
        prizeCount(held, modelX(state[4]), modelY(state[5]), modelZ(state[6]), pose, buffers, light);
        if (!price.isEmpty()) {
            text(Component.literal(price.getCount() + " X"), 26, 16.1F, .075F,
                .16F, 0x173849, pose, buffers, 0xF000F0);
        }
        pose.popPose();
    }

    private static float modelX(float x) { return 8 + 32 * x; }
    private static float modelY(float y) { return 36.5F - 16 * y; }
    private static float modelZ(float z) { return 8 + 16 * z; }

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
        float[][] v = {{x0,y0,z0},{x1,y0,z0},{x1,y1,z0},{x0,y1,z0},
            {x0,y0,z1},{x1,y0,z1},{x1,y1,z1},{x0,y1,z1}};
        int[][] sides = {{3,2,1,0},{6,7,4,5},{2,6,5,1},{7,3,0,4},{7,6,2,3},{0,1,5,4}};
        float[][] normals = {{0,0,-1},{0,0,1},{1,0,0},{-1,0,0},{0,1,0},{0,-1,0}};
        int red = color >> 16 & 255, green = color >> 8 & 255, blue = color & 255;
        for (int side = 0; side < 6; side++) {
            for (int corner = 0; corner < 4; corner++) {
                float[] point = v[sides[side][corner]], normal = normals[side];
                out.addVertex(pose.last(), point[0], point[1], point[2]).setColor(red, green, blue, 255)
                    .setUv(corner == 0 || corner == 3 ? 0 : 1, corner < 2 ? 0 : 1)
                    .setOverlay(overlay).setLight(light).setNormal(pose.last(), normal[0], normal[1], normal[2]);
            }
        }
    }

    @Override
    public AABB getRenderBoundingBox(ClawMachineBlockEntity machine) {
        Direction facing = machine.getBlockState().getValue(ClawMachineBlock.FACING);
        Vec3 a = ClawMachineBlock.localToWorld(machine.getBlockPos(), facing, 0, 0, -2);
        Vec3 b = ClawMachineBlock.localToWorld(machine.getBlockPos(), facing, 48, 48, 32);
        return new AABB(a, b).inflate(.125);
    }

    @Override public int getViewDistance() { return 96; }
}
