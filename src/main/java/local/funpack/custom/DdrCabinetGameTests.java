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
import net.minecraft.world.entity.MoverType;
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

/** Twelve-cell DDR placement, one saved jukebox, and connected removal in every facing. */
@GameTestHolder(FunPackCustom.MOD_ID)
@PrefixGameTestTemplate(false)
public final class DdrCabinetGameTests {
    private static BlockPos section(BlockPos anchor, Direction facing, int index) {
        return DdrCabinetBlock.sectionPosition(anchor, facing,
            DdrCabinetBlock.Side.values()[index/6], DdrCabinetBlock.Section.values()[index%6]);
    }

    private static void floors(GameTestHelper helper, BlockPos anchor, Direction facing) {
        for (int side=0; side<2; side++) {
            for (int depth=0; depth<3; depth++) {
                helper.setBlock(anchor.relative(facing.getClockWise(),side).relative(facing,depth).below(), Blocks.STONE);
            }
        }
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
        player.setItemInHand(InteractionHand.MAIN_HAND, new ItemStack(FunPackCustom.DDR_SUPERNOVA_ITEM.get()));
        helper.assertTrue(place(helper, player, BASE, facing), "ddr placement failed facing " + facing);
        assertTwelveCells(helper, BASE, facing);
        return player;
    }

    private static void assertTwelveCells(GameTestHelper helper, BlockPos anchor, Direction facing) {
        for (int i=0; i<12; i++) {
            BlockPos pos = section(anchor, facing, i);
            helper.assertBlockPresent(FunPackCustom.DDR_SUPERNOVA.get(), pos);
            helper.assertBlockProperty(pos, NostalgiaCabinetBlock.FACING, facing);
            helper.assertBlockProperty(pos, NostalgiaCabinetBlock.PART, NostalgiaCabinetBlock.Part.values()[DdrCabinetBlock.Section.values()[i%6].height]);
            helper.assertBlockProperty(pos, DdrCabinetBlock.SIDE, DdrCabinetBlock.Side.values()[i/6]);
            helper.assertBlockProperty(pos, DdrCabinetBlock.SECTION, DdrCabinetBlock.Section.values()[i%6]);
            var blockEntity = helper.getLevel().getBlockEntity(helper.absolutePos(pos));
            helper.assertTrue(i == 0 ? blockEntity instanceof NostalgiaJukeboxBlockEntity : blockEntity == null,
                "Only the primary base may have a jukebox inventory");
        }
        for (int side=0; side<2; side++) {
            BlockPos lane = anchor.relative(facing.getClockWise(), side);
            helper.assertBlockPresent(Blocks.AIR, lane.relative(facing).above());
            helper.assertBlockPresent(Blocks.AIR, lane.relative(facing).above(2));
            helper.assertBlockPresent(Blocks.AIR, lane.relative(facing,2).above(2));
        }
    }

    private static void assertGone(GameTestHelper helper, BlockPos anchor, Direction facing) {
        for (int i=0; i<12; i++) {
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
    public static void ddrAllTwelveSectionsShareOnePlayerAndEjectInEveryFacing(GameTestHelper helper) {
        for (Direction facing : Direction.Plane.HORIZONTAL) {
            var player = cabinet(helper, GameType.SURVIVAL, facing);
            player.setItemInHand(InteractionHand.MAIN_HAND, new ItemStack(Items.STICK));
            helper.useBlock(section(BASE, facing, 4), player);
            helper.assertTrue(entity(helper).isEmpty(), "A secondary section accepted a non-disc item");
            for (int i=0; i<12; i++) {
                insert(helper, player, section(BASE, facing, i));
                helper.assertTrue(player.getMainHandItem().getCount() == 1,
                    "A section did not consume exactly one disc");
                player.setItemInHand(InteractionHand.MAIN_HAND, ItemStack.EMPTY);
                helper.useBlock(section(BASE, facing, (i+6)%12), player);
                helper.assertTrue(entity(helper).isEmpty() && !entity(helper).getSongPlayer().isPlaying(),
                    "Ejection through the opposite column did not clear playback");
                var drops = helper.getEntities(EntityType.ITEM, BASE, 3);
                helper.assertTrue(drops.size() == 1 && drops.getFirst().getItem().is(Items.MUSIC_DISC_13),
                    "A section failed to eject exactly one disc");
                var disc = drops.getFirst();
                for (int j=0; j<12; j++) {
                    var pos = helper.absolutePos(section(BASE, facing, j));
                    for (var box : helper.getLevel().getBlockState(pos).getCollisionShape(helper.getLevel(), pos).toAabbs()) {
                        helper.assertFalse(box.move(pos.getX(), pos.getY(), pos.getZ()).intersects(disc.getBoundingBox()),
                            "A newly ejected disc intersects ddr facing " + facing);
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
    public static void ddrBreakingAnyCellDropsOneCabinetAndDiscInEveryFacing(GameTestHelper helper) {
        for (Direction facing : Direction.Plane.HORIZONTAL) {
            for (int broken=0; broken<12; broken++) {
                var player = cabinet(helper, GameType.SURVIVAL, facing);
                insert(helper, player, section(BASE, facing, 11));
                var removed = entity(helper);
                helper.getLevel().destroyBlock(helper.absolutePos(section(BASE, facing, broken)), true);
                assertGone(helper, BASE, facing);
                helper.assertItemEntityCountIs(FunPackCustom.DDR_SUPERNOVA_ITEM.get(), BASE, 3, 1);
                helper.assertItemEntityCountIs(Items.MUSIC_DISC_13, BASE, 3, 1);
                helper.assertFalse(removed.getSongPlayer().isPlaying(), "Removed ddr still plays");
                clearDrops(helper);
            }
        }
        helper.succeed();
    }

    @GameTest(template="nostalgia_test")
    public static void ddrCreativeRemovalKeepsAdjacentPairPlayingInEveryFacing(GameTestHelper helper) {
        for (Direction facing : Direction.Plane.HORIZONTAL) {
            for (int broken=0; broken<12; broken++) {
                var player = cabinet(helper, GameType.CREATIVE, facing);
                insert(helper, player, section(BASE, facing, 4));
                BlockPos neighbor = BASE.relative(facing.getClockWise(), 2);
                floors(helper, neighbor, facing);
                player.setItemInHand(InteractionHand.MAIN_HAND, new ItemStack(FunPackCustom.DDR_SUPERNOVA_ITEM.get()));
                helper.assertTrue(place(helper, player, neighbor, facing), "Adjacent ddr placement failed");
                assertTwelveCells(helper, neighbor, facing);
                player.setItemInHand(InteractionHand.MAIN_HAND, new ItemStack(Items.MUSIC_DISC_CAT));
                helper.useBlock(section(neighbor, facing, 11), player);
                var neighborEntity = (NostalgiaJukeboxBlockEntity)helper.getBlockEntity(neighbor);
                creativeRemove(helper, player, section(BASE, facing, broken));
                assertGone(helper, BASE, facing);
                assertTwelveCells(helper, neighbor, facing);
                helper.assertTrue(neighborEntity.getTheItem().is(Items.MUSIC_DISC_CAT)
                        && neighborEntity.getSongPlayer().isPlaying(),
                    "Removing one double cabinet affected the adjacent cabinet's playback");
                helper.assertItemEntityCountIs(FunPackCustom.DDR_SUPERNOVA_ITEM.get(), BASE, 3, 0);
                helper.assertItemEntityCountIs(Items.MUSIC_DISC_13, BASE, 3, 1);
                helper.assertItemEntityCountIs(Items.MUSIC_DISC_CAT, BASE, 3, 0);
                creativeRemove(helper, player, neighbor);
                clearDrops(helper);
            }
        }
        helper.succeed();
    }

    @GameTest(template="nostalgia_test")
    public static void ddrSavedDiscRestoresAndEjectsThroughSecondaryRail(GameTestHelper helper) {
        Direction facing = Direction.WEST;
        var player = player(helper, GameType.SURVIVAL);
        floors(helper, BASE, facing);
        ItemStack stack = new ItemStack(FunPackCustom.DDR_SUPERNOVA_ITEM.get());
        CompoundTag data = new CompoundTag();
        data.put("RecordItem", new ItemStack(Items.MUSIC_DISC_13).save(helper.getLevel().registryAccess()));
        data.putLong("ticks_since_song_started", 40);
        BlockItem.setBlockEntityData(stack, FunPackCustom.NOSTALGIA_JUKEBOX.get(), data);
        player.setItemInHand(InteractionHand.MAIN_HAND, stack);
        helper.assertTrue(place(helper, player, BASE, facing), "Saved-disc ddr placement failed");
        assertTwelveCells(helper, BASE, facing);
        helper.assertBlockProperty(BASE, NostalgiaCabinetBlock.HAS_RECORD, true);
        helper.runAfterDelay(25, () -> {
            var tag = entity(helper).saveWithFullMetadata(helper.getLevel().registryAccess());
            var restored = BlockEntity.loadStatic(helper.absolutePos(BASE), helper.getBlockState(BASE), tag,
                helper.getLevel().registryAccess());
            helper.assertTrue(restored instanceof NostalgiaJukeboxBlockEntity, "Saved ddr inventory did not load");
            var loaded = (NostalgiaJukeboxBlockEntity)restored;
            helper.assertTrue(loaded.getTheItem().is(Items.MUSIC_DISC_13)
                    && loaded.getSongPlayer().getTicksSinceSongStarted() >= 60,
                "ddr lost its saved disc or playback progress");
            helper.getLevel().setBlockEntity(loaded);
            player.setItemInHand(InteractionHand.MAIN_HAND, ItemStack.EMPTY);
            helper.useBlock(section(BASE, facing, 11), player);
            helper.assertTrue(loaded.isEmpty() && !loaded.getSongPlayer().isPlaying(),
                    "The saved disc did not eject through the secondary rail");
            helper.assertItemEntityCountIs(Items.MUSIC_DISC_13, BASE, 3, 1);
            helper.getLevel().destroyBlock(helper.absolutePos(section(BASE, facing, 3)), true);
            assertGone(helper, BASE, facing);
            helper.assertItemEntityCountIs(FunPackCustom.DDR_SUPERNOVA_ITEM.get(), BASE, 3, 1);
            helper.assertItemEntityCountIs(Items.MUSIC_DISC_13, BASE, 3, 1);
            helper.succeed();
        });
    }

    @GameTest(template="nostalgia_test")
    public static void ddrBlockedColumnsAndMissingPlatformSupportsLeaveNoFragments(GameTestHelper helper) {
        var player = player(helper, GameType.SURVIVAL);
        for (Direction facing : Direction.Plane.HORIZONTAL) {
            for (int blocked=1; blocked<12; blocked++) {
                floors(helper, BASE, facing);
                BlockPos obstacle = section(BASE, facing, blocked);
                helper.setBlock(obstacle, Blocks.STONE);
                player.setItemInHand(InteractionHand.MAIN_HAND, new ItemStack(FunPackCustom.DDR_SUPERNOVA_ITEM.get(), 2));
                helper.assertFalse(place(helper, player, BASE, facing), "ddr placed through an occupied cell");
                helper.assertTrue(player.getMainHandItem().getCount() == 2, "Failed placement consumed ddr");
                for (int i=0; i<12; i++) {
                    helper.assertBlockPresent(i == blocked ? Blocks.STONE : Blocks.AIR, section(BASE, facing, i));
                }
                helper.setBlock(obstacle, Blocks.AIR);
            }
            for (int support=0; support<6; support++) {
                floors(helper, BASE, facing);
                helper.setBlock(BASE.relative(facing,support%3).relative(facing.getClockWise(),support/3).below(), Blocks.AIR);
                player.setItemInHand(InteractionHand.MAIN_HAND, new ItemStack(FunPackCustom.DDR_SUPERNOVA_ITEM.get(), 2));
                helper.assertFalse(place(helper, player, BASE, facing), "DDR placed without one of its six supports");
                helper.assertTrue(player.getMainHandItem().getCount() == 2, "Unsupported placement consumed DDR");
                assertGone(helper, BASE, facing);
            }
        }
        helper.succeed();
    }

    @GameTest(template="nostalgia_test")
    public static void ddrLosingAnySupportRemovesThePairOnceInEveryFacing(GameTestHelper helper) {
        for (Direction facing : Direction.Plane.HORIZONTAL) {
            for (int support=0; support<6; support++) {
                var player = cabinet(helper, GameType.SURVIVAL, facing);
                insert(helper, player, section(BASE, facing, 11));
                helper.getLevel().destroyBlock(helper.absolutePos(BASE.relative(facing.getClockWise(), support/3).relative(facing,support%3).below()), false);
                assertGone(helper, BASE, facing);
                helper.assertItemEntityCountIs(FunPackCustom.DDR_SUPERNOVA_ITEM.get(), BASE, 3, 1);
                helper.assertItemEntityCountIs(Items.MUSIC_DISC_13, BASE, 3, 1);
                clearDrops(helper);
            }
        }
        helper.succeed();
    }

    private static Vec3 modelPoint(GameTestHelper helper, Direction facing, double x, double y, double z) {
        Direction across = facing.getClockWise();
        return Vec3.atCenterOf(helper.absolutePos(BASE)).add(
            across.getStepX()*(x/16-.5) + facing.getStepX()*(.5-z/16), y/16-.5,
            across.getStepZ()*(x/16-.5) + facing.getStepZ()*(.5-z/16));
    }

    @GameTest(template="nostalgia_test", timeoutTicks=120)
    public static void ddrStageSupportsStandingAndWalkOnInEveryFacing(GameTestHelper helper) {
        int rotation=0;
        for (Direction facing : Direction.Plane.HORIZONTAL) {
            long start = rotation++*25;
            helper.runAtTickTime(start, () -> {
                var player = cabinet(helper, GameType.SURVIVAL, facing);
                var first = helper.spawn(EntityType.ARMOR_STAND,
                    helper.relativeVec(modelPoint(helper, facing, 7.1, 22, -20)));
                var second = helper.spawn(EntityType.ARMOR_STAND,
                    helper.relativeVec(modelPoint(helper, facing, 24.9, 22, -20)));
                first.setNoGravity(false);
                second.setNoGravity(false);
                helper.runAfterDelay(18, () -> {
                    double surface = helper.absolutePos(BASE).getY()+DdrCabinetBlock.STAGE_HEIGHT;
                    for (var entity : java.util.List.of(first, second)) {
                        helper.assertTrue(entity.onGround() && Math.abs(entity.getY()-surface)<.001,
                            "A player-sized entity did not settle onto the stage facing " + facing);
                        helper.assertTrue(helper.getLevel().noCollision(entity, entity.getBoundingBox()),
                            "The stage or rails intrude into the standing space");
                    }
                    first.discard();
                    second.discard();
                    Direction across = facing.getClockWise();
                    helper.setBlock(BASE.relative(facing).relative(across,-1).below(), Blocks.STONE);
                    player.setPos(modelPoint(helper, facing, -8, 0, -8));
                    player.setOnGround(true);
                    player.move(MoverType.SELF, new Vec3(across.getStepX()*1.1, 0, across.getStepZ()*1.1));
                    helper.assertTrue(Math.abs(player.getY()-surface)<.001,
                        "Player cannot step onto the low stage without jumping facing " + facing);
                    Vec3 before = player.position();
                    player.move(MoverType.SELF, new Vec3(facing.getStepX()*.75, 0, facing.getStepZ()*.75));
                    helper.assertTrue(player.position().distanceTo(before)>.74,
                        "A full-height collision box blocks the open dance area");
                    helper.assertTrue(helper.getLevel().noCollision(player, player.getBoundingBox()),
                        "Player is obstructed inside the dance area");
                    before = player.position();
                    player.move(MoverType.SELF, new Vec3(facing.getStepX()*1.1, 0, facing.getStepZ()*1.1));
                    helper.assertTrue(player.position().distanceTo(before)<.9,
                        "Player passed through the physical handrail");
                    helper.getLevel().destroyBlock(helper.absolutePos(BASE), false);
                    assertGone(helper, BASE, facing);
                    clearDrops(helper);
                });
            });
        }
        helper.runAtTickTime(98, helper::succeed);
    }
}
