package local.japanesearcades;

import static local.japanesearcades.GachaponTransactionGameTests.BASE;
import static local.japanesearcades.GachaponTransactionGameTests.crankTicks;
import static local.japanesearcades.GachaponTransactionGameTests.createPlayer;

import com.mojang.logging.LogUtils;
import io.netty.buffer.Unpooled;
import net.minecraft.core.component.DataComponents;
import net.minecraft.gametest.framework.GameTest;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.RegistryFriendlyByteBuf;
import net.minecraft.network.chat.Component;
import net.minecraft.network.protocol.game.ClientboundBlockEntityDataPacket;
import net.minecraft.world.Container;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.GameType;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.neoforged.neoforge.gametest.GameTestHolder;
import net.neoforged.neoforge.gametest.PrefixGameTestTemplate;

/** Exercise the actual packet codec and receiving handler, including snapshot/delta ordering. */
@GameTestHolder(JapaneseArcades.MOD_ID)
@PrefixGameTestTemplate(false)
public final class MachineDisplaySyncGameTests {
    @GameTest(template = "nostalgia_test")
    public static void gachaponPosePacketsPreserveDisplaysAndStockChangesSendFullSnapshots(GameTestHelper helper) {
        var player = createPlayer(helper, "GachaSync", GameType.SURVIVAL);
        var machine = GachaponTransactionGameTests.configure(helper, BASE, player);
        fillPreviews(machine.operatorInventory());
        player.getInventory().setItem(0, new ItemStack(Items.EMERALD, 20));
        helper.assertTrue(machine.startCrank(player), "Sync fixture could not start its crank");
        var receiver = new GachaponBlockEntity(machine.getBlockPos(), machine.getBlockState());
        var full = capture(helper, machine);
        receive(helper, receiver, full);
        assertDisplays(helper, receiver, full.tag());

        crankTicks(machine, player, 2);
        var pose = capture(helper, machine);
        assertCompact(helper, "gachapon", full, pose);
        receive(helper, receiver, pose);
        helper.assertTrue(receiver.getCrankTicks() == 2 && receiver.isCranking(), "Crank pose did not advance through its wire packet");
        assertDisplays(helper, receiver, full.tag());
        assertFreshSnapshot(helper, machine);

        machine.operatorInventory().setItem(2, new ItemStack(Items.GOLD_INGOT, 4));
        var changed = capture(helper, machine);
        helper.assertFalse(changed.tag().getBoolean("AnimationOnly"), "Mid-crank stock edit emitted only a pose");
        receive(helper, receiver, changed);
        assertDisplays(helper, receiver, changed.tag());
        helper.assertTrue(receiver.getCrankTicks() == 0 && !receiver.isCranking(), "Stock edit did not reset the client's invalidated crank");

        machine.operatorInventory().clearContent();
        var empty = capture(helper, machine);
        helper.assertFalse(empty.tag().getBoolean("AnimationOnly"), "Empty stock did not send a replacement snapshot");
        receive(helper, receiver, empty);
        assertDisplays(helper, receiver, empty.tag());
        helper.assertTrue(((ItemStack)clientField(receiver, "publicPrice")).isEmpty(), "Absent price retained its stale display");
        helper.succeed();
    }

    @GameTest(template = "nostalgia_test")
    public static void clawPosePacketsPreserveHeldItemsAcrossPhasesEditsAndReload(GameTestHelper helper) {
        var player = createPlayer(helper, "ClawSync", GameType.SURVIVAL);
        var machine = ClawMachineTransactionGameTests.configure(helper, player, 100, 0);
        fillPreviews(machine.operatorInventory());
        helper.assertTrue(machine.startSession(player), "Sync fixture could not start claw controls");
        var receiver = new ClawMachineBlockEntity(machine.getBlockPos(), machine.getBlockState());
        var aiming = capture(helper, machine);
        receive(helper, receiver, aiming);
        helper.assertTrue(machine.handleAction(player, machine.getSessionId(), 0, 0), "Claw movement was refused");
        var movement = capture(helper, machine);
        assertCompact(helper, "claw aiming", aiming, movement);
        receive(helper, receiver, movement);
        helper.assertTrue((Float)clientField(receiver, "publicX") > aiming.tag().getFloat("X"), "Movement packet did not update the client pose");
        assertDisplays(helper, receiver, aiming.tag());

        helper.assertTrue(machine.drop(player), "Sync fixture could not pay for its claw drop");
        var descending = capture(helper, machine);
        helper.assertFalse(descending.tag().getBoolean("AnimationOnly"), "Paid phase transition omitted its public snapshot");
        receive(helper, receiver, descending);
        ClawMachineTransactionGameTests.ticks(machine, 2);
        var pose = capture(helper, machine);
        assertCompact(helper, "claw descending", descending, pose);
        receive(helper, receiver, pose);
        assertDisplays(helper, receiver, descending.tag());
        assertFreshSnapshot(helper, machine);

        ClawMachineTransactionGameTests.ticks(machine, 28);
        var grabbing = capture(helper, machine);
        helper.assertTrue(!grabbing.tag().getBoolean("AnimationOnly") && grabbing.tag().contains("Held")
            && !grabbing.tag().contains("Preview4"), "Grab transition did not move the selected preview into the held display");
        receive(helper, receiver, grabbing);
        ClawMachineTransactionGameTests.ticks(machine, 2);
        receive(helper, receiver, capture(helper, machine));
        assertDisplays(helper, receiver, grabbing.tag());

        machine.operatorInventory().setItem(1, new ItemStack(Items.GOLD_INGOT, 6));
        var edited = capture(helper, machine);
        helper.assertFalse(edited.tag().getBoolean("AnimationOnly"), "Paid-animation stock edit did not send item changes");
        receive(helper, receiver, edited);
        assertDisplays(helper, receiver, edited.tag());
        assertFreshSnapshot(helper, machine);

        ClawMachineTransactionGameTests.ticks(machine, 150);
        var finished = capture(helper, machine);
        helper.assertTrue(!finished.tag().getBoolean("AnimationOnly") && !finished.tag().contains("Held"), "Payout did not clear the held display");
        receive(helper, receiver, finished);
        assertDisplays(helper, receiver, finished.tag());
        machine.operatorInventory().clearContent();
        var empty = capture(helper, machine);
        receive(helper, receiver, empty);
        assertDisplays(helper, receiver, empty.tag());
        helper.succeed();
    }

    private static void fillPreviews(Container inventory) {
        for (int slot = 1; slot <= 9; slot++) {
            ItemStack item = new ItemStack(Items.DIAMOND, 17);
            item.set(DataComponents.CUSTOM_NAME, Component.literal("Arcade showcase reward " + slot));
            inventory.setItem(slot, item);
        }
    }

    private static WirePacket capture(GameTestHelper helper, BlockEntity machine) {
        var buffer = new RegistryFriendlyByteBuf(Unpooled.buffer(), helper.getLevel().registryAccess());
        try {
            var packet = machine.getUpdatePacket();
            helper.assertTrue(packet instanceof ClientboundBlockEntityDataPacket, "Machine did not provide a block entity data packet");
            ClientboundBlockEntityDataPacket.STREAM_CODEC.encode(buffer, (ClientboundBlockEntityDataPacket)packet);
            int bytes = buffer.readableBytes();
            var decoded = ClientboundBlockEntityDataPacket.STREAM_CODEC.decode(buffer);
            helper.assertTrue(buffer.readableBytes() == 0 && decoded.getPos().equals(machine.getBlockPos())
                && decoded.getType() == machine.getType(), "Block entity packet codec lost its identity or left trailing data");
            assertPrivateStateAbsent(helper, decoded.getTag());
            return new WirePacket(decoded.getTag(), bytes);
        } finally { buffer.release(); }
    }

    private static void assertCompact(GameTestHelper helper, String label, WirePacket full, WirePacket pose) {
        helper.assertFalse(full.tag().getBoolean("AnimationOnly"), label + " initial packet was not a full snapshot");
        helper.assertTrue(pose.tag().getBoolean("AnimationOnly") && pose.bytes() * 2 < full.bytes(),
            label + " did not cut recurring packet bytes by at least half: " + full.bytes() + " -> " + pose.bytes());
        helper.assertFalse(pose.tag().contains("Price") || pose.tag().contains("Held"), label + " pose redundantly serialized display items");
        for (int slot = 0; slot < 9; slot++) { helper.assertFalse(pose.tag().contains("Preview" + slot), label + " pose included preview items"); }
        LogUtils.getLogger().info("Machine sync wire check: {} full={} bytes, pose={} bytes", label, full.bytes(), pose.bytes());
    }

    private static void assertFreshSnapshot(GameTestHelper helper, BlockEntity machine) {
        var registry = helper.getLevel().registryAccess();
        var snapshot = machine.getUpdateTag(registry);
        helper.assertTrue(!snapshot.getBoolean("AnimationOnly") && snapshot.contains("Price") && snapshot.contains("Preview0"),
            "Chunk/late-viewer snapshot was consumed by prior animation packets");
        var receiver = machine.getType().create(machine.getBlockPos(), machine.getBlockState());
        receiver.handleUpdateTag(snapshot, registry);
        assertDisplays(helper, receiver, snapshot);
        var reloaded = BlockEntity.loadStatic(machine.getBlockPos(), machine.getBlockState(), machine.saveWithFullMetadata(registry), registry);
        helper.assertTrue(reloaded != null, "Sync fixture failed persistence round trip");
        reloaded.setLevel(helper.getLevel());
        var packet = capture(helper, reloaded);
        helper.assertTrue(!packet.tag().getBoolean("AnimationOnly") && packet.tag().contains("Price"), "Reload started with a delta before its display snapshot");
    }

    private static void receive(GameTestHelper helper, BlockEntity receiver, WirePacket packet) {
        receiver.handleUpdateTag(packet.tag(), helper.getLevel().registryAccess());
    }

    private static void assertDisplays(GameTestHelper helper, BlockEntity receiver, CompoundTag expected) {
        helper.assertTrue(ItemStack.matches((ItemStack)clientField(receiver, "publicPrice"), item(helper, expected, "Price")), "Price changed or lost components during client merge");
        var rewards = (ItemStack[])clientField(receiver, "publicRewards");
        for (int slot = 0; slot < 9; slot++) {
            helper.assertTrue(ItemStack.matches(rewards[slot], item(helper, expected, "Preview" + slot)), "Client preview changed or failed to clear: " + slot);
        }
        if (receiver instanceof ClawMachineBlockEntity) {
            helper.assertTrue(ItemStack.matches((ItemStack)clientField(receiver, "publicHeld"), item(helper, expected, "Held")), "Held display changed or failed to clear");
        }
    }

    private static ItemStack item(GameTestHelper helper, CompoundTag tag, String key) {
        return tag.contains(key) ? ItemStack.parse(helper.getLevel().registryAccess(), tag.getCompound(key)).orElseThrow() : ItemStack.EMPTY;
    }

    private static Object clientField(BlockEntity receiver, String name) {
        // Inspect only the receiving cache: a dedicated-server GameTest must not load ClientLevel.
        try {
            var field = receiver.getClass().getDeclaredField(name);
            field.setAccessible(true);
            return field.get(receiver);
        } catch (ReflectiveOperationException exception) { throw new AssertionError("Cannot inspect receiving cache " + name, exception); }
    }

    private static void assertPrivateStateAbsent(GameTestHelper helper, CompoundTag tag) {
        for (String key : new String[]{"Owner", "PasswordSalt", "PasswordHash", "Items", "PlannedWin", "Buyer", "BaseWinChance", "GuaranteePlay"}) {
            helper.assertFalse(tag.contains(key), "Public sync leaked private state: " + key);
        }
    }

    private record WirePacket(CompoundTag tag, int bytes) {}
}
