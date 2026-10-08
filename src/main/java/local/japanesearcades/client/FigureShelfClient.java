package local.japanesearcades.client;

import local.japanesearcades.JapaneseArcades;
import net.neoforged.api.distmarker.Dist;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.client.event.EntityRenderersEvent;
import net.neoforged.neoforge.client.event.ModelEvent;
import net.neoforged.neoforge.client.event.RegisterMenuScreensEvent;

@EventBusSubscriber(modid = JapaneseArcades.MOD_ID, value = Dist.CLIENT, bus = EventBusSubscriber.Bus.MOD)
public final class FigureShelfClient {
    private FigureShelfClient() {}
    @SubscribeEvent public static void renderers(EntityRenderersEvent.RegisterRenderers event) {
        event.registerBlockEntityRenderer(JapaneseArcades.FIGURE_SHELF_ENTITY.get(), FigureShelfRenderer::new);
    }
    @SubscribeEvent public static void screens(RegisterMenuScreensEvent event) {
        event.register(JapaneseArcades.FIGURE_SHELF_MENU.get(), FigureShelfScreen::new);
    }
    @SubscribeEvent public static void baked(ModelEvent.BakingCompleted event) { FigureShelfRenderer.clear(); }
}
