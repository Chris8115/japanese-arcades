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

/** Broad clock controls and a low floor platform with the shared jukebox behavior. */
public final class ChronoCircleCabinetBlock extends NostalgiaCabinetBlock {
    public static final MapCodec<ChronoCircleCabinetBlock> CODEC = simpleCodec(ChronoCircleCabinetBlock::new);
    private static final Map<Direction, VoxelShape> BASE_SHAPES = createBaseShapes();

    public ChronoCircleCabinetBlock(Properties properties) { super(properties); }

    @Override
    protected MapCodec<? extends HorizontalDirectionalBlock> codec() { return CODEC; }

    @Override
    protected Vec3 discEjectionPosition(BlockPos pos, BlockState state) {
        Direction facing = state.getValue(FACING);
        return Vec3.atCenterOf(pos).add(facing.getStepX() * 1.15, .35, facing.getStepZ() * 1.15);
    }

    @Override
    protected VoxelShape getShape(BlockState state, BlockGetter level, BlockPos pos, CollisionContext context) {
        Direction facing = state.getValue(FACING);
        return switch (state.getValue(PART)) {
            case BASE -> BASE_SHAPES.get(facing);
            case CONSOLE -> rotatedBox(facing, -2.5, -6.4, 18.5, 15.5);
            case MARQUEE -> rotatedBox(facing, -2.5, -1.0, 18.5, 15.25);
        };
    }

    private static Map<Direction, VoxelShape> createBaseShapes() {
        Map<Direction, VoxelShape> shapes = new EnumMap<>(Direction.class);
        for (Direction facing : Direction.Plane.HORIZONTAL) {
            VoxelShape platform = switch (facing) {
                case EAST -> Block.box(17.5, 0, -2, 30.7, 1.45, 18);
                case SOUTH -> Block.box(-2, 0, 17.5, 18, 1.45, 30.7);
                case WEST -> Block.box(-14.7, 0, -2, -1.5, 1.45, 18);
                default -> Block.box(-2, 0, -14.7, 18, 1.45, -1.5);
            };
            // The reclined clock backing crosses the top of the base section.
            VoxelShape clockLedge = switch (facing) {
                case EAST -> Block.box(.5, 15.75, -1.5, 21.7, 16, 17.5);
                case SOUTH -> Block.box(-1.5, 15.75, .5, 17.5, 16, 21.7);
                case WEST -> Block.box(-5.7, 15.75, -1.5, 15.5, 16, 17.5);
                default -> Block.box(-1.5, 15.75, -5.7, 17.5, 16, 15.5);
            };
            shapes.put(facing, Shapes.or(rotatedBox(facing, -.7, -5.7, 16.7, 15.5),
                platform, clockLedge));
        }
        return shapes;
    }
}
