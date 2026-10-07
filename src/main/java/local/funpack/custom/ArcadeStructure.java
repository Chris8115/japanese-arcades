package local.funpack.custom;

import com.mojang.datafixers.util.Either;
import com.mojang.serialization.Codec;
import com.mojang.serialization.MapCodec;
import com.mojang.serialization.codecs.RecordCodecBuilder;
import java.util.Optional;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Holder;
import net.minecraft.world.level.levelgen.Heightmap;
import net.minecraft.world.level.levelgen.structure.BoundingBox;
import net.minecraft.world.level.levelgen.structure.Structure;
import net.minecraft.world.level.levelgen.structure.StructureType;
import net.minecraft.world.level.levelgen.structure.pools.DimensionPadding;
import net.minecraft.world.level.levelgen.structure.pools.JigsawPlacement;
import net.minecraft.world.level.levelgen.structure.pools.StructureTemplatePool;
import net.minecraft.world.level.levelgen.structure.pools.alias.PoolAliasLookup;
import net.minecraft.world.level.levelgen.structure.templatesystem.LiquidSettings;

/** Native jigsaw generation with a dry, gentle site suitable for a rigid two-storey building. */
public final class ArcadeStructure extends Structure {
    public static final MapCodec<ArcadeStructure> CODEC = RecordCodecBuilder.mapCodec(instance -> instance.group(
        settingsCodec(instance),
        StructureTemplatePool.CODEC.fieldOf("start_pool").forGetter(structure -> structure.startPool),
        Codec.intRange(0, 12).optionalFieldOf("max_terrain_height_difference", 3).forGetter(structure -> structure.maxSlope),
        Codec.intRange(-16, 16).optionalFieldOf("surface_height_offset", -1).forGetter(structure -> structure.surfaceOffset)
    ).apply(instance, ArcadeStructure::new));

    private final Holder<StructureTemplatePool> startPool;
    private final int maxSlope;
    private final int surfaceOffset;

    public ArcadeStructure(StructureSettings settings, Holder<StructureTemplatePool> startPool, int maxSlope, int surfaceOffset) {
        super(settings);
        this.startPool = startPool;
        this.maxSlope = maxSlope;
        this.surfaceOffset = surfaceOffset;
    }

    @Override
    protected Optional<GenerationStub> findGenerationPoint(GenerationContext context) {
        if (!ArcadeWorldgenConfig.standaloneEnabled()) { return Optional.empty(); }
        BlockPos origin = new BlockPos(context.chunkPos().getMinBlockX(), surfaceOffset, context.chunkPos().getMinBlockZ());
        // In 1.21.1 depth zero never appends the starting piece. Depth one places the connector-free start template.
        var candidate = JigsawPlacement.addPieces(context, startPool, Optional.empty(), 1, origin, false,
            Optional.of(Heightmap.Types.WORLD_SURFACE_WG), 32, PoolAliasLookup.EMPTY, new DimensionPadding(0, 2),
            LiquidSettings.IGNORE_WATERLOGGING);
        if (candidate.isEmpty()) { return Optional.empty(); }
        var pieces = candidate.get().getPiecesBuilder();
        if (pieces.isEmpty() || !suitableTerrain(context, pieces.getBoundingBox(), maxSlope)) { return Optional.empty(); }
        return Optional.of(new GenerationStub(candidate.get().position(), Either.right(pieces)));
    }

    static boolean suitableTerrain(GenerationContext context, BoundingBox bounds, int maxSlope) {
        if (bounds.minY() < context.heightAccessor().getMinBuildHeight()
                || bounds.maxY() + 2 >= context.heightAccessor().getMaxBuildHeight()) { return false; }
        int minimum = Integer.MAX_VALUE;
        int maximum = Integer.MIN_VALUE;
        int[] xs = {bounds.minX(), (bounds.minX() + bounds.maxX()) / 2, bounds.maxX()};
        int[] zs = {bounds.minZ(), (bounds.minZ() + bounds.maxZ()) / 2, bounds.maxZ()};
        for (int x : xs) {
            for (int z : zs) {
                int surface = context.chunkGenerator().getFirstFreeHeight(x, z, Heightmap.Types.WORLD_SURFACE_WG,
                    context.heightAccessor(), context.randomState());
                var column = context.chunkGenerator().getBaseColumn(x, z, context.heightAccessor(), context.randomState());
                var ground = column.getBlock(surface - 1);
                if (ground.isAir() || !ground.getFluidState().isEmpty() || !ground.blocksMotion()) { return false; }
                minimum = Math.min(minimum, surface);
                maximum = Math.max(maximum, surface);
                if (maximum - minimum > maxSlope) { return false; }
            }
        }
        return true;
    }

    @Override
    public StructureType<?> type() { return ArcadeWorldgen.ARCADE.get(); }
}
