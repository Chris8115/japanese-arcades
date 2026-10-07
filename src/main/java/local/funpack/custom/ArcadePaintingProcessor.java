package local.funpack.custom;

import com.mojang.serialization.MapCodec;
import net.minecraft.core.BlockPos;
import net.minecraft.world.level.LevelReader;
import net.minecraft.world.level.levelgen.structure.templatesystem.StructurePlaceSettings;
import net.minecraft.world.level.levelgen.structure.templatesystem.StructureProcessor;
import net.minecraft.world.level.levelgen.structure.templatesystem.StructureProcessorType;
import net.minecraft.world.level.levelgen.structure.templatesystem.StructureTemplate;
import net.minecraft.world.phys.Vec3;

/** Keeps vanilla paintings attached to their transformed template anchor, including far from spawn. */
public final class ArcadePaintingProcessor extends StructureProcessor {
    public static final ArcadePaintingProcessor INSTANCE = new ArcadePaintingProcessor();
    public static final MapCodec<ArcadePaintingProcessor> CODEC = MapCodec.unit(() -> INSTANCE);

    private ArcadePaintingProcessor() {}

    @Override
    public StructureTemplate.StructureEntityInfo processEntity(LevelReader world, BlockPos origin,
            StructureTemplate.StructureEntityInfo raw, StructureTemplate.StructureEntityInfo transformed,
            StructurePlaceSettings settings, StructureTemplate template) {
        if (!transformed.nbt.getString("id").equals("minecraft:painting")) { return transformed; }
        var tag = transformed.nbt.copy();
        BlockPos anchor = transformed.blockPos;
        // StructureTemplate transforms blockPos and Pos, but leaves these native attachment fields untouched.
        tag.putInt("TileX", anchor.getX());
        tag.putInt("TileY", anchor.getY());
        tag.putInt("TileZ", anchor.getZ());
        // Native moveTo floors Pos back into the attachment block. Actual painting centers shift for even
        // widths/heights, so use the anchor center and let HangingEntity rebuild its final display bounds.
        // Facing is deliberately left local: native placement rotates/mirrors the entity exactly once.
        return new StructureTemplate.StructureEntityInfo(Vec3.atCenterOf(anchor), anchor, tag);
    }

    @Override
    protected StructureProcessorType<?> getType() { return ArcadeWorldgen.PAINTING_ANCHOR.get(); }
}
