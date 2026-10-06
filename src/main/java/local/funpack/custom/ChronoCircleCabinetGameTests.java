package local.funpack.custom;

import static local.funpack.custom.NostalgiaCabinetGameTests.BASE;
import static local.funpack.custom.NostalgiaCabinetGameTests.cabinet;
import static local.funpack.custom.NostalgiaCabinetGameTests.insert;

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

/** Real placement/playback scenarios and the clock cabinet's broad floor platform. */
@GameTestHolder(FunPackCustom.MOD_ID)
@PrefixGameTestTemplate(false)
public final class ChronoCircleCabinetGameTests {
    @GameTest(template="nostalgia_test")
    public static void chronoCircleEverySectionPlaysAndEjectsBeforeSingleDropRemoval(GameTestHelper helper) {
        WaccaCabinetGameTests.everySectionPlaysAndEjectsBeforeSingleDropRemoval(helper,
            FunPackCustom.CHRONO_CIRCLE_ITEM.get());
    }

    @GameTest(template="nostalgia_test")
    public static void chronoCircleSavedDiscPlacementRestoresPlaybackAndCanEject(GameTestHelper helper) {
        WaccaCabinetGameTests.savedDiscPlacementRestoresPlaybackAndCanEject(helper,
            FunPackCustom.CHRONO_CIRCLE_ITEM.get());
    }

    @GameTest(template="nostalgia_test")
    public static void chronoCircleCreativeRemovalLeavesAdjacentProjectDivaPlaying(GameTestHelper helper) {
        SoundVoltexCabinetGameTests.creativeRemovalLeavesNeighborPlaying(helper,
            FunPackCustom.CHRONO_CIRCLE_ITEM.get(), FunPackCustom.PROJECT_DIVA_ITEM.get());
    }

    @GameTest(template="nostalgia_test")
    public static void chronoCircleClockPlatformAndDiscClearanceWorkInEveryFacing(GameTestHelper helper) {
        var player = cabinet(helper, GameType.SURVIVAL, FunPackCustom.CHRONO_CIRCLE_ITEM.get());
        var base = helper.absolutePos(BASE);
        for (Direction facing : Direction.Plane.HORIZONTAL) {
            // Keep all three sections intact while rotating the placed cabinet.
            for (int section=0; section<3; section++) {
                var pos = base.above(section);
                helper.getLevel().setBlock(pos, helper.getLevel().getBlockState(pos)
                    .setValue(NostalgiaCabinetBlock.FACING, facing), 18);
            }
            Vec3 front = new Vec3(facing.getStepX(), 0, facing.getStepZ());
            Direction side = facing.getClockWise();
            Vec3 sideways = new Vec3(side.getStepX(), 0, side.getStepZ());
            var consolePos = base.above();
            Vec3 consoleCenter = Vec3.atCenterOf(consolePos);
            var console = helper.getLevel().getBlockState(consolePos).getShape(helper.getLevel(), consolePos);
            var frontHit = console.clip(consoleCenter.add(front.scale(2)), consoleCenter, consolePos);
            helper.assertTrue(frontHit != null && frontHit.getDirection() == facing
                    && frontHit.getLocation().subtract(consoleCenter).dot(front) > .89,
                "Selection does not cover the forward clock controls");
            var sideHit = console.clip(consoleCenter.add(sideways.scale(2)), consoleCenter, consolePos);
            helper.assertTrue(sideHit != null && sideHit.getDirection() == side
                    && sideHit.getLocation().subtract(consoleCenter).dot(sideways) > .65,
                "Selection does not cover the clock face's side overhang");
            var upperPos = base.above(2);
            Vec3 upperCenter = Vec3.atCenterOf(upperPos);
            var upper = helper.getLevel().getBlockState(upperPos).getShape(helper.getLevel(), upperPos);
            var upperHit = upper.clip(upperCenter.add(sideways.scale(2)), upperCenter, upperPos);
            helper.assertTrue(upperHit != null && upperHit.getDirection() == side
                    && upperHit.getLocation().subtract(upperCenter).dot(sideways) > .65,
                "The character hood lies outside selection bounds");

            var lower = helper.getBlockState(BASE).getCollisionShape(helper.getLevel(), base);
            Vec3 lowerClock = Vec3.atCenterOf(base).add(0,.49,0);
            var lowerClockHit = lower.clip(lowerClock.add(sideways.scale(2)), lowerClock, base);
            helper.assertTrue(lowerClockHit != null && lowerClockHit.getDirection() == side
                    && lowerClockHit.getLocation().subtract(lowerClock).dot(sideways) > .59,
                "The reclined clock's lower edge is missing collision at the section boundary");
            Vec3 abovePlatform = Vec3.atCenterOf(base).add(front.scale(1.15));
            for (double offset : new double[] {-.55, 0, .55}) {
                Vec3 point = abovePlatform.add(sideways.scale(offset));
                var hit = lower.clip(point, point.add(0,-1,0), base);
                helper.assertTrue(hit != null && hit.getDirection() == Direction.UP
                        && hit.getLocation().y < base.getY()+.12,
                    "The broad floor platform is missing low collision");
            }
            helper.assertTrue(lower.clip(abovePlatform.add(front), abovePlatform, base) == null,
                "Invisible collision fills the space above the low floor platform");

            insert(helper, player, BASE.above());
            player.setItemInHand(InteractionHand.MAIN_HAND, ItemStack.EMPTY);
            helper.useBlock(BASE.above(2), player);
            var drops = helper.getEntities(EntityType.ITEM, BASE, 3);
            helper.assertTrue(drops.size() == 1 && drops.getFirst().getItem().is(Items.MUSIC_DISC_13),
                "Chrono Circle did not eject exactly one disc");
            var disc = drops.getFirst();
            for (int section=0; section<3; section++) {
                var pos = base.above(section);
                for (var box : helper.getLevel().getBlockState(pos).getCollisionShape(helper.getLevel(), pos).toAabbs()) {
                    helper.assertFalse(box.move(pos.getX(), pos.getY(), pos.getZ()).intersects(disc.getBoundingBox()),
                        "A newly ejected disc intersects Chrono Circle collision facing " + facing);
                }
            }
            helper.assertTrue(helper.getLevel().noCollision(disc, disc.getBoundingBox()),
                "World collision obstructs the ejected disc");
            disc.discard();
        }
        helper.succeed();
    }
}
