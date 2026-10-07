package local.japanesearcades;

import com.mojang.serialization.MapCodec;
import net.minecraft.core.BlockPos;
import net.minecraft.world.level.BlockGetter;
import net.minecraft.world.level.block.HorizontalDirectionalBlock;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.shapes.CollisionContext;
import net.minecraft.world.phys.shapes.VoxelShape;

/** Valkyrie's broad control deck and speaker wings overhang its one-block placement column. */
public final class SoundVoltexCabinetBlock extends NostalgiaCabinetBlock {
    public static final MapCodec<SoundVoltexCabinetBlock> CODEC = simpleCodec(SoundVoltexCabinetBlock::new);

    public SoundVoltexCabinetBlock(Properties properties) { super(properties); }

    @Override
    protected MapCodec<? extends HorizontalDirectionalBlock> codec() { return CODEC; }

    @Override
    protected VoxelShape getShape(BlockState state, BlockGetter level, BlockPos pos, CollisionContext context) {
        return switch (state.getValue(PART)) {
            case BASE -> rotatedBox(state.getValue(FACING), -.75, 3.4, 16.75, 15.8);
            case CONSOLE -> rotatedBox(state.getValue(FACING), -1.5, 0, 17.5, 15.8);
            case MARQUEE -> rotatedBox(state.getValue(FACING), -3, 4.6, 19, 15.8);
        };
    }
}
