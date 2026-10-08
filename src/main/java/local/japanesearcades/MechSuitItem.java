package local.japanesearcades;

import java.util.List;
import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.component.DataComponents;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.chat.Component;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.util.Mth;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.TooltipFlag;
import net.minecraft.world.item.component.CustomData;
import net.minecraft.world.item.context.UseOnContext;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.gameevent.GameEvent;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;

/** A compact reward that unfolds into a persistent vehicle, preserving its hull on recovery. */
public final class MechSuitItem extends Item {
    static final String HULL_TAG = "IvoryMechHull";
    public MechSuitItem(Properties properties) { super(properties); }

    public static float hull(ItemStack stack) {
        CompoundTag tag = stack.getOrDefault(DataComponents.CUSTOM_DATA, CustomData.EMPTY).copyTag();
        float value = tag.contains(HULL_TAG) ? tag.getFloat(HULL_TAG) : MechSuitEntity.MAX_HULL;
        return Float.isFinite(value) ? Mth.clamp(value, 0, MechSuitEntity.MAX_HULL) : MechSuitEntity.MAX_HULL;
    }

    static ItemStack packed(float health) {
        ItemStack stack = new ItemStack(JapaneseArcades.MECH_SUIT_ITEM.get());
        CompoundTag tag = new CompoundTag();
        tag.putFloat(HULL_TAG, Mth.clamp(health, 0, MechSuitEntity.MAX_HULL));
        stack.set(DataComponents.CUSTOM_DATA, CustomData.of(tag));
        return stack;
    }

    @Override public InteractionResult useOn(UseOnContext context) {
        Player player = context.getPlayer();
        Level level = context.getLevel();
        if (player == null || player.isSpectator() || player.isPassenger() || context.getClickedFace() != Direction.UP) {
            return InteractionResult.FAIL;
        }
        BlockPos support = context.getClickedPos();
        BlockPos base = support.above();
        if (!player.mayUseItemAt(base, Direction.UP, context.getItemInHand()) || !level.mayInteract(player, support)) {
            return InteractionResult.FAIL;
        }
        Vec3 position = Vec3.atBottomCenterOf(base);
        AABB bounds = JapaneseArcades.MECH_SUIT.get().getDimensions().makeBoundingBox(position);
        if (!MechSuitEntity.loadedAndWithinBounds(level, bounds) || !level.noCollision(null, bounds)
                || !level.getEntities((Entity)null, bounds, entity -> entity.isAlive() && !entity.isSpectator()).isEmpty()
                || !level.getBlockState(support).isFaceSturdy(level, support, Direction.UP)
                || level.containsAnyLiquid(bounds)) {
            if (!level.isClientSide) { player.displayClientMessage(Component.translatable("message.japanesearcades.mech.blocked"), true); }
            return InteractionResult.FAIL;
        }
        if (!level.isClientSide) {
            MechSuitEntity mech = new MechSuitEntity(JapaneseArcades.MECH_SUIT.get(), level);
            mech.moveTo(position.x, position.y, position.z, player.getYRot(), 0);
            mech.configure(player.getUUID(), hull(context.getItemInHand()));
            mech.setCustomName(context.getItemInHand().get(DataComponents.CUSTOM_NAME));
            if (!level.addFreshEntity(mech)) { return InteractionResult.FAIL; }
            if (!player.getAbilities().instabuild) { context.getItemInHand().shrink(1); }
            level.playSound(null, mech.blockPosition(), SoundEvents.IRON_GOLEM_REPAIR, SoundSource.PLAYERS, 1, .6f);
            mech.gameEvent(GameEvent.ENTITY_PLACE, player);
        }
        return InteractionResult.sidedSuccess(level.isClientSide);
    }

    @Override public void appendHoverText(ItemStack stack, TooltipContext context, List<Component> lines, TooltipFlag flags) {
        super.appendHoverText(stack, context, lines, flags);
        lines.add(Component.translatable("tooltip.japanesearcades.mech.deploy").withStyle(ChatFormatting.GRAY));
        lines.add(Component.translatable("tooltip.japanesearcades.mech.hull", Mth.ceil(hull(stack)), (int)MechSuitEntity.MAX_HULL)
            .withStyle(ChatFormatting.AQUA));
        lines.add(Component.translatable("tooltip.japanesearcades.mech.repair").withStyle(ChatFormatting.GRAY));
    }
}
