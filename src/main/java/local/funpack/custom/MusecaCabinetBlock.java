package local.funpack.custom;

import com.mojang.serialization.MapCodec;
import java.util.EnumMap;
import java.util.Map;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.world.level.BlockGetter;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.HorizontalDirectionalBlock;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.Vec3;
import net.minecraft.world.phys.shapes.CollisionContext;
import net.minecraft.world.phys.shapes.Shapes;
import net.minecraft.world.phys.shapes.VoxelShape;

/** Broad spinner deck and low projecting pedal, sharing the saved jukebox behavior. */
public final class MusecaCabinetBlock extends NostalgiaCabinetBlock {
    public static final MapCodec<MusecaCabinetBlock> CODEC = simpleCodec(MusecaCabinetBlock::new);
    private static final Map<Direction, VoxelShape> BASE_SHAPES = createBaseShapes();

    public MusecaCabinetBlock(Properties properties) { super(properties); }

    @Override
    protected MapCodec<? extends HorizontalDirectionalBlock> codec() { return CODEC; }

    @Override
    protected Vec3 discEjectionPosition(BlockPos pos, BlockState state) {
        Direction facing = state.getValue(FACING);
        return Vec3.atCenterOf(pos).add(facing.getStepX() * 1.1, .35, facing.getStepZ() * 1.1);
    }

    @Override
    protected VoxelShape getShape(BlockState state, BlockGetter level, BlockPos pos, CollisionContext context) {
        Direction facing = state.getValue(FACING);
        return switch (state.getValue(PART)) {
            case BASE -> BASE_SHAPES.get(facing);
            case CONSOLE -> rotatedBox(facing, -2.8, -7.6, 18.8, 16);
            case MARQUEE -> rotatedBox(facing, -2.6, 8.1, 18, 16.2);
        };
    }

    private static Map<Direction, VoxelShape> createBaseShapes() {
        Map<Direction, VoxelShape> shapes = new EnumMap<>(Direction.class);
        for (Direction facing : Direction.Plane.HORIZONTAL) {
            shapes.put(facing, Shapes.or(rotatedBox(facing, -.6, -7.05, 16.6, 15.5), pedalShape(facing)));
        }
        return shapes;
    }

    private static VoxelShape pedalShape(Direction facing) {
        return switch (facing) {
            case EAST -> Block.box(22.8, 0, 4, 27.95, 2.3, 12);
            case SOUTH -> Block.box(4, 0, 22.8, 12, 2.3, 27.95);
            case WEST -> Block.box(-11.95, 0, 4, -6.8, 2.3, 12);
            default -> Block.box(4, 0, -11.95, 12, 2.3, -6.8);
        };
    }
}
