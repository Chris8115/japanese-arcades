package local.funpack.custom;

import java.util.UUID;
import net.minecraft.core.BlockPos;
import net.minecraft.network.FriendlyByteBuf;
import net.minecraft.network.codec.StreamCodec;
import net.minecraft.network.protocol.common.custom.CustomPacketPayload;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.level.ServerPlayer;
import net.neoforged.neoforge.network.event.RegisterPayloadHandlersEvent;

/** Only intent crosses the wire; session, payment, movement and results remain server-owned. */
public final class ClawMachineNetwork {
    public enum Action { LEFT, RIGHT, BACK, FRONT, DROP, EXIT, HEARTBEAT }
    private ClawMachineNetwork() {}
    private static ResourceLocation id(String path) { return ResourceLocation.fromNamespaceAndPath(FunPackCustom.MOD_ID, path); }

    public record ActionPayload(int containerId, BlockPos pos, UUID session, int sequence, Action action) implements CustomPacketPayload {
        public static final Type<ActionPayload> TYPE = new Type<>(id("claw_action"));
        public static final StreamCodec<FriendlyByteBuf, ActionPayload> CODEC = StreamCodec.of(
            (buf, value) -> { buf.writeVarInt(value.containerId); buf.writeBlockPos(value.pos); buf.writeUUID(value.session); buf.writeVarInt(value.sequence); buf.writeEnum(value.action); },
            buf -> new ActionPayload(buf.readVarInt(), buf.readBlockPos(), buf.readUUID(), buf.readVarInt(), buf.readEnum(Action.class)));
        @Override public Type<? extends CustomPacketPayload> type() { return TYPE; }
    }
    public record PasswordPayload(int containerId, String password) implements CustomPacketPayload {
        public static final Type<PasswordPayload> TYPE = new Type<>(id("claw_password"));
        public static final StreamCodec<FriendlyByteBuf, PasswordPayload> CODEC = StreamCodec.of(
            (buf, value) -> { buf.writeVarInt(value.containerId); buf.writeUtf(value.password, 32); },
            buf -> new PasswordPayload(buf.readVarInt(), buf.readUtf(32)));
        @Override public Type<? extends CustomPacketPayload> type() { return TYPE; }
    }
    public record SettingsPayload(int containerId, int baseChance, int guaranteePlay, String password) implements CustomPacketPayload {
        public static final Type<SettingsPayload> TYPE = new Type<>(id("claw_settings"));
        public static final StreamCodec<FriendlyByteBuf, SettingsPayload> CODEC = StreamCodec.of(
            (buf, value) -> { buf.writeVarInt(value.containerId); buf.writeVarInt(value.baseChance); buf.writeVarInt(value.guaranteePlay); buf.writeUtf(value.password, 32); },
            buf -> new SettingsPayload(buf.readVarInt(), buf.readVarInt(), buf.readVarInt(), buf.readUtf(32)));
        @Override public Type<? extends CustomPacketPayload> type() { return TYPE; }
    }
    public static void register(RegisterPayloadHandlersEvent event) {
        var registrar = event.registrar("claw-1");
        registrar.playToServer(ActionPayload.TYPE, ActionPayload.CODEC, (data, context) -> {
            if (context.player() instanceof ServerPlayer player) handleAction(player, data);
        });
        registrar.playToServer(PasswordPayload.TYPE, PasswordPayload.CODEC, (data, context) -> {
            if (context.player() instanceof ServerPlayer player) handlePassword(player, data);
        });
        registrar.playToServer(SettingsPayload.TYPE, SettingsPayload.CODEC, (data, context) -> {
            if (context.player() instanceof ServerPlayer player) handleSettings(player, data);
        });
    }
    static void handleAction(ServerPlayer player, ActionPayload data) {
        if (player.containerMenu instanceof ClawMachineMenu menu && menu.containerId == data.containerId
            && !menu.isOperator() && menu.getBlockPos().equals(data.pos) && menu.stillValid(player))
            menu.action(player, data.pos, data.session, data.sequence, data.action);
    }
    static void handlePassword(ServerPlayer player, PasswordPayload data) {
        if (player.containerMenu instanceof ClawMachineAccessMenu menu && menu.containerId == data.containerId && menu.stillValid(player))
            menu.submitPassword(player, data.password);
    }
    static void handleSettings(ServerPlayer player, SettingsPayload data) {
        if (player.containerMenu instanceof ClawMachineMenu menu && menu.containerId == data.containerId && menu.isOperator() && menu.stillValid(player))
            menu.applySettings(player, data.baseChance, data.guaranteePlay, data.password);
    }
}
