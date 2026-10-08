package local.japanesearcades;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import net.minecraft.core.Direction;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.shapes.ArrayVoxelShape;
import net.minecraft.world.phys.shapes.BitSetDiscreteVoxelShape;
import net.minecraft.world.phys.shapes.Shapes;
import net.minecraft.world.phys.shapes.VoxelShape;

/** An immutable cabinet shape whose outline and raycast boxes are computed only once. */
final class CachedCabinetShape extends ArrayVoxelShape {
    private final List<AABB> boxes;
    private final Edge[] edges;

    static VoxelShape of(VoxelShape source) {
        double[] xs = source.getCoords(Direction.Axis.X).toDoubleArray();
        double[] ys = source.getCoords(Direction.Axis.Y).toDoubleArray();
        double[] zs = source.getCoords(Direction.Axis.Z).toDoubleArray();
        var boxes = List.copyOf(source.toAabbs());
        var edges = new ArrayList<Edge>();
        source.forAllEdges((x0, y0, z0, x1, y1, z1) -> edges.add(new Edge(x0, y0, z0, x1, y1, z1)));

        // Retain every original coordinate and occupied cell, so vanilla collision,
        // inside-ray handling, clipping, and face shapes keep exactly the same geometry.
        var cells = new BitSetDiscreteVoxelShape(xs.length - 1, ys.length - 1, zs.length - 1);
        for (var box : boxes) {
            int x0 = Arrays.binarySearch(xs, box.minX), x1 = Arrays.binarySearch(xs, box.maxX);
            int y0 = Arrays.binarySearch(ys, box.minY), y1 = Arrays.binarySearch(ys, box.maxY);
            int z0 = Arrays.binarySearch(zs, box.minZ), z1 = Arrays.binarySearch(zs, box.maxZ);
            for (int x = x0; x < x1; x++) {
                for (int y = y0; y < y1; y++) {
                    for (int z = z0; z < z1; z++) { cells.fill(x, y, z); }
                }
            }
        }
        return new CachedCabinetShape(cells, xs, ys, zs, boxes, edges.toArray(Edge[]::new));
    }

    private CachedCabinetShape(BitSetDiscreteVoxelShape cells, double[] xs, double[] ys, double[] zs,
            List<AABB> boxes, Edge[] edges) {
        super(cells, xs, ys, zs);
        this.boxes = boxes;
        this.edges = edges;
    }

    @Override
    public void forAllEdges(Shapes.DoubleLineConsumer action) {
        for (var edge : edges) { action.consume(edge.x0, edge.y0, edge.z0, edge.x1, edge.y1, edge.z1); }
    }

    @Override
    public void forAllBoxes(Shapes.DoubleLineConsumer action) {
        for (var box : boxes) { action.consume(box.minX, box.minY, box.minZ, box.maxX, box.maxY, box.maxZ); }
    }

    @Override
    public List<AABB> toAabbs() {
        // Preserve vanilla's mutable result without exposing the retained geometry.
        return new ArrayList<>(boxes);
    }

    private record Edge(double x0, double y0, double z0, double x1, double y1, double z1) {}
}
