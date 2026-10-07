package local.funpack.custom.client;

import local.funpack.custom.FunPackCustom;
import net.minecraft.client.renderer.BlockEntityWithoutLevelRenderer;
import net.neoforged.api.distmarker.Dist;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.client.event.EntityRenderersEvent;
import net.neoforged.neoforge.client.event.ModelEvent;
import net.neoforged.neoforge.client.extensions.common.IClientItemExtensions;
import net.neoforged.neoforge.client.extensions.common.RegisterClientExtensionsEvent;

@EventBusSubscriber(modid = FunPackCustom.MOD_ID, value = Dist.CLIENT, bus = EventBusSubscriber.Bus.MOD)
public final class CustomDisplayBoxClient {
    private CustomDisplayBoxClient() {}
    @SubscribeEvent public static void renderers(EntityRenderersEvent.RegisterRenderers event) {
        event.registerBlockEntityRenderer(FunPackCustom.CUSTOM_DISPLAY_BOX_ENTITY.get(), CustomDisplayBoxRenderer::new);
    }
    @SubscribeEvent public static void models(ModelEvent.RegisterAdditional event) { event.register(CustomDisplayBoxRenderer.SHELL); }
    @SubscribeEvent public static void baked(ModelEvent.BakingCompleted event) { CustomDisplayBoxAppearance.clear(); }
    @SubscribeEvent public static void items(RegisterClientExtensionsEvent event) {
        event.registerItem(new IClientItemExtensions() {
            private BlockEntityWithoutLevelRenderer renderer;
            @Override public BlockEntityWithoutLevelRenderer getCustomRenderer() {
                if (renderer == null) { renderer = new CustomDisplayBoxRenderer.ItemRenderer(); }
                return renderer;
            }
        }, FunPackCustom.CUSTOM_DISPLAY_BOX_ITEM.get());
    }
}
