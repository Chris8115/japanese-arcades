package local.japanesearcades.client;

import local.japanesearcades.JapaneseArcades;
import net.minecraft.client.Minecraft;
import net.neoforged.api.distmarker.Dist;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.client.event.RegisterMenuScreensEvent;
import net.neoforged.neoforge.client.event.ClientChatReceivedEvent;

@EventBusSubscriber(modid = JapaneseArcades.MOD_ID, value = Dist.CLIENT, bus = EventBusSubscriber.Bus.MOD)
public final class ClawMachineClient {
    private ClawMachineClient() {}
    @SubscribeEvent public static void screens(RegisterMenuScreensEvent event) {
        event.register(JapaneseArcades.CLAW_MACHINE_MENU.get(), ClawMachineOperatorScreen::new);
        event.register(JapaneseArcades.CLAW_MACHINE_PLAY_MENU.get(), ClawMachinePlayScreen::new);
        event.register(JapaneseArcades.CLAW_MACHINE_ACCESS_MENU.get(), ClawMachineAccessScreen::new);
    }
    @EventBusSubscriber(modid = JapaneseArcades.MOD_ID, value = Dist.CLIENT)
    public static final class PlayFeedback {
        private PlayFeedback() {}
        @SubscribeEvent public static void message(ClientChatReceivedEvent.System event) {
            if (event.isOverlay() && Minecraft.getInstance().screen instanceof ClawMachinePlayScreen screen)
                screen.showFeedback(event.getMessage());
        }
    }
}
