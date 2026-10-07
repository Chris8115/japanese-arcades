package local.japanesearcades;

import static local.japanesearcades.NostalgiaCabinetGameTests.BASE;
import static local.japanesearcades.NostalgiaCabinetGameTests.cabinet;
import static local.japanesearcades.NostalgiaCabinetGameTests.insert;

import net.minecraft.core.Direction;
import net.minecraft.gametest.framework.GameTest;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.GameType;
import net.minecraft.world.phys.Vec3;
import net.neoforged.neoforge.gametest.GameTestHolder;
import net.neoforged.neoforge.gametest.PrefixGameTestTemplate;

/** Shared jukebox scenarios plus selection rays for the larger controller stand. */
@GameTestHolder(JapaneseArcades.MOD_ID)
@PrefixGameTestTemplate(false)
public final class GrooveCoasterCabinetGameTests {
    @GameTest(template="nostalgia_test")
    public static void grooveCoasterEverySectionPlaysAndEjectsBeforeSingleDropRemoval(GameTestHelper helper) {
        WaccaCabinetGameTests.everySectionPlaysAndEjectsBeforeSingleDropRemoval(helper,
            JapaneseArcades.GROOVE_COASTER_ITEM.get());
    }

    @GameTest(template="nostalgia_test")
    public static void grooveCoasterSavedDiscPlacementRestoresPlaybackAndCanEject(GameTestHelper helper) {
        WaccaCabinetGameTests.savedDiscPlacementRestoresPlaybackAndCanEject(helper,
            JapaneseArcades.GROOVE_COASTER_ITEM.get());
    }

    @GameTest(template="nostalgia_test")
    public static void grooveCoasterCreativeRemovalLeavesAdjacentChunithmPlaying(GameTestHelper helper) {
        SoundVoltexCabinetGameTests.creativeRemovalLeavesNeighborPlaying(helper,
            JapaneseArcades.GROOVE_COASTER_ITEM.get(), JapaneseArcades.CHUNITHM_ITEM.get());
    }

    @GameTest(template="nostalgia_test")
    public static void grooveCoasterWideDeepConsoleCanBeSelectedInEveryFacing(GameTestHelper helper) {
        cabinet(helper, GameType.SURVIVAL, JapaneseArcades.GROOVE_COASTER_ITEM.get());
        var pos = helper.absolutePos(BASE.above());
        Vec3 center = Vec3.atCenterOf(pos);
        for (Direction facing : Direction.Plane.HORIZONTAL) {
            var state = helper.getBlockState(BASE.above()).setValue(NostalgiaCabinetBlock.FACING, facing);
            var shape = state.getShape(helper.getLevel(), pos);
            for (Direction approach : new Direction[] {facing, facing.getClockWise()}) {
                Vec3 outward = new Vec3(approach.getStepX(), 0, approach.getStepZ());
                var hit = shape.clip(center.add(outward.scale(2)), center, pos);
                helper.assertTrue(hit != null, "Selection ray missed the large console facing " + facing);
                helper.assertTrue(hit.getDirection() == approach, "Selection hit the wrong side of the rotated console");
                double minimumReach = approach == facing ? 1.0 : .75;
                helper.assertTrue(hit.getLocation().subtract(center).dot(outward) > minimumReach,
                    "Selection bounds fail to cover the console's " + (approach == facing ? "front" : "side") + " overhang");
            }
            var marqueePos = helper.absolutePos(BASE.above(2));
            Vec3 marqueeCenter = Vec3.atCenterOf(marqueePos);
            var marquee = helper.getBlockState(BASE.above(2)).setValue(NostalgiaCabinetBlock.FACING, facing);
            Direction side = facing.getClockWise();
            Vec3 outward = new Vec3(side.getStepX(), 0, side.getStepZ());
            var hit = marquee.getShape(helper.getLevel(), marqueePos)
                .clip(marqueeCenter.add(outward.scale(2)), marqueeCenter, marqueePos);
            helper.assertTrue(hit != null && hit.getDirection() == side,
                "Selection ray missed the marquee's side overhang");
            helper.assertTrue(hit.getLocation().subtract(marqueeCenter).dot(outward) > .60,
                "The wide header's outer edge lies outside the marquee selection bounds");
        }
        helper.succeed();
    }

    @GameTest(template="nostalgia_test")
    public static void grooveCoasterOpenFootwellKeepsEjectedDiscsClearInEveryFacing(GameTestHelper helper) {
        var player = cabinet(helper, GameType.SURVIVAL, JapaneseArcades.GROOVE_COASTER_ITEM.get());
        var base = helper.absolutePos(BASE);
        Vec3 center = Vec3.atCenterOf(base);
        for (Direction facing : Direction.Plane.HORIZONTAL) {
            // Known-shape updates avoid tearing down the other sections mid-rotation.
            for (int section=0; section<3; section++) {
                var pos = base.above(section);
                helper.getLevel().setBlock(pos, helper.getLevel().getBlockState(pos)
                    .setValue(NostalgiaCabinetBlock.FACING, facing), 18);
            }
            var state = helper.getBlockState(BASE);
            Vec3 front = new Vec3(facing.getStepX(), 0, facing.getStepZ());
            var right = facing.getClockWise();
            Vec3 sideways = new Vec3(right.getStepX(), 0, right.getStepZ());
            var collision = state.getCollisionShape(helper.getLevel(), base);
            helper.assertTrue(collision.clip(center.add(front.scale(2)), center, base) == null,
                "The central legroom is blocked by invisible collision facing " + facing);
            helper.assertTrue(state.getShape(helper.getLevel(), base).clip(center.add(front.scale(2)), center, base) == null,
                "The selection outline closes the central legroom");
            for (int side : new int[] {-1, 1}) {
                Vec3 column = center.add(sideways.scale(side * .6));
                helper.assertTrue(collision.clip(column.add(front.scale(2)), column, base) != null,
                    "A front support column is missing collision");
            }
            var floorHit = collision.clip(center, center.add(0,-1,0), base);
            helper.assertTrue(floorHit != null && floorHit.getDirection() == Direction.UP,
                "The footwell floor is missing collision");

            insert(helper, player, BASE.above());
            player.setItemInHand(InteractionHand.MAIN_HAND, ItemStack.EMPTY);
            helper.useBlock(BASE.above(2), player);
            var drops = helper.getEntities(EntityType.ITEM, BASE, 3);
            helper.assertTrue(drops.size() == 1 && drops.getFirst().getItem().is(Items.MUSIC_DISC_13),
                "Ejection did not produce exactly one disc");
            var disc = drops.getFirst();
            for (int section=0; section<3; section++) {
                var pos = base.above(section);
                var shape = helper.getLevel().getBlockState(pos).getCollisionShape(helper.getLevel(), pos);
                for (var box : shape.toAabbs()) {
                    helper.assertFalse(box.move(pos.getX(), pos.getY(), pos.getZ()).intersects(disc.getBoundingBox()),
                        "The newly ejected disc intersects cabinet collision facing " + facing);
                }
            }
            helper.assertTrue(helper.getLevel().noCollision(disc, disc.getBoundingBox()),
                "The newly ejected disc is obstructed by world collision");
            disc.discard();
        }
        helper.succeed();
    }
}
