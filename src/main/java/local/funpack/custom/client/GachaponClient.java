package local.funpack.custom.client;

import local.funpack.custom.FunPackCustom;
import local.funpack.custom.GachaponBlock;
import local.funpack.custom.GachaponNetwork;
import net.minecraft.client.Minecraft;
import net.minecraft.core.BlockPos;
import net.minecraft.world.phys.BlockHitResult;
import net.minecraft.world.phys.HitResult;
import net.neoforged.api.distmarker.Dist;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.client.event.ClientTickEvent;
import net.neoforged.neoforge.client.event.EntityRenderersEvent;
import net.neoforged.neoforge.client.event.ModelEvent;
import net.neoforged.neoforge.client.event.RegisterMenuScreensEvent;
import net.neoforged.neoforge.network.PacketDistributor;

/** Client-only registrations; common initialization never links Minecraft client classes. */
@EventBusSubscriber(modid = FunPackCustom.MOD_ID, value = Dist.CLIENT, bus = EventBusSubscriber.Bus.MOD)
public final class GachaponClient {
    private GachaponClient() {}

    @SubscribeEvent
    public static void screens(RegisterMenuScreensEvent event) {
        event.register(FunPackCustom.GACHAPON_MENU.get(), GachaponScreen::new);
        event.register(FunPackCustom.GACHAPON_ACCESS_MENU.get(), GachaponAccessScreen::new);
    }

    @SubscribeEvent
    public static void renderers(EntityRenderersEvent.RegisterRenderers event) {
        event.registerBlockEntityRenderer(FunPackCustom.GACHAPON_ENTITY.get(), GachaponRenderer::new);
    }

    @SubscribeEvent
    public static void additionalModels(ModelEvent.RegisterAdditional event) {
        event.register(GachaponRenderer.CRANK_MODEL);
    }

    /** Heartbeats are only evidence of holding use; all payment and roll decisions stay on the server. */
    @EventBusSubscriber(modid = FunPackCustom.MOD_ID, value = Dist.CLIENT)
    public static final class Cranking {
        private static BlockPos heldMachine;
        private static int ticks;

        @SubscribeEvent
        public static void tick(ClientTickEvent.Post event) {
            Minecraft minecraft = Minecraft.getInstance();
            BlockPos target = null;
            if (minecraft.level != null && minecraft.player != null && minecraft.screen == null
                && !minecraft.isPaused() && minecraft.options.keyUse.isDown()
                && !minecraft.player.isShiftKeyDown() && !minecraft.player.isSpectator()
                && minecraft.hitResult instanceof BlockHitResult hit
                && hit.getType() == HitResult.Type.BLOCK
                && minecraft.level.getBlockState(hit.getBlockPos()).getBlock() instanceof GachaponBlock) {
                target = hit.getBlockPos();
            }
            if (heldMachine != null && !heldMachine.equals(target)) {
                if (minecraft.getConnection() != null) {
                    PacketDistributor.sendToServer(new GachaponNetwork.CrankPayload(heldMachine, false));
                }
                heldMachine = null;
                ticks = 0;
            }
            if (target != null) {
                if (!target.equals(heldMachine)) {
                    heldMachine = target.immutable();
                    ticks = 0;
                }
                if (ticks++ % 4 == 0) {
                    PacketDistributor.sendToServer(new GachaponNetwork.CrankPayload(heldMachine, true));
                }
            }
        }
    }
}
