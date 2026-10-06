package local.funpack.custom;

import java.util.Map;
import java.util.WeakHashMap;
import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.phys.BlockHitResult;
import net.minecraft.world.phys.HitResult;
import net.neoforged.bus.api.EventPriority;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.neoforge.event.entity.player.PlayerInteractEvent;

/** Paid simulation for existing cabinets. No blockstate or idle artwork changes. */
public final class ArcadePlayInteraction {
    private record Cooldown(ServerLevel level, long until) {}
    private static final Map<Player, Cooldown> COOLDOWNS = new WeakHashMap<>();
    private ArcadePlayInteraction() {}

    @SubscribeEvent(priority = EventPriority.HIGH)
    public static void rightClick(PlayerInteractEvent.RightClickBlock event) {
        Player player = event.getEntity();
        if (!(player.level().getBlockState(event.getPos()).getBlock() instanceof NostalgiaCabinetBlock)) { return; }
        // A pass in the main hand wins. An offhand pass is usable with an empty
        // main hand, so inserting a music disc remains an intentional action.
        InteractionHand hand = player.getMainHandItem().getItem() instanceof ArcadePassItem ? InteractionHand.MAIN_HAND
            : player.getMainHandItem().isEmpty() && player.getOffhandItem().getItem() instanceof ArcadePassItem ? InteractionHand.OFF_HAND : null;
        if (hand == null) { return; }
        event.setCanceled(true);
        event.setCancellationResult(InteractionResult.sidedSuccess(player.level().isClientSide));
        if (player instanceof ServerPlayer serverPlayer) { play(serverPlayer, event.getPos(), hand); }
    }

    static boolean play(ServerPlayer player, BlockPos clicked, InteractionHand hand) {
        ServerLevel level = player.serverLevel();
        ItemStack stack = player.getItemInHand(hand);
        ArcadePassData pass = ArcadePassItem.data(stack);
        if (pass == null) { message(player, "arcade.pass.invalid"); return false; }
        if (!player.isAlive() || player.isSpectator() || !level.hasChunkAt(clicked) || !player.canInteractWithBlock(clicked, 0)) { return false; }
        var state = level.getBlockState(clicked);
        if (!(state.getBlock() instanceof NostalgiaCabinetBlock block)) { return false; }
        BlockPos anchor = block.basePosition(clicked, state);
        if (!level.getBlockState(anchor).is(block) || !(level.getBlockEntity(anchor) instanceof NostalgiaJukeboxBlockEntity)) { return false; }
        HitResult target = player.pick(player.blockInteractionRange(), 1, false);
        if (!(target instanceof BlockHitResult visible) || target.getType() != HitResult.Type.BLOCK) { return false; }
        var hitState = level.getBlockState(visible.getBlockPos());
        if (!hitState.is(block) || !block.basePosition(visible.getBlockPos(), hitState).equals(anchor)) { return false; }
        long tick = level.getGameTime();
        Cooldown cooldown = COOLDOWNS.get(player);
        if (cooldown != null && cooldown.level == level && cooldown.until > tick) {
            message(player, "arcade.play.cooldown", (cooldown.until-tick+19)/20); return false;
        }
        var profile = ArcadeEconomyConfig.profile(BuiltInRegistries.BLOCK.getKey(block));
        if (profile.ranks().isEmpty()) { message(player, "arcade.play.unavailable"); return false; }
        if (pass.credits() < profile.credits()) { message(player, "arcade.play.insufficient", profile.credits(), pass.credits()); return false; }
        if (pass.prizePoints() > ArcadePassData.MAX_BALANCE-profile.maximumPoints()) { message(player, "arcade.play.full"); return false; }
        var rank = ArcadeEconomyConfig.roll(profile, level.random);
        // Debit and reward commit together before any sound, event or packet.
        // A disconnect, machine break, pass movement or server shutdown cannot
        // strand a charged play or pay the same play into a different card.
        ArcadePassItem.setData(stack, pass.withBalances(pass.credits()-profile.credits(), pass.prizePoints()+rank.points()));
        COOLDOWNS.put(player, new Cooldown(level, tick+ArcadeEconomyConfig.cooldownTicks()));
        player.getInventory().setChanged();
        player.containerMenu.broadcastChanges();
        player.inventoryMenu.broadcastChanges();
        float quality = rank.points() / (float)Math.max(1, profile.maximumPoints());
        level.playSound(null, clicked, SoundEvents.NOTE_BLOCK_CHIME.value(), SoundSource.BLOCKS, .7F, .8F+quality);
        level.playSound(null, clicked, SoundEvents.NOTE_BLOCK_BELL.value(), SoundSource.BLOCKS, .35F, 1.1F+quality*.7F);
        var impact = visible.getLocation();
        level.sendParticles(quality >= .5F ? ParticleTypes.END_ROD : ParticleTypes.HAPPY_VILLAGER,
            impact.x, impact.y+.15, impact.z, 8+(int)(quality*14), .18, .2, .18, .01);
        player.displayClientMessage(Component.translatable("arcade.play.result", rank.label(), rank.points(), profile.credits())
            .withStyle(quality >= .5F ? ChatFormatting.GOLD : ChatFormatting.AQUA), false);
        message(player, "arcade.pass.balance", pass.credits()-profile.credits(), pass.prizePoints()+rank.points());
        return true;
    }
    private static void message(Player player, String key, Object... args) {
        player.displayClientMessage(Component.translatable(key, args), true);
    }
}
