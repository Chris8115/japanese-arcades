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
import net.minecraft.world.phys.shapes.CollisionContext;
import net.minecraft.world.phys.shapes.Shapes;
import net.minecraft.world.phys.shapes.VoxelShape;

/** Compact pedestal, raked 4-by-4 control deck and cube topper with shared jukebox behavior. */
public final class JubeatCabinetBlock extends NostalgiaCabinetBlock {
    public static final MapCodec<JubeatCabinetBlock> CODEC = simpleCodec(JubeatCabinetBlock::new);
    private static final Map<Part, Map<Direction, VoxelShape>> SHAPES = createShapes();

    public JubeatCabinetBlock(Properties properties) { super(properties); }

    @Override
    protected MapCodec<? extends HorizontalDirectionalBlock> codec() { return CODEC; }

    @Override
    protected VoxelShape getShape(BlockState state, BlockGetter level, BlockPos pos, CollisionContext context) {
        return SHAPES.get(state.getValue(PART)).get(state.getValue(FACING));
    }

    private static Map<Part, Map<Direction, VoxelShape>> createShapes() {
        Map<Part, Map<Direction, VoxelShape>> shapes = new EnumMap<>(Part.class);
        for (Part part : Part.values()) {
            Map<Direction, VoxelShape> rotations = new EnumMap<>(Direction.class);
            for (Direction facing : Direction.Plane.HORIZONTAL) {
                VoxelShape shape = switch (part) {
                    case BASE -> Shapes.or(
                        box(facing, .55, 0, .55, 15.45, .8, 15.15),
                        box(facing, .6, .65, 2.15, 1.32, 1.05, 14.7),
                        box(facing, 14.68, .65, 2.15, 15.4, 1.05, 14.7),
                        box(facing, 3.3, .8, 8.6, 12.7, 14, 13.4),
                        box(facing, 3.3, 14, 10.5, 12.7, 15.85, 13.4),
                        box(facing, 2.8, 1.15, 1.4, 13.2, 10.95, 8.5),
                        box(facing, 3.1, 1, 1.8, 3.35, 11.15, 9.1),
                        box(facing, 12.65, 1, 1.8, 12.9, 11.15, 9.1),
                        box(facing, 3, 11.308, 5.901, 13, 12.5, 8.438),
                        box(facing, 3, 12.5, 4.851, 13, 14, 10.58),
                        box(facing, 3, 14, 3.45, 13, 16, 13.436));
                    // The control housing is one rigid 10-unit cube, including its rotated underside.
                    case CONSOLE -> Shapes.or(
                        box(facing, 3, 0, 2.4, 13, 1.5, 14.928),
                        box(facing, 3, 1.5, 1, 13, 3.5, 14.609),
                        box(facing, 3, 3.5, 1, 13, 5.5, 13.208),
                        box(facing, 3, 5.5, 3.856, 13, 7.5, 11.808),
                        box(facing, 3, 7.5, 6.712, 13, 9.236, 10.407),
                        box(facing, 3.1, 8.99, 9.153, 12.9, 10, 10.212),
                        box(facing, 3.1, 10, 9.524, 12.9, 11, 10.837),
                        box(facing, 3.1, 11, 10.148, 12.9, 11.8, 11.172),
                        box(facing, 3.45, 11.8, 10.9, 12.55, 13.45, 11.3),
                        box(facing, 3.8, 11.65, 11.8, 12.2, 13.55, 13.1),
                        box(facing, .65, 11.4, 10.05, 3.3, 14.15, 13.4),
                        box(facing, 12.7, 11.4, 10.05, 15.35, 14.15, 13.4),
                        box(facing, 1.1, 11.8, 11.65, 14.9, 13.3, 13.4),
                        box(facing, 5.2, 0, 12.1, 10.8, 14, 13.4),
                        box(facing, 6.4, 13.1, 10.5, 9.6, 16, 13),
                        box(facing, 3.5, 14.662, 6.699, 12.5, 16, 13.276));
                    // Horizontal slices follow the cube's 12-degree forward pitch about (8,36,10.45).
                    case MARQUEE -> Shapes.or(
                        box(facing, 3.5, 0, 6.274, 12.5, 2, 15.788),
                        box(facing, 3.5, 2, 5.849, 12.5, 4, 15.476),
                        box(facing, 3.5, 4, 5.424, 12.5, 6, 15.051),
                        box(facing, 3.5, 6, 5.112, 12.5, 8, 14.626),
                        box(facing, 3.5, 8, 7.624, 12.5, 9.338, 14.201));
                };
                rotations.put(facing, shape.optimize());
            }
            shapes.put(part, rotations);
        }
        return shapes;
    }

    private static VoxelShape box(Direction facing, double x1, double y1, double z1,
            double x2, double y2, double z2) {
        return switch (facing) {
            case EAST -> Block.box(16-z2, y1, x1, 16-z1, y2, x2);
            case SOUTH -> Block.box(16-x2, y1, 16-z2, 16-x1, y2, 16-z1);
            case WEST -> Block.box(z1, y1, 16-x2, z2, y2, 16-x1);
            default -> Block.box(x1, y1, z1, x2, y2, z2);
        };
    }
}
