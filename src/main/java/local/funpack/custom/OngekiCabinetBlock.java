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

/** ONGEKI's forward light arch and recessed portrait monitor share the standard disc inventory. */
public final class OngekiCabinetBlock extends NostalgiaCabinetBlock {
    public static final MapCodec<OngekiCabinetBlock> CODEC = simpleCodec(OngekiCabinetBlock::new);
    private static final Map<Part, Map<Direction, VoxelShape>> SHAPES = createShapes();

    public OngekiCabinetBlock(Properties properties) { super(properties); }

    @Override
    protected MapCodec<? extends HorizontalDirectionalBlock> codec() { return CODEC; }

    @Override
    protected VoxelShape getShape(BlockState state, BlockGetter level, BlockPos pos, CollisionContext context) {
        return SHAPES.get(state.getValue(PART)).get(state.getValue(FACING));
    }

    private static Map<Part, Map<Direction, VoxelShape>> createShapes() {
        // A few chassis volumes cover the artwork; the empty space between the
        // arch and monitor remains empty. These twelve shapes are built only once.
        double[][] volumes = {
            {-1.25, 0, -1.12, 17.25, 1.18, 16},
            {-.3, 1.1, .55, 16.3, 17.1, 15.65},
            {-.3, 16.9, -1.01, 16.3, 19.45, 9.4},
            {-1.14, 17.2, -.64, .18, 46.02, 7.3},
            {15.82, 17.2, -.64, 17.14, 46.02, 7.3},
            {-1.8, 28.82, -.65, 1.6, 35.62, 6.15},
            {14.4, 28.82, -.65, 17.8, 35.62, 6.15},
            {1.45, 16.98, 9.145, 14.55, 38.6, 15.39},
            {-1.47, 43.65, .11, 17.47, 47.4, 7.16},
            {1.05, 39.98, 4.27, 14.95, 43.95, 4.92}
        };
        Map<Part, Map<Direction, VoxelShape>> shapes = new EnumMap<>(Part.class);
        for (Part part : Part.values()) {
            Map<Direction, VoxelShape> rotations = new EnumMap<>(Direction.class);
            double bottom = part.ordinal() * 16;
            for (Direction facing : Direction.Plane.HORIZONTAL) {
                VoxelShape shape = Shapes.empty();
                for (double[] volume : volumes) {
                    double y1 = Math.max(bottom, volume[1]);
                    double y2 = Math.min(bottom + 16, volume[4]);
                    if (y2 > y1) {
                        shape = Shapes.or(shape, box(facing, volume[0], y1 - bottom, volume[2],
                            volume[3], y2 - bottom, volume[5]));
                    }
                }
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
