package local.funpack.custom;

import static local.funpack.custom.NostalgiaCabinetGameTests.BASE;
import static local.funpack.custom.NostalgiaCabinetGameTests.place;
import static local.funpack.custom.NostalgiaCabinetGameTests.player;

import java.util.ArrayList;
import java.util.List;
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
import net.minecraft.world.level.GameType;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.phys.Vec3;
import net.neoforged.neoforge.gametest.GameTestHolder;
import net.neoforged.neoforge.gametest.PrefixGameTestTemplate;

/** Real item placement and saved playback, including tightly packed single-width rows. */
@GameTestHolder(FunPackCustom.MOD_ID)
@PrefixGameTestTemplate(false)
public final class JubeatCabinetGameTests {
    @GameTest(template="nostalgia_test")
    public static void jubeatEverySectionPlaysAndEjectsBeforeSingleDropRemoval(GameTestHelper helper) {
        WaccaCabinetGameTests.everySectionPlaysAndEjectsBeforeSingleDropRemoval(helper,
            FunPackCustom.JUBEAT_ITEM.get());
    }

    @GameTest(template="nostalgia_test")
    public static void jubeatSavedDiscPlacementTicksAndReloadsInEveryFacing(GameTestHelper helper) {
        List<BlockPos> bases = List.of(new BlockPos(1,1,1), new BlockPos(5,1,1),
            new BlockPos(1,1,5), new BlockPos(5,1,5));
        List<Player> players = new ArrayList<>();
        int index = 0;
        for (Direction facing : Direction.Plane.HORIZONTAL) {
            Player operator = player(helper, GameType.SURVIVAL);
            players.add(operator);
            ItemStack stack = new ItemStack(FunPackCustom.JUBEAT_ITEM.get());
            CompoundTag data = new CompoundTag();
            data.put("RecordItem", new ItemStack(Items.MUSIC_DISC_13).save(helper.getLevel().registryAccess()));
            data.putLong("ticks_since_song_started", 40);
            BlockItem.setBlockEntityData(stack, FunPackCustom.NOSTALGIA_JUKEBOX.get(), data);
            placeFacing(helper, operator, bases.get(index++), facing, stack);
        }
        helper.runAfterDelay(25, () -> {
            for (int i=0; i<bases.size(); i++) {
                BlockPos base = bases.get(i);
                var original = entity(helper, base);
                var loaded = BlockEntity.loadStatic(helper.absolutePos(base), helper.getBlockState(base),
                    original.saveWithFullMetadata(helper.getLevel().registryAccess()), helper.getLevel().registryAccess());
                helper.assertTrue(loaded instanceof NostalgiaJukeboxBlockEntity, "Jubeat saved inventory did not load");
                var restored = (NostalgiaJukeboxBlockEntity)loaded;
                helper.assertTrue(restored.getTheItem().is(Items.MUSIC_DISC_13)
                    && restored.getSongPlayer().getTicksSinceSongStarted() >= 60,
                    "Jubeat lost its disc or restored playback did not tick");
                helper.getLevel().setBlockEntity(restored);
                players.get(i).setItemInHand(InteractionHand.MAIN_HAND, ItemStack.EMPTY);
                helper.useBlock(base.above(2), players.get(i));
                helper.assertTrue(restored.isEmpty() && !restored.getSongPlayer().isPlaying(),
                    "Reloaded Jubeat could not eject from its topper");
                helper.assertBlockProperty(base, NostalgiaCabinetBlock.HAS_RECORD, false);
            }
            helper.assertItemEntityCountIs(Items.MUSIC_DISC_13, BASE, 6, 4);
            helper.succeed();
        });
    }

    @GameTest(template="nostalgia_test")
    public static void jubeatFlushNeighborsSurviveCreativeRemovalInEveryFacing(GameTestHelper helper) {
        for (Direction facing : Direction.Plane.HORIZONTAL) {
            Player operator = player(helper, GameType.CREATIVE);
            BlockPos neighbor = BASE.relative(facing.getClockWise());
            placeFacing(helper, operator, BASE, facing, new ItemStack(FunPackCustom.JUBEAT_ITEM.get()));
            placeFacing(helper, operator, neighbor, facing, new ItemStack(FunPackCustom.JUBEAT_ITEM.get()));
            operator.setItemInHand(InteractionHand.MAIN_HAND, new ItemStack(Items.MUSIC_DISC_13));
            helper.useBlock(BASE.above(), operator);
            operator.setItemInHand(InteractionHand.MAIN_HAND, new ItemStack(Items.MUSIC_DISC_CAT));
            helper.useBlock(neighbor.above(2), operator);
            var neighborEntity = entity(helper, neighbor);
            for (int section=0; section<3; section++) {
                BlockPos first = helper.absolutePos(BASE.above(section));
                BlockPos second = helper.absolutePos(neighbor.above(section));
                for (var firstBox : helper.getLevel().getBlockState(first).getCollisionShape(helper.getLevel(), first).toAabbs()) {
                    for (var secondBox : helper.getLevel().getBlockState(second).getCollisionShape(helper.getLevel(), second).toAabbs()) {
                        helper.assertFalse(firstBox.move(first.getX(),first.getY(),first.getZ())
                                .intersects(secondBox.move(second.getX(),second.getY(),second.getZ())),
                            "Flush Jubeat cabinets overlap collision facing " + facing);
                    }
                }
            }
            BlockPos top = helper.absolutePos(BASE.above(2));
            var state = helper.getLevel().getBlockState(top);
            state.getBlock().playerWillDestroy(helper.getLevel(), top, state, operator);
            helper.getLevel().destroyBlock(top, false, operator);
            for (int section=0; section<3; section++) {
                helper.assertBlockPresent(Blocks.AIR, BASE.above(section));
                helper.assertBlockPresent(FunPackCustom.JUBEAT.get(), neighbor.above(section));
            }
            helper.assertTrue(neighborEntity.getTheItem().is(Items.MUSIC_DISC_CAT)
                    && neighborEntity.getSongPlayer().isPlaying(),
                "Removing Jubeat affected the adjacent cabinet's disc");
            helper.assertItemEntityCountIs(Items.MUSIC_DISC_13, BASE, 3, 1);
            helper.assertItemEntityCountIs(Items.MUSIC_DISC_CAT, BASE, 3, 0);
            helper.assertItemEntityCountIs(FunPackCustom.JUBEAT_ITEM.get(), BASE, 3, 0);
            helper.getLevel().destroyBlock(helper.absolutePos(neighbor), true);
            helper.assertItemEntityCountIs(FunPackCustom.JUBEAT_ITEM.get(), BASE, 3, 1);
            helper.assertItemEntityCountIs(Items.MUSIC_DISC_CAT, BASE, 3, 1);
            discardDrops(helper);
        }
        helper.succeed();
    }

    @GameTest(template="nostalgia_test")
    public static void jubeatSlopedControlsNarrowPedestalAndDiscClearanceRotateTogether(GameTestHelper helper) {
        for (Direction facing : Direction.Plane.HORIZONTAL) {
            Player operator = player(helper, GameType.SURVIVAL);
            placeFacing(helper, operator, BASE, facing, new ItemStack(FunPackCustom.JUBEAT_ITEM.get()));
            BlockPos base = helper.absolutePos(BASE);
            var lower = helper.getBlockState(BASE).getCollisionShape(helper.getLevel(), base);
            var lowerHit = lower.clip(point(base,facing,-8,8,11), point(base,facing,8,8,11), base);
            helper.assertTrue(lowerHit != null && lowerHit.getLocation().distanceTo(point(base,facing,3.3,8,11)) < .001,
                "Jubeat's pedestal collision is wider than its body facing " + facing);
            var plaqueHit = lower.clip(point(base,facing,-8,10.5,7.5),point(base,facing,8,10.5,7.5),base);
            helper.assertTrue(plaqueHit != null && plaqueHit.getLocation().distanceTo(point(base,facing,2.8,10.5,7.5)) < .001,
                "The raised lower blue panel cannot be selected");
            helper.assertTrue(lower.clip(point(base,facing,-8,14,3),point(base,facing,24,14,3),base) == null,
                "The old wedge collision remains below the tilted control cube");
            BlockPos consolePos = base.above();
            var console = helper.getLevel().getBlockState(consolePos).getShape(helper.getLevel(), consolePos);
            helper.assertTrue(console.clip(point(base,facing,-8,26,2.5), point(base,facing,24,26,2.5),consolePos) == null,
                "Invisible selection fills the open space above the tilted controls");
            var controlsHit = console.clip(point(base,facing,-8,21.5,7.5),point(base,facing,8,21.5,7.5),consolePos);
            helper.assertTrue(controlsHit != null && controlsHit.getLocation().distanceTo(point(base,facing,3,21.5,7.5)) < .001,
                "The lower control cube has the wrong width facing " + facing);
            helper.assertTrue(console.clip(point(base,facing,-8,26.5,10.1), point(base,facing,8,26.5,10.1),consolePos) != null,
                "The sloped display neck above the controls cannot be selected");
            helper.assertTrue(console.clip(point(base,facing,-8,26,9), point(base,facing,24,26,9),consolePos) == null,
                "Invisible collision fills the space in front of the sloped display neck");
            BlockPos topPos = base.above(2);
            var top = helper.getLevel().getBlockState(topPos).getCollisionShape(helper.getLevel(), topPos);
            var topHit = top.clip(point(base,facing,8,48,13.5),point(base,facing,8,35,13.5),topPos);
            helper.assertTrue(topHit != null && Math.abs(topHit.getLocation().y-base.getY()-41.338/16) < .001,
                "The cube topper has the wrong collision height");
            helper.assertTrue(top.clip(point(base,facing,-8,40.5,15.2),point(base,facing,24,40.5,15.2),topPos) == null,
                "Upright collision remains behind the forward-tilted cube");
            for (int section=0; section<3; section++) {
                BlockPos pos = base.above(section);
                var bounds = helper.getLevel().getBlockState(pos).getCollisionShape(helper.getLevel(), pos).bounds();
                helper.assertTrue(bounds.minX >= 0 && bounds.maxX <= 1 && bounds.minZ >= 0 && bounds.maxZ <= 1
                    && bounds.minY >= 0 && bounds.maxY <= 1, "Jubeat collision protrudes into an adjacent cell");
            }
            operator.setItemInHand(InteractionHand.MAIN_HAND, new ItemStack(Items.MUSIC_DISC_13));
            helper.useBlock(BASE.above(),operator);
            operator.setItemInHand(InteractionHand.MAIN_HAND,ItemStack.EMPTY);
            helper.useBlock(BASE,operator);
            var drops = helper.getEntities(EntityType.ITEM,BASE,3);
            helper.assertTrue(drops.size()==1 && drops.getFirst().getItem().is(Items.MUSIC_DISC_13),
                "Jubeat must eject exactly one disc");
            var disc = drops.getFirst();
            helper.assertTrue(helper.getLevel().noCollision(disc,disc.getBoundingBox()),
                "Jubeat ejected its disc inside collision facing " + facing);
            discardDrops(helper);
            helper.getLevel().destroyBlock(base,false);
        }
        helper.succeed();
    }

    @GameTest(template="nostalgia_test")
    public static void jubeatRejectsBlockedTopAndDropsOnceWhenSupportBreaks(GameTestHelper helper) {
        for (Direction facing : Direction.Plane.HORIZONTAL) {
            Player operator = player(helper,GameType.SURVIVAL);
            operator.setYRot(facing.getOpposite().toYRot());
            operator.setItemInHand(InteractionHand.MAIN_HAND,new ItemStack(FunPackCustom.JUBEAT_ITEM.get()));
            helper.setBlock(BASE.above(2),Blocks.STONE);
            helper.assertFalse(place(helper,operator),"Jubeat replaced an obstructed topper cell");
            helper.assertTrue(operator.getMainHandItem().getCount()==1,"Failed placement consumed the cabinet");
            helper.assertBlockPresent(Blocks.AIR,BASE);
            helper.assertBlockPresent(Blocks.AIR,BASE.above());
            helper.assertBlockPresent(Blocks.STONE,BASE.above(2));
            helper.setBlock(BASE.above(2),Blocks.AIR);
            helper.assertTrue(place(helper,operator),"Jubeat failed to place after obstruction removal");
            helper.getLevel().destroyBlock(helper.absolutePos(BASE.below()),false);
            for (int section=0; section<3; section++) helper.assertBlockPresent(Blocks.AIR,BASE.above(section));
            helper.assertItemEntityCountIs(FunPackCustom.JUBEAT_ITEM.get(),BASE,3,1);
            discardDrops(helper);
        }
        helper.succeed();
    }

    private static void placeFacing(GameTestHelper helper,Player operator,BlockPos base,Direction facing,ItemStack stack) {
        operator.setYRot(facing.getOpposite().toYRot());
        operator.setItemInHand(InteractionHand.MAIN_HAND,stack);
        helper.assertTrue(place(helper,operator,base),"Jubeat placement failed facing " + facing);
        for (int section=0; section<3; section++) {
            helper.assertBlockPresent(FunPackCustom.JUBEAT.get(),base.above(section));
            helper.assertBlockProperty(base.above(section),NostalgiaCabinetBlock.PART,NostalgiaCabinetBlock.Part.values()[section]);
            helper.assertBlockProperty(base.above(section),NostalgiaCabinetBlock.FACING,facing);
            if (section>0) helper.assertTrue(helper.getLevel().getBlockEntity(helper.absolutePos(base.above(section)))==null,
                "Jubeat created a duplicate disc inventory");
        }
    }

    private static NostalgiaJukeboxBlockEntity entity(GameTestHelper helper,BlockPos base) {
        return (NostalgiaJukeboxBlockEntity)helper.getBlockEntity(base);
    }

    /** Rotate a north-facing model point without changing the actual placed cabinet's state. */
    private static Vec3 point(BlockPos base,Direction facing,double x,double y,double z) {
        Vec3 local = switch(facing) {
            case EAST -> new Vec3(16-z,y,x);
            case SOUTH -> new Vec3(16-x,y,16-z);
            case WEST -> new Vec3(z,y,16-x);
            default -> new Vec3(x,y,z);
        };
        return Vec3.atLowerCornerOf(base).add(local.scale(1.0/16));
    }

    private static void discardDrops(GameTestHelper helper) {
        helper.getEntities(EntityType.ITEM,BASE,5).forEach(item -> item.discard());
    }
}
