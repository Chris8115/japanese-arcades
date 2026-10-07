package local.funpack.custom;

import com.mojang.serialization.MapCodec;
import java.util.EnumMap;
import java.util.Map;
import javax.annotation.Nullable;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.world.item.context.BlockPlaceContext;
import net.minecraft.world.level.BlockGetter;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.HorizontalDirectionalBlock;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.Vec3;
import net.minecraft.world.phys.shapes.CollisionContext;
import net.minecraft.world.phys.shapes.Shapes;
import net.minecraft.world.phys.shapes.VoxelShape;

/** Sloping circular controls and a round illuminated header with one shared disc inventory. */
public final class MusicDiverCabinetBlock extends NostalgiaCabinetBlock {
    public static final MapCodec<MusicDiverCabinetBlock> CODEC = simpleCodec(MusicDiverCabinetBlock::new);
    private static final Map<Part, Map<Direction, VoxelShape>> SHAPES = createShapes();

    public MusicDiverCabinetBlock(Properties properties) { super(properties); }

    @Override
    protected MapCodec<? extends HorizontalDirectionalBlock> codec() { return CODEC; }

    @Nullable
    @Override
    public BlockState getStateForPlacement(BlockPlaceContext context) {
        BlockState base = super.getStateForPlacement(context);
        if (base == null) { return null; }
        for (Part part : Part.values()) {
            if (!context.getLevel().isUnobstructed(base.setValue(PART, part),
                    context.getClickedPos().above(part.ordinal()), CollisionContext.empty())) {
                return null;
            }
        }
        return base;
    }

    @Override
    protected Vec3 discEjectionPosition(BlockPos pos, BlockState state) {
        Direction facing = state.getValue(FACING);
        return Vec3.atCenterOf(pos).add(facing.getStepX() * 1.05, .35, facing.getStepZ() * 1.05);
    }

    @Override
    protected VoxelShape getShape(BlockState state, BlockGetter level, BlockPos pos, CollisionContext context) {
        return SHAPES.get(state.getValue(PART)).get(state.getValue(FACING));
    }

    private static Map<Part, Map<Direction, VoxelShape>> createShapes() {
        // Component envelopes keep the sloping front and circular header recognizable.
        // All twelve part/facing shapes are assembled once, not while aiming at the cabinet.
        double[][] volumes = {
            {.20, 0, .01, 15.80, 1.41, 15.75},
            {.15, 1.39, -.73, 15.85, 13.61, 15.93},
            {-.94, 13.59, -1.39, 16.94, 16, 15.93},
            {-1.15, 15.99, -2.08, 17.15, 19, 15.81},
            {-1.06, 19, -.02, 17.06, 22, 15.81},
            {-1.02, 22, 3.41, 17.02, 25, 15.81},
            {-.84, 25, 6.70, 16.84, 28, 15.75},
            {-.72, 28, 10.03, 16.72, 32, 15.75},
            {1.04, 32, 15.20, 14.96, 36.60, 15.55},
            // Separate front holster and reader keep the surrounding foot space open.
            {14.22, 5.06, -2.27, 16.72, 18.41, -.66},
            {3.92, 13.60, -1.39, 14.10, 16.22, -.44},
            // Five bands approximate the large round topper and its toothed backing.
            {1.58, 27.68, 14.22, 14.42, 30, 16},
            {-.89, 30, 14.21, 16.89, 34, 16},
            {-2.04, 34, 14.10, 18.04, 42, 16},
            {-.89, 42, 14.21, 16.89, 45, 16},
            {1.47, 45, 14.22, 14.53, 47.76, 16},
            {-1.95, 28.31, 13.05, 1.77, 33.04, 15.94},
            {14.23, 28.31, 13.05, 17.95, 33.04, 15.94}
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
