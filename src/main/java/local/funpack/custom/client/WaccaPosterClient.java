package local.funpack.custom.client;

import local.funpack.custom.FunPackCustom;
import net.neoforged.api.distmarker.Dist;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.client.event.EntityRenderersEvent;

/** Client-only rendering for the poster's original print proportions. */
@EventBusSubscriber(modid = FunPackCustom.MOD_ID, value = Dist.CLIENT, bus = EventBusSubscriber.Bus.MOD)
public final class WaccaPosterClient {
    private WaccaPosterClient() {}

    @SubscribeEvent
    public static void renderers(EntityRenderersEvent.RegisterRenderers event) {
        event.registerEntityRenderer(FunPackCustom.WACCA_POSTER_ENTITY.get(), WaccaPosterRenderer::new);
    }
}
