package local.funpack.custom;

import static local.funpack.custom.NostalgiaCabinetGameTests.BASE;
import static local.funpack.custom.NostalgiaCabinetGameTests.place;
import static local.funpack.custom.NostalgiaCabinetGameTests.player;

import net.minecraft.core.Direction;
import net.minecraft.gametest.framework.GameTest;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.GameType;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.phys.Vec3;
import net.neoforged.neoforge.gametest.GameTestHolder;
import net.neoforged.neoforge.gametest.PrefixGameTestTemplate;

/** Native placements and saved jukebox behavior for ONGEKI's independent registry entry. */
@GameTestHolder(FunPackCustom.MOD_ID)
@PrefixGameTestTemplate(false)
public final class OngekiCabinetGameTests {
    @GameTest(template = "nostalgia_test")
    public static void ongekiEverySectionPlaysEjectsAndDropsOneCabinet(GameTestHelper helper) {
        WaccaCabinetGameTests.everySectionPlaysAndEjectsBeforeSingleDropRemoval(helper,
            FunPackCustom.ONGEKI_ITEM.get());
    }

    @GameTest(template = "nostalgia_test")
    public static void ongekiSavedDiscPlacementRestoresPlaybackAndCanEject(GameTestHelper helper) {
        WaccaCabinetGameTests.savedDiscPlacementRestoresPlaybackAndCanEject(helper,
            FunPackCustom.ONGEKI_ITEM.get());
    }

    @GameTest(template = "nostalgia_test")
    public static void ongekiCreativeRemovalLeavesAdjacentChunithmPlaying(GameTestHelper helper) {
        SoundVoltexCabinetGameTests.creativeRemovalLeavesNeighborPlaying(helper,
            FunPackCustom.ONGEKI_ITEM.get(), FunPackCustom.CHUNITHM_ITEM.get());
    }

    @GameTest(template = "nostalgia_test")
    public static void ongekiRotatesAllPartsAndRejectsBlockedPlacement(GameTestHelper helper) {
        Player operator = player(helper, GameType.SURVIVAL);
        for (Direction facing : Direction.Plane.HORIZONTAL) {
            operator.setYRot(facing.getOpposite().toYRot());
            operator.setItemInHand(InteractionHand.MAIN_HAND, new ItemStack(FunPackCustom.ONGEKI_ITEM.get(), 2));
            helper.setBlock(BASE.above(2), Blocks.STONE);
            helper.assertFalse(place(helper, operator), "ONGEKI placed through an occupied arch cell");
            helper.assertTrue(operator.getMainHandItem().getCount() == 2, "Blocked placement consumed ONGEKI");
            helper.assertBlockPresent(Blocks.AIR, BASE);
            helper.assertBlockPresent(Blocks.AIR, BASE.above());
            helper.setBlock(BASE.above(2), Blocks.AIR);
            helper.assertTrue(place(helper, operator), "ONGEKI placement failed facing " + facing);
            helper.assertTrue(operator.getMainHandItem().getCount() == 1, "Placement must consume one cabinet");
            for (int section = 0; section < 3; section++) {
                helper.assertBlockPresent(FunPackCustom.ONGEKI.get(), BASE.above(section));
                helper.assertBlockProperty(BASE.above(section), NostalgiaCabinetBlock.FACING, facing);
                helper.assertBlockProperty(BASE.above(section), NostalgiaCabinetBlock.PART,
                    NostalgiaCabinetBlock.Part.values()[section]);
                if (section > 0) {
                    helper.assertTrue(helper.getLevel().getBlockEntity(helper.absolutePos(BASE.above(section))) == null,
                        "ONGEKI created another inventory above its base");
                }
            }
            helper.getLevel().destroyBlock(helper.absolutePos(BASE.below()), false);
            for (int section = 0; section < 3; section++) {
                helper.assertBlockPresent(Blocks.AIR, BASE.above(section));
            }
            helper.assertItemEntityCountIs(FunPackCustom.ONGEKI_ITEM.get(), BASE, 4, 1);
            helper.getEntities(EntityType.ITEM, BASE, 5).forEach(item -> item.discard());
        }
        helper.succeed();
    }

    @GameTest(template = "nostalgia_test")
    public static void ongekiArchAndRecessedMonitorRemainSelectableInEveryFacing(GameTestHelper helper) {
        NostalgiaCabinetGameTests.cabinet(helper, GameType.SURVIVAL, FunPackCustom.ONGEKI_ITEM.get());
        for (Direction facing : Direction.Plane.HORIZONTAL) {
            for (int section = 1; section < 3; section++) {
                var pos = helper.absolutePos(BASE.above(section));
                var state = helper.getBlockState(BASE.above(section)).setValue(NostalgiaCabinetBlock.FACING, facing);
                var shape = state.getShape(helper.getLevel(), pos);
                Vec3 origin = Vec3.atLowerCornerOf(pos);
                var wing = shape.clip(origin.add(rotated(facing, .1, 6, -16)),
                    origin.add(rotated(facing, .1, 6, 8)), pos);
                helper.assertTrue(wing != null && wing.getDirection() == facing,
                    "The forward arch was not selectable facing " + facing);
                Vec3 forward = new Vec3(facing.getStepX(), 0, facing.getStepZ());
                double overhang = wing.getLocation().subtract(origin.add(rotated(facing, .1, 6, 0))).dot(forward);
                helper.assertTrue(overhang > (section == 1 ? .1 : .2),
                    "The selection outline did not follow the forward-leaning arch facing " + facing);
                var gap = shape.clip(origin.add(rotated(facing, 8, 6, 0)),
                    origin.add(rotated(facing, 8, 6, 8)), pos);
                helper.assertTrue(gap == null, "ONGEKI's open arch became an invisible solid wall");
                var monitor = shape.clip(origin.add(rotated(facing, 8, 6, 0)),
                    origin.add(rotated(facing, 8, 6, 16)), pos);
                helper.assertTrue(monitor != null && monitor.getDirection() == facing,
                    "The recessed monitor was not selectable through the arch facing " + facing);
            }
        }
        helper.succeed();
    }

    private static Vec3 rotated(Direction facing, double x, double y, double z) {
        return switch (facing) {
            case EAST -> new Vec3(16-z, y, x).scale(1.0/16);
            case SOUTH -> new Vec3(16-x, y, 16-z).scale(1.0/16);
            case WEST -> new Vec3(z, y, 16-x).scale(1.0/16);
            default -> new Vec3(x, y, z).scale(1.0/16);
        };
    }
}
