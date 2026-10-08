package local.japanesearcades;

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

/** Nine-button pop'n music cabinet with one shared, persistent music-disc inventory. */
public final class PopnMusicCabinetBlock extends NostalgiaCabinetBlock {
    public static final MapCodec<PopnMusicCabinetBlock> CODEC = simpleCodec(PopnMusicCabinetBlock::new);
    private static final Map<Part, Map<Direction, VoxelShape>> SHAPES = createShapes();

    public PopnMusicCabinetBlock(Properties properties) { super(properties); }

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
        // Cached component envelopes follow the body, projecting deck and rounded header.
        // Selection never rebuilds the detailed OBJ geometry when a player aims at it.
        double[][] volumes = {
            {-.56, 0, .72, .24, .99, 1.52},
            {15.76, 0, .72, 16.56, .99, 1.52},
            {-.56, 0, 13.38, .24, .99, 14.18},
            {15.76, 0, 13.38, 16.56, .99, 14.18},
            {-.40, .37, .27, 16.40, 1.30, 14.7},
            {-.665, .95, -.10, 16.665, 16, 14.96},
            {.45, 8.1, -.21, 2.55, 14, -.05},
            {-2.7, 15.6, -3.1, 18.7, 18.15, 8.2},
            {-1.7, 16, 8.2, 17.7, 18, 15.3},
            {5.99, 17.51, 5.835, 12.71, 19.31, 6.42},
            // Four bands follow the backward slope instead of filling its open front.
            {-1.7, 18, 6.25, 17.7, 22, 15.3},
            {-1.7, 22, 7.45, 17.7, 26, 15.3},
            {-1.7, 26, 8.65, 17.7, 30, 15.3},
            {-1.7, 30, 9.18, 17.7, 32.8, 15.3},
            {-1.8, 32.7, 7.94, 17.8, 39.8, 14.6},
            {-.9, 39.8, 11.55, 16.9, 40.37, 14.6},
            {-1.55, 39.57, 9.865, 17.55, 40.63, 12.05},
            {1.5, 40.4, 11.39, 2, 44.5, 11.7},
            {14, 40.4, 11.39, 14.5, 44.5, 11.7},
            {-.8, 40.47, 10.79, 16.8, 47.8, 10.91}
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
