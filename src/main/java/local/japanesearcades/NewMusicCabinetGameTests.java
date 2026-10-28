package local.japanesearcades;

import static local.japanesearcades.NostalgiaCabinetGameTests.BASE;
import static local.japanesearcades.NostalgiaCabinetGameTests.entity;
import static local.japanesearcades.NostalgiaCabinetGameTests.insert;
import static local.japanesearcades.NostalgiaCabinetGameTests.player;

import java.util.List;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.component.DataComponents;
import net.minecraft.gametest.framework.GameTest;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.BlockItem;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.item.context.BlockPlaceContext;
import net.minecraft.world.level.GameType;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.Mirror;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.material.PushReaction;
import net.minecraft.world.phys.BlockHitResult;
import net.minecraft.world.phys.Vec3;
import net.neoforged.neoforge.gametest.GameTestHolder;
import net.neoforged.neoforge.gametest.PrefixGameTestTemplate;

/** Real item placement, disc transactions and connected removal for the three new cabinets. */
@GameTestHolder(JapaneseArcades.MOD_ID)
@PrefixGameTestTemplate(false)
public final class NewMusicCabinetGameTests {
    private static List<Item> items() {
        return List.of(JapaneseArcades.BOMBERGIRL_ITEM.get(), JapaneseArcades.GITADORA_GUITARFREAKS_ITEM.get(),
            JapaneseArcades.GITADORA_DRUMMANIA_ITEM.get());
    }
    private static boolean wide(Item item) { return item == JapaneseArcades.GITADORA_DRUMMANIA_ITEM.get(); }
    private static int count(Item item) { return wide(item) ? GitadoraDrummaniaCabinetBlock.SECTION_COUNT : 3; }
    private static BlockPos section(Item item, BlockPos anchor, Direction facing, int index) {
        return wide(item) ? GitadoraDrummaniaCabinetBlock.sectionPosition(anchor, facing, index) : anchor.above(index);
    }
    private static void floor(GameTestHelper helper, Item item, BlockPos anchor, Direction facing) {
        for (int i = 0; i < (wide(item) ? 4 : 1); i++) helper.setBlock(section(item, anchor, facing, i).below(), Blocks.STONE);
    }
    private static boolean place(GameTestHelper helper, Player player, BlockPos anchor, Direction facing) {
        player.setYRot(facing.getOpposite().toYRot());
        BlockPos ground = helper.absolutePos(anchor.below());
        var hit = new BlockHitResult(Vec3.atCenterOf(ground).add(0, .5, 0), Direction.UP, ground, false);
        return ((BlockItem) player.getMainHandItem().getItem()).place(new BlockPlaceContext(player,
            InteractionHand.MAIN_HAND, player.getMainHandItem(), hit)).consumesAction();
    }
    private static void cabinet(GameTestHelper helper, Player player, Item item, BlockPos anchor, Direction facing) {
        floor(helper, item, anchor, facing);
        player.setItemInHand(InteractionHand.MAIN_HAND, new ItemStack(item, 2));
        helper.assertTrue(place(helper, player, anchor, facing), "Cabinet failed to place: " + item + " facing " + facing);
        helper.assertTrue(player.getMainHandItem().getCount() == (player.isCreative() ? 2 : 1), "Placement consumed the wrong count");
        complete(helper, item, anchor, facing);
    }
    private static void complete(GameTestHelper helper, Item item, BlockPos anchor, Direction facing) {
        var block = (NostalgiaCabinetBlock) ((BlockItem) item).getBlock();
        for (int i = 0; i < count(item); i++) {
            BlockPos relative = section(item, anchor, facing, i), absolute = helper.absolutePos(relative);
            var state = helper.getBlockState(relative);
            helper.assertBlockPresent(block, relative);
            helper.assertBlockProperty(relative, NostalgiaCabinetBlock.FACING, facing);
            helper.assertBlockProperty(relative, NostalgiaCabinetBlock.PART,
                NostalgiaCabinetBlock.Part.values()[wide(item) ? GitadoraDrummaniaCabinetBlock.height(i) : i]);
            if (wide(item)) helper.assertBlockProperty(relative, GitadoraDrummaniaCabinetBlock.SECTION, i);
            helper.assertTrue(block.basePosition(absolute, state).equals(helper.absolutePos(anchor)), "Section resolved another inventory anchor");
            helper.assertTrue(i == 0 ? helper.getLevel().getBlockEntity(absolute) instanceof NostalgiaJukeboxBlockEntity
                : helper.getLevel().getBlockEntity(absolute) == null, "Only the main base may contain a saved inventory");
            helper.assertTrue(state.getPistonPushReaction() == PushReaction.BLOCK, "Piston movement would split the cabinet");
        }
    }
    private static void gone(GameTestHelper helper, Item item, BlockPos anchor, Direction facing) {
        for (int i = 0; i < count(item); i++) helper.assertBlockPresent(Blocks.AIR, section(item, anchor, facing, i));
    }
    private static void clearDrops(GameTestHelper helper) { helper.getEntities(EntityType.ITEM, BASE, 7).forEach(drop -> drop.discard()); }
    private static void creativeRemove(GameTestHelper helper, ServerPlayer player, BlockPos relative) {
        helper.assertTrue(player.gameMode.destroyBlock(helper.absolutePos(relative)), "Native creative cabinet break failed");
    }

    @GameTest(template = "nostalgia_test")
    public static void newCabinetsPlaceEveryFacingAndRejectBlockedCellsAndEntities(GameTestHelper helper) {
        Player operator = player(helper, GameType.SURVIVAL);
        for (Item item : items()) for (Direction facing : Direction.Plane.HORIZONTAL) {
            floor(helper, item, BASE, facing);
            for (int blocked = 0; blocked < count(item); blocked++) {
                BlockPos target = section(item, BASE, facing, blocked);
                helper.setBlock(target, Blocks.STONE);
                operator.setItemInHand(InteractionHand.MAIN_HAND, new ItemStack(item, 2));
                helper.assertFalse(place(helper, operator, BASE, facing), "Cabinet placed through occupied section " + blocked);
                helper.assertTrue(operator.getMainHandItem().getCount() == 2, "Blocked placement consumed an item");
                for (int i = 0; i < count(item); i++) helper.assertBlockPresent(i == blocked ? Blocks.STONE : Blocks.AIR, section(item, BASE, facing, i));
                helper.setBlock(target, Blocks.AIR);
            }
            for (int support = 0; support < (wide(item) ? 4 : 1); support++) {
                BlockPos ground = section(item, BASE, facing, support).below();
                helper.setBlock(ground, Blocks.STONE_SLAB);
                operator.setItemInHand(InteractionHand.MAIN_HAND, new ItemStack(item, 2));
                helper.assertFalse(place(helper, operator, BASE, facing), "Cabinet accepted a non-sturdy support");
                helper.assertTrue(operator.getMainHandItem().getCount() == 2, "Unsupported placement consumed an item");
                gone(helper, item, BASE, facing);
                helper.setBlock(ground, Blocks.STONE);
            }
            // A real collidable entity intersects the upper screen in every orientation.
            Vec3 rotated = rotate(facing, 8, 34, 12);
            var occupant = helper.spawn(EntityType.ARMOR_STAND, Vec3.atLowerCornerOf(BASE).add(rotated));
            occupant.blocksBuilding = true;
            occupant.setNoGravity(true);
            operator.setItemInHand(InteractionHand.MAIN_HAND, new ItemStack(item, 2));
            helper.assertFalse(place(helper, operator, BASE, facing), "Upper cabinet placed through an entity");
            helper.assertTrue(operator.getMainHandItem().getCount() == 2, "Entity obstruction consumed an item");
            occupant.discard();
            if (item == JapaneseArcades.GITADORA_GUITARFREAKS_ITEM.get()) {
                BlockPos side = BASE.relative(facing.getClockWise()).above();
                helper.setBlock(side, Blocks.STONE);
                helper.assertFalse(place(helper, operator, BASE, facing), "GuitarFreaks side overhang intersected a solid neighbor");
                helper.assertTrue(operator.getMainHandItem().getCount() == 2, "Side obstruction consumed an item");
                helper.setBlock(side, Blocks.AIR);
            }
            cabinet(helper, operator, item, BASE, facing);
            helper.getLevel().destroyBlock(helper.absolutePos(BASE), true);
            gone(helper, item, BASE, facing);
            helper.assertItemEntityCountIs(item, BASE, 5, 1);
            clearDrops(helper);
        }
        helper.succeed();
    }

    @GameTest(template = "nostalgia_test")
    public static void newCabinetsAnySectionAndSupportRemoveOneItemAndOneDisc(GameTestHelper helper) {
        Player operator = player(helper, GameType.SURVIVAL);
        for (Item item : items()) for (Direction facing : Direction.Plane.HORIZONTAL) {
            int supportCount = wide(item) ? 4 : 1;
            for (int removed = -supportCount; removed < count(item); removed++) {
                cabinet(helper, operator, item, BASE, facing);
                insert(helper, operator, section(item, BASE, facing, count(item) - 1));
                var original = entity(helper);
                BlockPos target = removed < 0 ? section(item, BASE, facing, -removed - 1).below() : section(item, BASE, facing, removed);
                helper.getLevel().destroyBlock(helper.absolutePos(target), removed >= 0);
                gone(helper, item, BASE, facing);
                helper.assertItemEntityCountIs(item, BASE, 5, 1);
                helper.assertItemEntityCountIs(Items.MUSIC_DISC_13, BASE, 5, 1);
                helper.assertFalse(original.getSongPlayer().isPlaying(), "Removed cabinet kept playing");
                clearDrops(helper);
            }
        }
        helper.succeed();
    }

    @GameTest(template = "nostalgia_test")
    public static void newCabinetsEverySectionInsertsAndEjectsWithoutObstructingDisc(GameTestHelper helper) {
        Player operator = player(helper, GameType.SURVIVAL);
        for (Item item : items()) for (Direction facing : Direction.Plane.HORIZONTAL) {
            cabinet(helper, operator, item, BASE, facing);
            for (int clicked = 0; clicked < count(item); clicked++) {
                insert(helper, operator, section(item, BASE, facing, clicked));
                helper.assertTrue(operator.getMainHandItem().getCount() == 1, "Insert did not consume exactly one disc");
                operator.setItemInHand(InteractionHand.MAIN_HAND, ItemStack.EMPTY);
                helper.useBlock(section(item, BASE, facing, (clicked + 1) % count(item)), operator);
                helper.assertTrue(entity(helper).isEmpty() && !entity(helper).getSongPlayer().isPlaying(), "Ejection did not empty and stop shared inventory");
                helper.assertBlockProperty(BASE, NostalgiaCabinetBlock.HAS_RECORD, false);
                var drops = helper.getEntities(EntityType.ITEM, BASE, 5);
                helper.assertTrue(drops.size() == 1 && drops.getFirst().getItem().is(Items.MUSIC_DISC_13), "Ejection returned the wrong disc count");
                var disc = drops.getFirst();
                for (int i = 0; i < count(item); i++) {
                    BlockPos pos = helper.absolutePos(section(item, BASE, facing, i));
                    for (var box : helper.getLevel().getBlockState(pos).getCollisionShape(helper.getLevel(), pos).toAabbs()) {
                        helper.assertFalse(box.move(pos).intersects(disc.getBoundingBox()), "Freshly ejected disc intersects cabinet hardware");
                    }
                }
                clearDrops(helper);
            }
            helper.getLevel().destroyBlock(helper.absolutePos(BASE), false);
            clearDrops(helper);
        }
        helper.succeed();
    }

    @GameTest(template = "nostalgia_test")
    public static void newCabinetsSavedNamedDiscsTickReloadAndEject(GameTestHelper helper) {
        List<BlockPos> anchors = List.of(new BlockPos(1, 1, 4), new BlockPos(3, 1, 4), new BlockPos(5, 1, 4));
        List<Item> items = items();
        Player operator = player(helper, GameType.SURVIVAL);
        Component label = Component.literal("Cabinet persistence test");
        for (int i = 0; i < items.size(); i++) {
            Item item = items.get(i);
            BlockPos anchor = anchors.get(i);
            floor(helper, item, anchor, Direction.NORTH);
            ItemStack stack = new ItemStack(item), disc = new ItemStack(Items.MUSIC_DISC_13);
            disc.set(DataComponents.CUSTOM_NAME, label);
            CompoundTag tag = new CompoundTag();
            tag.put("RecordItem", disc.save(helper.getLevel().registryAccess()));
            tag.putLong("ticks_since_song_started", 40);
            BlockItem.setBlockEntityData(stack, JapaneseArcades.NOSTALGIA_JUKEBOX.get(), tag);
            operator.setItemInHand(InteractionHand.MAIN_HAND, stack);
            helper.assertTrue(place(helper, operator, anchor, Direction.NORTH), "Saved cabinet item could not be placed");
            helper.assertBlockProperty(anchor, NostalgiaCabinetBlock.HAS_RECORD, true);
        }
        helper.runAfterDelay(25, () -> {
            for (int i = 0; i < items.size(); i++) {
                BlockPos anchor = anchors.get(i);
                var original = (NostalgiaJukeboxBlockEntity) helper.getBlockEntity(anchor);
                var loaded = BlockEntity.loadStatic(helper.absolutePos(anchor), helper.getBlockState(anchor),
                    original.saveWithFullMetadata(helper.getLevel().registryAccess()), helper.getLevel().registryAccess());
                helper.assertTrue(loaded instanceof NostalgiaJukeboxBlockEntity, "New cabinet saved inventory could not reload");
                var restored = (NostalgiaJukeboxBlockEntity) loaded;
                helper.assertTrue(restored.getTheItem().is(Items.MUSIC_DISC_13)
                    && label.equals(restored.getTheItem().get(DataComponents.CUSTOM_NAME))
                    && restored.getSongPlayer().getTicksSinceSongStarted() >= 60, "Disc data or playback progress was lost");
                helper.getLevel().setBlockEntity(restored);
                operator.setItemInHand(InteractionHand.MAIN_HAND, ItemStack.EMPTY);
                helper.useBlock(section(items.get(i), anchor, Direction.NORTH, count(items.get(i)) - 1), operator);
                helper.assertTrue(restored.isEmpty() && !restored.getSongPlayer().isPlaying(), "Reloaded cabinet failed to eject through another section");
            }
            var discs = helper.getEntities(EntityType.ITEM, BASE, 6);
            helper.assertTrue(discs.size() == 3 && discs.stream().allMatch(drop -> drop.getItem().is(Items.MUSIC_DISC_13)
                && label.equals(drop.getItem().get(DataComponents.CUSTOM_NAME))), "Reloaded named discs were lost or duplicated");
            helper.succeed();
        });
    }

    @GameTest(template = "nostalgia_test")
    public static void newCabinetsCreativeRemovalKeepsNeighborAndDiscWithoutCabinetDrops(GameTestHelper helper) {
        Player operator = player(helper, GameType.SURVIVAL);
        ServerPlayer creative = GachaponTransactionGameTests.createPlayer(helper, "NewCabCreative", GameType.CREATIVE);
        // The real player's normal spawn overlaps the west-facing neighbor footprint.
        // Keep the break actor above every cabinet while the separate operator places them.
        BlockPos clearPosition = helper.absolutePos(BASE.above(5));
        creative.setPos(clearPosition.getX() + .5, clearPosition.getY(), clearPosition.getZ() + .5);
        for (Item item : items()) for (Direction facing : Direction.Plane.HORIZONTAL) for (int broken = 0; broken < count(item); broken++) {
            BlockPos neighbor = BASE.relative(facing.getClockWise(), 2);
            cabinet(helper, operator, item, BASE, facing);
            insert(helper, operator, BASE);
            cabinet(helper, operator, item, neighbor, facing);
            operator.setItemInHand(InteractionHand.MAIN_HAND, new ItemStack(Items.MUSIC_DISC_CAT));
            helper.useBlock(neighbor, operator);
            var neighborEntity = (NostalgiaJukeboxBlockEntity) helper.getBlockEntity(neighbor);
            creativeRemove(helper, creative, section(item, BASE, facing, broken));
            gone(helper, item, BASE, facing);
            complete(helper, item, neighbor, facing);
            helper.assertTrue(neighborEntity.getTheItem().is(Items.MUSIC_DISC_CAT) && neighborEntity.getSongPlayer().isPlaying(), "Creative removal touched neighboring inventory");
            helper.assertItemEntityCountIs(item, BASE, 6, 0);
            helper.assertItemEntityCountIs(Items.MUSIC_DISC_13, BASE, 6, 1);
            helper.assertItemEntityCountIs(Items.MUSIC_DISC_CAT, BASE, 6, 0);
            creativeRemove(helper, creative, neighbor);
            clearDrops(helper);
        }
        helper.succeed();
    }

    @GameTest(template = "nostalgia_test")
    public static void drumManiaMirroredStructuresStillResolveOneAnchorAndRemoveTogether(GameTestHelper helper) {
        Item item = JapaneseArcades.GITADORA_DRUMMANIA_ITEM.get();
        Player operator = player(helper, GameType.SURVIVAL);
        for (Direction facing : Direction.Plane.HORIZONTAL) for (Mirror mirror : List.of(Mirror.LEFT_RIGHT, Mirror.FRONT_BACK)) {
            var base = JapaneseArcades.GITADORA_DRUMMANIA.get().defaultBlockState().setValue(NostalgiaCabinetBlock.FACING, facing);
            var reflected = base.mirror(mirror);
            Direction nextFacing = reflected.getValue(NostalgiaCabinetBlock.FACING);
            BlockPos nextAnchor = section(item, BASE, nextFacing, 1);
            // Place the mirrored positions as a structure loader does, without incremental neighbor teardown.
            for (int i = 0; i < 10; i++) {
                BlockPos old = section(item, BlockPos.ZERO, facing, i);
                BlockPos relative = BASE.offset(mirror == Mirror.FRONT_BACK ? -old.getX() : old.getX(), old.getY(),
                    mirror == Mirror.LEFT_RIGHT ? -old.getZ() : old.getZ());
                var state = base.setValue(GitadoraDrummaniaCabinetBlock.SECTION, i)
                    .setValue(NostalgiaCabinetBlock.PART, NostalgiaCabinetBlock.Part.values()[GitadoraDrummaniaCabinetBlock.height(i)]).mirror(mirror);
                if (GitadoraDrummaniaCabinetBlock.height(i) == 0) helper.setBlock(relative.below(), Blocks.STONE);
                helper.getLevel().setBlock(helper.absolutePos(relative), state, 18);
                if (state.getValue(GitadoraDrummaniaCabinetBlock.SECTION) == 0) nextAnchor = relative;
            }
            complete(helper, item, nextAnchor, nextFacing);
            operator.setItemInHand(InteractionHand.MAIN_HAND, new ItemStack(Items.MUSIC_DISC_13));
            helper.useBlock(section(item, nextAnchor, nextFacing, 9), operator);
            helper.assertTrue(((NostalgiaJukeboxBlockEntity) helper.getBlockEntity(nextAnchor)).getSongPlayer().isPlaying(), "Mirrored control did not reach inventory");
            helper.getLevel().destroyBlock(helper.absolutePos(section(item, nextAnchor, nextFacing, 8)), true);
            gone(helper, item, nextAnchor, nextFacing);
            helper.assertItemEntityCountIs(item, BASE, 6, 1);
            helper.assertItemEntityCountIs(Items.MUSIC_DISC_13, BASE, 6, 1);
            clearDrops(helper);
        }
        helper.succeed();
    }

    private static Vec3 rotate(Direction facing, double x, double y, double z) {
        return switch (facing) {
            case EAST -> new Vec3(16-z, y, x).scale(1.0/16);
            case SOUTH -> new Vec3(16-x, y, 16-z).scale(1.0/16);
            case WEST -> new Vec3(z, y, 16-x).scale(1.0/16);
            default -> new Vec3(x, y, z).scale(1.0/16);
        };
    }
}
