package local.funpack.custom.client;

import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.math.Axis;
import local.funpack.custom.CustomDisplayBoxBlock;
import local.funpack.custom.CustomDisplayBoxBlockEntity;
import local.funpack.custom.CustomDisplayBoxData;
import local.funpack.custom.FunPackCustom;
import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.Font;
import net.minecraft.client.renderer.BlockEntityWithoutLevelRenderer;
import net.minecraft.client.renderer.MultiBufferSource;
import net.minecraft.client.renderer.RenderType;
import net.minecraft.client.renderer.blockentity.BlockEntityRenderer;
import net.minecraft.client.renderer.blockentity.BlockEntityRendererProvider;
import net.minecraft.client.resources.model.ModelResourceLocation;
import net.minecraft.network.chat.Component;
import net.minecraft.network.chat.Style;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.util.RandomSource;
import net.minecraft.world.item.ItemDisplayContext;
import net.minecraft.world.item.BlockItem;
import net.minecraft.world.item.ItemStack;
import net.neoforged.neoforge.client.RenderTypeHelper;
import net.neoforged.neoforge.client.model.data.ModelData;

/** One shared appearance path for placed, held, inventory, and arcade prize displays. */
public final class CustomDisplayBoxRenderer implements BlockEntityRenderer<CustomDisplayBoxBlockEntity> {
    public static final ModelResourceLocation SHELL = ModelResourceLocation.standalone(
        ResourceLocation.fromNamespaceAndPath(FunPackCustom.MOD_ID, "block/custom_display_box"));
    private static final ResourceLocation LABEL_FONT = ResourceLocation.fromNamespaceAndPath(FunPackCustom.MOD_ID, "custom_display_box");
    private static int renderDepth;
    public CustomDisplayBoxRenderer(BlockEntityRendererProvider.Context context) {}
    @Override public int getViewDistance() { return 32; }
    @Override public void render(CustomDisplayBoxBlockEntity box, float partialTick, PoseStack pose,
                                 MultiBufferSource buffers, int light, int overlay) {
        pose.pushPose();
        pose.translate(.5, 0, .5);
        pose.mulPose(Axis.YP.rotationDegrees(switch (box.getBlockState().getValue(CustomDisplayBoxBlock.FACING)) {
            case SOUTH -> 180; case EAST -> -90; case WEST -> 90; default -> 0;
        }));
        pose.translate(-.5, 0, -.5);
        draw(box.data(), pose, buffers, light, overlay, true);
        pose.popPose();
    }
    private static void draw(CustomDisplayBoxData data, PoseStack pose, MultiBufferSource buffers, int light, int overlay, boolean cullFromEye) {
        if (renderDepth >= 2) { return; }
        renderDepth++;
        try {
            Minecraft mc = Minecraft.getInstance();
            ItemStack sample = data.retainedItem();
            var look = CustomDisplayBoxAppearance.of(sample, data.straightOn());
            var shell = mc.getModelManager().getModel(SHELL);
            var state = FunPackCustom.CUSTOM_DISPLAY_BOX.get().defaultBlockState();
            int color = look.color();
            for (RenderType layer : shell.getRenderTypes(state, RandomSource.create(42), ModelData.EMPTY)) {
                mc.getBlockRenderer().getModelRenderer().renderModel(pose.last(),
                    buffers.getBuffer(RenderTypeHelper.getEntityRenderType(layer, false)), state, shell,
                    (color >> 16 & 255) / 255F, (color >> 8 & 255) / 255F, (color & 255) / 255F,
                    light, overlay, ModelData.EMPTY, layer);
            }
            ItemStack contents = data.containedItem();
            if (!contents.isEmpty() && !contents.is(FunPackCustom.CUSTOM_DISPLAY_BOX_ITEM.get())) {
                pose.pushPose();
                pose.translate(.5, .432, .49);
                // Baked block geometry faces north. Item icons and custom item renderers
                // (including vanilla chests) face +Z instead. NONE removes the GUI tilt.
                boolean northFacingModel = contents.getItem() instanceof BlockItem
                    && !mc.getItemRenderer().getModel(contents, mc.level, mc.player, 0).isCustomRenderer();
                if (!data.straightOn() || !northFacingModel) {
                    pose.mulPose(Axis.YP.rotationDegrees(180));
                }
                pose.scale(look.scale(), look.scale(), look.scale());
                pose.translate(-look.x(), -look.y(), -look.z());
                // Inventory projection is orthographic; a world-space eye test incorrectly
                // removes these nested meshes. Keep the cache, with native GPU culling.
                ItemDisplayContext context = data.straightOn() ? ItemDisplayContext.NONE : ItemDisplayContext.GUI;
                if (!DisplayItemMeshes.INSTANCE.render(contents, pose, buffers, light, overlay, cullFromEye, context)) {
                    mc.getItemRenderer().renderStatic(contents, context, light, overlay, pose, buffers, mc.level, 0);
                }
                pose.popPose();
            }
            Component label = sample.isEmpty() ? Component.translatable("label.funpackcustom.custom_display_box") : sample.getHoverName();
            // Strip item-specific formatting so enchantment rarity/obfuscation cannot change
            // the printed packaging. Full original names/components stay on the real item.
            String text = label.getString();
            if (text.codePointCount(0, text.length()) > 48) { text = text.substring(0, text.offsetByCodePoints(0, 47)) + "…"; }
            Component printed = Component.literal(text).setStyle(Style.EMPTY.withFont(LABEL_FONT));
            int width = mc.font.width(printed);
            float scale = Math.min(.0045F, .505F / Math.max(1, width));
            pose.pushPose();
            pose.translate(.5, .082, 3.975 / 16);
            pose.mulPose(Axis.YP.rotationDegrees(180));
            pose.scale(scale, -scale, scale);
            mc.font.drawInBatch(printed, -width / 2F, 0, 0xFFF3F3ED, false, pose.last().pose(), buffers,
                Font.DisplayMode.NORMAL, 0, light);
            pose.popPose();
        } finally { renderDepth--; }
    }
    static final class ItemRenderer extends BlockEntityWithoutLevelRenderer {
        ItemRenderer() { super(Minecraft.getInstance().getBlockEntityRenderDispatcher(), Minecraft.getInstance().getEntityModels()); }
        @Override public void renderByItem(ItemStack stack, ItemDisplayContext context, PoseStack pose,
                                           MultiBufferSource buffers, int light, int overlay) {
            draw(CustomDisplayBoxData.from(stack), pose, buffers, light, overlay, false);
        }
    }
}
