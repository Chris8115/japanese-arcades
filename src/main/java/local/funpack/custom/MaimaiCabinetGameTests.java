package local.funpack.custom;

import static local.funpack.custom.NostalgiaCabinetGameTests.BASE;
import static local.funpack.custom.NostalgiaCabinetGameTests.entity;
import static local.funpack.custom.NostalgiaCabinetGameTests.insert;
import static local.funpack.custom.NostalgiaCabinetGameTests.player;

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
import net.minecraft.world.item.context.BlockPlaceContext;
import net.minecraft.world.level.GameType;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.phys.BlockHitResult;
import net.minecraft.world.phys.Vec3;
import net.neoforged.neoforge.gametest.GameTestHolder;
import net.neoforged.neoforge.gametest.PrefixGameTestTemplate;

/** Six-cell maimai placement, one saved jukebox, and connected removal in every facing. */
@GameTestHolder(FunPackCustom.MOD_ID)
@PrefixGameTestTemplate(false)
public final class MaimaiCabinetGameTests {
    private static BlockPos section(BlockPos anchor, Direction facing, int index) {
        return MaimaiCabinetBlock.sectionPosition(anchor, facing,
            MaimaiCabinetBlock.Side.values()[index/3], NostalgiaCabinetBlock.Part.values()[index%3]);
    }

    private static void floors(GameTestHelper helper, BlockPos anchor, Direction facing) {
        helper.setBlock(anchor.below(), Blocks.STONE);
        helper.setBlock(anchor.relative(facing.getClockWise()).below(), Blocks.STONE);
    }

    private static boolean place(GameTestHelper helper, Player player, BlockPos anchor, Direction facing) {
        player.setYRot(facing.getOpposite().toYRot());
        BlockPos floor = helper.absolutePos(anchor.below());
        var hit = new BlockHitResult(Vec3.atCenterOf(floor).add(0,.5,0), Direction.UP, floor, false);
        var context = new BlockPlaceContext(player, InteractionHand.MAIN_HAND, player.getMainHandItem(), hit);
        return ((BlockItem)player.getMainHandItem().getItem()).place(context).consumesAction();
    }

    private static Player cabinet(GameTestHelper helper, GameType mode, Direction facing) {
        Player player = player(helper, mode);
        floors(helper, BASE, facing);
        player.setItemInHand(InteractionHand.MAIN_HAND, new ItemStack(FunPackCustom.MAIMAI_ITEM.get()));
        helper.assertTrue(place(helper, player, BASE, facing), "maimai placement failed facing " + facing);
        assertSixCells(helper, BASE, facing);
        return player;
    }

    private static void assertSixCells(GameTestHelper helper, BlockPos anchor, Direction facing) {
        for (int i=0; i<6; i++) {
            BlockPos pos = section(anchor, facing, i);
            helper.assertBlockPresent(FunPackCustom.MAIMAI.get(), pos);
            helper.assertBlockProperty(pos, NostalgiaCabinetBlock.FACING, facing);
            helper.assertBlockProperty(pos, NostalgiaCabinetBlock.PART, NostalgiaCabinetBlock.Part.values()[i%3]);
            helper.assertBlockProperty(pos, MaimaiCabinetBlock.SIDE, MaimaiCabinetBlock.Side.values()[i/3]);
            var blockEntity = helper.getLevel().getBlockEntity(helper.absolutePos(pos));
            helper.assertTrue(i == 0 ? blockEntity instanceof NostalgiaJukeboxBlockEntity : blockEntity == null,
                "Only the primary base may have a jukebox inventory");
        }
    }

    private static void assertGone(GameTestHelper helper, BlockPos anchor, Direction facing) {
        for (int i=0; i<6; i++) {
            helper.assertBlockPresent(Blocks.AIR, section(anchor, facing, i));
        }
    }

    private static void clearDrops(GameTestHelper helper) {
        helper.getEntities(EntityType.ITEM, BASE, 3).forEach(item -> item.discard());
    }

    private static void creativeRemove(GameTestHelper helper, Player player, BlockPos pos) {
        var absolute = helper.absolutePos(pos);
        var state = helper.getLevel().getBlockState(absolute);
        state.getBlock().playerWillDestroy(helper.getLevel(), absolute, state, player);
        helper.getLevel().destroyBlock(absolute, false, player);
    }

    @GameTest(template="nostalgia_test")
    public static void maimaiAllSixSectionsShareOnePlayerAndEjectInEveryFacing(GameTestHelper helper) {
        for (Direction facing : Direction.Plane.HORIZONTAL) {
            var player = cabinet(helper, GameType.SURVIVAL, facing);
            player.setItemInHand(InteractionHand.MAIN_HAND, new ItemStack(Items.STICK));
            helper.useBlock(section(BASE, facing, 4), player);
            helper.assertTrue(entity(helper).isEmpty(), "A secondary section accepted a non-disc item");
            for (int i=0; i<6; i++) {
                insert(helper, player, section(BASE, facing, i));
                helper.assertTrue(player.getMainHandItem().getCount() == 1,
                    "A section did not consume exactly one disc");
                player.setItemInHand(InteractionHand.MAIN_HAND, ItemStack.EMPTY);
                helper.useBlock(section(BASE, facing, (i+3)%6), player);
                helper.assertTrue(entity(helper).isEmpty() && !entity(helper).getSongPlayer().isPlaying(),
                    "Ejection through the opposite column did not clear playback");
                var drops = helper.getEntities(EntityType.ITEM, BASE, 3);
                helper.assertTrue(drops.size() == 1 && drops.getFirst().getItem().is(Items.MUSIC_DISC_13),
                    "A section failed to eject exactly one disc");
                var disc = drops.getFirst();
                for (int j=0; j<6; j++) {
                    var pos = helper.absolutePos(section(BASE, facing, j));
                    for (var box : helper.getLevel().getBlockState(pos).getCollisionShape(helper.getLevel(), pos).toAabbs()) {
                        helper.assertFalse(box.move(pos.getX(), pos.getY(), pos.getZ()).intersects(disc.getBoundingBox()),
                            "A newly ejected disc intersects maimai facing " + facing);
                    }
                }
                helper.assertTrue(helper.getLevel().noCollision(disc, disc.getBoundingBox()),
                    "World collision obstructs the ejected disc");
                disc.discard();
            }
            helper.getLevel().destroyBlock(helper.absolutePos(BASE), false);
            assertGone(helper, BASE, facing);
            clearDrops(helper);
        }
        helper.succeed();
    }

    @GameTest(template="nostalgia_test")
    public static void maimaiBreakingAnyCellDropsOneCabinetAndDiscInEveryFacing(GameTestHelper helper) {
        for (Direction facing : Direction.Plane.HORIZONTAL) {
            for (int broken=0; broken<6; broken++) {
                var player = cabinet(helper, GameType.SURVIVAL, facing);
                insert(helper, player, section(BASE, facing, 5));
                var removed = entity(helper);
                helper.getLevel().destroyBlock(helper.absolutePos(section(BASE, facing, broken)), true);
                assertGone(helper, BASE, facing);
                helper.assertItemEntityCountIs(FunPackCustom.MAIMAI_ITEM.get(), BASE, 3, 1);
                helper.assertItemEntityCountIs(Items.MUSIC_DISC_13, BASE, 3, 1);
                helper.assertFalse(removed.getSongPlayer().isPlaying(), "Removed maimai still plays");
                clearDrops(helper);
            }
        }
        helper.succeed();
    }

    @GameTest(template="nostalgia_test")
    public static void maimaiCreativeRemovalKeepsAdjacentPairPlayingInEveryFacing(GameTestHelper helper) {
        for (Direction facing : Direction.Plane.HORIZONTAL) {
            for (int broken=0; broken<6; broken++) {
                var player = cabinet(helper, GameType.CREATIVE, facing);
                insert(helper, player, section(BASE, facing, 4));
                BlockPos neighbor = BASE.relative(facing.getClockWise(), 2);
                floors(helper, neighbor, facing);
                player.setItemInHand(InteractionHand.MAIN_HAND, new ItemStack(FunPackCustom.MAIMAI_ITEM.get()));
                helper.assertTrue(place(helper, player, neighbor, facing), "Adjacent maimai placement failed");
                assertSixCells(helper, neighbor, facing);
                player.setItemInHand(InteractionHand.MAIN_HAND, new ItemStack(Items.MUSIC_DISC_CAT));
                helper.useBlock(section(neighbor, facing, 5), player);
                var neighborEntity = (NostalgiaJukeboxBlockEntity)helper.getBlockEntity(neighbor);
                creativeRemove(helper, player, section(BASE, facing, broken));
                assertGone(helper, BASE, facing);
                assertSixCells(helper, neighbor, facing);
                helper.assertTrue(neighborEntity.getTheItem().is(Items.MUSIC_DISC_CAT)
                        && neighborEntity.getSongPlayer().isPlaying(),
                    "Removing one double cabinet affected the adjacent cabinet's playback");
                helper.assertItemEntityCountIs(FunPackCustom.MAIMAI_ITEM.get(), BASE, 3, 0);
                helper.assertItemEntityCountIs(Items.MUSIC_DISC_13, BASE, 3, 1);
                helper.assertItemEntityCountIs(Items.MUSIC_DISC_CAT, BASE, 3, 0);
                creativeRemove(helper, player, neighbor);
                clearDrops(helper);
            }
        }
        helper.succeed();
    }

    @GameTest(template="nostalgia_test")
    public static void maimaiSavedDiscRestoresAndEjectsThroughSecondaryMarquee(GameTestHelper helper) {
        Direction facing = Direction.WEST;
        var player = player(helper, GameType.SURVIVAL);
        floors(helper, BASE, facing);
        ItemStack stack = new ItemStack(FunPackCustom.MAIMAI_ITEM.get());
        CompoundTag data = new CompoundTag();
        data.put("RecordItem", new ItemStack(Items.MUSIC_DISC_13).save(helper.getLevel().registryAccess()));
        data.putLong("ticks_since_song_started", 40);
        BlockItem.setBlockEntityData(stack, FunPackCustom.NOSTALGIA_JUKEBOX.get(), data);
        player.setItemInHand(InteractionHand.MAIN_HAND, stack);
        helper.assertTrue(place(helper, player, BASE, facing), "Saved-disc maimai placement failed");
        assertSixCells(helper, BASE, facing);
        helper.assertBlockProperty(BASE, NostalgiaCabinetBlock.HAS_RECORD, true);
        helper.runAfterDelay(25, () -> {
            var tag = entity(helper).saveWithFullMetadata(helper.getLevel().registryAccess());
            var restored = BlockEntity.loadStatic(helper.absolutePos(BASE), helper.getBlockState(BASE), tag,
                helper.getLevel().registryAccess());
            helper.assertTrue(restored instanceof NostalgiaJukeboxBlockEntity, "Saved maimai inventory did not load");
            var loaded = (NostalgiaJukeboxBlockEntity)restored;
            helper.assertTrue(loaded.getTheItem().is(Items.MUSIC_DISC_13)
                    && loaded.getSongPlayer().getTicksSinceSongStarted() >= 60,
                "maimai lost its saved disc or playback progress");
            helper.getLevel().setBlockEntity(loaded);
            player.setItemInHand(InteractionHand.MAIN_HAND, ItemStack.EMPTY);
            helper.useBlock(section(BASE, facing, 5), player);
            helper.assertTrue(loaded.isEmpty() && !loaded.getSongPlayer().isPlaying(),
                "The saved disc did not eject through the secondary marquee");
            helper.assertItemEntityCountIs(Items.MUSIC_DISC_13, BASE, 3, 1);
            helper.getLevel().destroyBlock(helper.absolutePos(section(BASE, facing, 3)), true);
            assertGone(helper, BASE, facing);
            helper.assertItemEntityCountIs(FunPackCustom.MAIMAI_ITEM.get(), BASE, 3, 1);
            helper.assertItemEntityCountIs(Items.MUSIC_DISC_13, BASE, 3, 1);
            helper.succeed();
        });
    }

    @GameTest(template="nostalgia_test")
    public static void maimaiBlockedColumnsAndMissingSecondSupportLeaveNoFragments(GameTestHelper helper) {
        var player = player(helper, GameType.SURVIVAL);
        for (Direction facing : Direction.Plane.HORIZONTAL) {
            for (int blocked=1; blocked<6; blocked++) {
                floors(helper, BASE, facing);
                BlockPos obstacle = section(BASE, facing, blocked);
                helper.setBlock(obstacle, Blocks.STONE);
                player.setItemInHand(InteractionHand.MAIN_HAND, new ItemStack(FunPackCustom.MAIMAI_ITEM.get(), 2));
                helper.assertFalse(place(helper, player, BASE, facing), "maimai placed through an occupied cell");
                helper.assertTrue(player.getMainHandItem().getCount() == 2, "Failed placement consumed maimai");
                for (int i=0; i<6; i++) {
                    helper.assertBlockPresent(i == blocked ? Blocks.STONE : Blocks.AIR, section(BASE, facing, i));
                }
                helper.setBlock(obstacle, Blocks.AIR);
            }
            floors(helper, BASE, facing);
            helper.setBlock(BASE.relative(facing.getClockWise()).below(), Blocks.AIR);
            player.setItemInHand(InteractionHand.MAIN_HAND, new ItemStack(FunPackCustom.MAIMAI_ITEM.get(), 2));
            helper.assertFalse(place(helper, player, BASE, facing), "maimai placed without its second support");
            helper.assertTrue(player.getMainHandItem().getCount() == 2, "Unsupported placement consumed maimai");
            assertGone(helper, BASE, facing);
        }
        helper.succeed();
    }

    @GameTest(template="nostalgia_test")
    public static void maimaiLosingEitherSupportRemovesThePairOnceInEveryFacing(GameTestHelper helper) {
        for (Direction facing : Direction.Plane.HORIZONTAL) {
            for (int support=0; support<2; support++) {
                var player = cabinet(helper, GameType.SURVIVAL, facing);
                insert(helper, player, section(BASE, facing, 5));
                helper.getLevel().destroyBlock(helper.absolutePos(BASE.relative(facing.getClockWise(), support).below()), false);
                assertGone(helper, BASE, facing);
                helper.assertItemEntityCountIs(FunPackCustom.MAIMAI_ITEM.get(), BASE, 3, 1);
                helper.assertItemEntityCountIs(Items.MUSIC_DISC_13, BASE, 3, 1);
                clearDrops(helper);
            }
        }
        helper.succeed();
    }
}
