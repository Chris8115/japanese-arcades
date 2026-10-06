package local.funpack.custom;

import com.mojang.serialization.Codec;
import com.mojang.serialization.DataResult;
import com.mojang.serialization.codecs.RecordCodecBuilder;
import java.util.UUID;
import net.minecraft.network.RegistryFriendlyByteBuf;
import net.minecraft.network.codec.StreamCodec;
import net.minecraft.resources.ResourceLocation;

/** Versioned bearer-card data. New progression fields can be optional codec fields. */
public record ArcadePassData(int version, UUID id, ResourceLocation design,
        long credits, long prizePoints, long revision) {
    public static final long MAX_BALANCE = 1_000_000_000L;
    public static final UUID UNASSIGNED = new UUID(0, 0);
    public static final ResourceLocation DEFAULT_DESIGN = ResourceLocation.fromNamespaceAndPath(FunPackCustom.MOD_ID, "default");
    public static final Codec<ArcadePassData> CODEC = RecordCodecBuilder.create(instance -> instance.group(
        Codec.intRange(1, Integer.MAX_VALUE).optionalFieldOf("version", 1).forGetter(ArcadePassData::version),
        net.minecraft.core.UUIDUtil.CODEC.optionalFieldOf("id", UNASSIGNED).forGetter(ArcadePassData::id),
        ResourceLocation.CODEC.optionalFieldOf("design", DEFAULT_DESIGN).forGetter(ArcadePassData::design),
        boundedLong(MAX_BALANCE).optionalFieldOf("credits", 0L).forGetter(ArcadePassData::credits),
        boundedLong(MAX_BALANCE).optionalFieldOf("prize_points", 0L).forGetter(ArcadePassData::prizePoints),
        boundedLong(Long.MAX_VALUE-1).optionalFieldOf("revision", 0L).forGetter(ArcadePassData::revision)
    ).apply(instance, ArcadePassData::new));
    public static final StreamCodec<RegistryFriendlyByteBuf, ArcadePassData> STREAM_CODEC = StreamCodec.of(
        (buffer, value) -> {
            buffer.writeVarInt(value.version); buffer.writeUUID(value.id); buffer.writeResourceLocation(value.design);
            buffer.writeVarLong(value.credits); buffer.writeVarLong(value.prizePoints); buffer.writeVarLong(value.revision);
        }, buffer -> new ArcadePassData(buffer.readVarInt(), buffer.readUUID(), buffer.readResourceLocation(),
            buffer.readVarLong(), buffer.readVarLong(), buffer.readVarLong()));

    public ArcadePassData {
        if (version < 1 || id == null || design == null || credits < 0 || credits > MAX_BALANCE
                || prizePoints < 0 || prizePoints > MAX_BALANCE || revision < 0 || revision >= Long.MAX_VALUE) {
            throw new IllegalArgumentException("Invalid arcade pass data");
        }
    }
    private static Codec<Long> boundedLong(long max) {
        return Codec.LONG.validate(value -> value >= 0 && value <= max ? DataResult.success(value)
            : DataResult.error(() -> "Arcade balance/revision outside allowed range"));
    }
    public static ArcadePassData empty() { return new ArcadePassData(1, UNASSIGNED, DEFAULT_DESIGN, 0, 0, 0); }
    public static ArcadePassData create() { return new ArcadePassData(1, UUID.randomUUID(), DEFAULT_DESIGN, 0, 0, 0); }
    public ArcadePassData withBalances(long credits, long points) {
        if (version != 1 || revision >= Long.MAX_VALUE-1) { throw new IllegalStateException("Unsupported or exhausted arcade pass"); }
        return new ArcadePassData(version, id.equals(UNASSIGNED) ? UUID.randomUUID() : id, design, credits, points, revision+1);
    }
}
