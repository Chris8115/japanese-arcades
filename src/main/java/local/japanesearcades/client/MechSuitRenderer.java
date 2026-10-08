package local.japanesearcades.client;

import com.google.gson.JsonArray;
import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.blaze3d.vertex.VertexConsumer;
import com.mojang.math.Axis;
import java.io.IOException;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import local.japanesearcades.JapaneseArcades;
import local.japanesearcades.MechSuitEntity;
import net.minecraft.client.Minecraft;
import net.minecraft.client.renderer.MultiBufferSource;
import net.minecraft.client.renderer.RenderType;
import net.minecraft.client.renderer.culling.Frustum;
import net.minecraft.client.renderer.entity.EntityRenderer;
import net.minecraft.client.renderer.entity.EntityRendererProvider;
import net.minecraft.client.renderer.texture.OverlayTexture;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.util.Mth;

/** Cached articulated armor: one shared material/buffer, no per-frame mesh construction. */
public final class MechSuitRenderer extends EntityRenderer<MechSuitEntity> {
    private static final ResourceLocation TEXTURE = ResourceLocation.fromNamespaceAndPath(
        JapaneseArcades.MOD_ID, "textures/entity/mech_suit.png");
    private static final ResourceLocation GEOMETRY = ResourceLocation.fromNamespaceAndPath(
        JapaneseArcades.MOD_ID, "meshes/mech_suit.json");
    private static final RenderType LAYER = RenderType.entityCutoutNoCull(TEXTURE);
    private final List<Part> roots;

    public MechSuitRenderer(EntityRendererProvider.Context context) {
        super(context);
        shadowRadius = 1.1F;
        // Renderer recreation on resource reload refreshes this cache as well as the texture.
        roots = loadMesh();
    }

    @Override
    public ResourceLocation getTextureLocation(MechSuitEntity suit) { return TEXTURE; }

    @Override
    public boolean shouldRender(MechSuitEntity suit, Frustum camera, double camX, double camY, double camZ) {
        // Blades and wing shields extend beyond the physical walking hull, particularly
        // during flight and sword swings. Retain the usual distance limit but include
        // their complete animated envelope in screen-edge visibility checks.
        return suit.shouldRender(camX, camY, camZ)
            && (suit.noCulling || camera.isVisible(suit.getBoundingBox().inflate(3, 2.5, 3)));
    }

    @Override
    public void render(MechSuitEntity suit, float yaw, float partialTick, PoseStack poses,
                       MultiBufferSource buffers, int light) {
        Minecraft minecraft = Minecraft.getInstance();
        boolean cockpit = minecraft.player != null && minecraft.player.getVehicle() == suit
            && minecraft.options.getCameraType().isFirstPerson();
        poses.pushPose();
        // Vanilla yaw zero looks toward +Z, while the editable armor faces local -Z.
        poses.mulPose(Axis.YP.rotationDegrees(180 - yaw));
        VertexConsumer out = buffers.getBuffer(LAYER);
        float movement = (float)Math.min(1, suit.getDeltaMovement().horizontalDistance() * 5);
        float walk = (suit.tickCount + partialTick) * .40F;
        float flight = suit.isFlying() ? 1 : 0;
        float left = swing(suit.getLeftSwingTicks(), partialTick);
        float right = swing(suit.getRightSwingTicks(), partialTick);
        for (Part root : roots) {
            renderPart(root, poses, out, light, cockpit, walk, movement, flight, left, right);
        }
        poses.popPose();
        super.render(suit, yaw, partialTick, poses, buffers, light);
    }

    private static float swing(int ticks, float partialTick) {
        if (ticks <= 0) { return 0; }
        float progress = Mth.clamp((10 - ticks + partialTick) / 10F, 0, 1);
        return Mth.sin(progress * Mth.PI);
    }

    private static void renderPart(Part part, PoseStack poses, VertexConsumer out, int light,
                                   boolean cockpit, float walk, float movement, float flight,
                                   float left, float right) {
        poses.pushPose();
        if (cockpit && part.name.startsWith("upper_arm_")) {
            // The pilot's eyes are more than a block above the wrists. A local cockpit
            // stance brings both working weapons into the bottom corners of the view.
            poses.translate(0, .35, -.75);
        }
        poses.translate(part.x, part.y, part.z);
        float side = part.name.endsWith("left") ? -1 : 1;
        float slash = side < 0 ? left : right;
        float step = Mth.sin(walk + (side < 0 ? Mth.PI : 0)) * movement * (1 - flight);
        if (part.name.startsWith("upper_arm_")) {
            poses.mulPose(Axis.ZP.rotationDegrees(side * (4 + (cockpit ? 0 : flight * 46) - slash * (cockpit ? 12 : 26))));
            poses.mulPose(Axis.XP.rotationDegrees(cockpit ? 50 - slash * 30 : flight * 24 + step * 8 + slash * 105));
            poses.mulPose(Axis.YP.rotationDegrees(side * slash * (cockpit ? 26 : 48)));
        } else if (part.name.startsWith("forearm_")) {
            poses.mulPose(Axis.XP.rotationDegrees(8 + (cockpit ? slash * 5 : flight * 25 + slash * 32)));
        } else if (part.name.startsWith("sword_")) {
            poses.mulPose(Axis.XP.rotationDegrees(slash * (cockpit ? 20 : 28)));
            poses.mulPose(Axis.ZP.rotationDegrees(-side * slash * (cockpit ? 12 : 25)));
        } else if (part.name.startsWith("thigh_")) {
            poses.mulPose(Axis.XP.rotationDegrees(step * 22 + flight * 25));
            poses.mulPose(Axis.ZP.rotationDegrees(side * 3));
        } else if (part.name.startsWith("shin_")) {
            poses.mulPose(Axis.XP.rotationDegrees(Math.max(0, -step) * 24 - flight * 42));
        } else if (part.name.startsWith("foot_")) {
            poses.mulPose(Axis.XP.rotationDegrees(flight * 14));
        }
        poses.translate(-part.x, -part.y, -part.z);
        // First-person camera lives inside the helmet. The outside shell and lower body
        // must not fill the view, while both working swords and arms remain visible.
        boolean visible = !cockpit || part.name.startsWith("upper_arm_")
            || part.name.startsWith("forearm_") || part.name.startsWith("sword_");
        if (visible) {
            PoseStack.Pose pose = poses.last();
            for (int face = 0, offset = 0; face < part.colors.length; face++, offset += 24) {
                int color = part.colors[face];
                int faceLight = part.emission[face] ? 0xF000F0 : light;
                for (int v = offset; v < offset + 24; v += 6) {
                    out.addVertex(pose, part.vertices[v], part.vertices[v + 1], part.vertices[v + 2])
                        .setColor((color >> 16) & 255, (color >> 8) & 255, color & 255, 255)
                        .setUv(.5F, .5F).setOverlay(OverlayTexture.NO_OVERLAY).setLight(faceLight)
                        .setNormal(pose, part.vertices[v + 3], part.vertices[v + 4], part.vertices[v + 5]);
                }
            }
        }
        for (Part child : part.children) {
            renderPart(child, poses, out, light, cockpit, walk, movement, flight, left, right);
        }
        poses.popPose();
    }

    private static List<Part> loadMesh() {
        Map<String, Part> parts = new LinkedHashMap<>();
        Map<String, String> parents = new LinkedHashMap<>();
        try (var stream = Minecraft.getInstance().getResourceManager().getResourceOrThrow(GEOMETRY).open();
             var reader = new InputStreamReader(stream, StandardCharsets.UTF_8)) {
            JsonObject root = JsonParser.parseReader(reader).getAsJsonObject();
            if (root.get("format").getAsInt() != 1) { throw new IOException("Unsupported mech mesh format"); }
            for (JsonElement element : root.getAsJsonArray("parts")) {
                JsonObject object = element.getAsJsonObject();
                String name = object.get("name").getAsString();
                JsonArray pivot = object.getAsJsonArray("pivot");
                JsonArray faces = object.getAsJsonArray("faces");
                int[] colors = new int[faces.size()];
                boolean[] emission = new boolean[faces.size()];
                float[] vertices = new float[faces.size() * 24];
                for (int i = 0; i < faces.size(); i++) {
                    JsonArray face = faces.get(i).getAsJsonArray();
                    colors[i] = face.get(0).getAsInt();
                    emission[i] = face.get(1).getAsInt() != 0;
                    JsonArray data = face.get(2).getAsJsonArray();
                    if (data.size() != 24) { throw new IOException("Invalid mech vertex count in " + name); }
                    for (int n = 0; n < 24; n++) { vertices[i * 24 + n] = data.get(n).getAsFloat(); }
                }
                parts.put(name, new Part(name, pivot.get(0).getAsFloat(), pivot.get(1).getAsFloat(),
                    pivot.get(2).getAsFloat(), vertices, colors, emission));
                parents.put(name, object.get("parent").getAsString());
            }
            List<Part> roots = new ArrayList<>();
            for (var entry : parts.entrySet()) {
                String parent = parents.get(entry.getKey());
                if (parent.isEmpty()) { roots.add(entry.getValue()); }
                else {
                    Part parentPart = parts.get(parent);
                    if (parentPart == null) { throw new IOException("Missing mech parent " + parent); }
                    parentPart.children.add(entry.getValue());
                }
            }
            return List.copyOf(roots);
        } catch (IOException | RuntimeException exception) {
            throw new IllegalStateException("Cannot load Ivory Mech Suit geometry", exception);
        }
    }

    private static final class Part {
        final String name;
        final float x, y, z;
        final float[] vertices;
        final int[] colors;
        final boolean[] emission;
        final List<Part> children = new ArrayList<>();
        Part(String name, float x, float y, float z, float[] vertices, int[] colors, boolean[] emission) {
            this.name = name; this.x = x; this.y = y; this.z = z;
            this.vertices = vertices; this.colors = colors; this.emission = emission;
        }
    }
}
