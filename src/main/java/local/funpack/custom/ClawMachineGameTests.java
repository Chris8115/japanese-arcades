package local.funpack.custom;

import static local.funpack.custom.GachaponTransactionGameTests.createPlayer;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.gametest.framework.GameTest;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.BlockItem;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.item.context.BlockPlaceContext;
import net.minecraft.world.level.GameType;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.phys.BlockHitResult;
import net.minecraft.world.phys.Vec3;
import net.neoforged.neoforge.capabilities.Capabilities;
import net.neoforged.neoforge.common.NeoForge;
import net.neoforged.neoforge.event.level.BlockEvent;
import net.neoforged.neoforge.gametest.GameTestHolder;
import net.neoforged.neoforge.gametest.PrefixGameTestTemplate;

/** Native block placement/removal and inventory protection across all eighteen cells. */
@GameTestHolder(FunPackCustom.MOD_ID)
@PrefixGameTestTemplate(false)
public final class ClawMachineGameTests {
    private static final BlockPos BASE = new BlockPos(3, 1, 3);

    private static Player player(GameTestHelper helper, Direction facing) {
        Player player = helper.makeMockPlayer(GameType.SURVIVAL);
        orient(helper, player, facing);
        return player;
    }
    private static void orient(GameTestHelper helper, Player player, Direction facing) {
        Vec3 front = Vec3.atCenterOf(helper.absolutePos(BASE)).add(facing.getStepX()*2.5, -.5, facing.getStepZ()*2.5);
        player.setPos(front);
        player.setYRot(facing.getOpposite().toYRot());
        player.setItemInHand(InteractionHand.MAIN_HAND, new ItemStack(FunPackCustom.CLAW_MACHINE_ITEM.get(), 2));
    }
    private static void floor(GameTestHelper helper, Direction facing) {
        for (int part=0; part<6; part++) helper.setBlock(ClawMachineBlock.partPosition(BASE, facing, part).below(), Blocks.STONE);
    }
    private static boolean place(GameTestHelper helper, Player player) {
        BlockPos ground = helper.absolutePos(BASE.below());
        var hit = new BlockHitResult(ground.getCenter().add(0,.5,0), Direction.UP, ground, false);
        return ((BlockItem)player.getMainHandItem().getItem()).place(
            new BlockPlaceContext(player, InteractionHand.MAIN_HAND, player.getMainHandItem(), hit)).consumesAction();
    }
    private static void empty(GameTestHelper helper, Direction facing) {
        for (int part=0; part<18; part++) helper.assertBlockPresent(Blocks.AIR, ClawMachineBlock.partPosition(BASE, facing, part));
    }

    @GameTest(template="nostalgia_test", timeoutTicks=150)
    public static void everyFacingAndBrokenSectionHasOneInventoryAndOneCabinetDrop(GameTestHelper helper) {
        for (Direction facing : Direction.Plane.HORIZONTAL) {
            floor(helper, facing);
            Player player = player(helper, facing);
            for (int broken=0; broken<18; broken++) {
                player.setItemInHand(InteractionHand.MAIN_HAND, new ItemStack(FunPackCustom.CLAW_MACHINE_ITEM.get(), 2));
                helper.assertTrue(place(helper, player), "Could not place claw facing " + facing);
                helper.assertTrue(player.getMainHandItem().getCount() == 1, "Placement did not consume exactly one cabinet");
                var machine = (ClawMachineBlockEntity)helper.getBlockEntity(BASE);
                machine.operatorInventory().setItem(1, new ItemStack(Items.DIAMOND, 13));
                machine.operatorInventory().setItem(10, new ItemStack(Items.EMERALD, 7));
                for (int part=0; part<18; part++) {
                    BlockPos cell = ClawMachineBlock.partPosition(BASE, facing, part);
                    helper.assertBlockProperty(cell, ClawMachineBlock.PART, part);
                    helper.assertBlockProperty(cell, ClawMachineBlock.FACING, facing);
                    helper.assertTrue(ClawMachineBlock.machineAt(helper.getLevel(), helper.absolutePos(cell)) == machine,
                        "Cabinet part did not resolve its controller");
                    helper.assertTrue(part == 0 || helper.getLevel().getBlockEntity(helper.absolutePos(cell)) == null,
                        "A secondary cell owns another inventory");
                }
                helper.getLevel().destroyBlock(helper.absolutePos(ClawMachineBlock.partPosition(BASE, facing, broken)), true);
                empty(helper, facing);
                var drops = helper.getEntities(EntityType.ITEM, BASE, 4);
                helper.assertTrue(drops.stream().filter(e -> e.getItem().is(FunPackCustom.CLAW_MACHINE_ITEM.get()))
                    .mapToInt(e -> e.getItem().getCount()).sum() == 1, "Breaking part " + broken + " duplicated/lost the cabinet");
                helper.assertTrue(drops.stream().filter(e -> e.getItem().is(Items.DIAMOND)).mapToInt(e -> e.getItem().getCount()).sum() == 13,
                    "Stored prize was lost or duplicated");
                helper.assertTrue(drops.stream().filter(e -> e.getItem().is(Items.EMERALD)).mapToInt(e -> e.getItem().getCount()).sum() == 7,
                    "Collected currency was lost or duplicated");
                drops.forEach(e -> e.discard());
            }
        }
        helper.succeed();
    }

    @GameTest(template="nostalgia_test")
    public static void obstructionAndMissingFloorRejectWholePlacementWithoutCharge(GameTestHelper helper) {
        Direction facing = Direction.NORTH;
        floor(helper, facing);
        Player player = player(helper, facing);
        for (int part=1; part<18; part++) {
            BlockPos blocked = ClawMachineBlock.partPosition(BASE, facing, part);
            helper.setBlock(blocked, Blocks.STONE);
            helper.assertFalse(place(helper, player), "Placement ignored blocked part " + part);
            helper.assertTrue(player.getMainHandItem().getCount() == 2, "Rejected placement consumed a cabinet");
            helper.assertBlockPresent(Blocks.AIR, BASE);
            helper.setBlock(blocked, Blocks.AIR);
        }
        for (int part=1; part<6; part++) {
            BlockPos support = ClawMachineBlock.partPosition(BASE, facing, part).below();
            helper.setBlock(support, Blocks.AIR);
            helper.assertFalse(place(helper, player), "Placement ignored a missing floor cell");
            helper.setBlock(support, Blocks.STONE);
        }
        helper.assertTrue(place(helper, player), "Clear footprint failed placement");
        helper.getLevel().destroyBlock(helper.absolutePos(ClawMachineBlock.partPosition(BASE, facing, 5).below()), false);
        empty(helper, facing);
        helper.assertItemEntityCountIs(FunPackCustom.CLAW_MACHINE_ITEM.get(), BASE, 4, 1);
        helper.succeed();
    }

    @GameTest(template="nostalgia_test")
    public static void ownerProtectionCoversEveryCellAndCreativeReturnsStockOnly(GameTestHelper helper) {
        Direction facing = Direction.NORTH;
        floor(helper, facing);
        ServerPlayer owner = createPlayer(helper, "ClawOwner", GameType.SURVIVAL);
        ServerPlayer visitor = createPlayer(helper, "ClawVisitor", GameType.SURVIVAL);
        try {
            orient(helper, owner, facing);
            helper.assertTrue(place(helper, owner), "Owner could not place machine");
            var machine = (ClawMachineBlockEntity)helper.getBlockEntity(BASE);
            helper.assertTrue(machine.isOwnerOrCreative(owner) && owner.containerMenu instanceof ClawMachineAccessMenu,
                "Placement lost owner or initial PIN prompt");
            owner.closeContainer();
            machine.operatorInventory().setItem(1, new ItemStack(Items.DIAMOND, 37));
            for (int part=0; part<18; part++) {
                BlockPos cell = helper.absolutePos(ClawMachineBlock.partPosition(BASE, facing, part));
                var denied = new BlockEvent.BreakEvent(helper.getLevel(), cell, helper.getLevel().getBlockState(cell), visitor);
                NeoForge.EVENT_BUS.post(denied);
                helper.assertTrue(denied.isCanceled(), "Visitor can break locked part " + part);
                var allowed = new BlockEvent.BreakEvent(helper.getLevel(), cell, helper.getLevel().getBlockState(cell), owner);
                NeoForge.EVENT_BUS.post(allowed);
                helper.assertFalse(allowed.isCanceled(), "Owner cannot remove their cabinet");
                helper.assertTrue(helper.getLevel().getCapability(Capabilities.ItemHandler.BLOCK, cell, Direction.DOWN) == null,
                    "Hopper can extract private prize inventory");
            }
            owner.setGameMode(GameType.CREATIVE);
            BlockPos upper = helper.absolutePos(ClawMachineBlock.partPosition(BASE, facing, 17));
            var state = helper.getLevel().getBlockState(upper);
            state.getBlock().playerWillDestroy(helper.getLevel(), upper, state, owner);
            helper.getLevel().destroyBlock(upper, false, owner);
            empty(helper, facing);
            helper.assertItemEntityCountIs(FunPackCustom.CLAW_MACHINE_ITEM.get(), BASE, 4, 0);
            helper.assertTrue(helper.getEntities(EntityType.ITEM, BASE, 4).stream().filter(e -> e.getItem().is(Items.DIAMOND))
                .mapToInt(e -> e.getItem().getCount()).sum() == 37, "Creative removal deleted loaded prize stack");
            helper.succeed();
        } finally {
            owner.closeContainer();
            owner.getServer().getPlayerList().remove(owner);
            visitor.getServer().getPlayerList().remove(visitor);
        }
    }
}
