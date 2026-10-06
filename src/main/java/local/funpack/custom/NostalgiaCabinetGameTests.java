package local.funpack.custom;

import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.gametest.framework.GameTest;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.BlockItem;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.item.context.BlockPlaceContext;
import net.minecraft.world.level.GameType;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.phys.BlockHitResult;
import net.minecraft.world.phys.Vec3;
import net.neoforged.neoforge.gametest.GameTestHolder;
import net.neoforged.neoforge.gametest.PrefixGameTestTemplate;

/** Integration tests run in a disposable world with dev.cmd GameTest. */
@GameTestHolder(FunPackCustom.MOD_ID)
@PrefixGameTestTemplate(false)
public final class NostalgiaCabinetGameTests {
    private static final BlockPos BASE = new BlockPos(3, 1, 3);

    private static Player player(GameTestHelper helper, GameType mode) {
        Player player = helper.makeMockPlayer(mode);
        player.getAbilities().instabuild = mode.isCreative();
        BlockPos abs = helper.absolutePos(BASE);
        player.setPos(abs.getX() + .5, abs.getY(), abs.getZ() - 2);
        player.setYRot(0);
        return player;
    }

    private static boolean place(GameTestHelper helper, Player player) {
        BlockPos floor = helper.absolutePos(BASE.below());
        helper.setBlock(BASE.below(), Blocks.STONE);
        BlockHitResult hit = new BlockHitResult(Vec3.atCenterOf(floor).add(0,.5,0), Direction.UP, floor, false);
        var context = new BlockPlaceContext(player, InteractionHand.MAIN_HAND, player.getMainHandItem(), hit);
        return ((BlockItem)FunPackCustom.NOSTALGIA_OP3_ITEM.get()).place(context).consumesAction();
    }

    private static Player cabinet(GameTestHelper helper, GameType mode) {
        Player player = player(helper, mode);
        player.setItemInHand(InteractionHand.MAIN_HAND, new ItemStack(FunPackCustom.NOSTALGIA_OP3_ITEM.get()));
        helper.assertTrue(place(helper, player), "Cabinet placement failed");
        for (int i=0; i<3; i++) {
            helper.assertBlockProperty(BASE.above(i), NostalgiaCabinetBlock.PART, NostalgiaCabinetBlock.Part.values()[i]);
            helper.assertBlockProperty(BASE.above(i), NostalgiaCabinetBlock.FACING, Direction.NORTH);
        }
        helper.assertTrue(helper.getLevel().getBlockEntity(helper.absolutePos(BASE.above())) == null,
            "The console must not contain a second disc inventory");
        return player;
    }

    private static NostalgiaJukeboxBlockEntity entity(GameTestHelper helper) {
        return (NostalgiaJukeboxBlockEntity)helper.getBlockEntity(BASE);
    }

    private static void insert(GameTestHelper helper, Player player, BlockPos section) {
        player.setItemInHand(InteractionHand.MAIN_HAND, new ItemStack(Items.MUSIC_DISC_13, 2));
        helper.useBlock(section, player);
        helper.assertTrue(entity(helper).getTheItem().is(Items.MUSIC_DISC_13), "Inserted disc was not stored in the base");
        helper.assertTrue(entity(helper).getTheItem().getCount() == 1, "Only one disc may be stored");
        helper.assertTrue(entity(helper).getSongPlayer().isPlaying(), "Song did not start");
        helper.assertBlockProperty(BASE, NostalgiaCabinetBlock.HAS_RECORD, true);
    }

    @GameTest(template="nostalgia_test")
    public static void insertAndEjectFromEverySection(GameTestHelper helper) {
        Player player = cabinet(helper, GameType.SURVIVAL);
        for (int i=0; i<3; i++) {
            insert(helper, player, BASE.above(i));
            helper.assertTrue(player.getMainHandItem().getCount() == 1, "Survival insertion did not consume exactly one disc");
            player.setItemInHand(InteractionHand.MAIN_HAND, ItemStack.EMPTY);
            helper.useBlock(BASE.above((i+1)%3), player);
            helper.assertTrue(entity(helper).isEmpty(), "Disc was not ejected");
            helper.assertFalse(entity(helper).getSongPlayer().isPlaying(), "Playback continued after ejection");
            helper.assertBlockProperty(BASE, NostalgiaCabinetBlock.HAS_RECORD, false);
            helper.assertItemEntityCountIs(Items.MUSIC_DISC_13, BASE, 3, i+1);
        }
        helper.succeed();
    }

    @GameTest(template="nostalgia_test")
    public static void songTicksAndNonDiscsAreRejected(GameTestHelper helper) {
        Player player = cabinet(helper, GameType.SURVIVAL);
        player.setItemInHand(InteractionHand.MAIN_HAND, new ItemStack(Items.STICK));
        helper.useBlock(BASE.above(), player);
        helper.assertTrue(entity(helper).isEmpty(), "A non-disc item was accepted");
        insert(helper, player, BASE.above(2));
        helper.assertTrue(entity(helper).comparatorOutput() > 0, "Disc comparator output is missing");
        helper.runAfterDelay(25, () -> {
            helper.assertTrue(entity(helper).getSongPlayer().getTicksSinceSongStarted() >= 20, "Server playback did not tick");
            helper.assertTrue(entity(helper).getSongPlayer().isPlaying(), "The song stopped prematurely");
            helper.succeed();
        });
    }

    @GameTest(template="nostalgia_test")
    public static void discPersistsAndBreakingMarqueeDropsItOnce(GameTestHelper helper) {
        Player player = cabinet(helper, GameType.SURVIVAL);
        insert(helper, player, BASE.above());
        helper.runAfterDelay(20, () -> {
            var original = entity(helper);
            var tag = original.saveWithFullMetadata(helper.getLevel().registryAccess());
            var restored = BlockEntity.loadStatic(helper.absolutePos(BASE), helper.getBlockState(BASE), tag,
                helper.getLevel().registryAccess());
            helper.assertTrue(restored instanceof NostalgiaJukeboxBlockEntity, "Saved block entity type did not load");
            var loaded = (NostalgiaJukeboxBlockEntity)restored;
            helper.assertTrue(loaded.getTheItem().is(Items.MUSIC_DISC_13), "Saved disc was lost");
            helper.assertTrue(loaded.getSongPlayer().getTicksSinceSongStarted() >= 15, "Playback progress was lost");
            helper.getLevel().setBlockEntity(loaded);
            helper.getLevel().destroyBlock(helper.absolutePos(BASE.above(2)), true);
            for (int i=0;i<3;i++) { helper.assertBlockPresent(Blocks.AIR, BASE.above(i)); }
            helper.assertItemEntityCountIs(Items.MUSIC_DISC_13, BASE, 3, 1);
            helper.assertItemEntityCountIs(FunPackCustom.NOSTALGIA_OP3_ITEM.get(), BASE, 3, 1);
            helper.assertFalse(loaded.getSongPlayer().isPlaying(), "Removed cabinet still plays");
            helper.succeed();
        });
    }

    @GameTest(template="nostalgia_test")
    public static void creativeBreakReturnsDiscWithoutCabinetDrop(GameTestHelper helper) {
        Player player = cabinet(helper, GameType.CREATIVE);
        insert(helper, player, BASE.above(2));
        helper.assertTrue(player.getMainHandItem().getCount() == 2, "Creative insertion consumed the held disc");
        BlockPos upper = helper.absolutePos(BASE.above());
        var state = helper.getLevel().getBlockState(upper);
        state.getBlock().playerWillDestroy(helper.getLevel(), upper, state, player);
        helper.getLevel().destroyBlock(upper, false, player);
        for (int i=0;i<3;i++) { helper.assertBlockPresent(Blocks.AIR, BASE.above(i)); }
        helper.assertItemEntityCountIs(Items.MUSIC_DISC_13, BASE, 3, 1);
        helper.assertItemEntityCountIs(FunPackCustom.NOSTALGIA_OP3_ITEM.get(), BASE, 3, 0);
        helper.succeed();
    }

    @GameTest(template="nostalgia_test")
    public static void blockedPlacementDoesNotConsumeCabinet(GameTestHelper helper) {
        Player player = player(helper, GameType.SURVIVAL);
        player.setItemInHand(InteractionHand.MAIN_HAND, new ItemStack(FunPackCustom.NOSTALGIA_OP3_ITEM.get(), 2));
        helper.setBlock(BASE.above(2), Blocks.STONE);
        helper.assertFalse(place(helper, player), "Cabinet was placed through an obstruction");
        helper.assertTrue(player.getMainHandItem().getCount() == 2, "Failed placement consumed the cabinet");
        helper.assertBlockPresent(Blocks.AIR, BASE);
        helper.assertBlockPresent(Blocks.AIR, BASE.above());
        helper.succeed();
    }

    @GameTest(template="nostalgia_test")
    public static void placementWithSavedDiscCanEjectIt(GameTestHelper helper) {
        Player player = player(helper, GameType.CREATIVE);
        ItemStack stack = new ItemStack(FunPackCustom.NOSTALGIA_OP3_ITEM.get());
        CompoundTag data = new CompoundTag();
        data.put("RecordItem", new ItemStack(Items.MUSIC_DISC_13).save(helper.getLevel().registryAccess()));
        BlockItem.setBlockEntityData(stack, FunPackCustom.NOSTALGIA_JUKEBOX.get(), data);
        player.setItemInHand(InteractionHand.MAIN_HAND, stack);
        helper.assertTrue(place(helper, player), "Cabinet with saved disc was not placed");
        helper.assertTrue(entity(helper).getTheItem().is(Items.MUSIC_DISC_13), "Placed cabinet lost its saved disc");
        helper.assertBlockProperty(BASE, NostalgiaCabinetBlock.HAS_RECORD, true);
        player.setItemInHand(InteractionHand.MAIN_HAND, ItemStack.EMPTY);
        helper.useBlock(BASE.above(), player);
        helper.assertTrue(entity(helper).isEmpty(), "Saved disc could not be ejected");
        helper.assertItemEntityCountIs(Items.MUSIC_DISC_13, BASE, 3, 1);
        helper.succeed();
    }
}
