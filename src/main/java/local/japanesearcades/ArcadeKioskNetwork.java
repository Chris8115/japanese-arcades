package local.japanesearcades;

import java.util.UUID;
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
            ResourceLocation.fromNamespaceAndPath(JapaneseArcades.MOD_ID, "arcade_order"));
        public static final StreamCodec<FriendlyByteBuf, OrderPayload> CODEC = StreamCodec.of(
            (buffer, payload) -> { buffer.writeVarInt(payload.containerId); buffer.writeResourceLocation(payload.entryId); },
            buffer -> new OrderPayload(buffer.readVarInt(), buffer.readResourceLocation()));
        @Override public Type<? extends CustomPacketPayload> type() { return TYPE; }
    }

    public record IssuePassPayload(int containerId) implements CustomPacketPayload {
        public static final Type<IssuePassPayload> TYPE = new Type<>(id("arcade_issue_pass"));
        public static final StreamCodec<FriendlyByteBuf, IssuePassPayload> CODEC = StreamCodec.of(
            (buffer, payload) -> buffer.writeVarInt(payload.containerId), buffer -> new IssuePassPayload(buffer.readVarInt()));
        @Override public Type<? extends CustomPacketPayload> type() { return TYPE; }
    }

    public record ExchangePayload(int containerId, int passSlot, UUID passId, long revision, ResourceLocation materialId) implements CustomPacketPayload {
        public static final Type<ExchangePayload> TYPE = new Type<>(id("arcade_exchange"));
        public static final StreamCodec<FriendlyByteBuf, ExchangePayload> CODEC = StreamCodec.of(
            (buffer, payload) -> {
                buffer.writeVarInt(payload.containerId); buffer.writeVarInt(payload.passSlot); buffer.writeUUID(payload.passId);
                buffer.writeLong(payload.revision); buffer.writeResourceLocation(payload.materialId);
            }, buffer -> new ExchangePayload(buffer.readVarInt(), buffer.readVarInt(), buffer.readUUID(), buffer.readLong(), buffer.readResourceLocation()));
        @Override public Type<? extends CustomPacketPayload> type() { return TYPE; }
    }

    public record TransferPayload(int containerId, int sourceSlot, UUID sourceId, long sourceRevision,
            int targetSlot, UUID targetId, long targetRevision) implements CustomPacketPayload {
        public static final Type<TransferPayload> TYPE = new Type<>(id("arcade_transfer"));
        public static final StreamCodec<FriendlyByteBuf, TransferPayload> CODEC = StreamCodec.of(
            (buffer, payload) -> {
                buffer.writeVarInt(payload.containerId); buffer.writeVarInt(payload.sourceSlot); buffer.writeUUID(payload.sourceId); buffer.writeLong(payload.sourceRevision);
                buffer.writeVarInt(payload.targetSlot); buffer.writeUUID(payload.targetId); buffer.writeLong(payload.targetRevision);
            }, buffer -> new TransferPayload(buffer.readVarInt(), buffer.readVarInt(), buffer.readUUID(), buffer.readLong(),
                buffer.readVarInt(), buffer.readUUID(), buffer.readLong()));
        @Override public Type<? extends CustomPacketPayload> type() { return TYPE; }
    }

    public record PrizePayload(int containerId, ResourceLocation prizeId, int passSlot, UUID passId, long revision) implements CustomPacketPayload {
        public static final Type<PrizePayload> TYPE = new Type<>(id("arcade_prize"));
        public static final StreamCodec<FriendlyByteBuf, PrizePayload> CODEC = StreamCodec.of(
            (buffer, payload) -> {
                buffer.writeVarInt(payload.containerId); buffer.writeResourceLocation(payload.prizeId);
                buffer.writeVarInt(payload.passSlot); buffer.writeUUID(payload.passId); buffer.writeLong(payload.revision);
            }, buffer -> new PrizePayload(buffer.readVarInt(), buffer.readResourceLocation(), buffer.readVarInt(), buffer.readUUID(), buffer.readLong()));
        @Override public Type<? extends CustomPacketPayload> type() { return TYPE; }
    }

    private static ResourceLocation id(String path) { return ResourceLocation.fromNamespaceAndPath(JapaneseArcades.MOD_ID, path); }

    public static void register(RegisterPayloadHandlersEvent event) {
        var registrar = event.registrar("arcade-kiosk-3");
        registrar.playToServer(OrderPayload.TYPE, OrderPayload.CODEC, (payload, context) -> {
            if (context.player() instanceof ServerPlayer player) { handleOrder(player, payload); }
        });
        registrar.playToServer(IssuePassPayload.TYPE, IssuePassPayload.CODEC, (payload, context) -> {
            if (context.player() instanceof ServerPlayer player) { handleIssuePass(player, payload); }
        });
        registrar.playToServer(ExchangePayload.TYPE, ExchangePayload.CODEC, (payload, context) -> {
            if (context.player() instanceof ServerPlayer player) { handleExchange(player, payload); }
        });
        registrar.playToServer(TransferPayload.TYPE, TransferPayload.CODEC, (payload, context) -> {
            if (context.player() instanceof ServerPlayer player) { handleTransfer(player, payload); }
        });
        registrar.playToServer(PrizePayload.TYPE, PrizePayload.CODEC, (payload, context) -> {
            if (context.player() instanceof ServerPlayer player) { handlePrize(player, payload); }
        });
    }

    static void handleOrder(ServerPlayer player, OrderPayload payload) {
        if (player.containerMenu instanceof ArcadeKioskMenu menu
                && menu.containerId == payload.containerId && menu.stillValid(player)) {
            menu.order(player, payload.entryId);
        }
    }
    static void handleIssuePass(ServerPlayer player, IssuePassPayload payload) {
        if (player.containerMenu instanceof ArcadeKioskMenu menu && menu.containerId == payload.containerId) { menu.issuePass(player); }
    }
    static void handleExchange(ServerPlayer player, ExchangePayload payload) {
        if (player.containerMenu instanceof ArcadeKioskMenu menu && menu.containerId == payload.containerId) {
            menu.exchange(player, payload.passSlot, payload.passId, payload.revision, payload.materialId);
        }
    }
    static void handleTransfer(ServerPlayer player, TransferPayload payload) {
        if (player.containerMenu instanceof ArcadeKioskMenu menu && menu.containerId == payload.containerId) {
            menu.transfer(player, payload.sourceSlot, payload.sourceId, payload.sourceRevision, payload.targetSlot, payload.targetId, payload.targetRevision);
        }
    }
    static void handlePrize(ServerPlayer player, PrizePayload payload) {
        if (player.containerMenu instanceof ArcadeKioskMenu menu && menu.containerId == payload.containerId) {
            menu.orderPrize(player, payload.prizeId, payload.passSlot, payload.passId, payload.revision);
        }
    }
}
