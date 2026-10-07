package local.japanesearcades;

import static local.japanesearcades.GachaponTransactionGameTests.aimAt;
import static local.japanesearcades.GachaponTransactionGameTests.configure;
import static local.japanesearcades.GachaponTransactionGameTests.createPlayer;

import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.component.DataComponents;
import net.minecraft.gametest.framework.GameTest;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.inventory.ClickType;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.BlockItem;
import net.minecraft.world.item.Items;
import net.minecraft.world.item.context.BlockPlaceContext;
import net.minecraft.world.level.GameType;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.entity.HopperBlockEntity;
import net.minecraft.world.phys.BlockHitResult;
import net.minecraft.world.phys.Vec3;
import net.neoforged.neoforge.capabilities.Capabilities;
import net.neoforged.neoforge.common.NeoForge;
import net.neoforged.neoforge.event.level.BlockEvent;
import net.neoforged.neoforge.event.entity.player.PlayerInteractEvent;
import net.neoforged.neoforge.gametest.GameTestHolder;
import net.neoforged.neoforge.gametest.PrefixGameTestTemplate;

/** Placement, access control, save data, extraction and capsule integration tests. */
@GameTestHolder(JapaneseArcades.MOD_ID)
@PrefixGameTestTemplate(false)
public final class GachaponGameTests {
    private static final BlockPos BASE = new BlockPos(3, 1, 3);

    private static void remove(ServerPlayer... players) {
        for (ServerPlayer player : players) { player.getServer().getPlayerList().remove(player); }
    }

    @GameTest(template="nostalgia_test")
    public static void placementPromptsOwnerAndStacksIndependently(GameTestHelper helper) {
        ServerPlayer owner = createPlayer(helper, "GachaPlacer", GameType.SURVIVAL);
        try {
            helper.setBlock(BASE.below(), Blocks.STONE);
            helper.setBlock(BASE.east().below(), Blocks.STONE);
            for (BlockPos relative : new BlockPos[]{BASE, BASE.above(), BASE.east(), BASE.east().above()}) {
                owner.closeContainer();
                owner.setItemInHand(InteractionHand.MAIN_HAND, new ItemStack(JapaneseArcades.GACHAPON_ITEM.get()));
                aimAt(owner, helper.absolutePos(relative));
                owner.setShiftKeyDown(true);
                BlockPos floor = helper.absolutePos(relative.below());
                var hit = new BlockHitResult(Vec3.atCenterOf(floor).add(0,.5,0), Direction.UP, floor, false);
                var context = new BlockPlaceContext(owner, InteractionHand.MAIN_HAND, owner.getMainHandItem(), hit);
                helper.assertTrue(((BlockItem)owner.getMainHandItem().getItem()).place(context).consumesAction(),
                    "Single machine failed to place beside or above another");
                var machine = (GachaponBlockEntity)helper.getBlockEntity(relative);
                helper.assertTrue(machine.isOwnerOrCreative(owner), "Placer must own each new machine");
                helper.assertTrue(owner.containerMenu instanceof GachaponAccessMenu access && access.isSetup(),
                    "Placement must immediately prompt for initial password");
                helper.assertFalse(machine.hasPassword(), "Fresh machine must not inherit another machine's password");
                helper.assertTrue(machine.setPassword(owner, "chosen-pin"), "Owner must be able to initialize a machine");
            }
            helper.assertBlockPresent(JapaneseArcades.GACHAPON.get(), BASE);
            helper.assertBlockPresent(JapaneseArcades.GACHAPON.get(), BASE.east());
            helper.assertBlockPresent(JapaneseArcades.GACHAPON.get(), BASE.above());
            helper.assertBlockPresent(JapaneseArcades.GACHAPON.get(), BASE.east().above());
            helper.getLevel().destroyBlock(helper.absolutePos(BASE.above()), true);
            helper.assertBlockPresent(JapaneseArcades.GACHAPON.get(), BASE.east().above());
            helper.succeed();
        } finally { remove(owner); }
    }

    @GameTest(template="nostalgia_test", timeoutTicks=100)
    public static void passwordsGateMenusAndInvalidateExistingSessions(GameTestHelper helper) {
        ServerPlayer owner = createPlayer(helper, "GachaOwner", GameType.SURVIVAL);
        ServerPlayer visitor = createPlayer(helper, "GachaVisitor", GameType.SURVIVAL);
        ServerPlayer creative = createPlayer(helper, "GachaCreative", GameType.CREATIVE);
        var machine = configure(helper, BASE, owner);
        aimAt(visitor, machine.getBlockPos());
        aimAt(creative, machine.getBlockPos());
        owner.setShiftKeyDown(true);
        owner.setItemInHand(InteractionHand.MAIN_HAND, ItemStack.EMPTY);
        owner.setItemInHand(InteractionHand.OFF_HAND, new ItemStack(Items.SHIELD));
        var shiftClick = new PlayerInteractEvent.RightClickBlock(owner, InteractionHand.MAIN_HAND, machine.getBlockPos(),
            new BlockHitResult(machine.getBlockPos().getCenter(), Direction.NORTH, machine.getBlockPos(), false));
        NeoForge.EVENT_BUS.post(shiftClick);
        helper.assertTrue(shiftClick.isCanceled(), "Empty main hand with offhand shield bypassed operator interaction");
        helper.assertTrue(owner.containerMenu instanceof GachaponMenu, "Owner bypass was lost");
        machine.openOperatorAccess(creative);
        helper.assertTrue(creative.containerMenu instanceof GachaponMenu, "Creative bypass was lost");
        machine.openOperatorAccess(visitor);
        helper.assertTrue(visitor.containerMenu instanceof GachaponAccessMenu, "Visitor bypassed password prompt");
        var access = (GachaponAccessMenu)visitor.containerMenu;
        helper.assertTrue(access.slots.isEmpty(), "Unauthenticated menu leaked inventory slots");
        GachaponNetwork.handlePassword(visitor, new GachaponNetwork.PasswordPayload(access.containerId + 1, "1234"));
        helper.assertTrue(visitor.containerMenu == access, "Wrong container id unlocked the machine");
        GachaponNetwork.handlePassword(visitor, new GachaponNetwork.PasswordPayload(access.containerId, "wrong"));
        helper.assertTrue(access.getStatus() == 1, "Incorrect password was accepted");
        GachaponNetwork.handlePassword(visitor, new GachaponNetwork.PasswordPayload(access.containerId, "1234"));
        helper.assertTrue(access.getStatus() == 2, "Wrong password attempts have no cooldown");
        helper.runAfterDelay(42, () -> {
            try {
                GachaponNetwork.handlePassword(visitor, new GachaponNetwork.PasswordPayload(access.containerId, "1234"));
                helper.assertTrue(visitor.containerMenu instanceof GachaponMenu, "Correct password did not unlock inventory");
                var guestMenu = (GachaponMenu)visitor.containerMenu;
                guestMenu.changePassword(visitor, "stolen-pin");
                helper.assertTrue(guestMenu.getStatus() == 6 && machine.authenticate(owner, "1234") == 0,
                    "Password holder changed the owner's password");
                GachaponNetwork.handleSettings(visitor, new GachaponNetwork.SettingsPayload(guestMenu.containerId + 1, 64, ""));
                helper.assertTrue(machine.getDispenseAmount() == 16, "Stale settings packet was accepted");
                guestMenu.updateDispenseAmount(visitor, 5);
                helper.assertTrue(machine.getDispenseAmount() == 5, "Authorized operator could not change reward amount");
                ((GachaponMenu)owner.containerMenu).changePassword(owner, "new-owner-pin");
                helper.assertFalse(guestMenu.stillValid(visitor), "Changing PIN did not revoke an existing visitor session");
                int stock = machine.operatorInventory().getItem(1).getCount();
                guestMenu.quickMoveStack(visitor, 1);
                guestMenu.clicked(1, 0, ClickType.PICKUP, visitor);
                helper.assertTrue(machine.operatorInventory().getItem(1).getCount() == stock, "Expired menu could withdraw prizes");
                helper.assertTrue(machine.authenticate(owner, "new-owner-pin") == 0, "New password was not applied");
                helper.succeed();
            } finally { remove(owner, visitor, creative); }
        });
    }

    @GameTest(template="nostalgia_test")
    public static void privateStatePersistsButPublicPacketsOnlyDescribeDisplays(GameTestHelper helper) {
        ServerPlayer owner = createPlayer(helper, "GachaSave", GameType.SURVIVAL);
        try {
            var machine = configure(helper, BASE, owner);
            machine.operatorInventory().setItem(10, new ItemStack(Items.EMERALD, 37));
            var registry = helper.getLevel().registryAccess();
            var saved = machine.saveWithFullMetadata(registry);
            helper.assertTrue(saved.getByteArray("PasswordSalt").length == 16 && saved.getByteArray("PasswordHash").length == 32
                && !saved.contains("Password") && !saved.contains("PIN"), "Password must persist as a salted hash");
            var publicTag = machine.getUpdateTag(registry);
            helper.assertFalse(publicTag.contains("Owner") || publicTag.contains("PasswordSalt")
                || publicTag.contains("PasswordHash") || publicTag.contains("Items"), "Public update leaked private state");
            helper.assertTrue(ItemStack.parse(registry, publicTag.getCompound("Preview0")).orElseThrow().getCount() == 1,
                "Prize preview unnecessarily exposed stock quantity");
            var restored = (GachaponBlockEntity)BlockEntity.loadStatic(machine.getBlockPos(), machine.getBlockState(), saved, registry);
            helper.assertTrue(restored != null, "Saved machine did not deserialize");
            helper.getLevel().setBlockEntity(restored);
            helper.assertTrue(restored.isOwnerOrCreative(owner) && restored.hasPassword(), "Ownership or password lost on reload");
            helper.assertTrue(restored.authenticate(owner, "1234") == 0, "Saved password no longer authenticates");
            helper.assertTrue(restored.getDispenseAmount() == 16 && restored.operatorInventory().getItem(1).getCount() == 8
                && restored.operatorInventory().getItem(10).getCount() == 37 && restored.getPrice().getCount() == 3,
                "Inventory, price or amount lost on reload");
            helper.assertFalse(restored.hasPendingCrank(), "Reload retained an unpaid crank session");
            helper.succeed();
        } finally { remove(owner); }
    }

    @GameTest(template="nostalgia_test")
    public static void hopperAndBreakProtectionPreserveStockAndNeighbor(GameTestHelper helper) {
        ServerPlayer owner = createPlayer(helper, "GachaProtect", GameType.SURVIVAL);
        ServerPlayer visitor = createPlayer(helper, "GachaThief", GameType.SURVIVAL);
        try {
            var machine = configure(helper, BASE, owner);
            var neighbor = configure(helper, BASE.above(), owner);
            machine.operatorInventory().setItem(10, new ItemStack(Items.EMERALD, 7));
            var pos = machine.getBlockPos();
            helper.assertTrue(HopperBlockEntity.getContainerAt(helper.getLevel(), pos) == null, "Hopper can access locked inventory");
            for (Direction side : Direction.values()) {
                helper.assertTrue(helper.getLevel().getCapability(Capabilities.ItemHandler.BLOCK, pos, side) == null,
                    "Automation capability bypasses password protection");
            }
            var denied = new BlockEvent.BreakEvent(helper.getLevel(), pos, machine.getBlockState(), visitor);
            NeoForge.EVENT_BUS.post(denied);
            helper.assertTrue(denied.isCanceled(), "Non-owner can mine locked inventory");
            var allowed = new BlockEvent.BreakEvent(helper.getLevel(), pos, machine.getBlockState(), owner);
            NeoForge.EVENT_BUS.post(allowed);
            helper.assertFalse(allowed.isCanceled(), "Owner cannot remove machine");
            helper.getLevel().destroyBlock(pos, true, owner);
            helper.assertBlockPresent(JapaneseArcades.GACHAPON.get(), BASE.above());
            helper.assertTrue(neighbor.operatorInventory().getItem(1).getCount() == 8, "Removing one unit changed stacked neighbor");
            var drops = helper.getEntities(EntityType.ITEM, BASE, 1.4);
            helper.assertTrue(drops.stream().filter(e -> e.getItem().is(Items.DIAMOND)).mapToInt(e -> e.getItem().getCount()).sum() == 8,
                "Reward stock lost or duplicated on removal");
            helper.assertTrue(drops.stream().filter(e -> e.getItem().is(Items.EMERALD)).mapToInt(e -> e.getItem().getCount()).sum() == 10,
                "Price template or collected currency lost/duplicated on removal");
            helper.assertTrue(drops.stream().filter(e -> e.getItem().is(JapaneseArcades.GACHAPON_ITEM.get())).count() == 1,
                "Block dropped more or less than once");
            helper.succeed();
        } finally { remove(owner, visitor); }
    }

    @GameTest(template="nostalgia_test")
    public static void capsuleKeepsWholeNamedRewardThroughSaveAndOpensOnlyOnce(GameTestHelper helper) {
        ServerPlayer player = createPlayer(helper, "GachaCapsule", GameType.SURVIVAL);
        try {
            ItemStack reward = new ItemStack(Items.DIAMOND, 8);
            reward.set(DataComponents.CUSTOM_NAME, Component.literal("Eight lucky gems"));
            ItemStack capsule = CapsuleItem.create(reward);
            reward.shrink(7);
            var registry = helper.getLevel().registryAccess();
            capsule = ItemStack.parse(registry, capsule.save(registry)).orElseThrow();
            var contents = capsule.get(DataComponents.CONTAINER).nonEmptyStream().toList();
            helper.assertTrue(capsule.getCount() == 1 && contents.size() == 1 && contents.getFirst().getCount() == 8,
                "One capsule must hold the complete copied reward amount");
            player.setItemInHand(InteractionHand.MAIN_HAND, capsule);
            helper.assertTrue(CapsuleItem.openCapsule(player, InteractionHand.MAIN_HAND), "Capsule did not open");
            helper.assertFalse(CapsuleItem.openCapsule(player, InteractionHand.MAIN_HAND), "Same capsule opened twice");
            int gems = player.getInventory().items.stream().filter(s -> s.is(Items.DIAMOND)
                && Component.literal("Eight lucky gems").equals(s.get(DataComponents.CUSTOM_NAME))).mapToInt(ItemStack::getCount).sum();
            helper.assertTrue(gems == 8, "Capsule lost amount or custom item components");
            helper.succeed();
        } finally { remove(player); }
    }

    @GameTest(template="nostalgia_test")
    public static void fullInventoryDropsRewardAndCreativeStillConsumesCapsule(GameTestHelper helper) {
        ServerPlayer player = createPlayer(helper, "GachaFull", GameType.SURVIVAL);
        try {
            aimAt(player, helper.absolutePos(BASE));
            for (int slot=0; slot<36; slot++) { player.getInventory().setItem(slot, new ItemStack(Items.STONE,64)); }
            var capsule = CapsuleItem.create(new ItemStack(Items.DIAMOND, 8));
            capsule.setCount(2);
            player.setItemInHand(InteractionHand.MAIN_HAND, capsule);
            helper.assertTrue(CapsuleItem.openCapsule(player, InteractionHand.MAIN_HAND), "Full inventory prevented opening");
            helper.assertTrue(player.getMainHandItem().getCount() == 1, "Opening consumed wrong number of capsules");
            var dropped = helper.getEntities(EntityType.ITEM, BASE, 5).stream().filter(e -> e.getItem().is(Items.DIAMOND)).toList();
            helper.assertTrue(dropped.size() == 1 && dropped.getFirst().getItem().getCount() == 8,
                "Full inventory lost or split the reward amount");
            player.getInventory().clearContent();
            player.setGameMode(GameType.CREATIVE);
            for (int slot=0; slot<36; slot++) { player.getInventory().setItem(slot, new ItemStack(Items.STONE,64)); }
            var creativeCapsules = CapsuleItem.create(new ItemStack(Items.EMERALD,4));
            creativeCapsules.setCount(2);
            player.setItemInHand(InteractionHand.MAIN_HAND, creativeCapsules);
            helper.assertTrue(CapsuleItem.openCapsule(player, InteractionHand.MAIN_HAND), "Creative player cannot open capsule");
            helper.assertTrue(player.getInventory().countItem(JapaneseArcades.GACHAPON_CAPSULE.get()) == 1,
                "Creative capsule can be repeatedly opened for free contents");
            helper.assertTrue(helper.getEntities(EntityType.ITEM, BASE, 5).stream().filter(e -> e.getItem().is(Items.EMERALD))
                .mapToInt(e -> e.getItem().getCount()).sum() == 4, "Creative inventory overflow destroyed a reward");
            helper.succeed();
        } finally { remove(player); }
    }
}
