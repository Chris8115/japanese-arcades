package local.japanesearcades;

import net.minecraft.core.BlockPos;
import net.minecraft.network.FriendlyByteBuf;
import net.minecraft.network.codec.StreamCodec;
import net.minecraft.network.protocol.common.custom.CustomPacketPayload;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.level.ServerPlayer;
import net.neoforged.neoforge.network.event.RegisterPayloadHandlersEvent;

/** Small serverbound requests; inventory, ownership, stock and payment stay server-authoritative. */
public final class GachaponNetwork {
    private GachaponNetwork() {}

    public record PasswordPayload(int containerId, String password) implements CustomPacketPayload {
        public static final Type<PasswordPayload> TYPE = new Type<>(id("gachapon_password"));
        public static final StreamCodec<FriendlyByteBuf, PasswordPayload> CODEC = StreamCodec.of(
            (buf, data) -> { buf.writeVarInt(data.containerId); buf.writeUtf(data.password, 32); },
            buf -> new PasswordPayload(buf.readVarInt(), buf.readUtf(32)));
        @Override public Type<? extends CustomPacketPayload> type() { return TYPE; }
    }

    public record SettingsPayload(int containerId, int amount, String newPassword) implements CustomPacketPayload {
        public static final Type<SettingsPayload> TYPE = new Type<>(id("gachapon_settings"));
        public static final StreamCodec<FriendlyByteBuf, SettingsPayload> CODEC = StreamCodec.of(
            (buf, data) -> { buf.writeVarInt(data.containerId); buf.writeVarInt(data.amount); buf.writeUtf(data.newPassword, 32); },
            buf -> new SettingsPayload(buf.readVarInt(), buf.readVarInt(), buf.readUtf(32)));
        @Override public Type<? extends CustomPacketPayload> type() { return TYPE; }
    }

    public record CrankPayload(BlockPos pos, boolean held) implements CustomPacketPayload {
        public static final Type<CrankPayload> TYPE = new Type<>(id("gachapon_crank"));
        public static final StreamCodec<FriendlyByteBuf, CrankPayload> CODEC = StreamCodec.of(
            (buf, data) -> { buf.writeBlockPos(data.pos); buf.writeBoolean(data.held); },
            buf -> new CrankPayload(buf.readBlockPos(), buf.readBoolean()));
        @Override public Type<? extends CustomPacketPayload> type() { return TYPE; }
    }

    private static ResourceLocation id(String name) { return ResourceLocation.fromNamespaceAndPath(JapaneseArcades.MOD_ID, name); }

    public static void register(RegisterPayloadHandlersEvent event) {
        var registrar = event.registrar("gachapon-1");
        // NeoForge runs these play handlers on the main server thread by default.
        registrar.playToServer(PasswordPayload.TYPE, PasswordPayload.CODEC, (data, context) -> {
            if (context.player() instanceof ServerPlayer player) { handlePassword(player, data); }
        });
        registrar.playToServer(SettingsPayload.TYPE, SettingsPayload.CODEC, (data, context) -> {
            if (context.player() instanceof ServerPlayer player) { handleSettings(player, data); }
        });
        registrar.playToServer(CrankPayload.TYPE, CrankPayload.CODEC, (data, context) -> {
            if (context.player() instanceof ServerPlayer player) { handleCrank(player, data); }
        });
    }

    static void handlePassword(ServerPlayer player, PasswordPayload data) {
        if (player.containerMenu instanceof GachaponAccessMenu menu && menu.containerId == data.containerId
                && menu.stillValid(player)) {
            menu.submitPassword(player, data.password);
        }
    }

    static void handleSettings(ServerPlayer player, SettingsPayload data) {
        if (player.containerMenu instanceof GachaponMenu menu && menu.containerId == data.containerId
                && menu.stillValid(player)) {
            menu.applySettings(player, data.amount, data.newPassword);
        }
    }

    static void handleCrank(ServerPlayer player, CrankPayload data) {
        // Check distance before looking up the block entity: arbitrary packet
        // positions must never force remote chunks to load.
        if (player.distanceToSqr(data.pos.getCenter()) > 64 || !player.level().hasChunkAt(data.pos)) { return; }
        if (player.level().getBlockEntity(data.pos) instanceof GachaponBlockEntity machine) {
            machine.heartbeat(player, data.held);
        }
    }
}
