package local.japanesearcades;

import static local.japanesearcades.NostalgiaCabinetGameTests.BASE;
import static local.japanesearcades.NostalgiaCabinetGameTests.place;
import static local.japanesearcades.NostalgiaCabinetGameTests.player;

import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.gametest.framework.GameTest;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.GameType;
import net.minecraft.world.level.block.Blocks;
import net.neoforged.neoforge.gametest.GameTestHolder;
import net.neoforged.neoforge.gametest.PrefixGameTestTemplate;

/** Exercises the independent BeatStream registration through the shared Nostalgia chassis. */
@GameTestHolder(JapaneseArcades.MOD_ID)
@PrefixGameTestTemplate(false)
public final class BeatStreamCabinetGameTests {
    @GameTest(template="nostalgia_test")
    public static void beatstreamEverySectionPlaysEjectsAndDropsOneCabinet(GameTestHelper helper) {
        WaccaCabinetGameTests.everySectionPlaysAndEjectsBeforeSingleDropRemoval(helper,
            JapaneseArcades.BEATSTREAM_ITEM.get());
    }

    @GameTest(template="nostalgia_test")
    public static void beatstreamSavedDiscPlacementTicksReloadsAndEjects(GameTestHelper helper) {
        WaccaCabinetGameTests.savedDiscPlacementRestoresPlaybackAndCanEject(helper,
            JapaneseArcades.BEATSTREAM_ITEM.get());
    }

    @GameTest(template="nostalgia_test")
    public static void beatstreamRotatesAndLeavesAdjacentNostalgiaPlaying(GameTestHelper helper) {
        var entry = ArcadeOrderCatalog.find(ResourceLocation.fromNamespaceAndPath(JapaneseArcades.MOD_ID, "beatstream"));
        helper.assertTrue(entry.isPresent() && entry.get().output().is(JapaneseArcades.BEATSTREAM_ITEM.get()),
            "The independent BeatStream item is missing from the machine ordering catalog");
        for (Direction facing : Direction.Plane.HORIZONTAL) {
            Player operator = player(helper, GameType.CREATIVE);
            operator.setYRot(facing.getOpposite().toYRot());
            operator.setItemInHand(InteractionHand.MAIN_HAND, new ItemStack(JapaneseArcades.BEATSTREAM_ITEM.get()));
            helper.assertTrue(place(helper, operator), "BeatStream placement failed facing " + facing);
            BlockPos neighbor = BASE.relative(facing.getClockWise());
            operator.setItemInHand(InteractionHand.MAIN_HAND, new ItemStack(JapaneseArcades.NOSTALGIA_OP3_ITEM.get()));
            helper.assertTrue(place(helper, operator, neighbor), "Adjacent Nostalgia placement failed");
            for (int section=0; section<3; section++) {
                helper.assertBlockPresent(JapaneseArcades.BEATSTREAM.get(), BASE.above(section));
                helper.assertBlockProperty(BASE.above(section), NostalgiaCabinetBlock.PART,
                    NostalgiaCabinetBlock.Part.values()[section]);
                helper.assertBlockProperty(BASE.above(section), NostalgiaCabinetBlock.FACING, facing);
                BlockPos first = helper.absolutePos(BASE.above(section));
                BlockPos second = helper.absolutePos(neighbor.above(section));
                var firstShape = helper.getLevel().getBlockState(first).getCollisionShape(helper.getLevel(), first);
                var secondShape = helper.getLevel().getBlockState(second).getCollisionShape(helper.getLevel(), second);
                helper.assertFalse(firstShape.bounds().move(first.getX(), first.getY(), first.getZ())
                    .intersects(secondShape.bounds().move(second.getX(), second.getY(), second.getZ())),
                    "Flush BeatStream and Nostalgia cabinets overlap facing " + facing);
                if (section>0) helper.assertTrue(helper.getLevel().getBlockEntity(first)==null,
                    "BeatStream created an extra disc inventory above its base");
            }
            operator.setItemInHand(InteractionHand.MAIN_HAND, new ItemStack(Items.MUSIC_DISC_13));
            helper.useBlock(BASE.above(), operator);
            operator.setItemInHand(InteractionHand.MAIN_HAND, new ItemStack(Items.MUSIC_DISC_CAT));
            helper.useBlock(neighbor.above(2), operator);
            var surviving = (NostalgiaJukeboxBlockEntity)helper.getBlockEntity(neighbor);
            BlockPos top = helper.absolutePos(BASE.above(2));
            var state = helper.getLevel().getBlockState(top);
            state.getBlock().playerWillDestroy(helper.getLevel(), top, state, operator);
            helper.getLevel().destroyBlock(top, false, operator);
            for (int section=0; section<3; section++) {
                helper.assertBlockPresent(Blocks.AIR, BASE.above(section));
                helper.assertBlockPresent(JapaneseArcades.NOSTALGIA_OP3.get(), neighbor.above(section));
            }
            helper.assertTrue(surviving.getTheItem().is(Items.MUSIC_DISC_CAT) && surviving.getSongPlayer().isPlaying(),
                "Removing BeatStream changed the adjacent Nostalgia disc or playback");
            helper.assertItemEntityCountIs(Items.MUSIC_DISC_13, BASE, 3, 1);
            helper.assertItemEntityCountIs(Items.MUSIC_DISC_CAT, BASE, 3, 0);
            helper.assertItemEntityCountIs(JapaneseArcades.BEATSTREAM_ITEM.get(), BASE, 3, 0);
            helper.getLevel().destroyBlock(helper.absolutePos(neighbor), false);
            discardDrops(helper);
        }
        helper.succeed();
    }

    @GameTest(template="nostalgia_test")
    public static void beatstreamRejectsBlockedTopAndDropsOnceAfterSupportRemoval(GameTestHelper helper) {
        for (Direction facing : Direction.Plane.HORIZONTAL) {
            Player operator = player(helper, GameType.SURVIVAL);
            operator.setYRot(facing.getOpposite().toYRot());
            operator.setItemInHand(InteractionHand.MAIN_HAND, new ItemStack(JapaneseArcades.BEATSTREAM_ITEM.get()));
            helper.setBlock(BASE.above(2), Blocks.STONE);
            helper.assertFalse(place(helper, operator), "BeatStream replaced an occupied topper cell");
            helper.assertTrue(operator.getMainHandItem().getCount()==1, "Blocked placement consumed BeatStream");
            helper.assertBlockPresent(Blocks.AIR, BASE);
            helper.assertBlockPresent(Blocks.AIR, BASE.above());
            helper.setBlock(BASE.above(2), Blocks.AIR);
            helper.assertTrue(place(helper, operator), "BeatStream could not place after the obstruction was removed");
            helper.getLevel().destroyBlock(helper.absolutePos(BASE.below()), false);
            for (int section=0; section<3; section++) helper.assertBlockPresent(Blocks.AIR, BASE.above(section));
            helper.assertItemEntityCountIs(JapaneseArcades.BEATSTREAM_ITEM.get(), BASE, 3, 1);
            helper.assertItemEntityCountIs(JapaneseArcades.NOSTALGIA_OP3_ITEM.get(), BASE, 3, 0);
            discardDrops(helper);
        }
        helper.succeed();
    }

    private static void discardDrops(GameTestHelper helper) {
        helper.getEntities(EntityType.ITEM, BASE, 5).forEach(item -> item.discard());
    }
}
