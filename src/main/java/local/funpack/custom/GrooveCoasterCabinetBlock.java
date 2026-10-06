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

/** Groove Coaster's broad, deep controller stand extends beyond its placement column. */
public final class GrooveCoasterCabinetBlock extends NostalgiaCabinetBlock {
    public static final MapCodec<GrooveCoasterCabinetBlock> CODEC = simpleCodec(GrooveCoasterCabinetBlock::new);
    private static final Map<Direction, VoxelShape> BASE_SHAPES = createBaseShapes();

    public GrooveCoasterCabinetBlock(Properties properties) { super(properties); }

    @Override
    protected MapCodec<? extends HorizontalDirectionalBlock> codec() { return CODEC; }

    @Override
    protected Vec3 discEjectionPosition(BlockPos pos, BlockState state) {
        Direction facing = state.getValue(FACING);
        // The full .25-block-tall item box must stay below the projecting console.
        return Vec3.atCenterOf(pos).add(facing.getStepX() * .9, .20, facing.getStepZ() * .9);
    }

    @Override
    protected VoxelShape getShape(BlockState state, BlockGetter level, BlockPos pos, CollisionContext context) {
        Direction facing = state.getValue(FACING);
        return switch (state.getValue(PART)) {
            case BASE -> BASE_SHAPES.get(facing);
            case CONSOLE -> rotatedBox(facing, -4.5, -10, 20.5, 17);
            case MARQUEE -> rotatedBox(facing, -1.9, 7, 17.9, 17);
        };
    }

    private static Map<Direction, VoxelShape> createBaseShapes() {
        Map<Direction, VoxelShape> shapes = new EnumMap<>(Direction.class);
        for (Direction facing : Direction.Plane.HORIZONTAL) {
            shapes.put(facing, Shapes.or(
                // Platform and feet, then the two separated controller columns.
                sectionBox(facing, -4, 0, -9.6, 20, 2.01, 16.9),
                sectionBox(facing, -3.5, 1.98, -9.05, 1.6, 12, 2.65),
                sectionBox(facing, 14.4, 1.98, -9.05, 19.5, 12, 2.65),
                sectionBox(facing, -3.3, 11.7, -9.3, 3.35, 16, 2.65),
                sectionBox(facing, 12.65, 11.7, -9.3, 19.3, 16, 2.65),
                // Rear monitor column and its low brace leave the middle open.
                sectionBox(facing, -.05, 1.98, 9.6, 16.05, 16, 16.9),
                sectionBox(facing, 1.65, 2.01, 7.6, 14.35, 3.5, 9.95)));
        }
        return shapes;
    }

    private static VoxelShape sectionBox(Direction facing, double minX, double minY, double minZ,
            double maxX, double maxY, double maxZ) {
        return switch (facing) {
            case EAST -> Block.box(16-maxZ, minY, minX, 16-minZ, maxY, maxX);
            case SOUTH -> Block.box(16-maxX, minY, 16-maxZ, 16-minX, maxY, 16-minZ);
            case WEST -> Block.box(minZ, minY, 16-maxX, maxZ, maxY, 16-minX);
            default -> Block.box(minX, minY, minZ, maxX, maxY, maxZ);
        };
    }
}
