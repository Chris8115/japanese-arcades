package local.funpack.custom;

import net.minecraft.network.FriendlyByteBuf;
import net.minecraft.network.codec.StreamCodec;
import net.minecraft.network.protocol.common.custom.CustomPacketPayload;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.level.ServerPlayer;
import net.neoforged.neoforge.network.event.RegisterPayloadHandlersEvent;

/** The client selects an entry; it cannot supply a price or an output stack. */
public final class ArcadeKioskNetwork {
    private ArcadeKioskNetwork() {}

    public record OrderPayload(int containerId, ResourceLocation entryId) implements CustomPacketPayload {
        public static final Type<OrderPayload> TYPE = new Type<>(
            ResourceLocation.fromNamespaceAndPath(FunPackCustom.MOD_ID, "arcade_order"));
        public static final StreamCodec<FriendlyByteBuf, OrderPayload> CODEC = StreamCodec.of(
            (buffer, payload) -> { buffer.writeVarInt(payload.containerId); buffer.writeResourceLocation(payload.entryId); },
            buffer -> new OrderPayload(buffer.readVarInt(), buffer.readResourceLocation()));
        @Override public Type<? extends CustomPacketPayload> type() { return TYPE; }
    }

    public static void register(RegisterPayloadHandlersEvent event) {
        event.registrar("arcade-kiosk-1").playToServer(OrderPayload.TYPE, OrderPayload.CODEC, (payload, context) -> {
            if (context.player() instanceof ServerPlayer player) { handleOrder(player, payload); }
        });
    }

    static void handleOrder(ServerPlayer player, OrderPayload payload) {
        if (player.containerMenu instanceof ArcadeKioskMenu menu
                && menu.containerId == payload.containerId && menu.stillValid(player)) {
            menu.order(player, payload.entryId);
        }
    }
}
