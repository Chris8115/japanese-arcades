package local.japanesearcades;

import static local.japanesearcades.NostalgiaCabinetGameTests.*;

import java.util.ArrayList;
import java.util.List;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.gametest.framework.GameTest;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.BlockItem;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.GameType;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.phys.Vec3;
import net.neoforged.neoforge.gametest.GameTestHolder;
import net.neoforged.neoforge.gametest.PrefixGameTestTemplate;

/** Real placement, playback persistence, removal and component-selection checks. */
@GameTestHolder(JapaneseArcades.MOD_ID)
@PrefixGameTestTemplate(false)
public final class PopnMusicCabinetGameTests {
    @GameTest(template = "nostalgia_test")
    public static void popnMusicEverySectionPlaysEjectsAndDropsOneCabinet(GameTestHelper helper) {
        WaccaCabinetGameTests.everySectionPlaysAndEjectsBeforeSingleDropRemoval(helper,
            JapaneseArcades.POPN_MUSIC_ITEM.get());
    }

    @GameTest(template = "nostalgia_test")
    public static void popnMusicSavedPlaybackTicksAndReloadsInEveryFacing(GameTestHelper helper) {
        List<BlockPos> bases = List.of(new BlockPos(1, 1, 1), new BlockPos(5, 1, 1),
            new BlockPos(1, 1, 5), new BlockPos(5, 1, 5));
        List<Player> players = new ArrayList<>();
        int index = 0;
        for (Direction facing : Direction.Plane.HORIZONTAL) {
            Player operator = player(helper, GameType.SURVIVAL);
            players.add(operator);
            ItemStack stack = new ItemStack(JapaneseArcades.POPN_MUSIC_ITEM.get());
            CompoundTag data = new CompoundTag();
            data.put("RecordItem", new ItemStack(Items.MUSIC_DISC_13).save(helper.getLevel().registryAccess()));
            data.putLong("ticks_since_song_started", 40);
            BlockItem.setBlockEntityData(stack, JapaneseArcades.NOSTALGIA_JUKEBOX.get(), data);
            operator.setYRot(facing.getOpposite().toYRot());
            operator.setItemInHand(InteractionHand.MAIN_HAND, stack);
            BlockPos base = bases.get(index++);
            helper.assertTrue(place(helper, operator, base), "Saved pop'n music cabinet could not be placed");
            helper.assertBlockProperty(base, NostalgiaCabinetBlock.HAS_RECORD, true);
        }
        helper.runAfterDelay(25, () -> {
            for (int i = 0; i < bases.size(); i++) {
                BlockPos base = bases.get(i);
                var original = (NostalgiaJukeboxBlockEntity) helper.getBlockEntity(base);
                var loaded = BlockEntity.loadStatic(helper.absolutePos(base), helper.getBlockState(base),
                    original.saveWithFullMetadata(helper.getLevel().registryAccess()), helper.getLevel().registryAccess());
                helper.assertTrue(loaded instanceof NostalgiaJukeboxBlockEntity, "pop'n music inventory did not load");
                var restored = (NostalgiaJukeboxBlockEntity) loaded;
                helper.assertTrue(restored.getTheItem().is(Items.MUSIC_DISC_13)
                    && restored.getSongPlayer().getTicksSinceSongStarted() >= 60,
                    "pop'n music lost its saved disc or restored playback did not tick");
                helper.getLevel().setBlockEntity(restored);
                players.get(i).setItemInHand(InteractionHand.MAIN_HAND, ItemStack.EMPTY);
                helper.useBlock(base.above(2), players.get(i));
                helper.assertTrue(restored.isEmpty() && !restored.getSongPlayer().isPlaying(),
                    "Reloaded pop'n music could not eject through its marquee");
                helper.assertBlockProperty(base, NostalgiaCabinetBlock.HAS_RECORD, false);
            }
            helper.assertItemEntityCountIs(Items.MUSIC_DISC_13, BASE, 6, 4);
            helper.succeed();
        });
    }

    @GameTest(template = "nostalgia_test")
    public static void popnMusicCreativeRemovalLeavesNeighborPlaying(GameTestHelper helper) {
        SoundVoltexCabinetGameTests.creativeRemovalLeavesNeighborPlaying(helper,
            JapaneseArcades.POPN_MUSIC_ITEM.get(), JapaneseArcades.POPN_MUSIC_ITEM.get());
    }

    @GameTest(template = "nostalgia_test")
    public static void popnMusicEveryFacingRejectsObstructionsWithoutPartialPlacement(GameTestHelper helper) {
        Player operator = player(helper, GameType.SURVIVAL);
        for (Direction facing : Direction.Plane.HORIZONTAL) {
            operator.setYRot(facing.getOpposite().toYRot());
            for (int blocked = 1; blocked < 3; blocked++) {
                operator.setItemInHand(InteractionHand.MAIN_HAND, new ItemStack(JapaneseArcades.POPN_MUSIC_ITEM.get(), 2));
                helper.setBlock(BASE.above(blocked), Blocks.STONE);
                helper.assertFalse(place(helper, operator), "pop'n music placed through an upper block");
                helper.assertTrue(operator.getMainHandItem().getCount() == 2, "Obstructed placement consumed a cabinet");
                for (int section = 0; section < 3; section++) {
                    helper.assertBlockPresent(section == blocked ? Blocks.STONE : Blocks.AIR, BASE.above(section));
                }
                helper.setBlock(BASE.above(blocked), Blocks.AIR);
            }
            Vec3 upper = Vec3.atLowerCornerOf(BASE).add(rotated(facing, 8, 36, 12));
            var occupant = helper.spawn(EntityType.ARMOR_STAND, upper);
            occupant.blocksBuilding = true;
            occupant.setNoGravity(true);
            helper.assertFalse(place(helper, operator), "pop'n music placed its marquee through an entity");
            helper.assertTrue(operator.getMainHandItem().getCount() == 2, "Entity obstruction consumed a cabinet");
            occupant.discard();
            helper.assertTrue(place(helper, operator), "pop'n music placement failed facing " + facing);
            helper.assertTrue(operator.getMainHandItem().getCount() == 1, "Placement did not consume exactly one cabinet");
            for (int section = 0; section < 3; section++) {
                helper.assertBlockProperty(BASE.above(section), NostalgiaCabinetBlock.FACING, facing);
                helper.assertBlockProperty(BASE.above(section), NostalgiaCabinetBlock.PART, NostalgiaCabinetBlock.Part.values()[section]);
                if (section > 0) helper.assertTrue(helper.getLevel().getBlockEntity(helper.absolutePos(BASE.above(section))) == null,
                    "pop'n music created a second saved disc inventory");
            }
            helper.getLevel().destroyBlock(helper.absolutePos(BASE), true);
            helper.assertItemEntityCountIs(JapaneseArcades.POPN_MUSIC_ITEM.get(), BASE, 4, 1);
            clearDrops(helper);
        }
        helper.succeed();
    }

    @GameTest(template = "nostalgia_test")
    public static void popnMusicBreakingAnySectionOrSupportDropsInventoryOnce(GameTestHelper helper) {
        Player operator = player(helper, GameType.SURVIVAL);
        for (Direction facing : Direction.Plane.HORIZONTAL) for (int broken = -1; broken < 3; broken++) {
            operator.setYRot(facing.getOpposite().toYRot());
            operator.setItemInHand(InteractionHand.MAIN_HAND, new ItemStack(JapaneseArcades.POPN_MUSIC_ITEM.get()));
            helper.assertTrue(place(helper, operator), "pop'n music fixture placement failed");
            insert(helper, operator, BASE.above(2));
            var removed = entity(helper);
            helper.getLevel().destroyBlock(helper.absolutePos(BASE.offset(0, broken, 0)), broken >= 0);
            for (int section = 0; section < 3; section++) helper.assertBlockPresent(Blocks.AIR, BASE.above(section));
            helper.assertItemEntityCountIs(JapaneseArcades.POPN_MUSIC_ITEM.get(), BASE, 4, 1);
            helper.assertItemEntityCountIs(Items.MUSIC_DISC_13, BASE, 4, 1);
            helper.assertFalse(removed.getSongPlayer().isPlaying(), "Removed pop'n music kept playing");
            clearDrops(helper);
        }
        helper.succeed();
    }

    @GameTest(template = "nostalgia_test")
    public static void popnMusicDeckSpeakersAndTopperSelectWithoutFillingOpenFront(GameTestHelper helper) {
        Player operator = player(helper, GameType.SURVIVAL);
        for (Direction facing : Direction.Plane.HORIZONTAL) {
            operator.setYRot(facing.getOpposite().toYRot());
            operator.setItemInHand(InteractionHand.MAIN_HAND, new ItemStack(JapaneseArcades.POPN_MUSIC_ITEM.get()));
            helper.assertTrue(place(helper, operator), "pop'n music fixture placement failed");
            // Aim at the projecting deck corners, speaker fascia and upper artwork.
            for (double[] target : new double[][] {{-2.4, 17}, {18.4, 17}, {-1, 36}, {17, 36}, {8, 46}}) {
                int section = (int) target[1] / 16;
                var pos = helper.absolutePos(BASE.above(section));
                var shape = helper.getLevel().getBlockState(pos).getShape(helper.getLevel(), pos);
                Vec3 origin = Vec3.atLowerCornerOf(pos);
                var hit = shape.clip(origin.add(rotated(facing, target[0], target[1] - section * 16, -16)),
                    origin.add(rotated(facing, target[0], target[1] - section * 16, 16)), pos);
                helper.assertTrue(hit != null && hit.getDirection() == facing,
                    "pop'n music deck, speaker fascia or topper cannot be selected facing " + facing);
            }
            // The rear pedestal and speaker backing extend behind their front artwork.
            for (double[] rear : new double[][] {{-1.3, 17.5}, {8, 17.5}, {17.3, 17.5}, {8, 36}}) {
                double height = rear[1];
                int section = (int) height / 16;
                var pos = helper.absolutePos(BASE.above(section));
                var shape = helper.getLevel().getBlockState(pos).getShape(helper.getLevel(), pos);
                Vec3 origin = Vec3.atLowerCornerOf(pos);
                var hit = shape.clip(origin.add(rotated(facing, rear[0], height - section * 16, 32)),
                    origin.add(rotated(facing, rear[0], height - section * 16, 13)), pos);
                helper.assertTrue(hit != null && hit.getDirection() == facing.getOpposite(),
                    "pop'n music rear body or speaker backing cannot be selected facing " + facing);
            }
            for (double[] space : new double[][] {{28, 5}, {44, 8}}) {
                int section = (int) space[0] / 16;
                var pos = helper.absolutePos(BASE.above(section));
                var state = helper.getLevel().getBlockState(pos);
                Vec3 origin = Vec3.atLowerCornerOf(pos);
                Vec3 start = origin.add(rotated(facing, 8, space[0] - section * 16, -12));
                Vec3 end = origin.add(rotated(facing, 8, space[0] - section * 16, space[1]));
                helper.assertTrue(state.getShape(helper.getLevel(), pos).clip(start, end, pos) == null
                    && state.getCollisionShape(helper.getLevel(), pos).clip(start, end, pos) == null,
                    "Invisible selection or collision fills space in front of the recessed screen/topper");
            }
            helper.getLevel().destroyBlock(helper.absolutePos(BASE), false);
        }
        helper.succeed();
    }

    @GameTest(template = "nostalgia_test")
    public static void popnMusicDiscEjectionClearsCabinetInEveryFacing(GameTestHelper helper) {
        Player operator = player(helper, GameType.SURVIVAL);
        for (Direction facing : Direction.Plane.HORIZONTAL) {
            operator.setYRot(facing.getOpposite().toYRot());
            operator.setItemInHand(InteractionHand.MAIN_HAND, new ItemStack(JapaneseArcades.POPN_MUSIC_ITEM.get()));
            helper.assertTrue(place(helper, operator), "pop'n music fixture placement failed");
            for (int from = 0; from < 3; from++) {
                insert(helper, operator, BASE.above(from));
                operator.setItemInHand(InteractionHand.MAIN_HAND, ItemStack.EMPTY);
                helper.useBlock(BASE.above((from + 1) % 3), operator);
                var drops = helper.getEntities(EntityType.ITEM, BASE, 4);
                helper.assertTrue(drops.size() == 1 && drops.getFirst().getItem().is(Items.MUSIC_DISC_13),
                    "pop'n music did not eject exactly one disc");
                var disc = drops.getFirst();
                for (int section = 0; section < 3; section++) {
                    var pos = helper.absolutePos(BASE.above(section));
                    for (var box : helper.getLevel().getBlockState(pos).getCollisionShape(helper.getLevel(), pos).toAabbs()) {
                        helper.assertFalse(box.move(pos).intersects(disc.getBoundingBox()),
                            "The cabinet obstructs a freshly ejected disc facing " + facing);
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
