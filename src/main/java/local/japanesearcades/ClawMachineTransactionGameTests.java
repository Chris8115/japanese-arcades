package local.japanesearcades;

import static local.japanesearcades.GachaponTransactionGameTests.aimAt;
import static local.japanesearcades.GachaponTransactionGameTests.createPlayer;

import java.util.HashSet;
import java.util.Set;
import java.util.UUID;
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.function.Consumer;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.component.DataComponents;
import net.minecraft.gametest.framework.GameTest;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.item.ItemEntity;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.GameType;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;
import net.neoforged.neoforge.common.NeoForge;
import net.neoforged.neoforge.event.entity.EntityJoinLevelEvent;
import net.neoforged.neoforge.gametest.GameTestHolder;
import net.neoforged.neoforge.gametest.PrefixGameTestTemplate;

@GameTestHolder(JapaneseArcades.MOD_ID)
@PrefixGameTestTemplate(false)
public final class ClawMachineTransactionGameTests {
    private static final BlockPos BASE = new BlockPos(3, 1, 3);
    private static ItemStack price(int count) {
        ItemStack item = new ItemStack(Items.EMERALD, count);
        item.set(DataComponents.CUSTOM_NAME, Component.literal("Claw token"));
        return item;
    }
    private static ItemStack prize(int count) {
        ItemStack item = new ItemStack(Items.DIAMOND, count);
        item.set(DataComponents.CUSTOM_NAME, Component.literal("Whole crane prize"));
        return item;
    }
    private static ClawMachineBlockEntity configure(GameTestHelper helper, ServerPlayer owner, int chance, int guarantee) {
        return configure(helper, owner, chance, guarantee, Direction.NORTH);
    }
    private static ClawMachineBlockEntity configure(GameTestHelper helper, ServerPlayer owner, int chance, int guarantee, Direction facing) {
        var block = JapaneseArcades.CLAW_MACHINE.get();
        var state = block.defaultBlockState().setValue(ClawMachineBlock.FACING, facing);
        for (int part = 0; part < 6; part++) { helper.setBlock(ClawMachineBlock.partPosition(BASE, facing, part).below(), Blocks.STONE); }
        for (int part = 0; part < 18; part++) {
            helper.getLevel().setBlock(helper.absolutePos(ClawMachineBlock.partPosition(BASE, facing, part)), state.setValue(ClawMachineBlock.PART, part), 18);
        }
        var machine = (ClawMachineBlockEntity)helper.getBlockEntity(BASE);
        Vec3 center = Vec3.atCenterOf(machine.getBlockPos());
        owner.setPos(center.add(facing.getStepX() * 2, -.5, facing.getStepZ() * 2));
        Vec3 ray = center.subtract(owner.getEyePosition());
        owner.setYRot((float)Math.toDegrees(Math.atan2(-ray.x, ray.z)));
        owner.setYHeadRot(owner.getYRot());
        owner.setXRot((float)-Math.toDegrees(Math.atan2(ray.y, Math.sqrt(ray.x * ray.x + ray.z * ray.z))));
        machine.assignOwner(owner);
        helper.assertTrue(machine.setPassword(owner, "1234"), "Could not configure operator PIN");
        helper.assertTrue(machine.acquireOperator(owner) && machine.setWinSettings(owner, chance, guarantee), "Could not configure win odds");
        machine.operatorInventory().setItem(0, price(3));
        machine.operatorInventory().setItem(5, prize(17));
        machine.releaseOperator(owner);
        owner.getInventory().clearContent(); owner.getInventory().setItem(0, price(12));
        return machine;
    }
    private static void ticks(ClawMachineBlockEntity machine, int ticks) {
        for (int tick = 0; tick < ticks; tick++) {
            ClawMachineBlockEntity.serverTick(machine.getLevel(), machine.getBlockPos(), machine.getBlockState(), machine);
        }
    }
    private static int paid(ClawMachineBlockEntity machine) {
        int result = 0;
        for (int slot = 10; slot < 19; slot++) { result += machine.operatorInventory().getItem(slot).getCount(); }
        return result;
    }
    private static int stock(ClawMachineBlockEntity machine) {
        int result = 0;
        for (int slot = 1; slot < 10; slot++) { result += machine.operatorInventory().getItem(slot).getCount(); }
        return result;
    }
    private static int drops(GameTestHelper helper, Item item) {
        return helper.getEntities(EntityType.ITEM, BASE, 5).stream().filter(value -> value.getItem().is(item)).mapToInt(value -> value.getItem().getCount()).sum();
    }
    private static ClawMachineBlockEntity reload(GameTestHelper helper, ClawMachineBlockEntity original) {
        var registry = helper.getLevel().registryAccess();
        var restored = (ClawMachineBlockEntity)BlockEntity.loadStatic(original.getBlockPos(), original.getBlockState(), original.saveWithFullMetadata(registry), registry);
        helper.assertTrue(restored != null, "Saved claw machine failed to load");
        helper.getLevel().setBlockEntity(restored);
        return restored;
    }
    private static boolean prizeSpawn(GameTestHelper helper, EntityJoinLevelEvent event) {
        return event.getEntity() instanceof ItemEntity item && item.getItem().is(Items.DIAMOND)
            && item.position().distanceToSqr(helper.absolutePos(BASE).getCenter()) < 25;
    }

    @GameTest(template = "nostalgia_test")
    public static void clawExclusiveControlsFreeExitAndPaidEscapePreserveExactlyOneWholePrize(GameTestHelper helper) {
        ServerPlayer owner = createPlayer(helper, "ClawControl", GameType.SURVIVAL);
        ServerPlayer visitor = createPlayer(helper, "ClawOther", GameType.SURVIVAL);
        var machine = configure(helper, owner, 100, 0);
        aimAt(visitor, machine.getBlockPos());
        helper.assertTrue(ClawMachineMenu.openPlay(owner, machine), "Valid player could not open claw controls");
        var menu = (ClawMachineMenu)owner.containerMenu;
        UUID first = machine.getSessionId();
        helper.assertFalse(machine.startSession(visitor), "Two players acquired the same claw");
        helper.assertFalse(machine.handleAction(visitor, first, 0, 4), "Another controller could charge a drop");
        helper.assertTrue(machine.handleAction(owner, first, 0, 0) && machine.getClawX() > .5F, "Left control must move toward viewer-left/high X");
        float x = machine.getClawX();
        helper.assertFalse(machine.handleAction(owner, first, 0, 1), "Repeated action sequence was accepted");
        helper.assertFalse(machine.handleAction(owner, first, 1, 1), "Packet spam moved more than once in a tick");
        helper.assertTrue(machine.getClawX() == x, "Rejected movement changed the claw");
        ClawMachineNetwork.handleAction(owner, new ClawMachineNetwork.ActionPayload(menu.containerId + 1, machine.getBlockPos(), first, 2, ClawMachineNetwork.Action.DROP));
        helper.assertTrue(paid(machine) == 0, "An incorrect menu identifier charged a play");
        owner.closeContainer();
        helper.assertTrue(machine.getPhase() == ClawMachineBlockEntity.Phase.IDLE && owner.getInventory().getItem(0).getCount() == 12 && paid(machine) == 0,
            "Leaving before Drop charged currency");
        helper.assertTrue(ClawMachineMenu.openPlay(owner, machine), "A free exit left the machine reserved");
        helper.assertFalse(first.equals(machine.getSessionId()) || machine.handleAction(owner, first, 3, 4), "Old session nonce remained valid");
        helper.assertTrue(machine.handleAction(owner, machine.getSessionId(), 0, 4), "Valid Drop failed");
        helper.assertFalse(machine.drop(owner) || machine.acquireOperator(owner), "Paid play allowed a second charge or operator access");
        owner.closeContainer();
        owner.setPos(owner.getX() + 20, owner.getY(), owner.getZ());
        ticks(machine, 150);
        helper.assertTrue(machine.getPhase() == ClawMachineBlockEntity.Phase.IDLE && paid(machine) == 3
            && owner.getInventory().getItem(0).getCount() == 9 && stock(machine) == 0 && drops(helper, Items.DIAMOND) == 17,
            "Paid escape lost a prize, duplicated it, or charged incorrectly");
        helper.assertTrue(ArcadeOrderCatalog.count(owner, Items.DIAMOND) == 0, "Prize teleported to player inventory instead of the chute");
        var item = helper.getEntities(EntityType.ITEM, BASE, 5).stream().filter(value -> value.getItem().is(Items.DIAMOND)).findFirst().orElseThrow().getItem();
        helper.assertTrue(ItemStack.matches(item, prize(17)), "Full-stack payout lost exact item components");
        assertPayoutClearsCabinet(helper, Direction.NORTH);
        for (Direction facing : new Direction[]{Direction.EAST, Direction.SOUTH, Direction.WEST}) {
            helper.getLevel().destroyBlock(helper.absolutePos(BASE), false);
            helper.getEntities(EntityType.ITEM, BASE, 5).forEach(ItemEntity::discard);
            machine = configure(helper, owner, 100, 0, facing);
            helper.assertTrue(machine.startSession(owner) && machine.drop(owner), "Rotated payout failed to start: " + facing);
            ticks(machine, 150);
            assertPayoutClearsCabinet(helper, facing);
        }
        helper.succeed();
    }

    private static void assertPayoutClearsCabinet(GameTestHelper helper, Direction facing) {
        var prize = helper.getEntities(EntityType.ITEM, BASE, 5).stream().filter(value -> value.getItem().is(Items.DIAMOND)).findFirst().orElseThrow();
        for (int part = 0; part < 18; part++) {
            BlockPos cell = helper.absolutePos(ClawMachineBlock.partPosition(BASE, facing, part));
            helper.assertFalse(prize.getBoundingBox().intersects(new AABB(cell)),
                "Payout overlaps cabinet part " + part + " facing " + facing + " and could be pushed into the glass");
        }
        helper.assertTrue(ItemStack.matches(prize.getItem(), prize(17)), "Rotated payout changed the prize stack");
    }

    @GameTest(template = "nostalgia_test")
    public static void clawEmptyTargetWrongComponentsAndFullCashboxNeverCharge(GameTestHelper helper) {
        ServerPlayer owner = createPlayer(helper, "ClawPayment", GameType.SURVIVAL);
        var machine = configure(helper, owner, 0, 0);
        machine.operatorInventory().setItem(1, machine.operatorInventory().removeItemNoUpdate(5));
        helper.assertTrue(machine.startSession(owner) && !machine.drop(owner), "Empty target should reject Drop without charge");
        helper.assertTrue(paid(machine) == 0 && owner.getInventory().getItem(0).getCount() == 12, "Empty target charged currency");
        machine.operatorInventory().setItem(5, machine.operatorInventory().removeItemNoUpdate(1));
        helper.assertTrue(machine.startSession(owner), "Stock edit did not invalidate previous aim");
        owner.getInventory().setItem(0, new ItemStack(Items.EMERALD, 64));
        helper.assertFalse(machine.drop(owner), "Currency with the wrong components was accepted");
        owner.getInventory().setItem(0, price(12));
        for (int slot = 10; slot < 19; slot++) { machine.operatorInventory().setItem(slot, price(64)); }
        helper.assertTrue(machine.startSession(owner) && !machine.drop(owner), "Full payment storage accepted a paid play");
        helper.assertTrue(owner.getInventory().getItem(0).getCount() == 12 && stock(machine) == 17 && paid(machine) == 576,
            "Rejected payment lost player currency or stock");
        machine.operatorInventory().setItem(10, ItemStack.EMPTY);
        helper.assertTrue(machine.startSession(owner) && machine.drop(owner), "Free cashbox space did not restore payment");
        ticks(machine, 180);
        helper.assertTrue(owner.getInventory().getItem(0).getCount() == 9 && paid(machine) == 515 && stock(machine) == 17
            && drops(helper, Items.DIAMOND) == 0, "Failed claw should retain the entire prize and exactly one payment");
        helper.succeed();
    }

    @GameTest(template = "nostalgia_test")
    public static void clawLossRelocatesWholeStackAndGuaranteeResetsOnlyAfterAWin(GameTestHelper helper) {
        ServerPlayer owner = createPlayer(helper, "ClawRamp", GameType.SURVIVAL);
        var machine = configure(helper, owner, 0, 2);
        helper.assertTrue(machine.getCurrentWinChance() == 0 && machine.startSession(owner) && machine.drop(owner), "First guaranteed-loss play did not start");
        ticks(machine, 180);
        helper.assertTrue(stock(machine) == 17 && machine.operatorInventory().getItem(5).isEmpty()
            && drops(helper, Items.DIAMOND) == 0 && machine.getPlaysSinceWin() == 1 && machine.getCurrentWinChance() == 100,
            "Loss did not relocate the stack or advance to the guaranteed second play");
        for (int slot = 1; slot < 10; slot++) {
            if (!machine.operatorInventory().getItem(slot).isEmpty()) {
                helper.assertTrue(ItemStack.matches(machine.operatorInventory().getItem(slot), prize(17)), "Slipping changed the prize contents");
                machine.operatorInventory().setItem(5, machine.operatorInventory().removeItemNoUpdate(slot));
                break;
            }
        }
        helper.assertTrue(machine.startSession(owner) && machine.drop(owner), "Guaranteed second play failed to start");
        helper.assertTrue(machine.getPlaysSinceWin() == 2, "Counter reset before delivery");
        ticks(machine, 150);
        helper.assertTrue(drops(helper, Items.DIAMOND) == 17 && paid(machine) == 6 && stock(machine) == 0
            && machine.getPlaysSinceWin() == 0 && machine.getCurrentWinChance() == 0, "Guaranteed win did not reset the progression exactly once");
        helper.succeed();
    }

    @GameTest(template = "nostalgia_test")
    public static void clawEveryPaidPhaseSurvivesReloadWithoutExposingPrivateState(GameTestHelper helper) {
        ServerPlayer owner = createPlayer(helper, "ClawSave", GameType.SURVIVAL);
        for (int chance : new int[]{0, 100}) {
            var machine = configure(helper, owner, chance, 0);
            helper.assertTrue(machine.startSession(owner), "Could not start unpaid save test");
            machine = reload(helper, machine);
            helper.assertTrue(machine.getPhase() == ClawMachineBlockEntity.Phase.IDLE && paid(machine) == 0,
                "Reload retained an unpaid reservation or took currency");
            helper.assertTrue(machine.authenticate(owner, "1234") == 0 && machine.startSession(owner) && machine.drop(owner), "Saved credentials or gameplay stopped working");
            Set<String> seen = new HashSet<>();
            for (int tick = 0; tick < 180 && machine.isPaid(); tick++) {
                String state = machine.getPhase().name() + ":" + machine.getHeldDisplay().isEmpty();
                if (seen.add(state)) {
                    var publicTag = machine.getUpdateTag(helper.getLevel().registryAccess());
                    helper.assertFalse(publicTag.contains("Owner") || publicTag.contains("PasswordSalt") || publicTag.contains("PasswordHash")
                        || publicTag.contains("Items") || publicTag.contains("PlannedWin") || publicTag.contains("BaseWinChance")
                        || publicTag.contains("GuaranteePlay") || publicTag.contains("Buyer"), "Public pose packet leaked private machine state");
                    var phase = machine.getPhase(); int elapsed = machine.getPhaseTicks();
                    machine = reload(helper, machine);
                    helper.assertTrue(machine.getPhase() == phase && machine.getPhaseTicks() == elapsed && paid(machine) == 3,
                        "Reload reset a paid phase or changed collected payment");
                }
                ticks(machine, 1);
            }
            helper.assertTrue(machine.getPhase() == ClawMachineBlockEntity.Phase.IDLE && paid(machine) == 3
                && stock(machine) == (chance == 0 ? 17 : 0) && drops(helper, Items.DIAMOND) == (chance == 100 ? 17 : 0),
                "Reloading animation lost or duplicated the committed prize");
            helper.getLevel().destroyBlock(helper.absolutePos(BASE), false);
            helper.getEntities(EntityType.ITEM, BASE, 5).forEach(ItemEntity::discard);
        }
        helper.succeed();
    }

    @GameTest(template = "nostalgia_test")
    public static void clawRejectedOrAlteredDeliveryRetainsPrizeAndBrokenStockSurvivesRecoverySave(GameTestHelper helper) {
        ServerPlayer owner = createPlayer(helper, "ClawVeto", GameType.SURVIVAL);
        var machine = configure(helper, owner, 100, 0);
        helper.assertTrue(machine.startSession(owner) && machine.drop(owner), "Paid veto test did not start");
        AtomicInteger mode = new AtomicInteger();
        Consumer<EntityJoinLevelEvent> veto = event -> {
            if (!prizeSpawn(helper, event)) { return; }
            if (mode.get() == 0) event.setCanceled(true);
            else if (mode.get() == 1) event.getEntity().discard();
            else ((ItemEntity)event.getEntity()).setItem(new ItemStack(Items.DIRT));
        };
        NeoForge.EVENT_BUS.addListener(veto);
        try {
            for (int index = 0; index < 3; index++) {
                mode.set(index); ticks(machine, 150);
                helper.assertTrue(machine.getPhase() == ClawMachineBlockEntity.Phase.DELIVERING
                    && ItemStack.matches(machine.getHeldDisplay(), prize(17)) && machine.getPlaysSinceWin() == 1
                    && paid(machine) == 3 && drops(helper, Items.DIAMOND) == 0, "Rejected delivery lost stock or reset the win counter");
                machine = reload(helper, machine);
            }
            mode.set(0);
            helper.getLevel().destroyBlock(helper.absolutePos(BASE), false);
            helper.assertTrue(drops(helper, Items.DIAMOND) == 0, "Vetoed broken-machine return escaped the recovery queue");
            var registry = helper.getLevel().registryAccess();
            var saved = ClawMachineRecovery.get(helper.getLevel()).save(new CompoundTag(), registry);
            helper.getLevel().getDataStorage().set(ClawMachineRecovery.NAME, ClawMachineRecovery.load(saved, registry));
        } finally { NeoForge.EVENT_BUS.unregister(veto); }
        ClawMachineRecovery.retry(helper.getLevel()); ClawMachineRecovery.retry(helper.getLevel());
        helper.assertTrue(drops(helper, Items.DIAMOND) == 17 && drops(helper, Items.DIRT) == 0,
            "Saved recovery did not return the original full stack exactly once");
        helper.succeed();
    }

    @GameTest(template = "nostalgia_test")
    public static void clawDeliveryCallbackCannotDuplicateByBreakingOrReenteringTheMachine(GameTestHelper helper) {
        ServerPlayer owner = createPlayer(helper, "ClawReentry", GameType.SURVIVAL);
        var machine = configure(helper, owner, 100, 0);
        machine.operatorInventory().setItem(1, new ItemStack(Items.GOLD_INGOT, 23));
        helper.assertTrue(machine.startSession(owner) && machine.drop(owner), "Paid reentry test did not start");
        AtomicBoolean ran = new AtomicBoolean();
        Consumer<EntityJoinLevelEvent> callback = event -> {
            if (prizeSpawn(helper, event) && ran.compareAndSet(false, true)) {
                helper.assertFalse(machine.drop(owner) || machine.startSession(owner), "Delivery callback reentered payment");
                helper.getLevel().destroyBlock(helper.absolutePos(BASE), false);
                machine.dropInventory();
            }
        };
        NeoForge.EVENT_BUS.addListener(callback);
        try { ticks(machine, 150); }
        finally { NeoForge.EVENT_BUS.unregister(callback); }
        ClawMachineRecovery.retry(helper.getLevel());
        helper.assertTrue(ran.get() && drops(helper, Items.DIAMOND) == 17 && drops(helper, Items.GOLD_INGOT) == 23
            && drops(helper, Items.EMERALD) == 6 && owner.getInventory().getItem(0).getCount() == 9,
            "Reentrant removal lost/duplicated held stock, stored prizes, payment or the price template");
        helper.succeed();
    }
}
