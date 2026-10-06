package local.funpack.custom;

import com.mojang.authlib.GameProfile;
import io.netty.channel.embedded.EmbeddedChannel;
import java.util.List;
import java.util.ArrayList;
import java.util.UUID;
import java.util.function.Consumer;
import net.minecraft.core.BlockPos;
import net.minecraft.core.component.DataComponents;
import net.minecraft.gametest.framework.GameTest;
import net.minecraft.gametest.framework.AfterBatch;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.network.Connection;
import net.minecraft.network.chat.Component;
import net.minecraft.network.protocol.PacketFlow;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ClientInformation;
import net.minecraft.server.network.CommonListenerCookie;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.item.ItemEntity;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.item.component.ItemContainerContents;
import net.minecraft.world.level.GameType;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.phys.Vec3;
import net.neoforged.neoforge.common.NeoForge;
import net.neoforged.neoforge.event.entity.EntityJoinLevelEvent;
import net.neoforged.neoforge.gametest.GameTestHolder;
import net.neoforged.neoforge.gametest.PrefixGameTestTemplate;
import net.neoforged.neoforge.network.connection.ConnectionType;
import net.neoforged.neoforge.network.registration.NetworkRegistry;

/** Real server transactions: exact components, payment rollback, crank reservation, and delayed reset. */
@GameTestHolder(FunPackCustom.MOD_ID)
@PrefixGameTestTemplate(false)
public final class GachaponTransactionGameTests {
    static final BlockPos BASE = new BlockPos(3, 1, 3);
    private static final List<ServerPlayer> TEST_PLAYERS = new ArrayList<>();

    static ServerPlayer createPlayer(GameTestHelper helper, String name, GameType mode) {
        GameProfile profile = new GameProfile(UUID.randomUUID(), name.substring(0, Math.min(name.length(), 16)));
        CommonListenerCookie cookie = new CommonListenerCookie(profile, 0, ClientInformation.createDefault(), false, ConnectionType.NEOFORGE);
        ServerPlayer player = new ServerPlayer(helper.getLevel().getServer(), helper.getLevel(), profile, cookie.clientInformation());
        Connection connection = new Connection(PacketFlow.SERVERBOUND);
        new EmbeddedChannel(connection);
        NetworkRegistry.configureMockConnection(connection);
        helper.getLevel().getServer().getPlayerList().placeNewPlayer(connection, player, cookie);
        TEST_PLAYERS.add(player);
        player.setGameMode(mode);
        player.setNoGravity(true);
        player.noPhysics = true;
        player.setInvulnerable(true);
        player.getInventory().clearContent();
        aimAt(player, helper.absolutePos(BASE));
        return player;
    }

    @AfterBatch(batch = "defaultBatch")
    public static void removeFixturePlayers(ServerLevel level) {
        // Run once all tests in the batch finish, including delayed and failed
        // tests. Keep their connections real throughout the assertions above.
        for (ServerPlayer player : TEST_PLAYERS) {
            if (level.getServer().getPlayerList().getPlayer(player.getUUID()) == player) {
                player.closeContainer();
                level.getServer().getPlayerList().remove(player);
            }
            if (player.connection.getConnection().channel() instanceof EmbeddedChannel channel) { channel.finishAndReleaseAll(); }
        }
        TEST_PLAYERS.clear();
    }

    static void aimAt(ServerPlayer player, BlockPos target) {
        player.setPos(target.getX() + .5, target.getY(), target.getZ() - 2);
        Vec3 direction = Vec3.atCenterOf(target).subtract(player.getEyePosition());
        float yaw = (float)Math.toDegrees(Math.atan2(-direction.x, direction.z));
        float pitch = (float)-Math.toDegrees(Math.atan2(direction.y, Math.sqrt(direction.x * direction.x + direction.z * direction.z)));
        player.setYRot(yaw);
        player.setYHeadRot(yaw);
        player.setXRot(pitch);
        player.setDeltaMovement(Vec3.ZERO);
    }

    static GachaponBlockEntity configure(GameTestHelper helper, BlockPos pos, ServerPlayer owner) {
        if (helper.getLevel().getBlockState(helper.absolutePos(pos.below())).isAir()) { helper.setBlock(pos.below(), Blocks.STONE); }
        helper.setBlock(pos, FunPackCustom.GACHAPON.get());
        GachaponBlockEntity machine = (GachaponBlockEntity)helper.getBlockEntity(pos);
        machine.assignOwner(owner);
        machine.setPassword(owner, "1234");
        machine.operatorInventory().setItem(GachaponBlockEntity.PRICE_SLOT, new ItemStack(Items.EMERALD, 3));
        machine.operatorInventory().setItem(GachaponBlockEntity.REWARD_START, new ItemStack(Items.DIAMOND, 8));
        machine.setDispenseAmount(16);
        owner.closeContainer();
        aimAt(owner, helper.absolutePos(pos));
        return machine;
    }

    static void crankTicks(GachaponBlockEntity machine, ServerPlayer player, int ticks) {
        for (int tick = 0; tick < ticks; tick++) {
            machine.heartbeat(player, true);
            GachaponBlockEntity.serverTick(player.level(), machine.getBlockPos(), machine.getBlockState(), machine);
        }
    }

    private static List<ItemEntity> capsules(GameTestHelper helper) {
        return helper.getEntities(EntityType.ITEM, BASE, 4).stream()
            .filter(entity -> entity.getItem().is(FunPackCustom.GACHAPON_CAPSULE.get())).toList();
    }

    private static int currency(ServerPlayer player) {
        int total = 0;
        for (ItemStack item : player.getInventory().items) { if (item.is(Items.EMERALD)) { total += item.getCount(); } }
        for (ItemStack item : player.getInventory().offhand) { if (item.is(Items.EMERALD)) { total += item.getCount(); } }
        return total;
    }

    @GameTest(template = "nostalgia_test")
    public static void gachaponOneCapsuleClampsAmountAndPreservesExactItemComponents(GameTestHelper helper) {
        ServerPlayer owner = createPlayer(helper, "gacha-owner", GameType.SURVIVAL);
        GachaponBlockEntity machine = configure(helper, BASE, owner);
        ServerPlayer buyer = createPlayer(helper, "gacha-buyer", GameType.SURVIVAL);
        ItemStack token = new ItemStack(Items.EMERALD, 3);
        token.set(DataComponents.CUSTOM_NAME, Component.literal("Festival token"));
        ItemStack reward = new ItemStack(Items.DIAMOND, 8);
        reward.set(DataComponents.CUSTOM_NAME, Component.literal("Festival reward"));
        machine.operatorInventory().setItem(0, token.copy());
        machine.operatorInventory().setItem(1, reward.copy());
        buyer.getInventory().setItem(0, new ItemStack(Items.EMERALD, 20));
        helper.assertTrue(!machine.startCrank(buyer), "Plain emeralds incorrectly paid for component-specific tokens");
        buyer.getInventory().setItem(1, token.copyWithCount(2));
        buyer.getInventory().setItem(40, token.copyWithCount(1));
        helper.assertTrue(machine.startCrank(buyer), "Matching currency split between inventory and offhand was refused");
        crankTicks(machine, buyer, 40);
        helper.assertTrue(currency(buyer) == 20 && buyer.getInventory().getItem(0).getCount() == 20,
            "Payment consumed the wrong currency or wrong count");
        helper.assertTrue(ItemStack.matches(machine.operatorInventory().getItem(10), token), "Collected payment lost components");
        helper.assertTrue(ItemStack.matches(machine.getPrice(), token), "The physical price template was consumed");
        helper.assertTrue(machine.operatorInventory().getItem(1).isEmpty(), "Selected stack was not decremented by its available eight items");
        List<ItemEntity> output = capsules(helper);
        helper.assertTrue(output.size() == 1 && output.getFirst().getItem().getCount() == 1, "A roll must dispense exactly one capsule");
        List<ItemStack> contents = output.getFirst().getItem().getOrDefault(DataComponents.CONTAINER, ItemContainerContents.EMPTY).nonEmptyStream().toList();
        helper.assertTrue(contents.size() == 1 && ItemStack.matches(contents.getFirst(), reward),
            "A requested sixteen from stock eight must seal all eight, preserving item components");
        helper.succeed();
    }

    @GameTest(template = "nostalgia_test")
    public static void gachaponFailedQuotesAndMidCrankChangesNeverTakePayment(GameTestHelper helper) {
        ServerPlayer owner = createPlayer(helper, "gacha-quotes", GameType.SURVIVAL);
        GachaponBlockEntity machine = configure(helper, BASE, owner);
        owner.getInventory().setItem(0, new ItemStack(Items.EMERALD, 3));
        for (int slot = 10; slot < 19; slot++) { machine.operatorInventory().setItem(slot, new ItemStack(Items.STONE, 64)); }
        helper.assertTrue(!machine.startCrank(owner) && currency(owner) == 3, "A full currency box charged the buyer");
        for (int slot = 10; slot < 19; slot++) { machine.operatorInventory().setItem(slot, ItemStack.EMPTY); }
        machine.operatorInventory().setItem(0, ItemStack.EMPTY);
        helper.assertTrue(!machine.startCrank(owner), "An unpriced machine started dispensing");
        machine.operatorInventory().setItem(0, new ItemStack(Items.EMERALD, 3));
        machine.operatorInventory().setItem(1, ItemStack.EMPTY);
        helper.assertTrue(!machine.startCrank(owner), "An empty reward inventory started dispensing");
        machine.operatorInventory().setItem(1, new ItemStack(Items.DIAMOND, 8));
        helper.assertTrue(machine.startCrank(owner), "A valid quote did not start");
        crankTicks(machine, owner, 12);
        machine.operatorInventory().setItem(0, new ItemStack(Items.EMERALD, 4));
        crankTicks(machine, owner, 40);
        helper.assertTrue(currency(owner) == 3 && machine.getCrankTicks() == 0 && capsules(helper).isEmpty(),
            "An operator changed the price during the crank and the old quote still charged");
        machine.operatorInventory().setItem(0, new ItemStack(Items.EMERALD, 3));
        helper.assertTrue(machine.startCrank(owner), "Fresh valid quote did not start");
        crankTicks(machine, owner, 12);
        owner.getInventory().setItem(0, ItemStack.EMPTY);
        crankTicks(machine, owner, 28);
        helper.assertTrue(machine.operatorInventory().getItem(1).getCount() == 8 && machine.operatorInventory().getItem(10).isEmpty()
            && capsules(helper).isEmpty(), "A buyer whose funds disappeared still received a reward or created currency");
        helper.succeed();
    }

    @GameTest(template = "nostalgia_test")
    public static void gachaponRejectedCapsuleSpawnKeepsCurrencyAndReward(GameTestHelper helper) {
        ServerPlayer owner = createPlayer(helper, "gacha-veto", GameType.SURVIVAL);
        GachaponBlockEntity machine = configure(helper, BASE, owner);
        owner.getInventory().setItem(0, new ItemStack(Items.EMERALD, 3));
        Consumer<EntityJoinLevelEvent> veto = event -> {
            if (event.getEntity() instanceof ItemEntity item && item.getItem().is(FunPackCustom.GACHAPON_CAPSULE.get())
                    && item.position().distanceToSqr(machine.getBlockPos().getCenter()) < 4) { event.setCanceled(true); }
        };
        NeoForge.EVENT_BUS.addListener(veto);
        try {
            helper.assertTrue(machine.startCrank(owner), "The valid transaction did not start");
            crankTicks(machine, owner, 40);
            helper.assertTrue(currency(owner) == 3 && machine.operatorInventory().getItem(1).getCount() == 8
                && machine.operatorInventory().getItem(10).isEmpty() && capsules(helper).isEmpty(),
                "A vetoed capsule spawn took currency or stock");
        } finally { NeoForge.EVENT_BUS.unregister(veto); }
        helper.succeed();
    }

    @GameTest(template = "nostalgia_test", timeoutTicks = 210)
    public static void gachaponWalkingAwayPausesThenResetsAfterFiveSeconds(GameTestHelper helper) {
        ServerPlayer owner = createPlayer(helper, "gacha-pause", GameType.SURVIVAL);
        GachaponBlockEntity machine = configure(helper, BASE, owner);
        owner.getInventory().setItem(0, new ItemStack(Items.EMERALD, 6));
        helper.assertTrue(machine.startCrank(owner), "Crank did not start");
        crankTicks(machine, owner, 12);
        machine.heartbeat(owner, false);
        owner.setPos(owner.getX() + 12, owner.getY(), owner.getZ());
        helper.runAfterDelay(50, () -> {
            helper.assertTrue(machine.getCrankTicks() == 12 && !machine.isCranking() && currency(owner) == 6,
                "Leaving the machine charged money, advanced, or reset before five seconds");
            aimAt(owner, machine.getBlockPos());
            crankTicks(machine, owner, 5);
            helper.assertTrue(machine.getCrankTicks() == 17, "Returning inside the grace period failed to resume the same crank");
            machine.heartbeat(owner, false);
            owner.setPos(owner.getX() + 12, owner.getY(), owner.getZ());
        });
        helper.runAfterDelay(140, () -> helper.assertTrue(machine.getCrankTicks() == 17 && machine.hasPendingCrank(),
            "Resuming failed to restart the five-second inactivity countdown"));
        helper.runAfterDelay(153, () -> {
            helper.assertTrue(machine.getCrankTicks() == 0 && !machine.hasPendingCrank() && currency(owner) == 6
                && machine.operatorInventory().getItem(1).getCount() == 8 && capsules(helper).isEmpty(),
                "Five seconds away failed to reset an unpaid crank cleanly");
            aimAt(owner, machine.getBlockPos());
            helper.assertTrue(machine.startCrank(owner), "The expired reservation prevented a fresh roll");
            crankTicks(machine, owner, 40);
            helper.assertTrue(currency(owner) == 3 && capsules(helper).size() == 1, "Fresh roll after expiry did not charge and dispense once");
            helper.succeed();
        });
    }

    @GameTest(template = "nostalgia_test")
    public static void gachaponConcurrentBuyersCannotShareOrRepeatAHeldCrank(GameTestHelper helper) {
        ServerPlayer first = createPlayer(helper, "gacha-first", GameType.SURVIVAL);
        GachaponBlockEntity machine = configure(helper, BASE, first);
        machine.operatorInventory().setItem(0, new ItemStack(Items.EMERALD));
        machine.operatorInventory().setItem(1, new ItemStack(Items.DIAMOND, 64));
        machine.setDispenseAmount(1);
        ServerPlayer second = createPlayer(helper, "gacha-second", GameType.SURVIVAL);
        first.getInventory().setItem(0, new ItemStack(Items.EMERALD, 5));
        second.getInventory().setItem(0, new ItemStack(Items.EMERALD, 5));
        helper.assertTrue(machine.startCrank(first) && !machine.startCrank(second), "Two players acquired the same crank");
        crankTicks(machine, first, 39);
        machine.heartbeat(second, true);
        helper.assertTrue(machine.getCrankTicks() == 39 && currency(first) == 5 && currency(second) == 5,
            "A second buyer advanced or paid the first buyer's crank");
        crankTicks(machine, first, 1);
        helper.assertTrue(currency(first) == 4 && currency(second) == 5 && capsules(helper).size() == 1, "Completion did not charge exactly its buyer");
        helper.assertTrue(!machine.startCrank(first), "Holding right-click immediately started another paid roll");
        helper.assertTrue(machine.startCrank(second), "The completed crank did not release the machine for a different buyer");
        crankTicks(machine, second, 40);
        helper.assertTrue(!machine.startCrank(first), "Another buyer's completion cleared the first buyer's release requirement");
        helper.assertTrue(currency(first) == 4 && currency(second) == 4 && capsules(helper).size() == 2,
            "Concurrent turns duplicated payment or capsules");
        machine.heartbeat(first, false);
        helper.assertTrue(machine.startCrank(first), "A genuine release did not allow another roll");
        machine.heartbeat(first, false);
        helper.succeed();
    }
}
