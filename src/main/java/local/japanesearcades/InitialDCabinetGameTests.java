package local.japanesearcades;

import static local.japanesearcades.NostalgiaCabinetGameTests.BASE;
import static local.japanesearcades.NostalgiaCabinetGameTests.entity;
import static local.japanesearcades.NostalgiaCabinetGameTests.insert;
import static local.japanesearcades.NostalgiaCabinetGameTests.player;
import static local.japanesearcades.GachaponTransactionGameTests.createPlayer;

import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.gametest.framework.GameTest;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.util.Mth;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.ai.attributes.Attributes;
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

/** Single-column placement, persistent jukebox, and actual server seat lifecycle. */
@GameTestHolder(JapaneseArcades.MOD_ID)
@PrefixGameTestTemplate(false)
public final class InitialDCabinetGameTests {
    private static BlockPos section(BlockPos anchor, Direction facing, int index) {
        return InitialDCabinetBlock.sectionPosition(anchor, facing, InitialDCabinetBlock.Section.values()[index]);
    }
    private static void floors(GameTestHelper helper, BlockPos anchor, Direction facing) {
        for (int depth = 0; depth < 3; depth++) { helper.setBlock(anchor.relative(facing, depth).below(), Blocks.STONE); }
    }
    private static void aisleFloor(GameTestHelper helper) {
        for (int x = 0; x <= 7; x++) { for (int z = 0; z <= 7; z++) { helper.setBlock(new BlockPos(x, 0, z), Blocks.STONE); } }
    }
    private static boolean place(GameTestHelper helper, Player player, BlockPos anchor, Direction facing) {
        player.setYRot(facing.getOpposite().toYRot());
        var floor = helper.absolutePos(anchor.below());
        var hit = new BlockHitResult(Vec3.atCenterOf(floor).add(0, .5, 0), Direction.UP, floor, false);
        return ((BlockItem)player.getMainHandItem().getItem()).place(
            new BlockPlaceContext(player, InteractionHand.MAIN_HAND, player.getMainHandItem(), hit)).consumesAction();
    }
    private static Player cabinet(GameTestHelper helper, BlockPos anchor, Direction facing) {
        Player placer = player(helper, GameType.SURVIVAL);
        floors(helper, anchor, facing);
        placer.setItemInHand(InteractionHand.MAIN_HAND, new ItemStack(JapaneseArcades.INITIAL_D_ITEM.get()));
        helper.assertTrue(place(helper, placer, anchor, facing), "Initial D placement failed facing " + facing);
        for (int index = 0; index < 7; index++) {
            BlockPos pos = section(anchor, facing, index);
            helper.assertBlockPresent(JapaneseArcades.INITIAL_D.get(), pos);
            helper.assertBlockProperty(pos, InitialDCabinetBlock.SECTION, InitialDCabinetBlock.Section.values()[index]);
            helper.assertBlockProperty(pos, InitialDCabinetBlock.FACING, facing);
            helper.assertTrue(index == 0 ? helper.getBlockEntity(pos) instanceof NostalgiaJukeboxBlockEntity
                : helper.getLevel().getBlockEntity(helper.absolutePos(pos)) == null, "Seat or controls created an extra disc inventory");
        }
        return placer;
    }
    private static void gone(GameTestHelper helper, BlockPos anchor, Direction facing) {
        for (int index = 0; index < 7; index++) { helper.assertBlockPresent(Blocks.AIR, section(anchor, facing, index)); }
    }
    private static void drops(GameTestHelper helper) { helper.getEntities(EntityType.ITEM, BASE, 5).forEach(item -> item.discard()); }
    private static void creativeRemove(GameTestHelper helper, Player player, BlockPos relative) {
        BlockPos pos = helper.absolutePos(relative);
        var state = helper.getLevel().getBlockState(pos);
        state.getBlock().playerWillDestroy(helper.getLevel(), pos, state, player);
        helper.getLevel().destroyBlock(pos, false, player);
    }

    @GameTest(template = "nostalgia_test")
    public static void initialDSevenCellsRemoveOnceAndStayInsideOneColumn(GameTestHelper helper) {
        for (Direction facing : Direction.Plane.HORIZONTAL) {
            for (int broken = 0; broken < 7; broken++) {
                Player placer = cabinet(helper, BASE, facing);
                for (int index = 0; index < 7; index++) {
                    BlockPos pos = helper.absolutePos(section(BASE, facing, index));
                    for (var box : helper.getLevel().getBlockState(pos).getCollisionShape(helper.getLevel(), pos).toAabbs()) {
                        helper.assertTrue(box.minX >= 0 && box.maxX <= 1 && box.minZ >= 0 && box.maxZ <= 1,
                            "Collision overhang would overlap the next cabinet in a row");
                    }
                }
                insert(helper, placer, section(BASE, facing, 1));
                helper.getLevel().destroyBlock(helper.absolutePos(section(BASE, facing, broken)), true);
                gone(helper, BASE, facing);
                helper.assertItemEntityCountIs(JapaneseArcades.INITIAL_D_ITEM.get(), BASE, 5, 1);
                helper.assertItemEntityCountIs(Items.MUSIC_DISC_13, BASE, 5, 1);
                drops(helper);
            }
            for (int broken = 0; broken < 7; broken++) {
                cabinet(helper, BASE, facing);
                BlockPos neighbor = BASE.relative(facing.getClockWise());
                cabinet(helper, neighbor, facing);
                Player creative = player(helper, GameType.CREATIVE);
                creativeRemove(helper, creative, section(BASE, facing, broken));
                gone(helper, BASE, facing);
                for (int index = 0; index < 7; index++) { helper.assertBlockPresent(JapaneseArcades.INITIAL_D.get(), section(neighbor, facing, index)); }
                helper.assertItemEntityCountIs(JapaneseArcades.INITIAL_D_ITEM.get(), BASE, 5, 0);
                creativeRemove(helper, creative, neighbor);
            }
        }
        helper.succeed();
    }

    @GameTest(template = "nostalgia_test")
    public static void initialDBlockedCellsAndMissingFloorNeverLeaveFragments(GameTestHelper helper) {
        Player placer = player(helper, GameType.SURVIVAL);
        for (Direction facing : Direction.Plane.HORIZONTAL) {
            for (int blocked = 1; blocked < 7; blocked++) {
                floors(helper, BASE, facing);
                BlockPos obstacle = section(BASE, facing, blocked);
                helper.setBlock(obstacle, Blocks.STONE);
                placer.setItemInHand(InteractionHand.MAIN_HAND, new ItemStack(JapaneseArcades.INITIAL_D_ITEM.get(), 2));
                helper.assertFalse(place(helper, placer, BASE, facing), "Cabinet placed through occupied controls or seat");
                helper.assertTrue(placer.getMainHandItem().getCount() == 2, "Blocked placement consumed an item");
                helper.assertBlockPresent(Blocks.AIR, BASE);
                helper.setBlock(obstacle, Blocks.AIR);
            }
            for (int depth = 0; depth < 3; depth++) {
                cabinet(helper, BASE, facing);
                helper.getLevel().destroyBlock(helper.absolutePos(BASE.relative(facing, depth).below()), false);
                gone(helper, BASE, facing);
                helper.assertItemEntityCountIs(JapaneseArcades.INITIAL_D_ITEM.get(), BASE, 4, 1);
                drops(helper);
            }
        }
        helper.succeed();
    }

    private static BlockPos aimSeat(GameTestHelper helper, ServerPlayer player, BlockPos anchor, Direction facing) {
        BlockPos absolute = helper.absolutePos(anchor);
        Vec3 target = Vec3.atCenterOf(absolute.relative(facing, 2)).add(facing.getStepX()*.32, .6, facing.getStepZ()*.32);
        Vec3 eye = target.add(facing.getStepX(), .6, facing.getStepZ());
        player.setPos(eye.x, eye.y-player.getEyeHeight(), eye.z);
        Vec3 delta = target.subtract(eye);
        player.setYRot((float)Math.toDegrees(Math.atan2(-delta.x, delta.z)));
        player.setYHeadRot(player.getYRot());
        player.setXRot((float)-Math.toDegrees(Math.atan2(delta.y, Math.sqrt(delta.x*delta.x+delta.z*delta.z))));
        player.setItemInHand(InteractionHand.MAIN_HAND, ItemStack.EMPTY);
        return section(anchor, facing, 6);
    }
    private static InitialDSeatEntity sit(GameTestHelper helper, ServerPlayer player, BlockPos anchor, Direction facing) {
        BlockPos seat = aimSeat(helper, player, anchor, facing);
        var ray = player.pick(player.blockInteractionRange(), 1, false);
        helper.assertTrue(ray instanceof BlockHitResult hit && helper.getLevel().getBlockState(hit.getBlockPos()).is(JapaneseArcades.INITIAL_D.get())
            && helper.getLevel().getBlockState(hit.getBlockPos()).getValue(InitialDCabinetBlock.SECTION).depth == 2,
            "The fixture must have an unobstructed view of the seat");
        helper.useBlock(seat, player);
        helper.assertTrue(player.getVehicle() instanceof InitialDSeatEntity, "An empty-hand seat click failed to mount");
        return (InitialDSeatEntity)player.getVehicle();
    }

    @GameTest(template = "nostalgia_test")
    public static void initialDSeatFacesMonitorIsExclusiveAndSneakDismountsEveryFacing(GameTestHelper helper) {
        aisleFloor(helper);
        for (Direction facing : Direction.Plane.HORIZONTAL) {
            cabinet(helper, BASE, facing);
            ServerPlayer rider = createPlayer(helper, "InitialDRider", GameType.SURVIVAL);
            ServerPlayer visitor = createPlayer(helper, "InitialDVisitor", GameType.SURVIVAL);
            InitialDSeatEntity seat = sit(helper, rider, BASE, facing);
            helper.assertTrue(seat.getAnchor().equals(helper.absolutePos(BASE)) && seat.getPassengers().size() == 1,
                "Seat must bind one player to the clicked cabinet");
            helper.assertTrue(Math.abs(Mth.wrapDegrees(rider.getYRot()-facing.getOpposite().toYRot())) < .1,
                "The seated player faces away from the monitor");
            helper.assertFalse(seat.save(new CompoundTag()), "An occupied utility seat must not persist a ghost vehicle");
            BlockPos visitorClick = aimSeat(helper, visitor, BASE, facing);
            helper.useBlock(visitorClick, visitor);
            helper.assertTrue(!visitor.isPassenger() && rider.getVehicle() == seat && seat.getPassengers().size() == 1,
                "Another visitor stole or joined an occupied seat");
            rider.setShiftKeyDown(true);
            seat.tick();
            helper.assertTrue(!rider.isPassenger() && seat.isRemoved(), "Sneaking failed to dismount and remove the riding anchor");
            helper.assertTrue(helper.getLevel().noCollision(rider, rider.getBoundingBox()), "Dismount placed the rider inside solid geometry");
            helper.getLevel().destroyBlock(helper.absolutePos(BASE), false);
            drops(helper);
        }
        helper.succeed();
    }

    @GameTest(template = "nostalgia_test")
    public static void initialDFullRowDismountUsesTheRearAisle(GameTestHelper helper) {
        aisleFloor(helper);
        Direction facing = Direction.NORTH;
        cabinet(helper, BASE, facing);
        cabinet(helper, BASE.east(), facing);
        cabinet(helper, BASE.west(), facing);
        ServerPlayer rider = createPlayer(helper, "InitialDRow", GameType.SURVIVAL);
        InitialDSeatEntity seat = sit(helper, rider, BASE, facing);
        rider.stopRiding();
        seat.tick();
        Vec3 rear = helper.absolutePos(BASE.relative(facing, 3)).getCenter();
        helper.assertTrue(Math.abs(rider.getX()-rear.x) < .01 && Math.abs(rider.getZ()-rear.z) < .01,
            "With both side exits occupied, dismount must choose the clear rear aisle");
        helper.assertTrue(helper.getLevel().noCollision(rider, rider.getBoundingBox()), "Rear dismount intersects another cabinet");
        for (int index = 0; index < 7; index++) {
            helper.assertBlockPresent(JapaneseArcades.INITIAL_D.get(), section(BASE.east(), facing, index));
            helper.assertBlockPresent(JapaneseArcades.INITIAL_D.get(), section(BASE.west(), facing, index));
        }
        helper.succeed();
    }

    @GameTest(template = "nostalgia_test")
    public static void initialDSeatRejectsRemoteSpectatorHeldItemAndBlockedHeadroom(GameTestHelper helper) {
        aisleFloor(helper);
        cabinet(helper, BASE, Direction.NORTH);
        ServerPlayer player = createPlayer(helper, "InitialDChecks", GameType.SURVIVAL);
        BlockPos click = helper.absolutePos(aimSeat(helper, player, BASE, Direction.NORTH));
        player.setItemInHand(InteractionHand.MAIN_HAND, new ItemStack(Items.STICK));
        helper.assertFalse(InitialDSeatEntity.mount(player, click), "A held item bypassed the empty-hand seat interaction");
        aimSeat(helper, player, BASE, Direction.NORTH);
        player.setPos(player.getX(), player.getY(), player.getZ()-15);
        helper.assertFalse(InitialDSeatEntity.mount(player, click), "A remote forged seat interaction mounted a player");
        aimSeat(helper, player, BASE, Direction.NORTH);
        player.setGameMode(GameType.SPECTATOR);
        helper.assertFalse(InitialDSeatEntity.mount(player, click), "A spectator mounted a seat");
        player.setGameMode(GameType.SURVIVAL);
        player.getAttribute(Attributes.SCALE).setBaseValue(1.2);
        player.refreshDimensions();
        aimSeat(helper, player, BASE, Direction.NORTH);
        helper.setBlock(section(BASE, Direction.NORTH, 6).above(), Blocks.STONE);
        helper.assertFalse(InitialDSeatEntity.mount(player, click), "An enlarged player's head clipped through the low ceiling");
        helper.assertTrue(helper.getEntities(JapaneseArcades.INITIAL_D_SEAT.get(), BASE, 5).isEmpty(), "Rejected requests left orphan riding anchors");
        helper.setBlock(section(BASE, Direction.NORTH, 6).above(), Blocks.AIR);
        helper.assertTrue(InitialDSeatEntity.mount(player, click), "Removing the low ceiling failed to allow the otherwise valid seat interaction");
        helper.getLevel().destroyBlock(helper.absolutePos(BASE), false);
        helper.succeed();
    }

    @GameTest(template = "nostalgia_test")
    public static void initialDRemovalSupportLossAndLogoutCleanUpOccupiedSeats(GameTestHelper helper) {
        aisleFloor(helper);
        for (int mode = 0; mode < 3; mode++) {
            cabinet(helper, BASE, Direction.NORTH);
            ServerPlayer rider = createPlayer(helper, "InitialDCleanup", GameType.SURVIVAL);
            InitialDSeatEntity seat = sit(helper, rider, BASE, Direction.NORTH);
            if (mode == 0) {
                helper.getLevel().destroyBlock(helper.absolutePos(section(BASE, Direction.NORTH, 4)), true);
            } else if (mode == 1) {
                helper.getLevel().destroyBlock(helper.absolutePos(BASE.north(2).below()), false);
            } else {
                helper.getLevel().getServer().getPlayerList().remove(rider);
            }
            helper.assertTrue(!rider.isPassenger() && seat.isRemoved(), "Seat anchor survived removal, support loss or logout");
            helper.assertTrue(helper.getLevel().noCollision(rider, rider.getBoundingBox()), "Seat cleanup failed to move the rider to a safe exit");
            if (mode == 2) { helper.getLevel().destroyBlock(helper.absolutePos(BASE), false); }
            gone(helper, BASE, Direction.NORTH);
            drops(helper);
            aisleFloor(helper);
        }
        helper.succeed();
    }

    @GameTest(template = "nostalgia_test", timeoutTicks = 80)
    public static void initialDSavedJukeboxPlaysWhileSeatedAndEjectsClearOfTheChair(GameTestHelper helper) {
        aisleFloor(helper);
        Player placer = cabinet(helper, BASE, Direction.NORTH);
        insert(helper, placer, BASE.above());
        CompoundTag saved = entity(helper).saveWithFullMetadata(helper.getLevel().registryAccess());
        var restored = (NostalgiaJukeboxBlockEntity)BlockEntity.loadStatic(helper.absolutePos(BASE), helper.getBlockState(BASE),
            saved, helper.getLevel().registryAccess());
        helper.getLevel().setBlockEntity(restored);
        ServerPlayer rider = createPlayer(helper, "InitialDMusic", GameType.SURVIVAL);
        InitialDSeatEntity seat = sit(helper, rider, BASE, Direction.NORTH);
        helper.runAfterDelay(5, () -> {
            helper.assertTrue(restored.getTheItem().is(Items.MUSIC_DISC_13) && restored.getSongPlayer().isPlaying()
                && restored.getSongPlayer().getTicksSinceSongStarted() >= 5, "Sitting interrupted saved jukebox playback");
            helper.assertTrue(rider.getVehicle() == seat, "Rider unexpectedly left the chair during playback");
            placer.setItemInHand(InteractionHand.MAIN_HAND, ItemStack.EMPTY);
            helper.useBlock(BASE.above(2), placer);
            helper.assertTrue(restored.isEmpty(), "Rear cabinet interaction failed to eject a disc while occupied");
            helper.assertItemEntityCountIs(Items.MUSIC_DISC_13, BASE, 5, 1);
            var disc = helper.getEntities(EntityType.ITEM, BASE, 5).stream().filter(item -> item.getItem().is(Items.MUSIC_DISC_13)).findFirst().orElseThrow();
            helper.assertTrue(helper.getLevel().noCollision(disc, disc.getBoundingBox()), "Ejected disc intersects the chair");
            helper.getLevel().destroyBlock(helper.absolutePos(BASE), false);
            helper.succeed();
        });
    }
}
