package local.japanesearcades;

import static local.japanesearcades.NostalgiaCabinetGameTests.BASE;
import static local.japanesearcades.NostalgiaCabinetGameTests.cabinet;

import net.minecraft.core.Direction;
import net.minecraft.gametest.framework.GameTest;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.world.level.GameType;
import net.minecraft.world.phys.Vec3;
import net.neoforged.neoforge.gametest.GameTestHolder;
import net.neoforged.neoforge.gametest.PrefixGameTestTemplate;

/** Runs the shared placement and playback scenarios against Chunithm's actual registrations. */
@GameTestHolder(JapaneseArcades.MOD_ID)
@PrefixGameTestTemplate(false)
public final class ChunithmCabinetGameTests {
    @GameTest(template="nostalgia_test")
    public static void chunithmEverySectionPlaysAndEjectsBeforeSingleDropRemoval(GameTestHelper helper) {
        WaccaCabinetGameTests.everySectionPlaysAndEjectsBeforeSingleDropRemoval(helper,
            JapaneseArcades.CHUNITHM_ITEM.get());
    }

    @GameTest(template="nostalgia_test")
    public static void chunithmSavedDiscPlacementRestoresPlaybackAndCanEject(GameTestHelper helper) {
        WaccaCabinetGameTests.savedDiscPlacementRestoresPlaybackAndCanEject(helper,
            JapaneseArcades.CHUNITHM_ITEM.get());
    }

    @GameTest(template="nostalgia_test")
    public static void chunithmCreativeRemovalLeavesAdjacentWaccaPlaying(GameTestHelper helper) {
        SoundVoltexCabinetGameTests.creativeRemovalLeavesNeighborPlaying(helper,
            JapaneseArcades.CHUNITHM_ITEM.get(), JapaneseArcades.WACCA_ITEM.get());
    }

    @GameTest(template="nostalgia_test")
    public static void chunithmOverhangingWingsCanBeSelectedInEveryFacing(GameTestHelper helper) {
        cabinet(helper, GameType.SURVIVAL, JapaneseArcades.CHUNITHM_ITEM.get());
        for (Direction facing : Direction.Plane.HORIZONTAL) {
            for (int section=1; section<3; section++) {
                var pos = helper.absolutePos(BASE.above(section));
                var state = helper.getBlockState(BASE.above(section)).setValue(NostalgiaCabinetBlock.FACING, facing);
                Vec3 center = Vec3.atCenterOf(pos);
                Vec3 towardFront = new Vec3(facing.getStepX(), 0, facing.getStepZ());
                var hit = state.getShape(helper.getLevel(), pos).clip(center.add(towardFront.scale(2)), center, pos);
                helper.assertTrue(hit != null, "Selection ray missed an upper cabinet section facing " + facing);
                helper.assertTrue(hit.getDirection() == facing, "Selection hit the wrong face of the rotated wing enclosure");
                helper.assertTrue(hit.getLocation().subtract(center).dot(towardFront) > .8,
                    "Selection does not extend far enough in front of the placement column to cover the acrylic wing");
            }
        }
        helper.succeed();
    }
}
