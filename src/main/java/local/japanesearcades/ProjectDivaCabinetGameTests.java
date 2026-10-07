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

/** Actual placement, saved playback, section selection, and clear disc ejection. */
@GameTestHolder(JapaneseArcades.MOD_ID)
@PrefixGameTestTemplate(false)
public final class ProjectDivaCabinetGameTests {
    @GameTest(template="nostalgia_test")
    public static void projectDivaEverySectionPlaysAndEjectsBeforeSingleDropRemoval(GameTestHelper helper) {
        WaccaCabinetGameTests.everySectionPlaysAndEjectsBeforeSingleDropRemoval(helper,
            JapaneseArcades.PROJECT_DIVA_ITEM.get());
    }

    @GameTest(template="nostalgia_test")
    public static void projectDivaSavedDiscPlacementRestoresPlaybackAndCanEject(GameTestHelper helper) {
        WaccaCabinetGameTests.savedDiscPlacementRestoresPlaybackAndCanEject(helper,
            JapaneseArcades.PROJECT_DIVA_ITEM.get());
    }

    @GameTest(template="nostalgia_test")
    public static void projectDivaCreativeRemovalLeavesAdjacentMusecaPlaying(GameTestHelper helper) {
        SoundVoltexCabinetGameTests.creativeRemovalLeavesNeighborPlaying(helper,
            JapaneseArcades.PROJECT_DIVA_ITEM.get(), JapaneseArcades.MUSECA_ITEM.get());
    }

    @GameTest(template="nostalgia_test")
    public static void projectDivaDeckMarqueeAndDiscClearanceWorkInEveryFacing(GameTestHelper helper) {
        var player = cabinet(helper, GameType.SURVIVAL, JapaneseArcades.PROJECT_DIVA_ITEM.get());
        var base = helper.absolutePos(BASE);
        for (Direction facing : Direction.Plane.HORIZONTAL) {
            // Keep all three sections intact while rotating the placed machine.
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
                    && frontHit.getLocation().subtract(consoleCenter).dot(front) > .99,
                "Selection does not cover Project DIVA's projecting button deck");
            var sideHit = console.clip(consoleCenter.add(sideways.scale(2)), consoleCenter, consolePos);
            helper.assertTrue(sideHit != null && sideHit.getDirection() == side
                    && sideHit.getLocation().subtract(consoleCenter).dot(sideways) > .57,
                "Selection does not cover the console's side overhang");
            var upperPos = base.above(2);
            Vec3 upperCenter = Vec3.atCenterOf(upperPos).subtract(front.scale(.1));
            var upper = helper.getLevel().getBlockState(upperPos).getShape(helper.getLevel(), upperPos);
            var upperHit = upper.clip(upperCenter.add(sideways.scale(2)), upperCenter, upperPos);
            helper.assertTrue(upperHit != null && upperHit.getDirection() == side
                    && upperHit.getLocation().subtract(upperCenter).dot(sideways) > .63,
                "The broad geometric topper lies outside selection bounds");

            var lower = helper.getBlockState(BASE).getCollisionShape(helper.getLevel(), base);
            Vec3 underDeck = Vec3.atCenterOf(base).add(front.scale(.95));
            helper.assertTrue(lower.clip(underDeck.add(front), underDeck, base) == null,
                "Invisible collision fills the clearance beneath the button deck");
            var ledgeHit = lower.clip(underDeck.add(0,.7,0), underDeck, base);
            helper.assertTrue(ledgeHit != null && ledgeHit.getDirection() == Direction.UP
                    && ledgeHit.getLocation().y > base.getY()+.98,
                "The projecting deck underside is missing collision at the section boundary");

            insert(helper, player, BASE.above());
            player.setItemInHand(InteractionHand.MAIN_HAND, ItemStack.EMPTY);
            helper.useBlock(BASE.above(2), player);
            var drops = helper.getEntities(EntityType.ITEM, BASE, 3);
            helper.assertTrue(drops.size() == 1 && drops.getFirst().getItem().is(Items.MUSIC_DISC_13),
                "Project DIVA did not eject exactly one disc");
            var disc = drops.getFirst();
            for (int section=0; section<3; section++) {
                var pos = base.above(section);
                for (var box : helper.getLevel().getBlockState(pos).getCollisionShape(helper.getLevel(), pos).toAabbs()) {
                    helper.assertFalse(box.move(pos.getX(), pos.getY(), pos.getZ()).intersects(disc.getBoundingBox()),
                        "A newly ejected disc intersects Project DIVA collision facing " + facing);
                }
            }
            helper.assertTrue(helper.getLevel().noCollision(disc, disc.getBoundingBox()),
                "World collision obstructs the ejected disc");
            disc.discard();
        }
        helper.succeed();
    }
}
