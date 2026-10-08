package local.japanesearcades;

import java.util.Optional;
import java.util.UUID;
import javax.annotation.Nullable;
import net.minecraft.core.component.DataComponents;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.chat.Component;
import net.minecraft.network.syncher.EntityDataAccessor;
import net.minecraft.network.syncher.EntityDataSerializers;
import net.minecraft.network.syncher.SynchedEntityData;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.tags.DamageTypeTags;
import net.minecraft.util.Mth;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityDimensions;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.MoverType;
import net.minecraft.world.entity.TamableAnimal;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.ClipContext;
import net.minecraft.world.level.Level;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.HitResult;
import net.minecraft.world.phys.Vec3;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.event.entity.living.LivingIncomingDamageEvent;
import net.neoforged.neoforge.event.entity.player.AttackEntityEvent;
import net.neoforged.neoforge.event.entity.player.PlayerInteractEvent;
import net.neoforged.neoforge.event.level.BlockEvent;
import net.neoforged.neoforge.event.tick.PlayerTickEvent;

/** A server-controlled vehicle: vanilla client vehicle movement cannot move this entity. */
@EventBusSubscriber(modid = JapaneseArcades.MOD_ID)
public final class MechSuitEntity extends Entity {
    public static final float MAX_HULL = 120;
    public static final int SWING_TICKS = 10;
    public static final int ATTACK_COOLDOWN = 14;
    private static final int INPUT_TIMEOUT = 6;
    private static final double SWORD_REACH = 5.5;
    private static final String EXIT_PROTECTION = "JapaneseArcadesMechExitUntil";
    private static final EntityDataAccessor<Float> HULL = SynchedEntityData.defineId(MechSuitEntity.class, EntityDataSerializers.FLOAT);
    private static final EntityDataAccessor<Boolean> FLYING = SynchedEntityData.defineId(MechSuitEntity.class, EntityDataSerializers.BOOLEAN);
    private static final EntityDataAccessor<Integer> LEFT_SWING = SynchedEntityData.defineId(MechSuitEntity.class, EntityDataSerializers.INT);
    private static final EntityDataAccessor<Integer> RIGHT_SWING = SynchedEntityData.defineId(MechSuitEntity.class, EntityDataSerializers.INT);
    private static final EntityDataAccessor<Optional<UUID>> OWNER = SynchedEntityData.defineId(MechSuitEntity.class, EntityDataSerializers.OPTIONAL_UUID);
    private MechSuitNetwork.InputPayload input = idleInput();
    private int lastInputTick = -100;
    private int leftCooldown, rightCooldown, hurtCooldown;
    private int lerpSteps;
    private double lerpX, lerpY, lerpZ;
    private float lerpYaw, lerpPitch;

    public MechSuitEntity(EntityType<? extends MechSuitEntity> type, Level level) {
        super(type, level);
        // Gravity is applied here; keeping vanilla's flag set also marks the vehicle as legitimately flying.
        setNoGravity(true);
        blocksBuilding = true;
    }

    @Override protected void defineSynchedData(SynchedEntityData.Builder builder) {
        builder.define(HULL, MAX_HULL);
        builder.define(FLYING, false);
        builder.define(LEFT_SWING, 0);
        builder.define(RIGHT_SWING, 0);
        builder.define(OWNER, Optional.empty());
    }

    private static MechSuitNetwork.InputPayload idleInput() {
        return new MechSuitNetwork.InputPayload(0, 0, false, false, false, false, 0, 0);
    }

    void configure(UUID owner, float hull) {
        entityData.set(OWNER, Optional.of(owner));
        entityData.set(HULL, Mth.clamp(hull, 0, MAX_HULL));
    }
    public boolean isFlying() { return entityData.get(FLYING); }
    public int getLeftSwingTicks() { return entityData.get(LEFT_SWING); }
    public int getRightSwingTicks() { return entityData.get(RIGHT_SWING); }
    public float getHullHealth() { return entityData.get(HULL); }
    public float getMaxHullHealth() { return MAX_HULL; }
    @Nullable public UUID getOwnerUUID() { return entityData.get(OWNER).orElse(null); }
    @Nullable public Player getPilot() { return getFirstPassenger() instanceof Player player ? player : null; }

    @Override public boolean isPickable() { return !isRemoved(); }
    @Override public boolean canBeCollidedWith() { return !isRemoved(); }
    @Override public boolean isPushable() { return false; }
    @Override protected boolean canAddPassenger(Entity passenger) {
        return passenger instanceof Player && getPassengers().isEmpty() && !isRemoved();
    }

    @Override public InteractionResult interact(Player player, InteractionHand hand) {
        if (isRemoved() || !player.isAlive() || player.isSpectator() || player.isPassenger()) { return InteractionResult.FAIL; }
        if (level().isClientSide) { return InteractionResult.SUCCESS; }
        if (!canInteract(player)) { return InteractionResult.FAIL; }
        if (getOwnerUUID() != null && !getOwnerUUID().equals(player.getUUID()) && !player.getAbilities().instabuild) {
            player.displayClientMessage(Component.translatable("message.japanesearcades.mech.owner"), true);
            return InteractionResult.FAIL;
        }
        if (isVehicle()) {
            player.displayClientMessage(Component.translatable("message.japanesearcades.mech.occupied"), true);
            return InteractionResult.FAIL;
        }
        if (player.isShiftKeyDown()) { return recover(player) ? InteractionResult.CONSUME : InteractionResult.FAIL; }
        if (player.getItemInHand(hand).is(Items.IRON_INGOT) && getHullHealth() < MAX_HULL) {
            entityData.set(HULL, Math.min(MAX_HULL, getHullHealth() + 20));
            if (!player.getAbilities().instabuild) { player.getItemInHand(hand).shrink(1); }
            level().playSound(null, blockPosition(), SoundEvents.IRON_GOLEM_REPAIR, SoundSource.PLAYERS, 1, 1);
            return InteractionResult.CONSUME;
        }
        if (getHullHealth() <= 0) {
            player.displayClientMessage(Component.translatable("message.japanesearcades.mech.wrecked"), true);
            return InteractionResult.FAIL;
        }
        if (getOwnerUUID() == null) { entityData.set(OWNER, Optional.of(player.getUUID())); }
        if (!player.startRiding(this)) { return InteractionResult.FAIL; }
        player.resetFallDistance();
        positionRider(player);
        player.displayClientMessage(Component.translatable("message.japanesearcades.mech.mounted"), true);
        return InteractionResult.CONSUME;
    }

    private boolean canInteract(Player player) {
        Vec3 eye = player.getEyePosition();
        AABB box = getBoundingBox();
        Vec3 nearest = new Vec3(Mth.clamp(eye.x, box.minX, box.maxX), Mth.clamp(eye.y, box.minY, box.maxY), Mth.clamp(eye.z, box.minZ, box.maxZ));
        double reach = player.entityInteractionRange() + .5;
        return eye.distanceToSqr(nearest) <= reach * reach && clearLine(eye, nearest, player);
    }

    private boolean recover(Player player) {
        if (isRemoved() || isVehicle()) { return false; }
        int freeSlot = player.getInventory().getFreeSlot();
        if (freeSlot < 0) {
            player.displayClientMessage(Component.translatable("message.japanesearcades.mech.inventory_full"), true);
            return false;
        }
        ItemStack packed = MechSuitItem.packed(getHullHealth());
        if (getCustomName() != null) { packed.set(DataComponents.CUSTOM_NAME, getCustomName()); }
        // The reserved empty slot and direct insertion cannot fire cancellable item-drop hooks.
        // A second interaction fails because the sole authoritative entity is already removed.
        discard();
        player.getInventory().setItem(freeSlot, packed);
        level().playSound(null, blockPosition(), SoundEvents.IRON_GOLEM_REPAIR, SoundSource.PLAYERS, .8f, 1.2f);
        return true;
    }

    void acceptInput(Player player, MechSuitNetwork.InputPayload data) {
        if (level().isClientSide || isRemoved() || getHullHealth() <= 0 || getPilot() != player || !player.isAlive() || player.isSpectator()
                || !Float.isFinite(data.forward()) || !Float.isFinite(data.strafe())
                || !Float.isFinite(data.yaw()) || !Float.isFinite(data.pitch())) { return; }
        input = new MechSuitNetwork.InputPayload(Mth.clamp(data.forward(), -1, 1), Mth.clamp(data.strafe(), -1, 1),
            data.ascend(), data.descend(), data.leftAttack(), data.rightAttack(), Mth.wrapDegrees(data.yaw()), Mth.clamp(data.pitch(), -85, 85));
        lastInputTick = tickCount;
    }

    @Override public void tick() {
        super.tick();
        if (level().isClientSide) {
            if (lerpSteps > 0) {
                lerpPositionAndRotationStep(lerpSteps--, lerpX, lerpY, lerpZ, lerpYaw, lerpPitch);
            }
            return;
        }
        if (hurtCooldown > 0) { hurtCooldown--; }
        if (leftCooldown > 0) { leftCooldown--; }
        if (rightCooldown > 0) { rightCooldown--; }
        if (getLeftSwingTicks() > 0) { entityData.set(LEFT_SWING, getLeftSwingTicks() - 1); }
        if (getRightSwingTicks() > 0) { entityData.set(RIGHT_SWING, getRightSwingTicks() - 1); }
        Player pilot = getPilot();
        if (pilot != null && (!pilot.isAlive() || pilot.isRemoved() || pilot.isSpectator() || pilot.isShiftKeyDown() || getHullHealth() <= 0)) {
            pilot.stopRiding();
            pilot = null;
        }
        boolean active = pilot != null && tickCount - lastInputTick <= INPUT_TIMEOUT;
        if (!active) { input = idleInput(); }
        if (active) {
            setYRot(Mth.approachDegrees(getYRot(), input.yaw(), 18));
            setXRot(input.pitch());
        }
        if (pilot != null && input.ascend() && !input.descend()) { entityData.set(FLYING, true); }
        Vec3 movement;
        if (pilot != null) {
            double speed = isFlying() ? .46 : .24;
            Vec3 local = new Vec3(input.strafe(), 0, input.forward());
            if (local.lengthSqr() > 1) { local = local.normalize(); }
            Vec3 horizontal = local.yRot(-getYRot() * Mth.DEG_TO_RAD).scale(speed);
            double vertical = isFlying() ? (input.ascend() == input.descend() ? 0 : input.ascend() ? .32 : -.32)
                : Math.max(getDeltaMovement().y - .08, -.8);
            movement = new Vec3(horizontal.x, vertical, horizontal.z);
        } else {
            // An empty suit lands gently instead of continuing the former rider's inputs.
            movement = new Vec3(0, Math.max(getDeltaMovement().y - .04, -.3), 0);
        }
        AABB next = getBoundingBox().expandTowards(movement);
        if (!loadedAndWithinBounds(level(), next)) {
            // Stop before touching missing chunks, the world border or either build limit.
            movement = Vec3.ZERO;
        }
        setDeltaMovement(movement);
        move(MoverType.SELF, movement);
        if (onGround()) { entityData.set(FLYING, false); }
        else if (pilot == null) { entityData.set(FLYING, true); }
        resetFallDistance();
        if (pilot != null) {
            positionRider(pilot);
            pilot.resetFallDistance();
            boolean left = active && input.leftAttack() && leftCooldown == 0;
            boolean right = active && input.rightAttack() && rightCooldown == 0;
            if (left && right) {
                // One combined damage event respects vanilla immunity frames without silently losing a blade.
                slash(pilot, true, 24);
                startSwing(false);
            } else if (left) { slash(pilot, true, 12); }
            else if (right) { slash(pilot, false, 12); }
        }
        if (getHullHealth() > 0 && isFlying() && tickCount % 4 == 0 && level() instanceof ServerLevel server) {
            Vec3 jet = new Vec3(0, 2.6, .55).yRot(-getYRot() * Mth.DEG_TO_RAD).add(position());
            server.sendParticles(ParticleTypes.END_ROD, jet.x, jet.y, jet.z, 2, .2, .2, .2, .015);
        }
    }

    static boolean loadedAndWithinBounds(Level level, AABB box) {
        if (box.minY < level.getMinBuildHeight() || box.maxY > level.getMaxBuildHeight()
                || !level.getWorldBorder().isWithinBounds(box)) { return false; }
        for (int x = Mth.floor(box.minX) >> 4; x <= Mth.floor(box.maxX) >> 4; x++) {
            for (int z = Mth.floor(box.minZ) >> 4; z <= Mth.floor(box.maxZ) >> 4; z++) {
                if (!level.hasChunk(x, z)) { return false; }
            }
        }
        return true;
    }

    private boolean clearLine(Vec3 start, Vec3 end, Entity context) {
        return level().clip(new ClipContext(start, end, ClipContext.Block.COLLIDER, ClipContext.Fluid.NONE, context)).getType() == HitResult.Type.MISS;
    }

    private void startSwing(boolean left) {
        if (left) { leftCooldown = ATTACK_COOLDOWN; entityData.set(LEFT_SWING, SWING_TICKS); }
        else { rightCooldown = ATTACK_COOLDOWN; entityData.set(RIGHT_SWING, SWING_TICKS); }
    }

    private void slash(Player pilot, boolean left, float damage) {
        startSwing(left);
        Vec3 start = position().add(0, 3.5, 0);
        Vec3 facing = Vec3.directionFromRotation(getXRot(), getYRot());
        level().playSound(null, start.x, start.y, start.z, SoundEvents.PLAYER_ATTACK_SWEEP, SoundSource.PLAYERS, 1.4f, left ? .6f : .8f);
        if (level() instanceof ServerLevel server) {
            Vec3 arc = start.add(facing.scale(2));
            server.sendParticles(ParticleTypes.SWEEP_ATTACK, arc.x, arc.y, arc.z, 2, .5, .6, .5, 0);
        }
        for (LivingEntity target : level().getEntitiesOfClass(LivingEntity.class, getBoundingBox().inflate(SWORD_REACH), entity -> entity.isAlive())) {
            if (target == pilot || target.isSpectator() || target.isPassengerOfSameVehicle(this) || pilot.isAlliedTo(target)
                    || target instanceof TamableAnimal tame && pilot.getUUID().equals(tame.getOwnerUUID())) { continue; }
            if (target instanceof Player other && !pilot.canHarmPlayer(other)) { continue; }
            AABB box = target.getBoundingBox();
            Vec3 point = new Vec3(Mth.clamp(start.x, box.minX, box.maxX), Mth.clamp(start.y, box.minY + .1, box.maxY - .1),
                Mth.clamp(start.z, box.minZ, box.maxZ));
            Vec3 offset = point.subtract(start);
            if (offset.lengthSqr() > SWORD_REACH * SWORD_REACH || offset.normalize().dot(facing) < .25 || !clearLine(start, point, pilot)) { continue; }
            if (target.hurt(damageSources().playerAttack(pilot), damage)) {
                Vec3 push = target.position().subtract(position());
                target.knockback(.6, -push.x, -push.z);
            }
        }
    }

    @Override public boolean hurt(DamageSource source, float amount) {
        if (!level().isClientSide && source.is(DamageTypeTags.BYPASSES_INVULNERABILITY) && amount >= MAX_HULL) {
            ejectPassengers(); discard(); return true;
        }
        if (level().isClientSide || getHullHealth() <= 0 || isInvulnerableTo(source) || !Float.isFinite(amount) || amount <= 0
                || source.is(DamageTypeTags.IS_FALL) || getPilot() != null && source.getEntity() == getPilot()) { return false; }
        if (source.getEntity() instanceof Player attacker && getPilot() != null && !attacker.canHarmPlayer(getPilot())) { return false; }
        if (hurtCooldown > 0 && !source.is(DamageTypeTags.BYPASSES_INVULNERABILITY)) { return false; }
        hurtCooldown = 8;
        float remaining = Math.max(0, getHullHealth() - amount);
        entityData.set(HULL, remaining);
        markHurt();
        level().playSound(null, blockPosition(), SoundEvents.IRON_GOLEM_HURT, SoundSource.PLAYERS, 1, .8f);
        if (remaining == 0) {
            ejectPassengers();
            if (level() instanceof ServerLevel server) {
                server.sendParticles(ParticleTypes.EXPLOSION, getX(), getY() + 2.5, getZ(), 2, .7, 1, .7, 0);
            }
            level().playSound(null, blockPosition(), SoundEvents.IRON_GOLEM_DEATH, SoundSource.PLAYERS, 1.2f, .6f);
            // A high-tier reward becomes a repairable wreck. It never produces another reward item here.
            entityData.set(FLYING, false);
        }
        return true;
    }

    @Override protected Vec3 getPassengerAttachmentPoint(Entity passenger, EntityDimensions dimensions, float partialTick) {
        return new Vec3(0, 3.4, 0);
    }
    @Override protected void positionRider(Entity passenger, MoveFunction callback) {
        super.positionRider(passenger, callback);
        passenger.resetFallDistance();
    }
    @Override protected void removePassenger(Entity passenger) {
        super.removePassenger(passenger);
        input = idleInput();
        lastInputTick = -100;
        if (!level().isClientSide && passenger instanceof Player player) {
            player.resetFallDistance();
            player.getPersistentData().putLong(EXIT_PROTECTION, level().getGameTime() + 6000);
            player.addEffect(new MobEffectInstance(MobEffects.SLOW_FALLING, 40, 0, false, false, true));
        }
    }

    @Override public Vec3 getDismountLocationForPassenger(LivingEntity passenger) {
        // Exit sideways at cockpit height; the temporary descent assist ends as soon as the pilot lands.
        for (double height : new double[]{2.4, 0, 5.1}) {
            for (int angle = 0; angle < 8; angle++) {
                Vec3 candidate = position().add(new Vec3(1.8, height, 0).yRot((getYRot() + angle * 45) * Mth.DEG_TO_RAD));
                AABB bounds = passenger.getDimensions(passenger.getPose()).makeBoundingBox(candidate);
                if (loadedAndWithinBounds(level(), bounds) && level().noCollision(passenger, bounds)
                        && !level().containsAnyLiquid(bounds)) { return candidate; }
            }
        }
        return position().add(0, 5.1, 0);
    }

    @Override public void lerpTo(double x, double y, double z, float yaw, float pitch, int steps) {
        lerpX = x; lerpY = y; lerpZ = z; lerpYaw = yaw; lerpPitch = pitch;
        lerpSteps = Math.max(1, Math.min(steps, 3));
    }

    @Override protected void readAdditionalSaveData(CompoundTag tag) {
        entityData.set(OWNER, tag.hasUUID("Owner") ? Optional.of(tag.getUUID("Owner")) : Optional.empty());
        float hull = tag.contains("Hull") ? tag.getFloat("Hull") : MAX_HULL;
        entityData.set(HULL, Float.isFinite(hull) ? Mth.clamp(hull, 0, MAX_HULL) : MAX_HULL);
        entityData.set(FLYING, tag.getBoolean("Flying"));
        input = idleInput(); lastInputTick = -100;
        setNoGravity(true);
    }
    @Override protected void addAdditionalSaveData(CompoundTag tag) {
        if (getOwnerUUID() != null) { tag.putUUID("Owner", getOwnerUUID()); }
        tag.putFloat("Hull", getHullHealth());
        tag.putBoolean("Flying", isFlying());
    }

    @SubscribeEvent public static void protectPilot(LivingIncomingDamageEvent event) {
        if (!event.getEntity().level().isClientSide && event.getEntity() instanceof Player player
                && player.getVehicle() instanceof MechSuitEntity mech
                && !event.getSource().is(DamageTypeTags.BYPASSES_INVULNERABILITY)) {
            mech.hurt(event.getSource(), event.getAmount());
            event.setCanceled(true);
        }
    }

    @SubscribeEvent public static void safeExitTick(PlayerTickEvent.Post event) {
        Player player = event.getEntity();
        if (player.level().isClientSide || !player.getPersistentData().contains(EXIT_PROTECTION)) { return; }
        if (player.onGround() || player.isInWaterOrBubble() || player.isPassenger() || !player.isAlive()
                || player.level().getGameTime() > player.getPersistentData().getLong(EXIT_PROTECTION)) {
            player.getPersistentData().remove(EXIT_PROTECTION);
            return;
        }
        player.resetFallDistance();
        if (player.tickCount % 20 == 0) { player.addEffect(new MobEffectInstance(MobEffects.SLOW_FALLING, 40, 0, false, false, true)); }
    }

    // Client input cancellation improves controls; these checks also cover hand-crafted vanilla packets.
    @SubscribeEvent public static void blockPilotAttack(AttackEntityEvent event) {
        if (event.getEntity().getVehicle() instanceof MechSuitEntity) { event.setCanceled(true); }
    }
    @SubscribeEvent public static void blockPilotMining(PlayerInteractEvent.LeftClickBlock event) {
        if (event.getEntity().getVehicle() instanceof MechSuitEntity) { event.setCanceled(true); }
    }
    @SubscribeEvent public static void blockPilotBreak(BlockEvent.BreakEvent event) {
        if (event.getPlayer().getVehicle() instanceof MechSuitEntity) { event.setCanceled(true); }
    }
    @SubscribeEvent public static void blockPilotUseBlock(PlayerInteractEvent.RightClickBlock event) {
        if (event.getEntity().getVehicle() instanceof MechSuitEntity) { event.setCanceled(true); event.setCancellationResult(InteractionResult.FAIL); }
    }
    @SubscribeEvent public static void blockPilotUseItem(PlayerInteractEvent.RightClickItem event) {
        if (event.getEntity().getVehicle() instanceof MechSuitEntity) { event.setCanceled(true); event.setCancellationResult(InteractionResult.FAIL); }
    }
    @SubscribeEvent public static void blockPilotUseEntity(PlayerInteractEvent.EntityInteract event) {
        if (event.getEntity().getVehicle() instanceof MechSuitEntity) { event.setCanceled(true); event.setCancellationResult(InteractionResult.FAIL); }
    }
    @SubscribeEvent public static void blockPilotUseEntityPart(PlayerInteractEvent.EntityInteractSpecific event) {
        if (event.getEntity().getVehicle() instanceof MechSuitEntity) { event.setCanceled(true); event.setCancellationResult(InteractionResult.FAIL); }
    }
}
