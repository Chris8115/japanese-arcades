package local.funpack.custom.client;

import local.funpack.custom.FunPackCustom;
import net.neoforged.api.distmarker.Dist;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.client.event.EntityRenderersEvent;
import net.neoforged.neoforge.client.event.ModelEvent;

/** The moving mechanism is client-only; static cabinet cells use native block models. */
@EventBusSubscriber(modid = FunPackCustom.MOD_ID, value = Dist.CLIENT, bus = EventBusSubscriber.Bus.MOD)
public final class ClawMachineRenderClient {
    private ClawMachineRenderClient() {}

    @SubscribeEvent
    public static void renderers(EntityRenderersEvent.RegisterRenderers event) {
        event.registerBlockEntityRenderer(FunPackCustom.CLAW_MACHINE_ENTITY.get(), ClawMachineRenderer::new);
    }

    @SubscribeEvent
    public static void modelsBaked(ModelEvent.BakingCompleted event) {
        DisplayItemMeshes.INSTANCE.clear();
    }
}
