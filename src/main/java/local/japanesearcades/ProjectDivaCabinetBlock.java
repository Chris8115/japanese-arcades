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
import net.minecraft.world.phys.Vec3;
import net.minecraft.world.phys.shapes.CollisionContext;
import net.minecraft.world.phys.shapes.Shapes;
import net.minecraft.world.phys.shapes.VoxelShape;

/** Raked display and four-button deck with the shared saved jukebox behavior. */
public final class ProjectDivaCabinetBlock extends NostalgiaCabinetBlock {
    public static final MapCodec<ProjectDivaCabinetBlock> CODEC = simpleCodec(ProjectDivaCabinetBlock::new);
    private static final Map<Direction, VoxelShape> BASE_SHAPES = createBaseShapes();

    public ProjectDivaCabinetBlock(Properties properties) { super(properties); }

    @Override
    protected MapCodec<? extends HorizontalDirectionalBlock> codec() { return CODEC; }

    @Override
    protected Vec3 discEjectionPosition(BlockPos pos, BlockState state) {
        Direction facing = state.getValue(FACING);
        return Vec3.atCenterOf(pos).add(facing.getStepX() * 1.16, .35, facing.getStepZ() * 1.16);
    }

    @Override
    protected VoxelShape getShape(BlockState state, BlockGetter level, BlockPos pos, CollisionContext context) {
        Direction facing = state.getValue(FACING);
        return switch (state.getValue(PART)) {
            case BASE -> BASE_SHAPES.get(facing);
            case CONSOLE -> rotatedBox(facing, -1.3, -7.95, 17.3, 15.5);
            case MARQUEE -> rotatedBox(facing, -2.2, 5.8, 18.2, 13.5);
        };
    }

    private static Map<Direction, VoxelShape> createBaseShapes() {
        Map<Direction, VoxelShape> shapes = new EnumMap<>(Direction.class);
        for (Direction facing : Direction.Plane.HORIZONTAL) {
            // The forward deck underside enters only the top .03 units of this section.
            VoxelShape ledge = switch (facing) {
                case EAST -> Block.box(.5, 15.97, -1.15, 23.95, 16, 17.15);
                case SOUTH -> Block.box(-1.15, 15.97, .5, 17.15, 16, 23.95);
                case WEST -> Block.box(-7.95, 15.97, -1.15, 15.5, 16, 17.15);
                default -> Block.box(-1.15, 15.97, -7.95, 17.15, 16, 15.5);
            };
            shapes.put(facing, Shapes.or(rotatedBox(facing, -.7, -2.5, 16.7, 15.5), ledge));
        }
        return shapes;
    }
}
