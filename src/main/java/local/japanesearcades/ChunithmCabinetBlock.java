package local.japanesearcades;

import com.mojang.serialization.MapCodec;
import net.minecraft.core.BlockPos;
import net.minecraft.world.level.BlockGetter;
import net.minecraft.world.level.block.HorizontalDirectionalBlock;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.shapes.CollisionContext;
import net.minecraft.world.phys.shapes.VoxelShape;

/** Chunithm's broad slider and upper enclosure share the standard three-part cabinet behavior. */
public final class ChunithmCabinetBlock extends NostalgiaCabinetBlock {
    public static final MapCodec<ChunithmCabinetBlock> CODEC = simpleCodec(ChunithmCabinetBlock::new);

    public ChunithmCabinetBlock(Properties properties) { super(properties); }

    @Override
    protected MapCodec<? extends HorizontalDirectionalBlock> codec() { return CODEC; }

    @Override
    protected VoxelShape getShape(BlockState state, BlockGetter level, BlockPos pos, CollisionContext context) {
        return state.getValue(PART) == Part.BASE
            ? rotatedBox(state.getValue(FACING), -.8, -.8, 16.8, 16)
            : rotatedBox(state.getValue(FACING), -1.8, -5.8, 17.8, 16);
    }
}
