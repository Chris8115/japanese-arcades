package local.funpack.custom;

import static local.funpack.custom.NostalgiaCabinetGameTests.*;

import net.minecraft.core.Direction;
import net.minecraft.gametest.framework.GameTest;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.GameType;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.phys.Vec3;
import net.neoforged.neoforge.gametest.GameTestHolder;
import net.neoforged.neoforge.gametest.PrefixGameTestTemplate;

/** Real placement, inventory, removal and ray/collision coverage of the sloping MUSIC DIVER. */
@GameTestHolder(FunPackCustom.MOD_ID)
@PrefixGameTestTemplate(false)
public final class MusicDiverCabinetGameTests {
    @GameTest(template = "nostalgia_test")
    public static void musicDiverEverySectionPlaysEjectsAndDropsOneCabinet(GameTestHelper helper) {
        WaccaCabinetGameTests.everySectionPlaysAndEjectsBeforeSingleDropRemoval(helper,
            FunPackCustom.MUSIC_DIVER_ITEM.get());
    }

    @GameTest(template = "nostalgia_test")
    public static void musicDiverSavedDiscPlacementRestoresPlaybackAndCanEject(GameTestHelper helper) {
        WaccaCabinetGameTests.savedDiscPlacementRestoresPlaybackAndCanEject(helper,
            FunPackCustom.MUSIC_DIVER_ITEM.get());
    }

    @GameTest(template = "nostalgia_test")
    public static void musicDiverCreativeRemovalLeavesAdjacentMusicDiverPlaying(GameTestHelper helper) {
        SoundVoltexCabinetGameTests.creativeRemovalLeavesNeighborPlaying(helper,
            FunPackCustom.MUSIC_DIVER_ITEM.get(), FunPackCustom.MUSIC_DIVER_ITEM.get());
    }

    @GameTest(template = "nostalgia_test")
    public static void musicDiverEveryFacingRejectsObstructionsWithoutPartialPlacement(GameTestHelper helper) {
        Player operator = player(helper, GameType.SURVIVAL);
        for (Direction facing : Direction.Plane.HORIZONTAL) {
            operator.setYRot(facing.getOpposite().toYRot());
            for (int blocked = 1; blocked < 3; blocked++) {
                operator.setItemInHand(InteractionHand.MAIN_HAND, new ItemStack(FunPackCustom.MUSIC_DIVER_ITEM.get(), 2));
                helper.setBlock(BASE.above(blocked), Blocks.STONE);
                helper.assertFalse(place(helper, operator), "MUSIC DIVER placed through an upper block");
                helper.assertTrue(operator.getMainHandItem().getCount() == 2, "Obstructed placement consumed a cabinet");
                for (int section = 0; section < 3; section++) {
                    helper.assertBlockPresent(section == blocked ? Blocks.STONE : Blocks.AIR, BASE.above(section));
                }
                helper.setBlock(BASE.above(blocked), Blocks.AIR);
            }
            Vec3 upper = Vec3.atLowerCornerOf(BASE).add(rotated(facing, 8, 33, 13));
            var occupant = helper.spawn(EntityType.ARMOR_STAND, upper);
            occupant.blocksBuilding = true;
            occupant.setNoGravity(true);
            helper.assertFalse(place(helper, operator), "MUSIC DIVER placed its marquee through an entity");
            helper.assertTrue(operator.getMainHandItem().getCount() == 2, "Entity obstruction consumed a cabinet");
            occupant.discard();
            helper.assertTrue(place(helper, operator), "MUSIC DIVER placement failed facing " + facing);
            helper.assertTrue(operator.getMainHandItem().getCount() == 1, "Placement did not consume exactly one cabinet");
            for (int section = 0; section < 3; section++) {
                helper.assertBlockProperty(BASE.above(section), NostalgiaCabinetBlock.FACING, facing);
                helper.assertBlockProperty(BASE.above(section), NostalgiaCabinetBlock.PART, NostalgiaCabinetBlock.Part.values()[section]);
                if (section > 0) helper.assertTrue(helper.getLevel().getBlockEntity(helper.absolutePos(BASE.above(section))) == null,
                    "MUSIC DIVER created a second saved disc inventory");
            }
            helper.getLevel().destroyBlock(helper.absolutePos(BASE), true);
            helper.assertItemEntityCountIs(FunPackCustom.MUSIC_DIVER_ITEM.get(), BASE, 4, 1);
            clearDrops(helper);
        }
        helper.succeed();
    }

    @GameTest(template = "nostalgia_test")
    public static void musicDiverBreakingAnySectionOrSupportDropsInventoryOnce(GameTestHelper helper) {
        Player operator = player(helper, GameType.SURVIVAL);
        for (Direction facing : Direction.Plane.HORIZONTAL) for (int broken = -1; broken < 3; broken++) {
            operator.setYRot(facing.getOpposite().toYRot());
            operator.setItemInHand(InteractionHand.MAIN_HAND, new ItemStack(FunPackCustom.MUSIC_DIVER_ITEM.get()));
            helper.assertTrue(place(helper, operator), "MUSIC DIVER fixture placement failed");
            insert(helper, operator, BASE.above(2));
            var removed = entity(helper);
            helper.getLevel().destroyBlock(helper.absolutePos(BASE.offset(0, broken, 0)), broken >= 0);
            for (int section = 0; section < 3; section++) helper.assertBlockPresent(Blocks.AIR, BASE.above(section));
            helper.assertItemEntityCountIs(FunPackCustom.MUSIC_DIVER_ITEM.get(), BASE, 4, 1);
            helper.assertItemEntityCountIs(Items.MUSIC_DISC_13, BASE, 4, 1);
            helper.assertFalse(removed.getSongPlayer().isPlaying(), "Removed MUSIC DIVER kept playing");
            clearDrops(helper);
        }
        helper.succeed();
    }

    @GameTest(template = "nostalgia_test")
    public static void musicDiverTiltedRimMarqueeAndHolsterCanBeSelectedInEveryFacing(GameTestHelper helper) {
        Player operator = player(helper, GameType.SURVIVAL);
        for (Direction facing : Direction.Plane.HORIZONTAL) {
            operator.setYRot(facing.getOpposite().toYRot());
            operator.setItemInHand(InteractionHand.MAIN_HAND, new ItemStack(FunPackCustom.MUSIC_DIVER_ITEM.get()));
            helper.assertTrue(place(helper, operator), "MUSIC DIVER fixture placement failed");
            // Model-space points on the real sloping rim, round upper header and hanging stick holster.
            for (double[] target : new double[][] {{0, 21.5, 4}, {16, 21.5, 4}, {-1, 38, 15}, {17, 38, 15}, {16.2, 10, -1}}) {
                int section = (int) target[1] / 16;
                var pos = helper.absolutePos(BASE.above(section));
                var shape = helper.getLevel().getBlockState(pos).getShape(helper.getLevel(), pos);
                Vec3 origin = Vec3.atLowerCornerOf(pos);
                Vec3 start = origin.add(rotated(facing, target[0], target[1] - section * 16, -16));
                Vec3 end = origin.add(rotated(facing, target[0], target[1] - section * 16, 16));
                var hit = shape.clip(start, end, pos);
                helper.assertTrue(hit != null && hit.getDirection() == facing,
                    "MUSIC DIVER rim, marquee or stick holster cannot be selected facing " + facing);
            }
            var top = helper.absolutePos(BASE.above(2));
            var shape = helper.getLevel().getBlockState(top).getShape(helper.getLevel(), top);
            Vec3 origin = Vec3.atLowerCornerOf(top);
            helper.assertTrue(shape.clip(origin.add(rotated(facing, 8, 8, -12)), origin.add(rotated(facing, 8, 8, 8)), top) == null,
                "Invisible collision fills the open space in front of the vertical marquee");
            var console = helper.absolutePos(BASE.above());
            var consoleShape = helper.getLevel().getBlockState(console).getShape(helper.getLevel(), console);
            origin = Vec3.atLowerCornerOf(console);
            helper.assertTrue(consoleShape.clip(origin.add(rotated(facing, 8, 13, -12)),
                    origin.add(rotated(facing, 8, 13, 6)), console) == null,
                "Invisible collision fills the air above the sloping play surface");
            helper.getLevel().destroyBlock(helper.absolutePos(BASE), false);
        }
        helper.succeed();
    }

    @GameTest(template = "nostalgia_test")
    public static void musicDiverDiscEjectionClearsSlopingCabinetAndHolster(GameTestHelper helper) {
        Player operator = player(helper, GameType.SURVIVAL);
        for (Direction facing : Direction.Plane.HORIZONTAL) {
            operator.setYRot(facing.getOpposite().toYRot());
            operator.setItemInHand(InteractionHand.MAIN_HAND, new ItemStack(FunPackCustom.MUSIC_DIVER_ITEM.get()));
            helper.assertTrue(place(helper, operator), "MUSIC DIVER fixture placement failed");
            for (int from = 0; from < 3; from++) {
                insert(helper, operator, BASE.above(from));
                operator.setItemInHand(InteractionHand.MAIN_HAND, ItemStack.EMPTY);
                helper.useBlock(BASE.above((from + 1) % 3), operator);
                var drops = helper.getEntities(EntityType.ITEM, BASE, 4);
                helper.assertTrue(drops.size() == 1 && drops.getFirst().getItem().is(Items.MUSIC_DISC_13),
                    "MUSIC DIVER did not eject exactly one disc");
                var disc = drops.getFirst();
                for (int section = 0; section < 3; section++) {
                    var pos = helper.absolutePos(BASE.above(section));
                    for (var box : helper.getLevel().getBlockState(pos).getCollisionShape(helper.getLevel(), pos).toAabbs()) {
                        helper.assertFalse(box.move(pos).intersects(disc.getBoundingBox()),
                            "A MUSIC DIVER component obstructs the freshly ejected disc facing " + facing);
                    }
                }
                helper.assertTrue(helper.getLevel().noCollision(disc, disc.getBoundingBox()), "World collision obstructs the ejected disc");
                disc.discard();
            }
            helper.getLevel().destroyBlock(helper.absolutePos(BASE), false);
        }
        helper.succeed();
    }

    private static void clearDrops(GameTestHelper helper) {
        helper.getEntities(EntityType.ITEM, BASE, 5).forEach(item -> item.discard());
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
