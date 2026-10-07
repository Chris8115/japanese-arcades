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

/** Registration, inventory persistence and the older cabinet's overhanging selection geometry. */
@GameTestHolder(FunPackCustom.MOD_ID)
@PrefixGameTestTemplate(false)
public final class SoundVoltexNemsysCabinetGameTests {
    @GameTest(template = "nostalgia_test")
    public static void nemsysEverySectionPlaysEjectsAndDropsOneCabinet(GameTestHelper helper) {
        WaccaCabinetGameTests.everySectionPlaysAndEjectsBeforeSingleDropRemoval(helper,
            FunPackCustom.SOUND_VOLTEX_NEMSYS_ITEM.get());
    }

    @GameTest(template = "nostalgia_test")
    public static void nemsysSavedDiscPlacementRestoresPlaybackAndCanEject(GameTestHelper helper) {
        WaccaCabinetGameTests.savedDiscPlacementRestoresPlaybackAndCanEject(helper,
            FunPackCustom.SOUND_VOLTEX_NEMSYS_ITEM.get());
    }

    @GameTest(template = "nostalgia_test")
    public static void nemsysPlacementRotatesItsWingAndMonitorSelection(GameTestHelper helper) {
        Player operator = player(helper, GameType.SURVIVAL);
        for (Direction facing : Direction.Plane.HORIZONTAL) {
            operator.setYRot(facing.getOpposite().toYRot());
            operator.setItemInHand(InteractionHand.MAIN_HAND, new ItemStack(FunPackCustom.SOUND_VOLTEX_NEMSYS_ITEM.get(), 2));
            helper.setBlock(BASE.above(2), Blocks.STONE);
            helper.assertFalse(place(helper, operator), "NEMSYS replaced an occupied marquee cell");
            helper.assertTrue(operator.getMainHandItem().getCount() == 2, "Blocked placement consumed NEMSYS");
            helper.setBlock(BASE.above(2), Blocks.AIR);
            helper.assertTrue(place(helper, operator), "NEMSYS placement failed facing " + facing);
            helper.assertTrue(operator.getMainHandItem().getCount() == 1, "Placement must consume one NEMSYS cabinet");
            for (int section = 0; section < 3; section++) {
                helper.assertBlockPresent(FunPackCustom.SOUND_VOLTEX_NEMSYS.get(), BASE.above(section));
                helper.assertBlockProperty(BASE.above(section), NostalgiaCabinetBlock.FACING, facing);
                helper.assertBlockProperty(BASE.above(section), NostalgiaCabinetBlock.PART,
                    NostalgiaCabinetBlock.Part.values()[section]);
                if (section == 0) { continue; }
                var pos = helper.absolutePos(BASE.above(section));
                helper.assertTrue(helper.getLevel().getBlockEntity(pos) == null,
                    "NEMSYS created a second saved inventory above the base");
                var shape = helper.getLevel().getBlockState(pos).getShape(helper.getLevel(), pos);
                Vec3 origin = Vec3.atLowerCornerOf(pos);
                double y = section == 1 ? 8 : 4;
                for (double x : new double[]{-2, 18}) {
                    var wing = shape.clip(origin.add(rotated(facing, x, y, -16)),
                        origin.add(rotated(facing, x, y, 16)), pos);
                    helper.assertTrue(wing != null && wing.getDirection() == facing,
                        "A projecting NEMSYS wing cannot be selected facing " + facing);
                }
                var gap = shape.clip(origin.add(rotated(facing, 8, y, 0)),
                    origin.add(rotated(facing, 8, y, 7)), pos);
                helper.assertTrue(gap == null, "NEMSYS fills the open space in front of its monitor");
                var monitor = shape.clip(origin.add(rotated(facing, 8, y, 0)),
                    origin.add(rotated(facing, 8, y, 16)), pos);
                helper.assertTrue(monitor != null && monitor.getDirection() == facing,
                    "The NEMSYS monitor cannot be selected facing " + facing);
            }
            helper.getLevel().destroyBlock(helper.absolutePos(BASE.above()), true);
            for (int section = 0; section < 3; section++) {
                helper.assertBlockPresent(Blocks.AIR, BASE.above(section));
            }
            helper.assertItemEntityCountIs(FunPackCustom.SOUND_VOLTEX_NEMSYS_ITEM.get(), BASE, 4, 1);
            helper.getEntities(EntityType.ITEM, BASE, 5).forEach(item -> item.discard());
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
