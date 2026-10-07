package local.japanesearcades;

import static local.japanesearcades.NostalgiaCabinetGameTests.BASE;
import static local.japanesearcades.NostalgiaCabinetGameTests.entity;
import static local.japanesearcades.NostalgiaCabinetGameTests.insert;
import static local.japanesearcades.NostalgiaCabinetGameTests.player;

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

/** Eight-cell cabinet lifecycle, shared inventory and a genuinely standable front platform. */
@GameTestHolder(JapaneseArcades.MOD_ID)
@PrefixGameTestTemplate(false)
public final class BeatmaniaIidxCabinetGameTests {
    private static BlockPos section(BlockPos anchor, Direction facing, int index) {
        return BeatmaniaIidxCabinetBlock.sectionPosition(anchor, facing,
            BeatmaniaIidxCabinetBlock.Side.values()[index / 4], BeatmaniaIidxCabinetBlock.Section.values()[index % 4]);
    }

    private static void floors(GameTestHelper helper, BlockPos anchor, Direction facing) {
        for (int side = 0; side < 2; side++) for (int depth = 0; depth < 2; depth++) {
            helper.setBlock(anchor.relative(facing.getClockWise(), side).relative(facing, depth).below(), Blocks.STONE);
        }
    }

    private static boolean place(GameTestHelper helper, Player player, BlockPos anchor, Direction facing) {
        player.setYRot(facing.getOpposite().toYRot());
        BlockPos floor = helper.absolutePos(anchor.below());
        var hit = new BlockHitResult(Vec3.atCenterOf(floor).add(0, .5, 0), Direction.UP, floor, false);
        return ((BlockItem)player.getMainHandItem().getItem()).place(
            new BlockPlaceContext(player, InteractionHand.MAIN_HAND, player.getMainHandItem(), hit)).consumesAction();
    }

    private static Player cabinet(GameTestHelper helper, GameType mode, Direction facing) {
        Player operator = player(helper, mode);
        floors(helper, BASE, facing);
        operator.setItemInHand(InteractionHand.MAIN_HAND, new ItemStack(JapaneseArcades.BEATMANIA_IIDX_LIGHTNING_ITEM.get(), 2));
        helper.assertTrue(place(helper, operator, BASE, facing), "IIDX placement failed facing " + facing);
        helper.assertTrue(operator.getMainHandItem().getCount() == (mode.isCreative() ? 2 : 1), "Wrong placement item count");
        assertCells(helper, BASE, facing);
        return operator;
    }

    private static void assertCells(GameTestHelper helper, BlockPos anchor, Direction facing) {
        for (int i = 0; i < 8; i++) {
            BlockPos pos = section(anchor, facing, i);
            helper.assertBlockPresent(JapaneseArcades.BEATMANIA_IIDX_LIGHTNING.get(), pos);
            helper.assertBlockProperty(pos, NostalgiaCabinetBlock.FACING, facing);
            helper.assertBlockProperty(pos, NostalgiaCabinetBlock.PART,
                NostalgiaCabinetBlock.Part.values()[BeatmaniaIidxCabinetBlock.Section.values()[i % 4].height]);
            helper.assertBlockProperty(pos, BeatmaniaIidxCabinetBlock.SIDE, BeatmaniaIidxCabinetBlock.Side.values()[i / 4]);
            helper.assertBlockProperty(pos, BeatmaniaIidxCabinetBlock.SECTION, BeatmaniaIidxCabinetBlock.Section.values()[i % 4]);
            var blockEntity = helper.getLevel().getBlockEntity(helper.absolutePos(pos));
            helper.assertTrue(i == 0 ? blockEntity instanceof NostalgiaJukeboxBlockEntity : blockEntity == null,
                "Only the primary IIDX cabinet base may own a disc inventory");
        }
        for (int side = 0; side < 2; side++) {
            BlockPos platform = section(anchor, facing, side * 4 + 3);
            helper.assertBlockPresent(Blocks.AIR, platform.above());
            helper.assertBlockPresent(Blocks.AIR, platform.above(2));
        }
    }

    private static void assertGone(GameTestHelper helper, BlockPos anchor, Direction facing) {
        for (int i = 0; i < 8; i++) helper.assertBlockPresent(Blocks.AIR, section(anchor, facing, i));
    }

    private static void clearDrops(GameTestHelper helper) {
        helper.getEntities(EntityType.ITEM, BASE, 5).forEach(item -> item.discard());
    }

    private static void creativeRemove(GameTestHelper helper, Player player, BlockPos relative) {
        var pos = helper.absolutePos(relative);
        var state = helper.getLevel().getBlockState(pos);
        state.getBlock().playerWillDestroy(helper.getLevel(), pos, state, player);
        helper.getLevel().destroyBlock(pos, false, player);
    }

    @GameTest(template = "nostalgia_test")
    public static void iidxAllEightSectionsUseOneDiscInventoryInEveryFacing(GameTestHelper helper) {
        for (Direction facing : Direction.Plane.HORIZONTAL) {
            Player operator = cabinet(helper, GameType.SURVIVAL, facing);
            BlockPos anchor = helper.absolutePos(BASE);
            BlockPos top = anchor.above(2);
            var topShape = helper.getLevel().getBlockState(top).getShape(helper.getLevel(), top);
            helper.assertTrue(topShape.clip(BeatmaniaIidxCabinetBlock.localToWorld(anchor, facing, 15, 40.5, -8),
                BeatmaniaIidxCabinetBlock.localToWorld(anchor, facing, 15, 40.5, 14.81), top) == null,
                "An invisible wall fills the recess in front of the IIDX upper backing");
            var backingHit = topShape.clip(BeatmaniaIidxCabinetBlock.localToWorld(anchor, facing, 15, 40.5, -8),
                BeatmaniaIidxCabinetBlock.localToWorld(anchor, facing, 15, 40.5, 16), top);
            helper.assertTrue(backingHit != null && backingHit.getLocation().distanceTo(
                BeatmaniaIidxCabinetBlock.localToWorld(anchor, facing, 15, 40.5, 14.82)) < .00001,
                "The upper ray must meet the physical backing at the rear of the recess");
            for (int i = 0; i < 8; i++) {
                insert(helper, operator, section(BASE, facing, i));
                helper.assertTrue(operator.getMainHandItem().getCount() == 1, "A section did not consume exactly one disc");
                operator.setItemInHand(InteractionHand.MAIN_HAND, ItemStack.EMPTY);
                helper.useBlock(section(BASE, facing, (i + 4) % 8), operator);
                helper.assertTrue(entity(helper).isEmpty() && !entity(helper).getSongPlayer().isPlaying(),
                    "Opposite-column interaction did not eject the shared disc");
                var drops = helper.getEntities(EntityType.ITEM, BASE, 4);
                helper.assertTrue(drops.size() == 1 && drops.getFirst().getItem().is(Items.MUSIC_DISC_13),
                    "A section ejected the wrong number of discs");
                var disc = drops.getFirst();
                for (int cell = 0; cell < 8; cell++) {
                    BlockPos pos = helper.absolutePos(section(BASE, facing, cell));
                    for (var box : helper.getLevel().getBlockState(pos).getCollisionShape(helper.getLevel(), pos).toAabbs()) {
                        helper.assertFalse(box.move(pos.getX(), pos.getY(), pos.getZ()).intersects(disc.getBoundingBox()),
                            "IIDX ejected its disc into the cabinet or platform");
                    }
                }
                helper.assertTrue(helper.getLevel().noCollision(disc, disc.getBoundingBox()), "Ejected disc is obstructed");
                disc.discard();
            }
            helper.getLevel().destroyBlock(helper.absolutePos(BASE), false);
            assertGone(helper, BASE, facing);
            clearDrops(helper);
        }
        helper.succeed();
    }

    @GameTest(template = "nostalgia_test")
    public static void iidxBreakingAnySectionDropsOneCabinetAndDisc(GameTestHelper helper) {
        for (Direction facing : Direction.Plane.HORIZONTAL) for (int broken = 0; broken < 8; broken++) {
            Player operator = cabinet(helper, GameType.SURVIVAL, facing);
            insert(helper, operator, section(BASE, facing, 7));
            var inventory = entity(helper);
            helper.getLevel().destroyBlock(helper.absolutePos(section(BASE, facing, broken)), true);
            assertGone(helper, BASE, facing);
            helper.assertItemEntityCountIs(JapaneseArcades.BEATMANIA_IIDX_LIGHTNING_ITEM.get(), BASE, 4, 1);
            helper.assertItemEntityCountIs(Items.MUSIC_DISC_13, BASE, 4, 1);
            helper.assertFalse(inventory.getSongPlayer().isPlaying(), "Removed IIDX still plays its disc");
            clearDrops(helper);
        }
        helper.succeed();
    }

    @GameTest(template = "nostalgia_test")
    public static void iidxCreativeRemovalNeverDamagesAnAdjacentCabinet(GameTestHelper helper) {
        for (Direction facing : Direction.Plane.HORIZONTAL) for (int broken = 0; broken < 8; broken++) {
            Player operator = cabinet(helper, GameType.CREATIVE, facing);
            insert(helper, operator, section(BASE, facing, 3));
            BlockPos neighbor = BASE.relative(facing.getClockWise(), 2);
            floors(helper, neighbor, facing);
            operator.setItemInHand(InteractionHand.MAIN_HAND, new ItemStack(JapaneseArcades.BEATMANIA_IIDX_LIGHTNING_ITEM.get()));
            helper.assertTrue(place(helper, operator, neighbor, facing), "Adjacent IIDX placement failed");
            operator.setItemInHand(InteractionHand.MAIN_HAND, new ItemStack(Items.MUSIC_DISC_CAT));
            helper.useBlock(section(neighbor, facing, 7), operator);
            var neighborInventory = (NostalgiaJukeboxBlockEntity)helper.getBlockEntity(neighbor);
            creativeRemove(helper, operator, section(BASE, facing, broken));
            assertGone(helper, BASE, facing);
            assertCells(helper, neighbor, facing);
            helper.assertTrue(neighborInventory.getTheItem().is(Items.MUSIC_DISC_CAT) && neighborInventory.getSongPlayer().isPlaying(),
                "Removing one IIDX changed its neighbor's saved disc or playback");
            helper.assertItemEntityCountIs(JapaneseArcades.BEATMANIA_IIDX_LIGHTNING_ITEM.get(), BASE, 5, 0);
            helper.assertItemEntityCountIs(Items.MUSIC_DISC_13, BASE, 5, 1);
            helper.assertItemEntityCountIs(Items.MUSIC_DISC_CAT, BASE, 5, 0);
            creativeRemove(helper, operator, neighbor);
            clearDrops(helper);
        }
        helper.succeed();
    }

    @GameTest(template = "nostalgia_test")
    public static void iidxSavedDiscResumesAndEjectsThroughThePlatform(GameTestHelper helper) {
        Direction facing = Direction.WEST;
        Player operator = player(helper, GameType.SURVIVAL);
        floors(helper, BASE, facing);
        ItemStack cabinet = new ItemStack(JapaneseArcades.BEATMANIA_IIDX_LIGHTNING_ITEM.get());
        CompoundTag saved = new CompoundTag();
        saved.put("RecordItem", new ItemStack(Items.MUSIC_DISC_13).save(helper.getLevel().registryAccess()));
        saved.putLong("ticks_since_song_started", 40);
        BlockItem.setBlockEntityData(cabinet, JapaneseArcades.NOSTALGIA_JUKEBOX.get(), saved);
        operator.setItemInHand(InteractionHand.MAIN_HAND, cabinet);
        helper.assertTrue(place(helper, operator, BASE, facing), "Saved IIDX placement failed");
        assertCells(helper, BASE, facing);
        helper.assertBlockProperty(BASE, NostalgiaCabinetBlock.HAS_RECORD, true);
        helper.runAfterDelay(25, () -> {
            var tag = entity(helper).saveWithFullMetadata(helper.getLevel().registryAccess());
            var restored = BlockEntity.loadStatic(helper.absolutePos(BASE), helper.getBlockState(BASE), tag,
                helper.getLevel().registryAccess());
            helper.assertTrue(restored instanceof NostalgiaJukeboxBlockEntity, "IIDX inventory did not reload");
            var loaded = (NostalgiaJukeboxBlockEntity)restored;
            helper.assertTrue(loaded.getTheItem().is(Items.MUSIC_DISC_13) && loaded.getSongPlayer().getTicksSinceSongStarted() >= 60,
                "IIDX lost its saved disc or server playback progress");
            helper.getLevel().setBlockEntity(loaded);
            operator.setItemInHand(InteractionHand.MAIN_HAND, ItemStack.EMPTY);
            helper.useBlock(section(BASE, facing, 7), operator);
            helper.assertTrue(loaded.isEmpty() && !loaded.getSongPlayer().isPlaying(), "Platform interaction could not eject the saved disc");
            helper.assertItemEntityCountIs(Items.MUSIC_DISC_13, BASE, 4, 1);
            helper.getLevel().destroyBlock(helper.absolutePos(section(BASE, facing, 2)), true);
            assertGone(helper, BASE, facing);
            helper.assertItemEntityCountIs(JapaneseArcades.BEATMANIA_IIDX_LIGHTNING_ITEM.get(), BASE, 4, 1);
            helper.succeed();
        });
    }

    @GameTest(template = "nostalgia_test")
    public static void iidxObstructionsAndMissingSupportsNeverPartiallyPlace(GameTestHelper helper) {
        Player operator = player(helper, GameType.SURVIVAL);
        for (Direction facing : Direction.Plane.HORIZONTAL) {
            for (int blocked = 0; blocked < 8; blocked++) {
                floors(helper, BASE, facing);
                BlockPos obstacle = section(BASE, facing, blocked);
                helper.setBlock(obstacle, Blocks.STONE);
                operator.setItemInHand(InteractionHand.MAIN_HAND, new ItemStack(JapaneseArcades.BEATMANIA_IIDX_LIGHTNING_ITEM.get(), 2));
                helper.assertFalse(place(helper, operator, BASE, facing), "IIDX replaced an occupied footprint cell");
                helper.assertTrue(operator.getMainHandItem().getCount() == 2, "Failed placement consumed IIDX");
                for (int i = 0; i < 8; i++) helper.assertBlockPresent(i == blocked ? Blocks.STONE : Blocks.AIR, section(BASE, facing, i));
                helper.setBlock(obstacle, Blocks.AIR);
            }
            floors(helper, BASE, facing);
            for (int occupied = 0; occupied < 4; occupied++) {
                Vec3 point = BeatmaniaIidxCabinetBlock.localToWorld(helper.absolutePos(BASE), facing,
                    occupied / 2 * 16 + 8, 0, occupied % 2 == 0 ? 8 : -8);
                var occupant = helper.spawn(EntityType.ARMOR_STAND, helper.relativeVec(point));
                occupant.blocksBuilding = true;
                occupant.setNoGravity(true);
                operator.setItemInHand(InteractionHand.MAIN_HAND, new ItemStack(JapaneseArcades.BEATMANIA_IIDX_LIGHTNING_ITEM.get(), 2));
                helper.assertFalse(place(helper, operator, BASE, facing), "IIDX placed through an entity in its cabinet or platform");
                helper.assertTrue(operator.getMainHandItem().getCount() == 2, "Entity obstruction consumed IIDX");
                assertGone(helper, BASE, facing);
                occupant.discard();
            }
            for (int support = 0; support < 4; support++) {
                floors(helper, BASE, facing);
                helper.setBlock(BASE.relative(facing.getClockWise(), support / 2).relative(facing, support % 2).below(), Blocks.AIR);
                operator.setItemInHand(InteractionHand.MAIN_HAND, new ItemStack(JapaneseArcades.BEATMANIA_IIDX_LIGHTNING_ITEM.get(), 2));
                helper.assertFalse(place(helper, operator, BASE, facing), "IIDX placed without one of its four supports");
                helper.assertTrue(operator.getMainHandItem().getCount() == 2, "Unsupported placement consumed IIDX");
                assertGone(helper, BASE, facing);
            }
        }
        helper.succeed();
    }

    @GameTest(template = "nostalgia_test")
    public static void iidxLosingAnyFloorSupportRemovesTheEntireMachineOnce(GameTestHelper helper) {
        for (Direction facing : Direction.Plane.HORIZONTAL) for (int support = 0; support < 4; support++) {
            Player operator = cabinet(helper, GameType.SURVIVAL, facing);
            insert(helper, operator, section(BASE, facing, 7));
            BlockPos floor = BASE.relative(facing.getClockWise(), support / 2).relative(facing, support % 2).below();
            helper.getLevel().destroyBlock(helper.absolutePos(floor), false);
            assertGone(helper, BASE, facing);
            helper.assertItemEntityCountIs(JapaneseArcades.BEATMANIA_IIDX_LIGHTNING_ITEM.get(), BASE, 4, 1);
            helper.assertItemEntityCountIs(Items.MUSIC_DISC_13, BASE, 4, 1);
            clearDrops(helper);
        }
        helper.succeed();
    }

    @GameTest(template = "nostalgia_test")
    public static void iidxWorldBorderAndBuildCeilingRejectTheWholeFootprint(GameTestHelper helper) {
        Player operator = player(helper, GameType.SURVIVAL);
        floors(helper, BASE, Direction.NORTH);
        var border = helper.getLevel().getWorldBorder();
        var savedBorder = border.createSettings();
        BlockPos anchor = helper.absolutePos(BASE);
        operator.setItemInHand(InteractionHand.MAIN_HAND, new ItemStack(JapaneseArcades.BEATMANIA_IIDX_LIGHTNING_ITEM.get(), 2));
        try {
            border.setCenter(anchor.getX() + .5, anchor.getZ() + .5);
            border.setSize(1);
            helper.assertTrue(border.isWithinBounds(anchor) && !border.isWithinBounds(anchor.north()), "World-border fixture must exclude the platform");
            helper.assertFalse(place(helper, operator, BASE, Direction.NORTH), "IIDX placed its platform outside the world border");
            helper.assertTrue(operator.getMainHandItem().getCount() == 2, "Border rejection consumed IIDX");
            assertGone(helper, BASE, Direction.NORTH);
        } finally {
            border.applySettings(savedBorder);
        }
        BlockPos high = new BlockPos(anchor.getX(), helper.getLevel().getMaxBuildHeight() - 2, anchor.getZ());
        var previous = helper.getLevel().getBlockState(high.below());
        try {
            helper.getLevel().setBlock(high.below(), Blocks.STONE.defaultBlockState(), 3);
            var hit = new BlockHitResult(Vec3.atCenterOf(high.below()).add(0, .5, 0), Direction.UP, high.below(), false);
            var context = new BlockPlaceContext(operator, InteractionHand.MAIN_HAND, operator.getMainHandItem(), hit);
            helper.assertTrue(JapaneseArcades.BEATMANIA_IIDX_LIGHTNING.get().getStateForPlacement(context) == null,
                "IIDX allowed its marquee to extend above the build ceiling");
        } finally {
            helper.getLevel().setBlock(high.below(), previous, 3);
        }
        helper.succeed();
    }

    @GameTest(template = "nostalgia_test", timeoutTicks = 120)
    public static void iidxPlatformSupportsStandingAndWalkingAcrossBothHalves(GameTestHelper helper) {
        int rotation = 0;
        for (Direction facing : Direction.Plane.HORIZONTAL) {
            helper.runAtTickTime(rotation++ * 25, () -> {
                Player operator = cabinet(helper, GameType.SURVIVAL, facing);
                var left = helper.spawn(EntityType.ARMOR_STAND, helper.relativeVec(
                    BeatmaniaIidxCabinetBlock.localToWorld(helper.absolutePos(BASE), facing, 8, 20, -8)));
                var right = helper.spawn(EntityType.ARMOR_STAND, helper.relativeVec(
                    BeatmaniaIidxCabinetBlock.localToWorld(helper.absolutePos(BASE), facing, 24, 20, -8)));
                helper.runAfterDelay(18, () -> {
                    double surface = helper.absolutePos(BASE).getY() + BeatmaniaIidxCabinetBlock.PLATFORM_HEIGHT;
                    for (var stand : java.util.List.of(left, right)) {
                        helper.assertTrue(stand.onGround() && Math.abs(stand.getY() - surface) < .001,
                            "A player-sized entity did not settle on the low IIDX platform facing " + facing);
                        helper.assertTrue(helper.getLevel().noCollision(stand, stand.getBoundingBox()), "IIDX blocks the standing space");
                        stand.discard();
                    }
                    helper.setBlock(BASE.relative(facing, 2).below(), Blocks.STONE);
                    operator.setPos(BeatmaniaIidxCabinetBlock.localToWorld(helper.absolutePos(BASE), facing, 8, 0, -24));
                    operator.setOnGround(true);
                    operator.move(MoverType.SELF, new Vec3(-facing.getStepX() * 1.1, 0, -facing.getStepZ() * 1.1));
                    helper.assertTrue(Math.abs(operator.getY() - surface) < .001, "The IIDX platform cannot be stepped onto without jumping");
                    Vec3 before = operator.position();
                    Direction across = facing.getClockWise();
                    operator.move(MoverType.SELF, new Vec3(across.getStepX(), 0, across.getStepZ()));
                    helper.assertTrue(operator.position().distanceTo(before) > .99 && helper.getLevel().noCollision(operator, operator.getBoundingBox()),
                        "The platform seam or an invisible wall blocks walking between IIDX players");
                    helper.getLevel().destroyBlock(helper.absolutePos(BASE), false);
                    assertGone(helper, BASE, facing);
                    clearDrops(helper);
                });
            });
        }
        helper.runAtTickTime(98, helper::succeed);
    }
}
