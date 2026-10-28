package local.japanesearcades;

import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.neoforge.event.entity.player.PlayerInteractEvent;
import net.neoforged.neoforge.event.level.BlockEvent;
import net.neoforged.neoforge.event.level.ExplosionEvent;

/** Access protection resolves every glass/frame cell to the cabinet's one controller. */
public final class ClawMachineProtection {
    private ClawMachineProtection() {}

    @SubscribeEvent
    public static void operatorInteraction(PlayerInteractEvent.RightClickBlock event) {
        if (event.getHand() == InteractionHand.MAIN_HAND && event.getEntity().isShiftKeyDown()
                && event.getEntity().getMainHandItem().isEmpty()) {
            ClawMachineBlockEntity machine = ClawMachineBlock.machineAt(event.getLevel(), event.getPos());
            if (machine == null) { return; }
            if (event.getEntity() instanceof ServerPlayer player) { ClawMachineBlock.openOperator(player, machine); }
            event.setCancellationResult(InteractionResult.SUCCESS);
            event.setCanceled(true);
        }
    }

    @SubscribeEvent
    public static void beforeBreak(BlockEvent.BreakEvent event) {
        ClawMachineBlockEntity machine = ClawMachineBlock.machineAt(event.getLevel(), event.getPos());
        if (machine != null && !machine.isOwnerOrCreative(event.getPlayer())) {
            event.setCanceled(true);
            event.getPlayer().displayClientMessage(Component.translatable("message.japanesearcades.claw_owner_break"), true);
        }
    }

    @SubscribeEvent
    public static void beforeMining(PlayerInteractEvent.LeftClickBlock event) {
        if (event.getLevel().isClientSide) { return; }
        ClawMachineBlockEntity machine = ClawMachineBlock.machineAt(event.getLevel(), event.getPos());
        if (machine != null && !machine.isOwnerOrCreative(event.getEntity())) {
            event.setCanceled(true);
            if (event.getAction() == PlayerInteractEvent.LeftClickBlock.Action.START) {
                event.getEntity().displayClientMessage(Component.translatable("message.japanesearcades.claw_owner_break"), true);
            }
        }
    }

    @SubscribeEvent
    public static void explosion(ExplosionEvent.Detonate event) {
        event.getAffectedBlocks().removeIf(pos -> event.getLevel().getBlockState(pos).getBlock() instanceof ClawMachineBlock);
    }
}
