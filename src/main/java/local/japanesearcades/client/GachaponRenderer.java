package local.japanesearcades.client;

import java.util.Map;
import java.util.WeakHashMap;
import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.math.Axis;
import local.japanesearcades.JapaneseArcades;
import local.japanesearcades.GachaponBlock;
import local.japanesearcades.GachaponBlockEntity;
import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.Font;
import net.minecraft.client.renderer.MultiBufferSource;
import net.minecraft.client.renderer.RenderType;
import net.minecraft.client.renderer.blockentity.BlockEntityRenderer;
import net.minecraft.client.renderer.blockentity.BlockEntityRendererProvider;
import net.minecraft.client.resources.model.ModelResourceLocation;
import net.minecraft.core.Direction;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.util.RandomSource;
import net.minecraft.world.item.ItemDisplayContext;
import net.minecraft.world.item.ItemStack;
import net.neoforged.neoforge.client.RenderTypeHelper;
import net.neoforged.neoforge.client.model.data.ModelData;

/** The window is an actual live prize display: icons update with stock, price and crank state. */
public final class GachaponRenderer implements BlockEntityRenderer<GachaponBlockEntity> {
    public static final ModelResourceLocation CRANK_MODEL = ModelResourceLocation.standalone(
        ResourceLocation.fromNamespaceAndPath(JapaneseArcades.MOD_ID, "block/gachapon_crank"));
    private final Font font;
    private final DisplayItemMeshes prizeMeshes = DisplayItemMeshes.INSTANCE;
    private final Map<GachaponBlockEntity, CrankSample> crankSamples = new WeakHashMap<>();

    public GachaponRenderer(BlockEntityRendererProvider.Context context) {
        font = context.getFont();
    }

    @Override
    public void render(GachaponBlockEntity machine, float partialTick, PoseStack pose,
                       MultiBufferSource buffers, int packedLight, int packedOverlay) {
        pose.pushPose();
        Direction facing = machine.getBlockState().getValue(GachaponBlock.FACING);
        pose.translate(.5, 0, .5);
        pose.mulPose(Axis.YP.rotationDegrees(switch (facing) {
            case SOUTH -> 180;
            case EAST -> -90;
            case WEST -> 90;
            default -> 0;
        }));
        pose.translate(-.5, 0, -.5);

        // Model X increases toward the viewer's left when the machine faces north.
        for (int index = 0; index < 9; index++) {
            ItemStack prize = machine.getRewardDisplay(index);
            if (!prize.isEmpty()) {
                double x = (11.9 - 3.9 * (index % 3)) / 16;
                double y = (13.72 - 1.97 * (index / 3)) / 16;
                icon(prize, x, y, 1.48 / 16, 1.55 / 16, machine, pose, buffers, packedLight, packedOverlay);
            }
        }
        ItemStack price = machine.getPrice();
        if (!price.isEmpty()) {
            icon(price, 11.85 / 16, 7.0 / 16, .92 / 16, .91 / 16,
                machine, pose, buffers, packedLight, packedOverlay);
        }

        pose.pushPose();
        pose.translate(8.2 / 16, 5.0 / 16, 1.0 / 16);
        float progress = crankProgress(machine, partialTick);
        // Positive model Z rotation appears clockwise when viewed from the north-facing front.
        pose.mulPose(Axis.ZP.rotationDegrees(360 * progress));
        Minecraft minecraft = Minecraft.getInstance();
        var crankModel = minecraft.getModelManager().getModel(CRANK_MODEL);
        // Block geometry needs the entity-compatible layer when drawn from a BER. A terrain
        // cutout buffer uses the chunk shader and can silently displace the entire handle.
        for (RenderType layer : crankModel.getRenderTypes(machine.getBlockState(), RandomSource.create(42), ModelData.EMPTY)) {
            minecraft.getBlockRenderer().getModelRenderer().renderModel(pose.last(),
                buffers.getBuffer(RenderTypeHelper.getEntityRenderType(layer, false)), machine.getBlockState(),
                crankModel, 1, 1, 1, packedLight, packedOverlay, ModelData.EMPTY, layer);
        }
        pose.popPose();
        if (!price.isEmpty()) {
            // Draw text after the item batch so the font does not flush it mid-display.
            text(Component.literal(price.getCount() + " X"), 13.66 / 16, 7.0 / 16,
                .93 / 16, .0067F, 0xFFFFFF, pose, buffers, packedLight);
        }
        pose.popPose();
    }

    private float crankProgress(GachaponBlockEntity machine, float partialTick) {
        int ticks = machine.getCrankTicks();
        if (ticks <= 0 || machine.getLevel() == null) {
            crankSamples.remove(machine);
            return 0;
        }
        if (!machine.isCranking()) {
            crankSamples.remove(machine);
            return (float) ticks / GachaponBlockEntity.CRANK_DURATION;
        }
        long now = machine.getLevel().getGameTime();
        CrankSample sample = crankSamples.get(machine);
        if (sample == null || sample.ticks != ticks) {
            sample = new CrankSample(ticks, now);
            crankSamples.put(machine, sample);
        }
        // Public progress arrives every two server ticks. Extrapolate only that small gap,
        // rather than restarting partialTick on each client tick and making the wheel jerk.
        float betweenUpdates = Math.min(2, Math.max(0, now - sample.receivedAt + partialTick));
        return Math.min(1, (sample.ticks + betweenUpdates) / GachaponBlockEntity.CRANK_DURATION);
    }

    private record CrankSample(int ticks, long receivedAt) {}

    private void icon(ItemStack item, double x, double y, double z, double size,
                      GachaponBlockEntity machine, PoseStack pose, MultiBufferSource buffers,
                      int light, int overlay) {
        pose.pushPose();
        pose.translate(x, y, z);
        pose.mulPose(Axis.YP.rotationDegrees(180));
        // GUI perspective gives even readable icons for tools, blocks and custom items. Depth is
        // compressed so tall 3D item models cannot protrude through the neighbouring machine.
        pose.scale((float) size, (float) size, .005F);
        if (!prizeMeshes.render(item, pose, buffers, light, overlay)) {
            Minecraft.getInstance().getItemRenderer().renderStatic(item, ItemDisplayContext.GUI,
                light, overlay, pose, buffers, machine.getLevel(), 0);
        }
        pose.popPose();
    }

    private void text(Component value, double x, double y, double z, float scale, int color,
                      PoseStack pose, MultiBufferSource buffers, int light) {
        pose.pushPose();
        pose.translate(x, y, z);
        pose.mulPose(Axis.YP.rotationDegrees(180));
        pose.scale(scale, -scale, scale);
        font.drawInBatch(value, -font.width(value) / 2F, -font.lineHeight / 2F,
            color, false, pose.last().pose(), buffers, Font.DisplayMode.NORMAL, 0, light);
        pose.popPose();
    }
}
