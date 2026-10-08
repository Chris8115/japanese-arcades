package local.japanesearcades;

import net.minecraft.network.FriendlyByteBuf;
import net.minecraft.network.codec.StreamCodec;
import net.minecraft.network.protocol.common.custom.CustomPacketPayload;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.level.ServerPlayer;
import net.neoforged.neoforge.network.event.RegisterPayloadHandlersEvent;

/** Inputs contain no entity id, position, target or damage: all authority stays with the server. */
public final class MechSuitNetwork {
    private MechSuitNetwork() {}

    public record InputPayload(float forward, float strafe, boolean ascend, boolean descend,
            boolean leftAttack, boolean rightAttack, float yaw, float pitch) implements CustomPacketPayload {
        public static final Type<InputPayload> TYPE = new Type<>(ResourceLocation.fromNamespaceAndPath(JapaneseArcades.MOD_ID, "mech_input"));
        public static final StreamCodec<FriendlyByteBuf, InputPayload> CODEC = StreamCodec.of(
            (buf, data) -> {
                buf.writeFloat(data.forward); buf.writeFloat(data.strafe);
                buf.writeBoolean(data.ascend); buf.writeBoolean(data.descend);
                buf.writeBoolean(data.leftAttack); buf.writeBoolean(data.rightAttack);
                buf.writeFloat(data.yaw); buf.writeFloat(data.pitch);
            }, buf -> new InputPayload(buf.readFloat(), buf.readFloat(), buf.readBoolean(), buf.readBoolean(),
                buf.readBoolean(), buf.readBoolean(), buf.readFloat(), buf.readFloat()));
        @Override public Type<? extends CustomPacketPayload> type() { return TYPE; }
    }

    public static void register(RegisterPayloadHandlersEvent event) {
        event.registrar("mech-1").playToServer(InputPayload.TYPE, InputPayload.CODEC, (data, context) -> {
            if (context.player() instanceof ServerPlayer player) { handleInput(player, data); }
        });
    }

    static void handleInput(ServerPlayer player, InputPayload data) {
        if (player.getVehicle() instanceof MechSuitEntity mech && mech.getPilot() == player) {
            mech.acceptInput(player, data);
        }
    }
}
