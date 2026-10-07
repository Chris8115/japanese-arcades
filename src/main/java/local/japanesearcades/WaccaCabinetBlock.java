package local.japanesearcades;

import com.mojang.serialization.MapCodec;
import net.minecraft.core.BlockPos;
import net.minecraft.world.level.BlockGetter;
import net.minecraft.world.level.block.HorizontalDirectionalBlock;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.shapes.CollisionContext;
import net.minecraft.world.phys.shapes.VoxelShape;

/** WACCA's circular touch enclosure overhangs its three-block placement column. */
public final class WaccaCabinetBlock extends NostalgiaCabinetBlock {
    public static final MapCodec<WaccaCabinetBlock> CODEC = simpleCodec(WaccaCabinetBlock::new);

    public WaccaCabinetBlock(Properties properties) { super(properties); }

    @Override
    protected MapCodec<? extends HorizontalDirectionalBlock> codec() { return CODEC; }

    @Override
    protected VoxelShape getShape(BlockState state, BlockGetter level, BlockPos pos, CollisionContext context) {
        return state.getValue(PART) == Part.BASE
            ? rotatedBox(state.getValue(FACING), -.75, 4, 16.75, 15.8)
            : rotatedBox(state.getValue(FACING), -3, .4, 19, 15.8);
    }
}
