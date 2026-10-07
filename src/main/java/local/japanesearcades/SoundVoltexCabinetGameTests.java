package local.japanesearcades;

import static local.japanesearcades.NostalgiaCabinetGameTests.*;

import net.minecraft.core.BlockPos;
import net.minecraft.gametest.framework.GameTest;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.BlockItem;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.GameType;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.neoforged.neoforge.gametest.GameTestHolder;
import net.neoforged.neoforge.gametest.PrefixGameTestTemplate;

/** Exercises the second cabinet through the same placement and jukebox paths as Nostalgia. */
@GameTestHolder(JapaneseArcades.MOD_ID)
@PrefixGameTestTemplate(false)
public final class SoundVoltexCabinetGameTests {
    @GameTest(template="nostalgia_test")
    public static void valkyrieInsertsAndEjectsFromEverySection(GameTestHelper helper) {
        Player player = cabinet(helper, GameType.SURVIVAL, JapaneseArcades.SOUND_VOLTEX_VALKYRIE_ITEM.get());
        player.setItemInHand(InteractionHand.MAIN_HAND, new ItemStack(Items.STICK));
        helper.useBlock(BASE.above(), player);
        helper.assertTrue(entity(helper).isEmpty(), "Valkyrie accepted a non-disc item");
        for (int i=0; i<3; i++) {
            insert(helper, player, BASE.above(i));
            helper.assertTrue(player.getMainHandItem().getCount() == 1, "Insertion must consume exactly one disc");
            player.setItemInHand(InteractionHand.MAIN_HAND, ItemStack.EMPTY);
            helper.useBlock(BASE.above((i+1)%3), player);
            helper.assertTrue(entity(helper).isEmpty(), "Valkyrie did not eject its disc");
            helper.assertFalse(entity(helper).getSongPlayer().isPlaying(), "Valkyrie continued playing after ejection");
            helper.assertBlockProperty(BASE, NostalgiaCabinetBlock.HAS_RECORD, false);
            helper.assertItemEntityCountIs(Items.MUSIC_DISC_13, BASE, 3, i+1);
        }
        helper.succeed();
    }

    @GameTest(template="nostalgia_test")
    public static void valkyriePersistsPlaybackAndDropsExactlyOneDiscAndCabinet(GameTestHelper helper) {
        Player player = cabinet(helper, GameType.SURVIVAL, JapaneseArcades.SOUND_VOLTEX_VALKYRIE_ITEM.get());
        insert(helper, player, BASE.above(2));
        helper.runAfterDelay(25, () -> {
            var original = entity(helper);
            helper.assertTrue(original.getSongPlayer().getTicksSinceSongStarted() >= 20, "Valkyrie song is not ticking");
            helper.assertTrue(original.comparatorOutput() > 0, "Valkyrie has no disc comparator output");
            var tag = original.saveWithFullMetadata(helper.getLevel().registryAccess());
            var restored = BlockEntity.loadStatic(helper.absolutePos(BASE), helper.getBlockState(BASE), tag,
                helper.getLevel().registryAccess());
            helper.assertTrue(restored instanceof NostalgiaJukeboxBlockEntity, "Valkyrie inventory did not load");
            var loaded = (NostalgiaJukeboxBlockEntity)restored;
            helper.assertTrue(loaded.getTheItem().is(Items.MUSIC_DISC_13), "Valkyrie saved disc was lost");
            helper.assertTrue(loaded.getSongPlayer().getTicksSinceSongStarted() >= 20, "Valkyrie playback progress was lost");
            helper.getLevel().setBlockEntity(loaded);
            helper.getLevel().destroyBlock(helper.absolutePos(BASE.above()), true);
            for (int i=0; i<3; i++) { helper.assertBlockPresent(Blocks.AIR, BASE.above(i)); }
            helper.assertItemEntityCountIs(Items.MUSIC_DISC_13, BASE, 3, 1);
            helper.assertItemEntityCountIs(JapaneseArcades.SOUND_VOLTEX_VALKYRIE_ITEM.get(), BASE, 3, 1);
            helper.assertItemEntityCountIs(JapaneseArcades.NOSTALGIA_OP3_ITEM.get(), BASE, 3, 0);
            helper.assertFalse(loaded.getSongPlayer().isPlaying(), "Removed Valkyrie still plays");
            helper.succeed();
        });
    }

    @GameTest(template="nostalgia_test")
    public static void valkyrieCreativeRemovalLeavesAdjacentNostalgiaPlaying(GameTestHelper helper) {
        creativeRemovalLeavesNeighborPlaying(helper, JapaneseArcades.SOUND_VOLTEX_VALKYRIE_ITEM.get(),
            JapaneseArcades.NOSTALGIA_OP3_ITEM.get());
    }

    static void creativeRemovalLeavesNeighborPlaying(GameTestHelper helper, Item removedCabinet, Item neighborCabinet) {
        Player player = cabinet(helper, GameType.CREATIVE, removedCabinet);
        insert(helper, player, BASE.above());
        BlockPos neighbor = BASE.east();
        player.setItemInHand(InteractionHand.MAIN_HAND, new ItemStack(neighborCabinet));
        helper.assertTrue(place(helper, player, neighbor), "Neighboring cabinet placement failed");
        player.setItemInHand(InteractionHand.MAIN_HAND, new ItemStack(Items.MUSIC_DISC_CAT));
        helper.useBlock(neighbor.above(2), player);
        var neighborEntity = (NostalgiaJukeboxBlockEntity)helper.getBlockEntity(neighbor);
        helper.assertTrue(neighborEntity.getSongPlayer().isPlaying(), "Neighboring cabinet did not start playing");
        var top = helper.absolutePos(BASE.above(2));
        var state = helper.getLevel().getBlockState(top);
        state.getBlock().playerWillDestroy(helper.getLevel(), top, state, player);
        helper.getLevel().destroyBlock(top, false, player);
        for (int i=0; i<3; i++) {
            helper.assertBlockPresent(Blocks.AIR, BASE.above(i));
            helper.assertBlockPresent(((BlockItem)neighborCabinet).getBlock(), neighbor.above(i));
        }
        helper.assertTrue(neighborEntity.getTheItem().is(Items.MUSIC_DISC_CAT), "Removal affected the neighboring disc");
        helper.assertTrue(neighborEntity.getSongPlayer().isPlaying(), "Removal stopped the neighboring song");
        helper.assertItemEntityCountIs(Items.MUSIC_DISC_13, BASE, 3, 1);
        helper.assertItemEntityCountIs(Items.MUSIC_DISC_CAT, BASE, 3, 0);
        helper.assertItemEntityCountIs(removedCabinet, BASE, 3, 0);
        helper.assertItemEntityCountIs(neighborCabinet, BASE, 3, 0);
        helper.succeed();
    }

    @GameTest(template="nostalgia_test")
    public static void valkyriePlacementWithSavedDiscCanEjectIt(GameTestHelper helper) {
        Player player = player(helper, GameType.SURVIVAL);
        ItemStack stack = new ItemStack(JapaneseArcades.SOUND_VOLTEX_VALKYRIE_ITEM.get());
        CompoundTag data = new CompoundTag();
        data.put("RecordItem", new ItemStack(Items.MUSIC_DISC_13).save(helper.getLevel().registryAccess()));
        BlockItem.setBlockEntityData(stack, JapaneseArcades.NOSTALGIA_JUKEBOX.get(), data);
        player.setItemInHand(InteractionHand.MAIN_HAND, stack);
        helper.assertTrue(place(helper, player), "Valkyrie with saved disc was not placed");
        helper.assertTrue(entity(helper).getTheItem().is(Items.MUSIC_DISC_13), "Placed Valkyrie lost its saved disc");
        helper.assertBlockProperty(BASE, NostalgiaCabinetBlock.HAS_RECORD, true);
        helper.useBlock(BASE.above(), player);
        helper.assertTrue(entity(helper).isEmpty(), "Valkyrie saved disc could not be ejected");
        helper.assertItemEntityCountIs(Items.MUSIC_DISC_13, BASE, 3, 1);
        helper.succeed();
    }
}
