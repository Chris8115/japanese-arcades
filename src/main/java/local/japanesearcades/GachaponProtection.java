package local.japanesearcades;

import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.neoforge.event.entity.player.PlayerInteractEvent;
import net.neoforged.neoforge.event.level.BlockEvent;
import net.neoforged.neoforge.event.level.ExplosionEvent;

/** Password protection also covers the usual ways to extract a locked inventory. */
public final class GachaponProtection {
    private GachaponProtection() {}

    @SubscribeEvent
    public static void operatorInteraction(PlayerInteractEvent.RightClickBlock event) {
        // Vanilla sneaking can skip the block when the offhand holds a shield or
        // another item. An empty main hand must still reach the operator controls.
        if (event.getHand() == InteractionHand.MAIN_HAND && event.getEntity().isShiftKeyDown()
                && event.getEntity().getMainHandItem().isEmpty()
                && event.getLevel().getBlockEntity(event.getPos()) instanceof GachaponBlockEntity machine) {
            if (event.getEntity() instanceof ServerPlayer player) { machine.openOperatorAccess(player); }
            event.setCancellationResult(InteractionResult.SUCCESS);
            event.setCanceled(true);
        }
    }

    @SubscribeEvent
    public static void beforeBreak(BlockEvent.BreakEvent event) {
        if (event.getLevel().getBlockEntity(event.getPos()) instanceof GachaponBlockEntity machine
                && !machine.isOwnerOrCreative(event.getPlayer())) {
            event.setCanceled(true);
            event.getPlayer().displayClientMessage(Component.translatable("message.japanesearcades.gachapon_owner_break"), true);
        }
    }

    @SubscribeEvent
    public static void beforeMining(PlayerInteractEvent.LeftClickBlock event) {
        if (!event.getLevel().isClientSide && event.getLevel().getBlockEntity(event.getPos()) instanceof GachaponBlockEntity machine
                && !machine.isOwnerOrCreative(event.getEntity())) {
            event.setCanceled(true);
            if (event.getAction() == PlayerInteractEvent.LeftClickBlock.Action.START) {
                event.getEntity().displayClientMessage(Component.translatable("message.japanesearcades.gachapon_owner_break"), true);
            }
        }
    }

    @SubscribeEvent
    public static void explosion(ExplosionEvent.Detonate event) {
        event.getAffectedBlocks().removeIf(pos -> event.getLevel().getBlockState(pos).is(JapaneseArcades.GACHAPON.get()));
    }
}
