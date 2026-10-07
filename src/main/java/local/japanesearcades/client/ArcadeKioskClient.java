package local.japanesearcades.client;

import local.japanesearcades.JapaneseArcades;
import net.neoforged.api.distmarker.Dist;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.client.event.RegisterMenuScreensEvent;

/** Client registration is isolated from the dedicated-server entry point. */
@EventBusSubscriber(modid = JapaneseArcades.MOD_ID, value = Dist.CLIENT, bus = EventBusSubscriber.Bus.MOD)
public final class ArcadeKioskClient {
    private ArcadeKioskClient() {}

    @SubscribeEvent
    public static void screens(RegisterMenuScreensEvent event) {
        event.register(JapaneseArcades.ARCADE_KIOSK_MENU.get(), ArcadeKioskScreen::new);
    }
}
