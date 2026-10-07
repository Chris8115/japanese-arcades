package local.japanesearcades;

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

/** Older NEMSYS chassis with a narrow monitor, projecting controls and four angular side wings. */
public final class SoundVoltexNemsysCabinetBlock extends NostalgiaCabinetBlock {
    public static final MapCodec<SoundVoltexNemsysCabinetBlock> CODEC = simpleCodec(SoundVoltexNemsysCabinetBlock::new);
    private static final Map<Part, Map<Direction, VoxelShape>> SHAPES = createShapes();

    public SoundVoltexNemsysCabinetBlock(Properties properties) { super(properties); }

    @Override
    protected MapCodec<? extends HorizontalDirectionalBlock> codec() { return CODEC; }

    @Override
    protected VoxelShape getShape(BlockState state, BlockGetter level, BlockPos pos, CollisionContext context) {
        return SHAPES.get(state.getValue(PART)).get(state.getValue(FACING));
    }

    private static Map<Part, Map<Direction, VoxelShape>> createShapes() {
        // Static coarse component volumes leave the space in front of the recessed
        // monitor open. Rotation and outline construction happen only at startup.
        double[][] volumes = {
            {-.6, 0, 1.47, 16.6, 1.4, 15.5},
            {.2, 1, 1.97, 15.8, 15.18, 15.2},
            {-2, 14.6, -1.96, 18, 17.43, 9.2},
            {.3, 16.8, 3.5, 15.7, 17.9, 5.75},
            {5.9, 17.06, 4.74, 10.1, 18.18, 7.37},
            {2.4, 18.35, 7.08, 13.6, 20.04, 7.7},
            {2.4, 15, 7.65, 13.6, 38.49, 14.7},
            {-3, 15.06, 3.97, 2.41, 29.3, 7.76},
            {13.59, 15.06, 3.97, 19, 29.3, 7.76},
            {-3, 28.3, 4.5, 2.4, 33.34, 9.44},
            {13.6, 28.3, 4.5, 19, 33.34, 9.44},
            {-3, 33.2, 5.59, 2.41, 44, 7.2},
            {13.59, 33.2, 5.59, 19, 44, 7.2},
            {.2, 38.62, 6.07, 15.8, 43.02, 8.02},
            {.08, 41.1, 7.768, 15.92, 47.43, 8.3}
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
