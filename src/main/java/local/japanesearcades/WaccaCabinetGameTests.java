package local.japanesearcades;

import static local.japanesearcades.NostalgiaCabinetGameTests.*;

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

/** Verifies WACCA's registration through real placement, saved inventory, and removal. */
@GameTestHolder(JapaneseArcades.MOD_ID)
@PrefixGameTestTemplate(false)
public final class WaccaCabinetGameTests {
    @GameTest(template="nostalgia_test")
    public static void waccaEverySectionPlaysAndEjectsBeforeSingleDropRemoval(GameTestHelper helper) {
        everySectionPlaysAndEjectsBeforeSingleDropRemoval(helper, JapaneseArcades.WACCA_ITEM.get());
    }

    static void everySectionPlaysAndEjectsBeforeSingleDropRemoval(GameTestHelper helper, Item cabinetItem) {
        Player player = cabinet(helper, GameType.SURVIVAL, cabinetItem);
        for (int i=0; i<3; i++) {
            insert(helper, player, BASE.above(i));
            helper.assertTrue(player.getMainHandItem().getCount() == 1, "The cabinet must consume exactly one disc");
            player.setItemInHand(InteractionHand.MAIN_HAND, ItemStack.EMPTY);
            helper.useBlock(BASE.above((i+1)%3), player);
            helper.assertTrue(entity(helper).isEmpty(), "The cabinet did not eject its disc");
            helper.assertFalse(entity(helper).getSongPlayer().isPlaying(), "The cabinet kept playing after ejection");
            helper.assertBlockProperty(BASE, NostalgiaCabinetBlock.HAS_RECORD, false);
            helper.assertItemEntityCountIs(Items.MUSIC_DISC_13, BASE, 3, i+1);
        }
        insert(helper, player, BASE.above(2));
        var removed = entity(helper);
        helper.getLevel().destroyBlock(helper.absolutePos(BASE.above()), true);
        for (int i=0; i<3; i++) { helper.assertBlockPresent(Blocks.AIR, BASE.above(i)); }
        helper.assertItemEntityCountIs(Items.MUSIC_DISC_13, BASE, 3, 4);
        helper.assertItemEntityCountIs(cabinetItem, BASE, 3, 1);
        helper.assertFalse(removed.getSongPlayer().isPlaying(), "The removed cabinet still plays");
        helper.succeed();
    }

    @GameTest(template="nostalgia_test")
    public static void waccaSavedDiscPlacementRestoresPlaybackAndCanEject(GameTestHelper helper) {
        savedDiscPlacementRestoresPlaybackAndCanEject(helper, JapaneseArcades.WACCA_ITEM.get());
    }

    static void savedDiscPlacementRestoresPlaybackAndCanEject(GameTestHelper helper, Item cabinetItem) {
        Player player = player(helper, GameType.SURVIVAL);
        ItemStack stack = new ItemStack(cabinetItem);
        CompoundTag data = new CompoundTag();
        data.put("RecordItem", new ItemStack(Items.MUSIC_DISC_13).save(helper.getLevel().registryAccess()));
        data.putLong("ticks_since_song_started", 40);
        BlockItem.setBlockEntityData(stack, JapaneseArcades.NOSTALGIA_JUKEBOX.get(), data);
        player.setItemInHand(InteractionHand.MAIN_HAND, stack);
        helper.assertTrue(place(helper, player), "The cabinet with a saved disc was not placed");
        helper.assertTrue(entity(helper).getTheItem().is(Items.MUSIC_DISC_13), "The placed cabinet lost its saved disc");
        helper.assertBlockProperty(BASE, NostalgiaCabinetBlock.HAS_RECORD, true);
        helper.runAfterDelay(25, () -> {
            var tag = entity(helper).saveWithFullMetadata(helper.getLevel().registryAccess());
            var restored = BlockEntity.loadStatic(helper.absolutePos(BASE), helper.getBlockState(BASE), tag,
                helper.getLevel().registryAccess());
            helper.assertTrue(restored instanceof NostalgiaJukeboxBlockEntity, "The cabinet inventory did not load");
            var loaded = (NostalgiaJukeboxBlockEntity)restored;
            helper.assertTrue(loaded.getSongPlayer().getTicksSinceSongStarted() >= 60, "Playback was not restored and ticked");
            helper.assertTrue(loaded.getTheItem().is(Items.MUSIC_DISC_13), "Reloading the cabinet lost its saved disc");
            helper.getLevel().setBlockEntity(loaded);
            player.setItemInHand(InteractionHand.MAIN_HAND, ItemStack.EMPTY);
            helper.useBlock(BASE.above(2), player);
            helper.assertTrue(loaded.isEmpty(), "The saved disc could not be ejected");
            helper.assertFalse(loaded.getSongPlayer().isPlaying(), "The reloaded cabinet did not stop after ejection");
            helper.assertItemEntityCountIs(Items.MUSIC_DISC_13, BASE, 3, 1);
            helper.succeed();
        });
    }

    @GameTest(template="nostalgia_test")
    public static void waccaCreativeRemovalLeavesAdjacentValkyriePlaying(GameTestHelper helper) {
        SoundVoltexCabinetGameTests.creativeRemovalLeavesNeighborPlaying(helper,
            JapaneseArcades.WACCA_ITEM.get(), JapaneseArcades.SOUND_VOLTEX_VALKYRIE_ITEM.get());
    }
}
