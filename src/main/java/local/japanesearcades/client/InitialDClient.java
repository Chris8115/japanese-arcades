package local.japanesearcades.client;

import local.japanesearcades.JapaneseArcades;
import net.minecraft.client.renderer.entity.NoopRenderer;
import net.neoforged.api.distmarker.Dist;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.client.event.EntityRenderersEvent;

/** The seat is a riding anchor; its visible chair is part of the cabinet model. */
@EventBusSubscriber(modid = JapaneseArcades.MOD_ID, value = Dist.CLIENT, bus = EventBusSubscriber.Bus.MOD)
public final class InitialDClient {
    private InitialDClient() {}
    @SubscribeEvent public static void renderers(EntityRenderersEvent.RegisterRenderers event) {
        event.registerEntityRenderer(JapaneseArcades.INITIAL_D_SEAT.get(), NoopRenderer::new);
    }
}
