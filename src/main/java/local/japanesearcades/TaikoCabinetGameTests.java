package local.japanesearcades;

import static local.japanesearcades.NostalgiaCabinetGameTests.BASE;
import static local.japanesearcades.NostalgiaCabinetGameTests.entity;
import static local.japanesearcades.NostalgiaCabinetGameTests.insert;
import static local.japanesearcades.NostalgiaCabinetGameTests.player;

import java.util.ArrayList;
import java.util.List;
import java.util.function.Consumer;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.gametest.framework.GameTest;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.entity.EntityType;
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
import net.neoforged.neoforge.common.NeoForge;
import net.neoforged.neoforge.event.PlayLevelSoundEvent;
import net.neoforged.neoforge.event.entity.player.PlayerInteractEvent;
import net.neoforged.neoforge.gametest.GameTestHolder;
import net.neoforged.neoforge.gametest.PrefixGameTestTemplate;

/** Connected ten-cell placement and real server drum rays, interactions and sounds. */
@GameTestHolder(JapaneseArcades.MOD_ID)
@PrefixGameTestTemplate(false)
public final class TaikoCabinetGameTests {
    private static BlockPos section(BlockPos anchor, Direction facing, int index) {
        return TaikoCabinetBlock.sectionPosition(anchor, facing,
            TaikoCabinetBlock.Side.values()[index/5], TaikoCabinetBlock.Section.values()[index%5]);
    }

    private static void floors(GameTestHelper helper, BlockPos anchor, Direction facing) {
        for (int side = 0; side < 2; side++) {
            for (int depth = 0; depth < 2; depth++) {
                helper.setBlock(anchor.relative(facing.getClockWise(), side).relative(facing, depth).below(), Blocks.STONE);
            }
        }
    }

    private static boolean place(GameTestHelper helper, Player player, BlockPos anchor, Direction facing) {
        player.setYRot(facing.getOpposite().toYRot());
        var floor = helper.absolutePos(anchor.below());
        var hit = new BlockHitResult(Vec3.atCenterOf(floor).add(0, .5, 0), Direction.UP, floor, false);
        return ((BlockItem)player.getMainHandItem().getItem()).place(
            new BlockPlaceContext(player, InteractionHand.MAIN_HAND, player.getMainHandItem(), hit)).consumesAction();
    }

    private static Player cabinet(GameTestHelper helper, Direction facing) {
        Player player = player(helper, GameType.SURVIVAL);
        floors(helper, BASE, facing);
        player.setItemInHand(InteractionHand.MAIN_HAND, new ItemStack(JapaneseArcades.TAIKO_ITEM.get()));
        helper.assertTrue(place(helper, player, BASE, facing), "Taiko placement failed facing " + facing);
        for (int index = 0; index < 10; index++) {
            BlockPos pos = section(BASE, facing, index);
            helper.assertBlockPresent(JapaneseArcades.TAIKO.get(), pos);
            helper.assertBlockProperty(pos, TaikoCabinetBlock.FACING, facing);
            helper.assertBlockProperty(pos, TaikoCabinetBlock.SIDE, TaikoCabinetBlock.Side.values()[index/5]);
            helper.assertBlockProperty(pos, TaikoCabinetBlock.SECTION, TaikoCabinetBlock.Section.values()[index%5]);
            helper.assertTrue(index == 0 ? helper.getBlockEntity(pos) instanceof NostalgiaJukeboxBlockEntity
                : helper.getLevel().getBlockEntity(helper.absolutePos(pos)) == null, "Only the primary rear base may store a disc");
        }
        return player;
    }

    private static void gone(GameTestHelper helper, BlockPos anchor, Direction facing) {
        for (int index = 0; index < 10; index++) { helper.assertBlockPresent(Blocks.AIR, section(anchor, facing, index)); }
    }

    private static void drops(GameTestHelper helper) { helper.getEntities(EntityType.ITEM, BASE, 5).forEach(item -> item.discard()); }

    private static void creativeRemove(GameTestHelper helper, Player player, BlockPos relative) {
        BlockPos pos = helper.absolutePos(relative);
        var state = helper.getLevel().getBlockState(pos);
        state.getBlock().playerWillDestroy(helper.getLevel(), pos, state, player);
        helper.getLevel().destroyBlock(pos, false, player);
    }

    @GameTest(template = "nostalgia_test")
    public static void taikoAllTenCellsRemoveOnceAndKeepNeighborsInEveryFacing(GameTestHelper helper) {
        for (Direction facing : Direction.Plane.HORIZONTAL) {
            for (int broken = 0; broken < 10; broken++) {
                Player player = cabinet(helper, facing);
                insert(helper, player, section(BASE, facing, 6));
                helper.getLevel().destroyBlock(helper.absolutePos(section(BASE, facing, broken)), true);
                gone(helper, BASE, facing);
                helper.assertItemEntityCountIs(JapaneseArcades.TAIKO_ITEM.get(), BASE, 5, 1);
                helper.assertItemEntityCountIs(Items.MUSIC_DISC_13, BASE, 5, 1);
                drops(helper);
            }
            for (int broken = 0; broken < 10; broken++) {
                Player player = cabinet(helper, facing);
                insert(helper, player, BASE);
                BlockPos neighbor = BASE.relative(facing.getClockWise(), 2);
                floors(helper, neighbor, facing);
                player.setItemInHand(InteractionHand.MAIN_HAND, new ItemStack(JapaneseArcades.TAIKO_ITEM.get()));
                helper.assertTrue(place(helper, player, neighbor, facing), "Neighbor Taiko placement failed");
                Player creative = player(helper, GameType.CREATIVE);
                creativeRemove(helper, creative, section(BASE, facing, broken));
                gone(helper, BASE, facing);
                for (int index = 0; index < 10; index++) {
                    helper.assertBlockPresent(JapaneseArcades.TAIKO.get(), section(neighbor, facing, index));
                }
                helper.assertItemEntityCountIs(JapaneseArcades.TAIKO_ITEM.get(), BASE, 5, 0);
                helper.assertItemEntityCountIs(Items.MUSIC_DISC_13, BASE, 5, 1);
                creativeRemove(helper, creative, neighbor);
                drops(helper);
            }
        }
        helper.succeed();
    }

    @GameTest(template = "nostalgia_test")
    public static void taikoBlockedCellsAndMissingSupportsLeaveNoFragments(GameTestHelper helper) {
        Player player = player(helper, GameType.SURVIVAL);
        for (Direction facing : Direction.Plane.HORIZONTAL) {
            for (int blocked = 1; blocked < 10; blocked++) {
                floors(helper, BASE, facing);
                BlockPos obstacle = section(BASE, facing, blocked);
                helper.setBlock(obstacle, Blocks.STONE);
                player.setItemInHand(InteractionHand.MAIN_HAND, new ItemStack(JapaneseArcades.TAIKO_ITEM.get(), 2));
                helper.assertFalse(place(helper, player, BASE, facing), "Taiko placed through an occupied cell");
                helper.assertTrue(player.getMainHandItem().getCount() == 2, "Failed placement consumed Taiko");
                for (int index = 0; index < 10; index++) {
                    helper.assertBlockPresent(index == blocked ? Blocks.STONE : Blocks.AIR, section(BASE, facing, index));
                }
                helper.setBlock(obstacle, Blocks.AIR);
            }
            for (int support = 0; support < 4; support++) {
                cabinet(helper, facing);
                var floor = BASE.relative(facing.getClockWise(), support/2).relative(facing, support%2).below();
                helper.getLevel().destroyBlock(helper.absolutePos(floor), false);
                gone(helper, BASE, facing);
                helper.assertItemEntityCountIs(JapaneseArcades.TAIKO_ITEM.get(), BASE, 4, 1);
                drops(helper);
            }
        }
        helper.succeed();
    }

    @GameTest(template = "nostalgia_test")
    public static void taikoRearSectionsShareOneJukeboxAndDrumsNeverEjectIt(GameTestHelper helper) {
        for (Direction facing : Direction.Plane.HORIZONTAL) {
            Player player = cabinet(helper, facing);
            for (int index : new int[]{0,1,2,5,6,7}) {
                insert(helper, player, section(BASE, facing, index));
                player.setItemInHand(InteractionHand.MAIN_HAND, ItemStack.EMPTY);
                helper.useBlock(section(BASE, facing, 3), player);
                helper.useBlock(section(BASE, facing, 4), player);
                helper.useBlock(section(BASE, facing, 8), player);
                helper.useBlock(section(BASE, facing, 9), player);
                helper.assertTrue(entity(helper).getTheItem().is(Items.MUSIC_DISC_13), "A drum or pedestal ejected the music disc");
                helper.useBlock(section(BASE, facing, index < 5 ? 6 : 1), player);
                helper.assertTrue(entity(helper).isEmpty() && !entity(helper).getSongPlayer().isPlaying(), "Rear interaction did not eject the disc");
                helper.assertItemEntityCountIs(Items.MUSIC_DISC_13, BASE, 4, 1);
                var disc = helper.getEntities(EntityType.ITEM, BASE, 4).getFirst();
                helper.assertTrue(helper.getLevel().noCollision(disc, disc.getBoundingBox()), "Ejected disc intersects the drum plinth");
                drops(helper);
            }
            helper.getLevel().destroyBlock(helper.absolutePos(BASE), false);
            drops(helper);
        }
        helper.succeed();
    }

    private static Vec3 aim(Player player, BlockPos anchor, Direction facing, TaikoCabinetBlock.Side side, double radial) {
        Vec3 target = TaikoDrumInteraction.headCenter(anchor, facing, side);
        target = target.add(TaikoDrumInteraction.drumAcross(facing, side).scale(radial/16));
        Vec3 eye = target.add(TaikoDrumInteraction.drumNormal(facing, side).scale(2));
        look(player, eye, target);
        return target;
    }

    private static void look(Player player, Vec3 eye, Vec3 target) {
        player.setPos(eye.x, eye.y-player.getEyeHeight(), eye.z);
        Vec3 delta = target.subtract(eye);
        player.setYRot((float)Math.toDegrees(Math.atan2(-delta.x, delta.z)));
        player.setYHeadRot(player.getYRot());
        player.setXRot((float)-Math.toDegrees(Math.atan2(delta.y, Math.sqrt(delta.x*delta.x+delta.z*delta.z))));
    }

    private static boolean drumSound(GameTestHelper helper, PlayLevelSoundEvent.AtPosition sound) {
        return sound.getLevel() == helper.getLevel() && sound.getPosition().distanceToSqr(helper.absolutePos(BASE).getCenter()) < 16
            && (sound.getSound() == SoundEvents.NOTE_BLOCK_BASEDRUM || sound.getSound() == SoundEvents.NOTE_BLOCK_HAT);
    }

    @GameTest(template = "nostalgia_test")
    public static void taikoHeadRimAndBothHandsPlayOneCorrectSoundInEveryFacing(GameTestHelper helper) {
        List<PlayLevelSoundEvent.AtPosition> heard = new ArrayList<>();
        Consumer<PlayLevelSoundEvent.AtPosition> listener = sound -> { if (drumSound(helper, sound)) { heard.add(sound); } };
        NeoForge.EVENT_BUS.addListener(listener);
        try {
            for (Direction facing : Direction.Plane.HORIZONTAL) {
                cabinet(helper, facing);
                for (TaikoCabinetBlock.Side side : TaikoCabinetBlock.Side.values()) {
                    for (boolean rim : new boolean[]{false, true}) {
                        ServerPlayer player = GachaponTransactionGameTests.createPlayer(helper, "TaikoSound", GameType.SURVIVAL);
                        player.setItemInHand(InteractionHand.MAIN_HAND, rim ? new ItemStack(Items.STICK) : ItemStack.EMPTY);
                        BlockPos relative = TaikoCabinetBlock.sectionPosition(BASE, facing, side, TaikoCabinetBlock.Section.DRUMS);
                        BlockPos pos = helper.absolutePos(relative);
                        Vec3 hitPoint = aim(player, helper.absolutePos(BASE), facing, side, rim ? 6.45 : 0);
                        int before = heard.size();
                        helper.useBlock(relative, player);
                        helper.assertTrue(heard.size() == before+1, "Drum ray did not produce exactly one sound: " + facing + " " + side + " rim=" + rim);
                        var sound = heard.getLast();
                        helper.assertTrue(sound.getSound() == (rim ? SoundEvents.NOTE_BLOCK_HAT : SoundEvents.NOTE_BLOCK_BASEDRUM)
                            && sound.getSource() == SoundSource.BLOCKS && Math.abs(sound.getOriginalPitch()-(rim ? 1.2F : .8F)) < .001,
                            "Head and rim must emit distinct server-broadcast note-block sounds");
                        var state = helper.getLevel().getBlockState(pos);
                        JapaneseArcades.TAIKO.get().useItemOn(ItemStack.EMPTY, state, helper.getLevel(), pos, player,
                            InteractionHand.OFF_HAND, new BlockHitResult(hitPoint, facing, pos, false));
                        var left = new PlayerInteractEvent.LeftClickBlock(player, pos, facing, PlayerInteractEvent.LeftClickBlock.Action.START);
                        NeoForge.EVENT_BUS.post(left);
                        helper.assertTrue(left.isCanceled() && heard.size() == before+1,
                            "Same-tick other hand or left click duplicated a beat or began mining");
                        player.setShiftKeyDown(true);
                        var sneak = new PlayerInteractEvent.LeftClickBlock(player, pos, facing, PlayerInteractEvent.LeftClickBlock.Action.START);
                        NeoForge.EVENT_BUS.post(sneak);
                        helper.assertFalse(sneak.isCanceled(), "Sneak-left-click must allow intentional machine removal");
                    }
                }
                helper.getLevel().destroyBlock(helper.absolutePos(BASE), false);
                drops(helper);
            }
        } finally { NeoForge.EVENT_BUS.unregister(listener); }
        helper.succeed();
    }

    @GameTest(template = "nostalgia_test")
    public static void taikoInvalidRegionsToolsRangeAndWallsDoNotPlay(GameTestHelper helper) {
        Direction facing = Direction.NORTH;
        cabinet(helper, facing);
        ServerPlayer player = GachaponTransactionGameTests.createPlayer(helper, "TaikoRay", GameType.SURVIVAL);
        BlockPos pos = helper.absolutePos(section(BASE, facing, 4));
        BlockPos anchor = helper.absolutePos(BASE);
        player.setItemInHand(InteractionHand.MAIN_HAND, ItemStack.EMPTY);
        aim(player, anchor, facing, TaikoCabinetBlock.Side.PRIMARY, 7.4);
        helper.assertFalse(TaikoDrumInteraction.tryHit(player, pos), "A point beyond the outer rim played a sound");
        aim(player, anchor, facing, TaikoCabinetBlock.Side.PRIMARY, 0);
        player.setItemInHand(InteractionHand.MAIN_HAND, new ItemStack(Items.DIAMOND_PICKAXE));
        var mining = new PlayerInteractEvent.LeftClickBlock(player, pos, facing, PlayerInteractEvent.LeftClickBlock.Action.START);
        NeoForge.EVENT_BUS.post(mining);
        helper.assertFalse(mining.isCanceled(), "A real mining tool was prevented from removing the cabinet");
        helper.assertFalse(TaikoDrumInteraction.tryHit(player, pos), "A pickaxe played a drum");
        player.setItemInHand(InteractionHand.MAIN_HAND, ItemStack.EMPTY);
        Vec3 target = aim(player, anchor, facing, TaikoCabinetBlock.Side.PRIMARY, 0);
        Vec3 eye = player.getEyePosition();
        look(player, eye.add(0, 0, -8), target);
        helper.assertFalse(TaikoDrumInteraction.tryHit(player, pos), "An out-of-reach drum played");
        aim(player, anchor, facing, TaikoCabinetBlock.Side.PRIMARY, 0);
        BlockPos wall = BlockPos.containing(player.getEyePosition().lerp(target, .45));
        helper.getLevel().setBlock(wall, Blocks.STONE.defaultBlockState(), 3);
        helper.assertFalse(TaikoDrumInteraction.tryHit(player, pos), "A forged click played through an intervening wall");
        helper.getLevel().setBlock(wall, Blocks.AIR.defaultBlockState(), 3);
        helper.assertTrue(TaikoDrumInteraction.tryHit(player, pos), "Clearing the wall did not restore a valid drum strike");
        helper.succeed();
    }

    @GameTest(template = "nostalgia_test", timeoutTicks = 80)
    public static void taikoSavedDiscKeepsPlayingAndLeftClickBeatsResumeAfterCooldown(GameTestHelper helper) {
        Direction facing = Direction.WEST;
        Player placer = cabinet(helper, facing);
        insert(helper, placer, section(BASE, facing, 7));
        CompoundTag saved = entity(helper).saveWithFullMetadata(helper.getLevel().registryAccess());
        var restored = (NostalgiaJukeboxBlockEntity)BlockEntity.loadStatic(helper.absolutePos(BASE), helper.getBlockState(BASE),
            saved, helper.getLevel().registryAccess());
        helper.assertTrue(restored != null && restored.getTheItem().is(Items.MUSIC_DISC_13), "Taiko lost its saved jukebox inventory");
        helper.getLevel().setBlockEntity(restored);
        ServerPlayer drummer = GachaponTransactionGameTests.createPlayer(helper, "TaikoLeft", GameType.SURVIVAL);
        drummer.setItemInHand(InteractionHand.MAIN_HAND, new ItemStack(Items.STICK));
        BlockPos drum = helper.absolutePos(section(BASE, facing, 9));
        aim(drummer, helper.absolutePos(BASE), facing, TaikoCabinetBlock.Side.SECONDARY, 0);
        List<PlayLevelSoundEvent.AtPosition> heard = new ArrayList<>();
        Consumer<PlayLevelSoundEvent.AtPosition> listener = sound -> { if (drumSound(helper, sound)) { heard.add(sound); } };
        NeoForge.EVENT_BUS.addListener(listener);
        var click = new PlayerInteractEvent.LeftClickBlock(drummer, drum, facing, PlayerInteractEvent.LeftClickBlock.Action.START);
        NeoForge.EVENT_BUS.post(click);
        helper.assertTrue(click.isCanceled() && heard.size() == 1, "Initial left strike did not cancel mining and play a beat");
        helper.runAfterDelay(4, () -> {
            try {
                var second = new PlayerInteractEvent.LeftClickBlock(drummer, drum, facing, PlayerInteractEvent.LeftClickBlock.Action.START);
                NeoForge.EVENT_BUS.post(second);
                helper.assertTrue(second.isCanceled() && heard.size() == 2, "Beat cooldown never reopened for a second stroke");
                helper.assertTrue(restored.getTheItem().is(Items.MUSIC_DISC_13) && restored.getSongPlayer().isPlaying(),
                    "Striking the drums interrupted the saved song");
                helper.assertTrue(restored.getSongPlayer().getTicksSinceSongStarted() >= 4, "Saved jukebox did not continue ticking");
                helper.assertBlockPresent(JapaneseArcades.TAIKO.get(), section(BASE, facing, 9));
                helper.succeed();
            } finally { NeoForge.EVENT_BUS.unregister(listener); }
        });
    }
}
