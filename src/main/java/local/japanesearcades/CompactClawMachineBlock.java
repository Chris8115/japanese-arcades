package local.japanesearcades;

import com.mojang.serialization.MapCodec;
import net.minecraft.world.level.block.HorizontalDirectionalBlock;
import net.minecraft.world.level.block.state.properties.IntegerProperty;

/** Eight connected cells with the same protected crane controller as the large cabinet. */
public final class CompactClawMachineBlock extends ClawMachineBlock {
    public static final MapCodec<CompactClawMachineBlock> CODEC = simpleCodec(CompactClawMachineBlock::new);
    public static final IntegerProperty PART = IntegerProperty.create("part", 0, 7);
    public CompactClawMachineBlock(Properties properties) { super(properties); }
    @Override protected MapCodec<? extends HorizontalDirectionalBlock> codec() { return CODEC; }
    @Override public ClawMachineLayout layout() { return ClawMachineLayout.COMPACT; }
    @Override public IntegerProperty partProperty() { return PART; }
}
