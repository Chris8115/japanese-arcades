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

/** Exercises MUSECA's registrations, projecting deck/pedal, and clear disc ejection. */
@GameTestHolder(FunPackCustom.MOD_ID)
@PrefixGameTestTemplate(false)
public final class MusecaCabinetGameTests {
    @GameTest(template="nostalgia_test")
    public static void musecaEverySectionPlaysAndEjectsBeforeSingleDropRemoval(GameTestHelper helper) {
        WaccaCabinetGameTests.everySectionPlaysAndEjectsBeforeSingleDropRemoval(helper, FunPackCustom.MUSECA_ITEM.get());
    }

    @GameTest(template="nostalgia_test")
    public static void musecaSavedDiscPlacementRestoresPlaybackAndCanEject(GameTestHelper helper) {
        WaccaCabinetGameTests.savedDiscPlacementRestoresPlaybackAndCanEject(helper, FunPackCustom.MUSECA_ITEM.get());
    }

    @GameTest(template="nostalgia_test")
    public static void musecaCreativeRemovalLeavesAdjacentGrooveCoasterPlaying(GameTestHelper helper) {
        SoundVoltexCabinetGameTests.creativeRemovalLeavesNeighborPlaying(helper,
            FunPackCustom.MUSECA_ITEM.get(), FunPackCustom.GROOVE_COASTER_ITEM.get());
    }

    @GameTest(template="nostalgia_test")
    public static void musecaOverhangPedalAndDiscClearanceWorkInEveryFacing(GameTestHelper helper) {
        var player = cabinet(helper, GameType.SURVIVAL, FunPackCustom.MUSECA_ITEM.get());
        var base = helper.absolutePos(BASE);
        for (Direction facing : Direction.Plane.HORIZONTAL) {
            // Known-shape updates keep all three sections intact during the test rotation.
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
                    && frontHit.getLocation().subtract(consoleCenter).dot(front) > .95,
                "Selection does not cover MUSECA's projecting spinner deck");
            var sideHit = console.clip(consoleCenter.add(sideways.scale(2)), consoleCenter, consolePos);
            helper.assertTrue(sideHit != null && sideHit.getDirection() == side
                    && sideHit.getLocation().subtract(consoleCenter).dot(sideways) > .65,
                "Selection does not cover the spinner deck's side overhang");
            var upperPos = base.above(2);
            // The inclined display/header sits behind the placement column's center.
            Vec3 upperCenter = Vec3.atCenterOf(upperPos).subtract(front.scale(.26));
            var upper = helper.getLevel().getBlockState(upperPos).getShape(helper.getLevel(), upperPos);
            var upperHit = upper.clip(upperCenter.add(sideways.scale(2)), upperCenter, upperPos);
            helper.assertTrue(upperHit != null && upperHit.getLocation().subtract(upperCenter).dot(sideways) > .60,
                "The marquee ornament lies outside selection bounds");

            var body = helper.getBlockState(BASE).getCollisionShape(helper.getLevel(), base);
            Vec3 overPedal = Vec3.atCenterOf(base).add(front.scale(1.1));
            var pedalHit = body.clip(overPedal, overPedal.add(0,-1,0), base);
            helper.assertTrue(pedalHit != null && pedalHit.getDirection() == Direction.UP
                    && pedalHit.getLocation().y < base.getY()+.2,
                "The projecting pedal is missing low collision");
            Vec3 besidePedal = overPedal.add(sideways.scale(.5));
            helper.assertTrue(body.clip(besidePedal, besidePedal.add(0,-1,0), base) == null,
                "Invisible collision fills the space beside the narrow pedal");

            insert(helper, player, BASE.above());
            player.setItemInHand(InteractionHand.MAIN_HAND, ItemStack.EMPTY);
            helper.useBlock(BASE.above(2), player);
            var drops = helper.getEntities(EntityType.ITEM, BASE, 3);
            helper.assertTrue(drops.size() == 1 && drops.getFirst().getItem().is(Items.MUSIC_DISC_13),
                "MUSECA did not eject exactly one disc");
            var disc = drops.getFirst();
            for (int section=0; section<3; section++) {
                var pos = base.above(section);
                for (var box : helper.getLevel().getBlockState(pos).getCollisionShape(helper.getLevel(), pos).toAabbs()) {
                    helper.assertFalse(box.move(pos.getX(), pos.getY(), pos.getZ()).intersects(disc.getBoundingBox()),
                        "A newly ejected disc intersects MUSECA collision facing " + facing);
                }
            }
            helper.assertTrue(helper.getLevel().noCollision(disc, disc.getBoundingBox()),
                "World collision obstructs the ejected disc");
            disc.discard();
        }
        helper.succeed();
    }
}
