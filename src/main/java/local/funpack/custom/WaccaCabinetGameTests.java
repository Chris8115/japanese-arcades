package local.funpack.custom;

import static local.funpack.custom.NostalgiaCabinetGameTests.*;

import net.minecraft.gametest.framework.GameTest;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.BlockItem;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.GameType;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.neoforged.neoforge.gametest.GameTestHolder;
import net.neoforged.neoforge.gametest.PrefixGameTestTemplate;

/** Verifies WACCA's registration through real placement, saved inventory, and removal. */
@GameTestHolder(FunPackCustom.MOD_ID)
@PrefixGameTestTemplate(false)
public final class WaccaCabinetGameTests {
    @GameTest(template="nostalgia_test")
    public static void waccaEverySectionPlaysAndEjectsBeforeSingleDropRemoval(GameTestHelper helper) {
        Player player = cabinet(helper, GameType.SURVIVAL, FunPackCustom.WACCA_ITEM.get());
        for (int i=0; i<3; i++) {
            insert(helper, player, BASE.above(i));
            helper.assertTrue(player.getMainHandItem().getCount() == 1, "WACCA must consume exactly one disc");
            player.setItemInHand(InteractionHand.MAIN_HAND, ItemStack.EMPTY);
            helper.useBlock(BASE.above((i+1)%3), player);
            helper.assertTrue(entity(helper).isEmpty(), "WACCA did not eject its disc");
            helper.assertFalse(entity(helper).getSongPlayer().isPlaying(), "WACCA kept playing after ejection");
            helper.assertBlockProperty(BASE, NostalgiaCabinetBlock.HAS_RECORD, false);
            helper.assertItemEntityCountIs(Items.MUSIC_DISC_13, BASE, 3, i+1);
        }
        insert(helper, player, BASE.above(2));
        var removed = entity(helper);
        helper.getLevel().destroyBlock(helper.absolutePos(BASE.above()), true);
        for (int i=0; i<3; i++) { helper.assertBlockPresent(Blocks.AIR, BASE.above(i)); }
        helper.assertItemEntityCountIs(Items.MUSIC_DISC_13, BASE, 3, 4);
        helper.assertItemEntityCountIs(FunPackCustom.WACCA_ITEM.get(), BASE, 3, 1);
        helper.assertFalse(removed.getSongPlayer().isPlaying(), "Removed WACCA still plays");
        helper.succeed();
    }

    @GameTest(template="nostalgia_test")
    public static void waccaSavedDiscPlacementRestoresPlaybackAndCanEject(GameTestHelper helper) {
        Player player = player(helper, GameType.SURVIVAL);
        ItemStack stack = new ItemStack(FunPackCustom.WACCA_ITEM.get());
        CompoundTag data = new CompoundTag();
        data.put("RecordItem", new ItemStack(Items.MUSIC_DISC_13).save(helper.getLevel().registryAccess()));
        data.putLong("ticks_since_song_started", 40);
        BlockItem.setBlockEntityData(stack, FunPackCustom.NOSTALGIA_JUKEBOX.get(), data);
        player.setItemInHand(InteractionHand.MAIN_HAND, stack);
        helper.assertTrue(place(helper, player), "WACCA with saved disc was not placed");
        helper.assertTrue(entity(helper).getTheItem().is(Items.MUSIC_DISC_13), "Placed WACCA lost its saved disc");
        helper.assertBlockProperty(BASE, NostalgiaCabinetBlock.HAS_RECORD, true);
        helper.runAfterDelay(25, () -> {
            var tag = entity(helper).saveWithFullMetadata(helper.getLevel().registryAccess());
            var restored = BlockEntity.loadStatic(helper.absolutePos(BASE), helper.getBlockState(BASE), tag,
                helper.getLevel().registryAccess());
            helper.assertTrue(restored instanceof NostalgiaJukeboxBlockEntity, "WACCA inventory did not load");
            var loaded = (NostalgiaJukeboxBlockEntity)restored;
            helper.assertTrue(loaded.getSongPlayer().getTicksSinceSongStarted() >= 60, "WACCA playback was not restored and ticked");
            helper.assertTrue(loaded.getTheItem().is(Items.MUSIC_DISC_13), "Reloading WACCA lost its saved disc");
            helper.getLevel().setBlockEntity(loaded);
            player.setItemInHand(InteractionHand.MAIN_HAND, ItemStack.EMPTY);
            helper.useBlock(BASE.above(2), player);
            helper.assertTrue(loaded.isEmpty(), "WACCA saved disc could not be ejected");
            helper.assertFalse(loaded.getSongPlayer().isPlaying(), "Reloaded WACCA did not stop after ejection");
            helper.assertItemEntityCountIs(Items.MUSIC_DISC_13, BASE, 3, 1);
            helper.succeed();
        });
    }

    @GameTest(template="nostalgia_test")
    public static void waccaCreativeRemovalLeavesAdjacentValkyriePlaying(GameTestHelper helper) {
        SoundVoltexCabinetGameTests.creativeRemovalLeavesNeighborPlaying(helper,
            FunPackCustom.WACCA_ITEM.get(), FunPackCustom.SOUND_VOLTEX_VALKYRIE_ITEM.get());
    }
}
