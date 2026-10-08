package local.japanesearcades.client;

import com.mojang.blaze3d.platform.InputConstants;
import java.util.ArrayList;
import java.util.List;
import local.japanesearcades.JapaneseArcades;
import local.japanesearcades.MechSuitEntity;
import local.japanesearcades.MechSuitNetwork;
import net.minecraft.client.KeyMapping;
import net.minecraft.client.Minecraft;
import net.minecraft.network.chat.Component;
import net.minecraft.util.FormattedCharSequence;
import net.minecraft.util.Mth;
import net.neoforged.api.distmarker.Dist;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.client.event.CalculateDetachedCameraDistanceEvent;
import net.neoforged.neoforge.client.event.ClientTickEvent;
import net.neoforged.neoforge.client.event.EntityRenderersEvent;
import net.neoforged.neoforge.client.event.InputEvent;
import net.neoforged.neoforge.client.event.RegisterKeyMappingsEvent;
import net.neoforged.neoforge.client.event.RenderGuiEvent;
import net.neoforged.neoforge.client.event.RenderHandEvent;
import net.neoforged.neoforge.client.event.RenderPlayerEvent;
import net.neoforged.neoforge.client.settings.IKeyConflictContext;
import net.neoforged.neoforge.client.settings.KeyConflictContext;
import net.neoforged.neoforge.network.PacketDistributor;
import org.jetbrains.annotations.Nullable;
import org.lwjgl.glfw.GLFW;

/** Client input is intent only; movement, flight, attacks, and health remain server-authoritative. */
@EventBusSubscriber(modid = JapaneseArcades.MOD_ID, value = Dist.CLIENT, bus = EventBusSubscriber.Bus.MOD)
public final class MechSuitClient {
    private static final IKeyConflictContext PILOT_CONTEXT = new IKeyConflictContext() {
        @Override public boolean isActive() {
            return Minecraft.getInstance().screen == null && localSuit() != null;
        }
        @Override public boolean conflicts(IKeyConflictContext other) {
            return other == this || other == KeyConflictContext.IN_GAME || other == KeyConflictContext.UNIVERSAL;
        }
    };
    public static final KeyMapping DESCEND = new KeyMapping("key.japanesearcades.mech_descend",
        PILOT_CONTEXT, InputConstants.Type.KEYSYM, GLFW.GLFW_KEY_R, "key.categories.japanesearcades");

    private MechSuitClient() {}

    @SubscribeEvent public static void renderers(EntityRenderersEvent.RegisterRenderers event) {
        event.registerEntityRenderer(JapaneseArcades.MECH_SUIT.get(), MechSuitRenderer::new);
    }

    @SubscribeEvent public static void keys(RegisterKeyMappingsEvent event) { event.register(DESCEND); }

    @Nullable
    private static MechSuitEntity localSuit() {
        var player = Minecraft.getInstance().player;
        return player != null && player.getVehicle() instanceof MechSuitEntity suit ? suit : null;
    }

    @EventBusSubscriber(modid = JapaneseArcades.MOD_ID, value = Dist.CLIENT)
    public static final class Events {
        private static boolean leftQueued, rightQueued;
        private Events() {}

        @SubscribeEvent public static void tick(ClientTickEvent.Post event) {
            Minecraft mc = Minecraft.getInstance();
            if (localSuit() == null || mc.getConnection() == null) {
                leftQueued = rightQueued = false;
                return;
            }
            boolean active = mc.screen == null && !mc.isPaused() && mc.isWindowActive();
            float forward = active ? (mc.options.keyUp.isDown() ? 1 : 0) - (mc.options.keyDown.isDown() ? 1 : 0) : 0;
            float strafe = active ? (mc.options.keyLeft.isDown() ? 1 : 0) - (mc.options.keyRight.isDown() ? 1 : 0) : 0;
            // Send neutral controls while menus are open; a released key cannot leave the
            // suit flying or swinging indefinitely. The server also expires stale input.
            PacketDistributor.sendToServer(new MechSuitNetwork.InputPayload(forward, strafe,
                active && mc.options.keyJump.isDown(), active && DESCEND.isDown(),
                active && (leftQueued || mc.options.keyAttack.isDown()),
                active && (rightQueued || mc.options.keyUse.isDown()), mc.player.getYRot(), mc.player.getXRot()));
            leftQueued = rightQueued = false;
        }

        @SubscribeEvent public static void interaction(InputEvent.InteractionKeyMappingTriggered event) {
            if (localSuit() == null) { return; }
            event.setCanceled(true);
            event.setSwingHand(false);
            if (Minecraft.getInstance().screen == null) {
                leftQueued |= event.isAttack();
                rightQueued |= event.isUseItem();
            }
        }

        @SubscribeEvent public static void pilot(RenderPlayerEvent.Pre event) {
            if (event.getEntity().getVehicle() instanceof MechSuitEntity) { event.setCanceled(true); }
        }

        @SubscribeEvent public static void hands(RenderHandEvent event) {
            if (localSuit() != null) { event.setCanceled(true); }
        }

        @SubscribeEvent public static void camera(CalculateDetachedCameraDistanceEvent event) {
            if (event.getCamera().getEntity().getVehicle() instanceof MechSuitEntity) {
                // The five-block armor and deployed wings need more room than a player.
                // Vanilla still clips this distance against walls after the event.
                event.setDistance(Math.max(event.getDistance(), 7.5F));
            }
        }

        @SubscribeEvent public static void hud(RenderGuiEvent.Post event) {
            Minecraft mc = Minecraft.getInstance();
            MechSuitEntity suit = localSuit();
            if (suit == null || mc.options.hideGui || mc.screen != null) { return; }
            var graphics = event.getGuiGraphics();
            int width = graphics.guiWidth();
            int health = Mth.ceil(suit.getHullHealth()), maximum = Mth.ceil(suit.getMaxHullHealth());
            Component hull = Component.translatable("hud.japanesearcades.mech.hull", health, maximum);
            Component mode = Component.translatable(suit.isFlying()
                ? "hud.japanesearcades.mech.flight" : "hud.japanesearcades.mech.ground");
            int panelWidth = Math.max(136, mc.font.width(hull) + mc.font.width(mode) + 24);
            panelWidth = Math.min(panelWidth, width - 16);
            graphics.fill(8, 8, 8 + panelWidth, 36, 0xA0142028);
            graphics.drawString(mc.font, hull, 14, 13, 0xFFF1EBD7, false);
            graphics.drawString(mc.font, mode, 2 + panelWidth - mc.font.width(mode), 13, 0xFF70D8D1, false);
            graphics.fill(14, 27, panelWidth + 2, 30, 0xFF39454B);
            int fill = Mth.floor((panelWidth - 12) * Mth.clamp(suit.getHullHealth() / Math.max(1, suit.getMaxHullHealth()), 0, 1));
            graphics.fill(14, 27, 14 + fill, 30, health > maximum / 4 ? 0xFF70D8D1 : 0xFFFF846B);

            List<FormattedCharSequence> hints = new ArrayList<>();
            int hintWidth = Math.min(240, width - 28);
            hints.addAll(mc.font.split(Component.translatable("hud.japanesearcades.mech.move",
                mc.options.keyUp.getTranslatedKeyMessage(), mc.options.keyLeft.getTranslatedKeyMessage(),
                mc.options.keyDown.getTranslatedKeyMessage(), mc.options.keyRight.getTranslatedKeyMessage()), hintWidth));
            hints.addAll(mc.font.split(Component.translatable("hud.japanesearcades.mech.flight_controls",
                mc.options.keyJump.getTranslatedKeyMessage(), DESCEND.getTranslatedKeyMessage(),
                mc.options.keyShift.getTranslatedKeyMessage()), hintWidth));
            hints.addAll(mc.font.split(Component.translatable("hud.japanesearcades.mech.attack_controls",
                mc.options.keyAttack.getTranslatedKeyMessage(), mc.options.keyUse.getTranslatedKeyMessage()), hintWidth));
            // Keep the pilot's view, third-person armor, and vanilla dismount prompt clear.
            // Narrow windows naturally stack this panel below the hull header.
            int hintsWidth = hints.stream().mapToInt(mc.font::width).max().orElse(0) + 12;
            int right = width - 8;
            int y = 48;
            graphics.fill(right - hintsWidth, y - 6, right, y + hints.size() * 11 + 3, 0x88142028);
            for (var hint : hints) {
                graphics.drawString(mc.font, hint, right - 6 - mc.font.width(hint), y, 0xFFC8D5DC, false);
                y += 11;
            }
        }
    }
}
