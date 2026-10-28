package local.japanesearcades;

import static local.japanesearcades.GachaponTransactionGameTests.aimAt;
import static local.japanesearcades.GachaponTransactionGameTests.createPlayer;

import io.netty.buffer.Unpooled;
import java.util.Arrays;
import java.util.List;
import java.util.UUID;
import java.util.concurrent.atomic.AtomicInteger;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.NonNullList;
import net.minecraft.core.component.DataComponents;
import net.minecraft.gametest.framework.GameTest;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.RegistryFriendlyByteBuf;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.ContainerHelper;
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
import net.minecraft.world.phys.BlockHitResult;
import net.minecraft.world.phys.HitResult;
import net.minecraft.world.phys.Vec3;
import net.neoforged.neoforge.capabilities.Capabilities;
import net.neoforged.neoforge.common.NeoForge;
import net.neoforged.neoforge.event.level.BlockEvent;
import net.neoforged.neoforge.gametest.GameTestHolder;
import net.neoforged.neoforge.gametest.PrefixGameTestTemplate;

/** Real compact placement and menu/payment/save compatibility for both reward grids. */
@GameTestHolder(JapaneseArcades.MOD_ID)
@PrefixGameTestTemplate(false)
public final class ClawMachineLayoutGameTests {
    private static final BlockPos BASE = new BlockPos(3, 1, 3);
    private static ClawMachineBlock block(ClawMachineLayout layout) {
        return layout == ClawMachineLayout.COMPACT ? JapaneseArcades.COMPACT_CLAW_MACHINE.get() : JapaneseArcades.CLAW_MACHINE.get();
    }
    private static Item item(ClawMachineLayout layout) { return block(layout).asItem(); }
    private static ItemStack named(Item item, int count, String name) {
        ItemStack stack = new ItemStack(item, count);
        stack.set(DataComponents.CUSTOM_NAME, Component.literal(name));
        return stack;
    }
    private static void floor(GameTestHelper helper, ClawMachineLayout layout, BlockPos anchor, Direction facing) {
        for (int part = 0; part < layout.floorPartCount(); part++) helper.setBlock(layout.partPosition(anchor, facing, part).below(), Blocks.STONE);
    }
    private static boolean place(GameTestHelper helper, Player player, ClawMachineLayout layout, BlockPos anchor, Direction facing) {
        player.setYRot(facing.getOpposite().toYRot());
        player.setItemInHand(InteractionHand.MAIN_HAND, new ItemStack(item(layout), 2));
        BlockPos ground = helper.absolutePos(anchor.below());
        var hit = new BlockHitResult(ground.getCenter().add(0, .5, 0), Direction.UP, ground, false);
        return ((BlockItem) player.getMainHandItem().getItem()).place(new BlockPlaceContext(player,
            InteractionHand.MAIN_HAND, player.getMainHandItem(), hit)).consumesAction();
    }
    private static void complete(GameTestHelper helper, ClawMachineLayout layout, BlockPos anchor, Direction facing) {
        var machine = (ClawMachineBlockEntity) helper.getBlockEntity(anchor);
        helper.assertTrue(machine.layout() == layout, "Controller has the wrong layout");
        for (int part = 0; part < layout.partCount(); part++) {
            BlockPos relative = layout.partPosition(anchor, facing, part), absolute = helper.absolutePos(relative);
            helper.assertBlockPresent(block(layout), relative);
            helper.assertBlockProperty(relative, block(layout).partProperty(), part);
            helper.assertTrue(ClawMachineBlock.machineAt(helper.getLevel(), absolute) == machine
                && (part == 0 || helper.getLevel().getBlockEntity(absolute) == null), "A section lost or duplicated its controller");
        }
    }
    private static void gone(GameTestHelper helper, ClawMachineLayout layout, BlockPos anchor, Direction facing) {
        for (int part = 0; part < layout.partCount(); part++) helper.assertBlockPresent(Blocks.AIR, layout.partPosition(anchor, facing, part));
    }
    private static void clearDrops(GameTestHelper helper) { helper.getEntities(EntityType.ITEM, BASE, 8).forEach(drop -> drop.discard()); }
    private static int dropped(GameTestHelper helper, Item item) {
        return helper.getEntities(EntityType.ITEM, BASE, 7).stream().filter(drop -> drop.getItem().is(item)).mapToInt(drop -> drop.getItem().getCount()).sum();
    }
    private static ClawMachineBlockEntity fixture(GameTestHelper helper, ServerPlayer owner, ClawMachineLayout layout, BlockPos anchor) {
        floor(helper, layout, anchor, Direction.NORTH);
        aimAt(owner, helper.absolutePos(anchor));
        helper.assertTrue(place(helper, owner, layout, anchor, Direction.NORTH), "Could not place claw fixture");
        owner.closeContainer();
        owner.getInventory().clearContent();
        return (ClawMachineBlockEntity) helper.getBlockEntity(anchor);
    }
    private static ClawMachineBlockEntity load(GameTestHelper helper, ClawMachineBlockEntity original, CompoundTag tag) {
        var loaded = BlockEntity.loadStatic(original.getBlockPos(), original.getBlockState(), tag, helper.getLevel().registryAccess());
        helper.assertTrue(loaded instanceof ClawMachineBlockEntity, "Claw save did not reload");
        helper.getLevel().setBlockEntity(loaded);
        return (ClawMachineBlockEntity) loaded;
    }

    @GameTest(template = "nostalgia_test")
    public static void compactEveryFacingAndPartReturnsOneMachineAndWholeStoredStacks(GameTestHelper helper) {
        var layout = ClawMachineLayout.COMPACT;
        Player player = helper.makeMockPlayer(GameType.SURVIVAL);
        for (Direction facing : Direction.Plane.HORIZONTAL) for (int broken = 0; broken < layout.partCount(); broken++) {
            floor(helper, layout, BASE, facing);
            helper.assertTrue(place(helper, player, layout, BASE, facing), "Compact placement failed");
            helper.assertTrue(player.getMainHandItem().getCount() == 1, "Compact placement consumed the wrong count");
            complete(helper, layout, BASE, facing);
            var machine = (ClawMachineBlockEntity) helper.getBlockEntity(BASE);
            machine.operatorInventory().setItem(layout.rewardSlot(layout.rewardCount() - 1), named(Items.DIAMOND, 37, "Compact stock"));
            machine.operatorInventory().setItem(18, named(Items.EMERALD, 23, "Cash"));
            helper.getLevel().destroyBlock(helper.absolutePos(layout.partPosition(BASE, facing, broken)), true);
            gone(helper, layout, BASE, facing);
            helper.assertItemEntityCountIs(item(layout), BASE, 6, 1);
            helper.assertTrue(dropped(helper, Items.DIAMOND) == 37 && dropped(helper, Items.EMERALD) == 23, "Removal lost or duplicated prize/cash stacks");
            clearDrops(helper);
        }
        helper.succeed();
    }

    @GameTest(template = "nostalgia_test")
    public static void compactRejectsEveryBlockedCellEntityAndMissingFloorWithoutTakingItem(GameTestHelper helper) {
        var layout = ClawMachineLayout.COMPACT;
        Player player = helper.makeMockPlayer(GameType.SURVIVAL);
        for (Direction facing : Direction.Plane.HORIZONTAL) {
            floor(helper, layout, BASE, facing);
            for (int part = 0; part < layout.partCount(); part++) {
                BlockPos target = layout.partPosition(BASE, facing, part);
                helper.setBlock(target, Blocks.STONE);
                helper.assertFalse(place(helper, player, layout, BASE, facing), "Compact ignored an occupied cell");
                helper.assertTrue(player.getMainHandItem().getCount() == 2, "Blocked compact placement took an item");
                helper.setBlock(target, Blocks.AIR);
                gone(helper, layout, BASE, facing);
                var occupant = helper.spawn(EntityType.ARMOR_STAND, Vec3.atCenterOf(target));
                occupant.blocksBuilding = true; occupant.setNoGravity(true);
                helper.assertFalse(place(helper, player, layout, BASE, facing), "Compact ignored an entity in another cell");
                helper.assertTrue(player.getMainHandItem().getCount() == 2, "Entity obstruction took an item");
                occupant.discard();
            }
            for (int part = 0; part < layout.floorPartCount(); part++) {
                BlockPos ground = layout.partPosition(BASE, facing, part).below();
                helper.setBlock(ground, Blocks.STONE_SLAB);
                helper.assertFalse(place(helper, player, layout, BASE, facing), "Compact ignored missing full floor support");
                helper.assertTrue(player.getMainHandItem().getCount() == 2, "Missing floor took an item");
                helper.setBlock(ground, Blocks.STONE);
                helper.assertTrue(place(helper, player, layout, BASE, facing), "Clear compact failed to place");
                helper.getLevel().destroyBlock(helper.absolutePos(ground), false);
                gone(helper, layout, BASE, facing);
                helper.assertItemEntityCountIs(item(layout), BASE, 6, 1);
                helper.setBlock(ground, Blocks.STONE);
                clearDrops(helper);
            }
        }
        helper.succeed();
    }

    @GameTest(template = "nostalgia_test")
    public static void compactOwnerProtectionAndNativeCreativeBreakCoverAllEightParts(GameTestHelper helper) {
        var layout = ClawMachineLayout.COMPACT;
        ServerPlayer owner = createPlayer(helper, "CompactOwner", GameType.SURVIVAL);
        ServerPlayer visitor = createPlayer(helper, "CompactVisitor", GameType.SURVIVAL);
        Vec3 away = helper.absolutePos(BASE.above(5)).getCenter();
        visitor.setPos(away);
        for (Direction facing : Direction.Plane.HORIZONTAL) for (int broken = 0; broken < layout.partCount(); broken++) {
            floor(helper, layout, BASE, facing);
            owner.setGameMode(GameType.SURVIVAL);
            owner.setPos(helper.absolutePos(BASE).getCenter().add(facing.getStepX() * 2, -.5, facing.getStepZ() * 2));
            helper.assertTrue(place(helper, owner, layout, BASE, facing), "Owner could not place compact machine");
            var machine = (ClawMachineBlockEntity) helper.getBlockEntity(BASE);
            helper.assertTrue(machine.isOwnerOrCreative(owner) && owner.containerMenu instanceof ClawMachineAccessMenu, "Compact lost owner or initial PIN prompt");
            owner.closeContainer();
            machine.operatorInventory().setItem(layout.rewardSlot(layout.rewardCount() - 1), named(Items.DIAMOND, 31, "Protected prize"));
            for (int part = 0; part < layout.partCount(); part++) {
                BlockPos cell = helper.absolutePos(layout.partPosition(BASE, facing, part));
                var denied = new BlockEvent.BreakEvent(helper.getLevel(), cell, helper.getLevel().getBlockState(cell), visitor);
                NeoForge.EVENT_BUS.post(denied);
                helper.assertTrue(denied.isCanceled(), "Visitor can mine a compact section");
                helper.assertFalse(visitor.gameMode.destroyBlock(cell), "Native visitor break bypassed ownership");
                helper.assertTrue(helper.getLevel().getCapability(Capabilities.ItemHandler.BLOCK, cell, Direction.DOWN) == null, "Compact exposed operator stock to automation");
            }
            owner.setGameMode(GameType.CREATIVE);
            owner.setItemInHand(InteractionHand.MAIN_HAND, ItemStack.EMPTY);
            helper.assertTrue(owner.gameMode.destroyBlock(helper.absolutePos(layout.partPosition(BASE, facing, broken))), "Native creative removal failed");
            gone(helper, layout, BASE, facing);
            helper.assertItemEntityCountIs(item(layout), BASE, 6, 0);
            helper.assertTrue(dropped(helper, Items.DIAMOND) == 31, "Creative compact removal lost or duplicated loaded prize");
            clearDrops(helper);
        }
        helper.succeed();
    }

    @GameTest(template = "nostalgia_test")
    public static void mirroredClawFootprintsRetainOneControllerAndConnectedRemoval(GameTestHelper helper) {
        for (var layout : ClawMachineLayout.values()) for (Direction facing : Direction.Plane.HORIZONTAL)
            for (Mirror mirror : List.of(Mirror.LEFT_RIGHT, Mirror.FRONT_BACK)) {
                var base = block(layout).defaultBlockState().setValue(ClawMachineBlock.FACING, facing);
                BlockPos anchor = BASE;
                Direction reflectedFacing = base.mirror(mirror).getValue(ClawMachineBlock.FACING);
                for (int part = 0; part < layout.partCount(); part++) {
                    BlockPos old = layout.partPosition(BlockPos.ZERO, facing, part);
                    BlockPos pos = BASE.offset(mirror == Mirror.FRONT_BACK ? -old.getX() : old.getX(), old.getY(),
                        mirror == Mirror.LEFT_RIGHT ? -old.getZ() : old.getZ());
                    var state = base.setValue(block(layout).partProperty(), part).mirror(mirror);
                    if (part < layout.floorPartCount()) helper.setBlock(pos.below(), Blocks.STONE);
                    helper.getLevel().setBlock(helper.absolutePos(pos), state, 18);
                    if (ClawMachineBlock.part(state) == 0) anchor = pos;
                }
                complete(helper, layout, anchor, reflectedFacing);
                ((ClawMachineBlockEntity) helper.getBlockEntity(anchor)).operatorInventory().setItem(1, new ItemStack(Items.DIAMOND, 7));
                helper.getLevel().destroyBlock(helper.absolutePos(layout.partPosition(anchor, reflectedFacing, layout.partCount() - 1)), true);
                gone(helper, layout, anchor, reflectedFacing);
                helper.assertItemEntityCountIs(item(layout), BASE, 7, 1);
                helper.assertTrue(dropped(helper, Items.DIAMOND) == 7, "Mirrored machine lost its shared inventory");
                clearDrops(helper);
            }
        helper.succeed();
    }

    @GameTest(template = "nostalgia_test")
    public static void legacyLargeSavesPreserveEveryPhysicalSlotAndMapOldRowsWithoutSecondMigration(GameTestHelper helper) {
        ServerPlayer owner = createPlayer(helper, "ClawMigration", GameType.SURVIVAL);
        var machine = fixture(helper, owner, ClawMachineLayout.LARGE, BASE);
        helper.assertTrue(machine.setPassword(owner, "1234"), "Migration password fixture failed");
        var registry = helper.getLevel().registryAccess();
        CompoundTag legacy = machine.saveWithFullMetadata(registry);
        legacy.remove("RewardLayoutVersion");
        var original = NonNullList.withSize(19, ItemStack.EMPTY);
        for (int physical = 0; physical < 19; physical++) original.set(physical,
            named(physical == 0 ? Items.IRON_INGOT : physical < 10 ? Items.DIAMOND : Items.EMERALD, physical + 1, "Legacy slot " + physical));
        ContainerHelper.saveAllItems(legacy, original, registry);
        machine = load(helper, machine, legacy);
        helper.assertTrue(machine.isOwnerOrCreative(owner) && machine.authenticate(owner, "1234") == 0, "Legacy ownership/password was lost");
        for (int physical = 0; physical < 19; physical++) helper.assertTrue(ItemStack.matches(original.get(physical), machine.operatorInventory().getItem(physical)), "Legacy item moved or changed physical slot " + physical);
        for (int display = 0; display < machine.layout().rewardCount(); display++) {
            int row = display / machine.layout().columns(), column = display % machine.layout().columns();
            helper.assertTrue(column >= 3 ? machine.getRewardDisplay(display).isEmpty()
                : ItemStack.matches(machine.getRewardDisplay(display), original.get(1 + row * 3 + column)), "Legacy row ordering changed");
        }
        var saved = machine.saveWithFullMetadata(registry);
        helper.assertTrue(saved.getInt("RewardLayoutVersion") == 2
            && Arrays.equals(saved.getByteArray("PasswordHash"), legacy.getByteArray("PasswordHash")), "Save omitted migration version or changed credentials");
        machine = load(helper, machine, saved);
        for (int physical = 0; physical < 19; physical++) helper.assertTrue(ItemStack.matches(original.get(physical), machine.operatorInventory().getItem(physical)), "Second load migrated inventory again");
        helper.succeed();
    }

    @GameTest(template = "nostalgia_test")
    public static void legacyPaidPhasesKeepReservedPrizeAndOriginalCashAcrossMigration(GameTestHelper helper) {
        ServerPlayer owner = createPlayer(helper, "ClawPaidLegacy", GameType.SURVIVAL);
        var registry = helper.getLevel().registryAccess();
        for (var phase : ClawMachineBlockEntity.Phase.values()) {
            if (phase.ordinal() < ClawMachineBlockEntity.Phase.DESCENDING.ordinal()) continue;
            var machine = fixture(helper, owner, ClawMachineLayout.LARGE, BASE);
            CompoundTag legacy = machine.saveWithFullMetadata(registry);
            legacy.remove("RewardLayoutVersion");
            var items = NonNullList.withSize(19, ItemStack.EMPTY);
            items.set(0, named(Items.EMERALD, 3, "Token"));
            items.set(10, named(Items.EMERALD, 9, "Collected"));
            ContainerHelper.saveAllItems(legacy, items, registry);
            ItemStack held = named(Items.DIAMOND, 17, "Legacy reserved prize");
            legacy.putInt("PaidPhase", phase.ordinal()); legacy.putInt("PhaseTicks", 1);
            legacy.put("HeldPrize", held.save(registry)); legacy.putUUID("Buyer", owner.getUUID());
            legacy.putBoolean("PlannedWin", phase != ClawMachineBlockEntity.Phase.SLIPPING);
            legacy.putInt("SourceSlot", 4); legacy.putInt("SlipSlot", 6); legacy.putInt("SlipReturnTick", 10);
            legacy.putFloat("TargetX", .5F); legacy.putFloat("TargetZ", .5F);
            legacy.putFloat("SlipStartX", .6F); legacy.putFloat("SlipStartZ", .1F);
            machine = load(helper, machine, legacy);
            var saved = machine.saveWithFullMetadata(registry);
            helper.assertTrue(saved.getInt("SourceSlot") == machine.layout().migrateLegacyDisplaySlot(4)
                && saved.getInt("SlipSlot") == machine.layout().migrateLegacyDisplaySlot(6)
                && ItemStack.matches(machine.operatorInventory().getItem(10), items.get(10)), "Migration moved paid source/slip/cash incorrectly");
            float oldClawX = switch (phase) {
                case DESCENDING, GRABBING, RAISING -> .5F;
                case RETURNING -> .5F + .5F / ClawMachineBlockEntity.phaseDuration(phase);
                case SLIPPING -> .6F;
                default -> 1;
            };
            float oldHeldX = phase == ClawMachineBlockEntity.Phase.SLIPPING
                ? .6F + .4F / ClawMachineBlockEntity.phaseDuration(phase) : oldClawX;
            float oldClawZ = switch (phase) {
                case DESCENDING, GRABBING, RAISING -> .5F;
                case RETURNING -> .5F + (-.3125F - .5F) / ClawMachineBlockEntity.phaseDuration(phase);
                case SLIPPING -> .1F;
                default -> -.3125F;
            };
            float oldHeldZ = phase == ClawMachineBlockEntity.Phase.SLIPPING
                ? .1F - .1F / ClawMachineBlockEntity.phaseDuration(phase) : oldClawZ;
            helper.assertTrue(Math.abs(machine.getClawX() - machine.layout().migrateLegacyX(oldClawX)) < .00001F
                && Math.abs(machine.getHeldX() - machine.layout().migrateLegacyX(oldHeldX)) < .00001F
                && Math.abs(machine.getClawZ() - oldClawZ) < .00001F && Math.abs(machine.getHeldZ() - oldHeldZ) < .00001F,
                "Legacy claw/held pose did not follow its remapped source-to-chute path in " + phase);
            machine = load(helper, machine, saved);
            helper.assertTrue(machine.saveWithFullMetadata(registry).getInt("SourceSlot") == saved.getInt("SourceSlot")
                && Math.abs(machine.getHeldX() - machine.layout().migrateLegacyX(oldHeldX)) < .00001F,
                "Paid source or held pose migrated twice");
            ClawMachineTransactionGameTests.ticks(machine, 180);
            helper.assertTrue(machine.getPhase() == ClawMachineBlockEntity.Phase.IDLE
                && ItemStack.matches(machine.operatorInventory().getItem(10), items.get(10)), "Migrated paid animation lost payment or did not finish");
            if (phase == ClawMachineBlockEntity.Phase.SLIPPING) {
                helper.assertTrue(ItemStack.matches(machine.operatorInventory().getItem(7), held) && dropped(helper, Items.DIAMOND) == 0, "Legacy slip restored to wrong original physical slot");
            } else helper.assertTrue(dropped(helper, Items.DIAMOND) == 17, "Migrated winning animation duplicated/lost its held prize");
            helper.getLevel().destroyBlock(helper.absolutePos(BASE), false);
            clearDrops(helper);
        }
        helper.succeed();
    }

    @GameTest(template = "nostalgia_test")
    public static void bothOperatorMenusShiftWholeStacksIntoAppendedSlotsWithoutTouchingCash(GameTestHelper helper) {
        ServerPlayer owner = createPlayer(helper, "ClawSlots", GameType.SURVIVAL);
        for (var layout : ClawMachineLayout.values()) {
            var machine = fixture(helper, owner, layout, BASE);
            ItemStack cash = named(Items.EMERALD, 31, "Collected payment"), prize = named(Items.DIAMOND, 37, "Expanded stock");
            machine.operatorInventory().setItem(10, cash.copy());
            for (int display = 0; display < layout.rewardCount() - 1; display++) machine.operatorInventory().setItem(layout.rewardSlot(display), new ItemStack(Items.COBBLESTONE, 64));
            helper.assertTrue(ClawMachineMenu.openOperator(owner, machine, false), "Owner could not open expanded operator menu");
            var menu = (ClawMachineMenu) owner.containerMenu;
            helper.assertTrue(menu.layout() == layout && menu.slots.size() == layout.inventorySize() + 36, "Server operator menu has wrong slot count");
            owner.getInventory().setItem(9, prize.copy());
            helper.assertTrue(!menu.quickMoveStack(owner, layout.inventorySize()).isEmpty(), "Shift insertion into appended prize column failed");
            helper.assertTrue(owner.getInventory().getItem(9).isEmpty()
                && ItemStack.matches(machine.operatorInventory().getItem(layout.rewardSlot(layout.rewardCount() - 1)), prize)
                && ItemStack.matches(machine.operatorInventory().getItem(10), cash), "Shift insertion altered price/cash or split a whole prize");
            helper.assertTrue(!menu.quickMoveStack(owner, layout.rewardCount()).isEmpty()
                && machine.operatorInventory().getItem(layout.rewardSlot(layout.rewardCount() - 1)).isEmpty()
                && ArcadeOrderCatalog.count(owner, Items.DIAMOND) == 37, "Shift retrieval lost or duplicated appended prize");
            RegistryFriendlyByteBuf buffer = new RegistryFriendlyByteBuf(Unpooled.buffer(), helper.getLevel().registryAccess());
            try {
                buffer.writeBlockPos(machine.getBlockPos()); buffer.writeBoolean(true); buffer.writeBoolean(true);
                buffer.writeUUID(new UUID(0, 0)); buffer.writeEnum(layout);
                var decoded = new ClawMachineMenu(55, owner.getInventory(), buffer);
                helper.assertTrue(buffer.readableBytes() == 0 && decoded.layout() == layout && decoded.slots.size() == menu.slots.size(), "Client menu payload lost layout or slot synchronization");
                for (int index = 0; index < menu.slots.size(); index++) helper.assertTrue(decoded.getSlot(index).getContainerSlot() == menu.getSlot(index).getContainerSlot(), "Client physical slot order differs from server");
            } finally { buffer.release(); }
            owner.closeContainer();
            helper.getLevel().destroyBlock(helper.absolutePos(BASE), false);
            clearDrops(helper);
        }
        helper.succeed();
    }

    @GameTest(template = "nostalgia_test")
    public static void bothExpandedGridsCanAimPayReloadAndWinFromTheirNewLastColumn(GameTestHelper helper) {
        AtomicInteger finished = new AtomicInteger();
        for (var layout : ClawMachineLayout.values()) {
            // Keep both approach paths inside the cleared test volume, away from its external marker blocks.
            BlockPos anchor = layout == ClawMachineLayout.COMPACT ? new BlockPos(1, 1, 3) : new BlockPos(4, 1, 3);
            ServerPlayer owner = createPlayer(helper, "ClawGrid" + layout.ordinal(), GameType.SURVIVAL);
            var machine = fixture(helper, owner, layout, anchor);
            helper.assertTrue(machine.setPassword(owner, "1234") && machine.acquireOperator(owner)
                && machine.setWinSettings(owner, 100, 0), "Could not configure expanded-grid game");
            machine.operatorInventory().setItem(0, named(Items.EMERALD, 3, "Token"));
            int display = layout.columns() * 2 - 1;
            ItemStack prize = named(Items.DIAMOND, 37, "Appended " + layout);
            machine.operatorInventory().setItem(layout.rewardSlot(display), prize.copy());
            machine.releaseOperator(owner);
            owner.getInventory().setItem(0, named(Items.EMERALD, 12, "Token"));
            HitResult hit = owner.pick(owner.blockInteractionRange(), 1, false);
            helper.assertTrue(hit instanceof BlockHitResult blockHit && hit.getType() == HitResult.Type.BLOCK
                && ClawMachineBlock.machineAt(helper.getLevel(), blockHit.getBlockPos()) == machine,
                "Expanded-grid player is not looking at the " + layout + " fixture: " + hit);
            helper.assertTrue(ClawMachineMenu.openPlay(owner, machine), "Could not open " + layout + " expanded-grid play session");
            helper.assertTrue(((ClawMachineMenu) owner.containerMenu).slots.size() == 1, "Play menu exposed operator stock or collected cash");
            UUID session = machine.getSessionId();
            for (int step = 1; step <= 5; step++) {
                int sequence = step;
                helper.runAfterDelay(step, () -> helper.assertTrue(machine.handleAction(owner, session, sequence, 1), "Real right movement failed"));
            }
            helper.runAfterDelay(6, () -> {
                helper.assertTrue(machine.getSelectedSlot() == display && machine.drop(owner), "New final column could not be selected and purchased");
                helper.assertFalse(machine.drop(owner), "Duplicate drop charged a second play");
                helper.assertTrue(owner.getInventory().getItem(0).getCount() == 9 && machine.operatorInventory().getItem(10).getCount() == 3,
                    "Expanded-column payment took wrong currency count");
                var tag = machine.getUpdateTag(helper.getLevel().registryAccess());
                for (String secret : List.of("Items", "PasswordHash", "PasswordSalt", "Owner", "Buyer", "PlannedWin", "SourceSlot", "SlipSlot")) helper.assertFalse(tag.contains(secret), "Public grid update leaked " + secret);
                var restored = load(helper, machine, machine.saveWithFullMetadata(helper.getLevel().registryAccess()));
                ClawMachineTransactionGameTests.ticks(restored, 150);
                int returned = helper.getEntities(EntityType.ITEM, anchor, 5).stream()
                    .filter(drop -> ItemStack.isSameItemSameComponents(drop.getItem(), prize)).mapToInt(drop -> drop.getItem().getCount()).sum();
                helper.assertTrue(restored.getPhase() == ClawMachineBlockEntity.Phase.IDLE && returned == 37
                    && restored.operatorInventory().getItem(layout.rewardSlot(display)).isEmpty()
                    && restored.operatorInventory().getItem(10).getCount() == 3, "Reloading appended prize lost/duplicated stock or payment");
                owner.closeContainer();
                if (finished.incrementAndGet() == ClawMachineLayout.values().length) helper.succeed();
            });
        }
    }
}
