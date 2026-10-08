package local.japanesearcades;

import com.mojang.logging.LogUtils;
import java.util.ArrayList;
import java.util.IdentityHashMap;
import java.util.List;
import java.util.function.Function;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.gametest.framework.GameTest;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.BlockHitResult;
import net.minecraft.world.phys.Vec3;
import net.minecraft.world.phys.shapes.BooleanOp;
import net.minecraft.world.phys.shapes.CollisionContext;
import net.minecraft.world.phys.shapes.Shapes;
import net.minecraft.world.phys.shapes.VoxelShape;
import net.neoforged.neoforge.gametest.GameTestHolder;
import net.neoforged.neoforge.gametest.PrefixGameTestTemplate;

/** Compare the original geometry builder with the shape used by runtime collision and targeting. */
@GameTestHolder(JapaneseArcades.MOD_ID)
@PrefixGameTestTemplate(false)
public final class CabinetShapeCacheGameTests {
    @GameTest(template = "nostalgia_test")
    public static void ddrCachesEveryRailStageAndCabinetShapeWithoutChangingGeometry(GameTestHelper helper) {
        verify(helper, JapaneseArcades.DDR_SUPERNOVA.get(), state -> DdrCabinetBlock.buildShape(
            state.getValue(DdrCabinetBlock.FACING), state.getValue(DdrCabinetBlock.SIDE) == DdrCabinetBlock.Side.PRIMARY,
            state.getValue(DdrCabinetBlock.SECTION)), 48);
    }

    @GameTest(template = "nostalgia_test")
    public static void initialDCachesEverySeatFootwellAndCabinetShapeWithoutChangingGeometry(GameTestHelper helper) {
        verify(helper, JapaneseArcades.INITIAL_D.get(), state -> InitialDCabinetBlock.buildShape(
            state.getValue(InitialDCabinetBlock.FACING), state.getValue(InitialDCabinetBlock.SECTION)), 28);
    }

    @GameTest(template = "nostalgia_test")
    public static void maimaiCachesBothSidesAndFloorOverhangsWithoutChangingGeometry(GameTestHelper helper) {
        verify(helper, JapaneseArcades.MAIMAI.get(), state -> MaimaiCabinetBlock.buildShape(
            state.getValue(MaimaiCabinetBlock.FACING), state.getValue(MaimaiCabinetBlock.SIDE) == MaimaiCabinetBlock.Side.PRIMARY,
            state.getValue(MaimaiCabinetBlock.PART)), 24);
    }

    private static void verify(GameTestHelper helper, NostalgiaCabinetBlock block,
            Function<BlockState, VoxelShape> original, int physicalShapes) {
        var seen = new IdentityHashMap<VoxelShape, VoxelShape>();
        BlockPos pos = helper.absolutePos(new BlockPos(3, 1, 3));
        int boxCount = 0, edgeCount = 0;
        // Include inherited jukebox/part flags: non-geometric states must reuse the same objects.
        for (BlockState state : block.getStateDefinition().getPossibleStates()) {
            VoxelShape cached = block.getShape(state, helper.getLevel(), pos, CollisionContext.empty());
            helper.assertTrue(cached instanceof CachedCabinetShape, "Runtime targeting did not use the cached shape: " + state);
            VoxelShape raw = seen.get(cached);
            if (raw == null) {
                raw = original.apply(state);
                seen.put(cached, raw);
                assertGeometry(helper, raw, cached, state.toString());
                boxCount += raw.toAabbs().size();
                edgeCount += edges(raw).size();
                for (int repeat = 0; repeat < 64; repeat++) {
                    helper.assertTrue(block.getShape(state, helper.getLevel(), pos, CollisionContext.empty()) == cached,
                        "Repeated targeting rebuilt a shape instead of reusing it: " + state);
                }
            } else {
                helper.assertFalse(Shapes.joinIsNotEmpty(original.apply(state), raw, BooleanOp.NOT_SAME),
                    "Two different physical geometries aliased the same cache key: " + state);
            }
            helper.assertTrue(state.getShape(helper.getLevel(), pos) == cached,
                "BlockState targeting bypassed the retained shape: " + state);
            helper.assertFalse(Shapes.joinIsNotEmpty(raw, state.getCollisionShape(helper.getLevel(), pos), BooleanOp.NOT_SAME),
                "Runtime collision no longer matches the original targeting geometry: " + state);
        }
        helper.assertTrue(seen.size() == physicalShapes, "Non-geometric state changes duplicated shape caches or physical combinations were lost");
        LogUtils.getLogger().info("Cabinet shape cache check: {} states={}, physical shapes={}, boxes={}, edges={}, identical geometry and reused instances",
            block, block.getStateDefinition().getPossibleStates().size(), seen.size(), boxCount, edgeCount);
        helper.succeed();
    }

    private static void assertGeometry(GameTestHelper helper, VoxelShape raw, VoxelShape cached, String label) {
        helper.assertFalse(Shapes.joinIsNotEmpty(raw, cached, BooleanOp.NOT_SAME), "Occupied cells changed: " + label);
        helper.assertTrue(raw.bounds().equals(cached.bounds()), "Bounds changed: " + label);
        List<AABB> originalBoxes = raw.toAabbs();
        helper.assertTrue(originalBoxes.equals(cached.toAabbs()) && boxes(raw).equals(boxes(cached)), "Collision/raycast boxes changed: " + label);
        helper.assertTrue(edges(raw).equals(edges(cached)), "Visible selection edges changed: " + label);
        var mutableResult = cached.toAabbs();
        mutableResult.clear();
        helper.assertTrue(cached.toAabbs().equals(originalBoxes), "Caller mutation damaged retained boxes: " + label);
        for (Direction direction : Direction.values()) {
            helper.assertFalse(Shapes.joinIsNotEmpty(raw.getFaceShape(direction), cached.getFaceShape(direction), BooleanOp.NOT_SAME),
                "Collision face changed for " + direction + ": " + label);
            Vec3 step = Vec3.atLowerCornerOf(direction.getNormal());
            for (AABB box : originalBoxes) {
                Vec3 center = box.getCenter();
                assertHit(helper, raw.clip(center.add(step.scale(4)), center.subtract(step.scale(4)), BlockPos.ZERO),
                    cached.clip(center.add(step.scale(4)), center.subtract(step.scale(4)), BlockPos.ZERO), label);
                assertHit(helper, raw.clip(center, center.add(step.scale(4)), BlockPos.ZERO),
                    cached.clip(center, center.add(step.scale(4)), BlockPos.ZERO), label);
            }
        }
    }

    private static List<AABB> boxes(VoxelShape shape) {
        var result = new ArrayList<AABB>();
        shape.forAllBoxes((x0, y0, z0, x1, y1, z1) -> result.add(new AABB(x0, y0, z0, x1, y1, z1)));
        return result;
    }

    private static List<Edge> edges(VoxelShape shape) {
        var result = new ArrayList<Edge>();
        shape.forAllEdges((x0, y0, z0, x1, y1, z1) -> result.add(new Edge(x0, y0, z0, x1, y1, z1)));
        return result;
    }

    private static void assertHit(GameTestHelper helper, BlockHitResult expected, BlockHitResult actual, String label) {
        if (expected == null || actual == null) {
            helper.assertTrue(expected == actual, "Ray changed between hit and miss: " + label);
            return;
        }
        helper.assertTrue(expected.getLocation().distanceToSqr(actual.getLocation()) < 1e-20
            && expected.getDirection() == actual.getDirection() && expected.isInside() == actual.isInside(),
            "Ray hit position, normal, or inside state changed: " + label);
    }

    private record Edge(double x0, double y0, double z0, double x1, double y1, double z1) {}
}
