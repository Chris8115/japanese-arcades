package local.japanesearcades;

import java.security.GeneralSecurityException;
import java.security.MessageDigest;
import java.security.SecureRandom;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import javax.annotation.Nullable;
import javax.crypto.SecretKeyFactory;
import javax.crypto.spec.PBEKeySpec;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.HolderLookup;
import net.minecraft.core.NonNullList;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.Connection;
import net.minecraft.network.chat.Component;
import net.minecraft.network.protocol.game.ClientboundBlockEntityDataPacket;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.Container;
import net.minecraft.world.ContainerHelper;
import net.minecraft.world.SimpleContainer;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.BlockHitResult;
import net.minecraft.world.phys.HitResult;
import net.minecraft.world.phys.Vec3;

/** Exclusive, server-owned crane sessions. No Container/capability is exposed to automation. */
public final class ClawMachineBlockEntity extends BlockEntity {
    public static final int PRICE_SLOT = 0;
    public static final int REWARD_START = 1;
    public static final int PAYMENT_START = 10;
    public static final int INVENTORY_SIZE = 19;
    public static final int SESSION_TIMEOUT = 1200;
    public static final int HEARTBEAT_TIMEOUT = 60;
    public static final float CHUTE_X = 1;
    public static final float CHUTE_Z = -.3125F;
    public enum Phase { IDLE, AIMING, DESCENDING, GRABBING, RAISING, RETURNING, SLIPPING, DELIVERING }

    private static final SecureRandom PASSWORD_RANDOM = new SecureRandom();
    private final SimpleContainer inventory = new SimpleContainer(INVENTORY_SIZE) {
        @Override public void setChanged() { super.setChanged(); inventoryChanged(); }
    };
    private final ItemStack[] publicRewards = new ItemStack[9];
    private final Map<UUID, Attempt> attempts = new HashMap<>();
    @Nullable private UUID owner;
    private byte[] passwordSalt = new byte[0], passwordHash = new byte[0];
    private int passwordRevision;
    private int baseWinChance = 25, guaranteePlay = 5, playsSinceWin;
    @Nullable private UUID operator;
    private long operatorHeartbeat;
    @Nullable private UUID sessionPlayer, sessionId;
    private long sessionStarted, lastHeartbeat, lastMovement = Long.MIN_VALUE;
    private int lastSequence = -1;
    private Phase phase = Phase.IDLE;
    private int phaseTicks;
    private float aimX, aimZ, targetX, targetZ;
    private int sourceSlot = -1, slipSlot = -1, slipReturnTick;
    private float slipStartX, slipStartZ;
    private boolean plannedWin;
    private ItemStack held = ItemStack.EMPTY;
    private long nextDeliveryAttempt;
    private boolean suppressUpdates, deliveryAttempt, breakPending, inventoryDrained;
    // Retain inventory invalidation until the chunk broadcaster builds its next packet.
    private boolean fullPublicUpdate = true;
    private ItemStack publicPrice = ItemStack.EMPTY, publicHeld = ItemStack.EMPTY;
    private float publicX, publicZ = CHUTE_Z, publicY, publicGrip, publicHeldX, publicHeldZ, publicHeldY;

    public ClawMachineBlockEntity(BlockPos pos, BlockState state) {
        super(JapaneseArcades.CLAW_MACHINE_ENTITY.get(), pos, state);
        Arrays.fill(publicRewards, ItemStack.EMPTY);
    }

    public void assignOwner(ServerPlayer player) {
        if (owner == null) { owner = player.getUUID(); setChanged(); }
    }
    public boolean isOwnerOrCreative(Player player) { return player.isCreative() || player.getUUID().equals(owner); }
    public boolean hasPassword() { return passwordSalt.length == 16 && passwordHash.length == 32; }
    public int passwordRevision() { return passwordRevision; }
    public int getBaseWinChance() { return baseWinChance; }
    public int getGuaranteePlay() { return guaranteePlay; }
    public int getPlaysSinceWin() { return playsSinceWin; }
    public float getCurrentWinChance() {
        if (guaranteePlay == 0) { return baseWinChance; }
        if (guaranteePlay == 1) { return 100; }
        return Math.min(100, baseWinChance + (100F - baseWinChance) * playsSinceWin / (guaranteePlay - 1));
    }
    public Phase getPhase() { return phase; }
    public int getPhaseTicks() { return phaseTicks; }
    @Nullable public UUID getSessionId() { return sessionId; }
    public boolean hasSession(Player player) { return sessionId != null && player.getUUID().equals(sessionPlayer); }
    public boolean isBusy() { return phase != Phase.IDLE; }
    public boolean isPaid() { return phase.ordinal() >= Phase.DESCENDING.ordinal(); }
    public Container operatorInventory() { return inventory; }

    public boolean canReach(Player player) {
        if (level == null || isRemoved() || inventoryDrained || player.level() != level || !player.isAlive()
            || player.isSpectator() || level.getBlockEntity(worldPosition) != this) { return false; }
        Direction facing = getBlockState().getValue(ClawMachineBlock.FACING);
        for (int y = 0; y < 3; y++) {
            for (int z = 0; z < 2; z++) {
                for (int x = 0; x < 3; x++) {
                    BlockPos part = BlockPos.containing(ClawMachineBlock.localToWorld(worldPosition, facing, x * 16 + 8, y * 16 + 8, z * 16 + 8));
                    if (player.canInteractWithBlock(part, 0)) { return true; }
                }
            }
        }
        return false;
    }

    public boolean acquireOperator(ServerPlayer player) {
        if (!canReach(player)) { return false; }
        if (phase == Phase.AIMING && isOwnerOrCreative(player)) { finishSession(); }
        if (phase != Phase.IDLE || (operator != null && !operator.equals(player.getUUID()))) { tell(player, "busy"); return false; }
        operator = player.getUUID(); operatorHeartbeat = level.getGameTime();
        return true;
    }
    public void releaseOperator(Player player) { if (player.getUUID().equals(operator)) { operator = null; } }
    public boolean canOperate(Player player) {
        boolean allowed = phase == Phase.IDLE && player.getUUID().equals(operator) && canReach(player);
        if (allowed) { operatorHeartbeat = level.getGameTime(); }
        return allowed;
    }

    public static boolean validPassword(String value) { return GachaponBlockEntity.validPassword(value); }
    public int authenticate(ServerPlayer player, String password) {
        if (!canReach(player)) { return 6; }
        long now = level.getGameTime();
        Attempt previous = attempts.get(player.getUUID());
        if (previous != null && previous.afterTick > now) { return 2; }
        if (!hasPassword() || !validPassword(password) || !MessageDigest.isEqual(passwordHash, derive(password, passwordSalt))) {
            int failures = previous == null ? 1 : Math.min(6, previous.failures + 1);
            if (attempts.size() >= 128) { attempts.entrySet().removeIf(entry -> entry.getValue().afterTick <= now); }
            if (attempts.size() >= 128) { return 2; }
            attempts.put(player.getUUID(), new Attempt(now + 40L * failures, failures));
            return 1;
        }
        attempts.remove(player.getUUID());
        return 0;
    }
    public boolean setPassword(Player player, String password) {
        if (!canReach(player) || !isOwnerOrCreative(player) || !validPassword(password) || isPaid()) { return false; }
        if (phase == Phase.AIMING) { finishSession(); }
        byte[] salt = new byte[16]; PASSWORD_RANDOM.nextBytes(salt);
        passwordSalt = salt; passwordHash = derive(password, salt); passwordRevision++;
        attempts.clear(); setChanged();
        return true;
    }
    private static byte[] derive(String password, byte[] salt) {
        PBEKeySpec specification = new PBEKeySpec(password.toCharArray(), salt, 120_000, 256);
        try { return SecretKeyFactory.getInstance("PBKDF2WithHmacSHA256").generateSecret(specification).getEncoded(); }
        catch (GeneralSecurityException exception) { throw new IllegalStateException("Password hashing unavailable", exception); }
        finally { specification.clearPassword(); }
    }
    public boolean setWinSettings(Player player, int base, int guarantee) {
        if (!canOperate(player) || base < 0 || base > 100 || guarantee < 0 || guarantee > 1000) { return false; }
        baseWinChance = base; guaranteePlay = guarantee; setChanged();
        return true;
    }

    public boolean startSession(ServerPlayer player) {
        if (!canReach(player) || !isLookingAt(player)) { return false; }
        if (phase != Phase.IDLE || operator != null) { tell(player, "busy"); return false; }
        if (!hasPassword()) { tell(player, "not_configured"); return false; }
        if (inventory.getItem(PRICE_SLOT).isEmpty()) { tell(player, "no_price"); return false; }
        if (!hasRewards()) { tell(player, "out_of_stock"); return false; }
        sessionPlayer = player.getUUID(); sessionId = UUID.randomUUID();
        sessionStarted = lastHeartbeat = level.getGameTime(); lastMovement = Long.MIN_VALUE; lastSequence = -1;
        aimX = aimZ = .5F;
        setPhase(Phase.AIMING);
        return true;
    }
    private boolean isLookingAt(ServerPlayer player) {
        HitResult hit = player.pick(player.blockInteractionRange(), 1, false);
        return hit instanceof BlockHitResult blockHit && hit.getType() == HitResult.Type.BLOCK
            && ClawMachineBlock.machineAt(level, blockHit.getBlockPos()) == this;
    }
    public boolean handleAction(ServerPlayer player, UUID expectedSession, int sequence, int action) {
        if (!hasSession(player) || !sessionId.equals(expectedSession) || sequence <= lastSequence
            || action < 0 || action > 6 || !canReach(player)) { return false; }
        lastSequence = sequence;
        lastHeartbeat = level.getGameTime();
        if (action == 6) { return true; }
        if (action == 5) { cancelSession(player); return true; }
        if (phase != Phase.AIMING) { return false; }
        if (action == 4) { return drop(player); }
        if (lastMovement == level.getGameTime()) { return false; }
        lastMovement = level.getGameTime();
        aimX = Math.clamp(aimX + (action == 0 ? .08F : action == 1 ? -.08F : 0), 0, 1);
        aimZ = Math.clamp(aimZ + (action == 3 ? -.08F : action == 2 ? .08F : 0), 0, 1);
        sendAnimationUpdate();
        return true;
    }
    public void cancelSession(Player player) {
        if (phase == Phase.AIMING && hasSession(player)) { finishSession(); }
    }
    public int getSelectedSlot() { return (2 - Math.round(aimZ * 2)) * 3 + (2 - Math.round(aimX * 2)); }

    /** No callbacks run between validating payment, reserving stock and writing the committed state. */
    public boolean drop(ServerPlayer player) {
        if (phase != Phase.AIMING || !hasSession(player) || !canReach(player)) { return false; }
        int selected = getSelectedSlot();
        if (inventory.getItem(REWARD_START + selected).isEmpty()) { tell(player, "empty_cell"); return false; }
        ItemStack price = inventory.getItem(PRICE_SLOT).copy();
        if (price.isEmpty()) { tell(player, "no_price"); return false; }
        if (currencyCount(player, price) < price.getCount()) { tell(player, "insufficient_currency"); return false; }
        List<ItemStack> deposited = simulateDeposit(price);
        if (deposited == null) { tell(player, "payment_full"); return false; }
        float chance = getCurrentWinChance();
        suppressUpdates = true;
        try {
            int remaining = price.getCount();
            for (int slot = 0; slot < player.getInventory().getContainerSize() && remaining > 0; slot++) {
                ItemStack stack = player.getInventory().getItem(slot);
                if (currencySlot(slot) && ItemStack.isSameItemSameComponents(stack, price)) {
                    int count = Math.min(remaining, stack.getCount()); stack.shrink(count); remaining -= count;
                }
            }
            for (int slot = 0; slot < 9; slot++) { inventory.setItem(PAYMENT_START + slot, deposited.get(slot)); }
            sourceSlot = selected;
            held = inventory.removeItemNoUpdate(REWARD_START + selected);
            plannedWin = level.random.nextFloat() * 100 < chance;
            playsSinceWin = Math.min(1_000_000, playsSinceWin + 1);
            targetX = slotX(selected); targetZ = slotZ(selected);
            planSlip();
            nextDeliveryAttempt = 0;
            phase = Phase.DESCENDING; phaseTicks = 0;
        } finally { suppressUpdates = false; }
        player.getInventory().setChanged(); player.inventoryMenu.broadcastChanges();
        setChanged(); sendPublicUpdate();
        level.playSound(null, worldPosition, SoundEvents.TRIPWIRE_CLICK_ON, SoundSource.BLOCKS, .5F, .8F);
        return true;
    }

    private void planSlip() {
        slipSlot = sourceSlot; slipReturnTick = 2;
        float dx = CHUTE_X - targetX, dz = CHUTE_Z - targetZ, lengthSquared = dx * dx + dz * dz;
        float best = Float.MAX_VALUE;
        for (int slot = 0; slot < 9; slot++) {
            if (slot == sourceSlot || !inventory.getItem(REWARD_START + slot).isEmpty()) { continue; }
            float progress = ((slotX(slot) - targetX) * dx + (slotZ(slot) - targetZ) * dz) / lengthSquared;
            if (progress <= .1F || progress >= .95F) { continue; }
            float offsetX = targetX + dx * progress - slotX(slot), offsetZ = targetZ + dz * progress - slotZ(slot);
            float distance = offsetX * offsetX + offsetZ * offsetZ;
            if (distance <= .07F && distance < best) {
                best = distance; slipSlot = slot;
                slipReturnTick = Math.clamp(Math.round(progress * phaseDuration(Phase.RETURNING)), 2, 33);
            }
        }
    }
    private boolean hasRewards() {
        for (int slot = REWARD_START; slot < PAYMENT_START; slot++) { if (!inventory.getItem(slot).isEmpty()) { return true; } }
        return false;
    }
    private static boolean currencySlot(int slot) { return slot < 36 || slot == 40; }
    private static int currencyCount(ServerPlayer player, ItemStack price) {
        int count = 0;
        for (int slot = 0; slot < player.getInventory().getContainerSize(); slot++) {
            ItemStack stack = player.getInventory().getItem(slot);
            if (currencySlot(slot) && ItemStack.isSameItemSameComponents(stack, price)) { count += stack.getCount(); }
        }
        return count;
    }
    @Nullable private List<ItemStack> simulateDeposit(ItemStack price) {
        List<ItemStack> result = new ArrayList<>(9);
        for (int slot = PAYMENT_START; slot < INVENTORY_SIZE; slot++) { result.add(inventory.getItem(slot).copy()); }
        int remaining = price.getCount();
        for (int pass = 0; pass < 2; pass++) {
            for (int slot = 0; slot < result.size() && remaining > 0; slot++) {
                ItemStack stack = result.get(slot);
                if (pass == 0 && !stack.isEmpty() && ItemStack.isSameItemSameComponents(stack, price)) {
                    int count = Math.min(remaining, Math.max(0, Math.min(64, stack.getMaxStackSize()) - stack.getCount()));
                    stack.grow(count); remaining -= count;
                } else if (pass == 1 && stack.isEmpty()) {
                    int count = Math.min(remaining, Math.min(64, price.getMaxStackSize()));
                    result.set(slot, price.copyWithCount(count)); remaining -= count;
                }
            }
        }
        return remaining == 0 ? result : null;
    }

    public static void serverTick(Level level, BlockPos pos, BlockState state, ClawMachineBlockEntity machine) {
        if (machine.inventoryDrained) { return; }
        long now = level.getGameTime();
        if (machine.operator != null) {
            Player player = level.getPlayerByUUID(machine.operator);
            if (player == null || !machine.canReach(player) || now - machine.operatorHeartbeat > HEARTBEAT_TIMEOUT
                || player instanceof ServerPlayer serverPlayer && serverPlayer.hasDisconnected()) { machine.operator = null; }
        }
        if (machine.phase == Phase.AIMING) {
            Player player = machine.sessionPlayer == null ? null : level.getPlayerByUUID(machine.sessionPlayer);
            if (!(player instanceof ServerPlayer serverPlayer) || serverPlayer.hasDisconnected() || !machine.canReach(player)
                || now - machine.lastHeartbeat > HEARTBEAT_TIMEOUT || now - machine.sessionStarted >= SESSION_TIMEOUT) {
                machine.finishSession();
            }
            return;
        }
        if (!machine.isPaid()) { return; }
        // A vetoed payout stays in its final pose until its existing retry deadline.
        if (machine.phase == Phase.DELIVERING && machine.phaseTicks >= phaseDuration(Phase.DELIVERING)) {
            if (now >= machine.nextDeliveryAttempt) { machine.deliver(); }
            return;
        }
        machine.phaseTicks++;
        switch (machine.phase) {
            case DESCENDING -> { if (machine.phaseTicks >= phaseDuration(machine.phase)) { machine.setPhase(Phase.GRABBING); } }
            case GRABBING -> { if (machine.phaseTicks >= phaseDuration(machine.phase)) { machine.setPhase(Phase.RAISING); } }
            case RAISING -> { if (machine.phaseTicks >= phaseDuration(machine.phase)) { machine.setPhase(Phase.RETURNING); } }
            case RETURNING -> {
                if (!machine.plannedWin && !machine.held.isEmpty() && machine.phaseTicks >= machine.slipReturnTick) {
                    machine.slipStartX = machine.getClawX(); machine.slipStartZ = machine.getClawZ();
                    machine.setPhase(Phase.SLIPPING);
                } else if (machine.phaseTicks >= phaseDuration(machine.phase)) {
                    if (machine.held.isEmpty()) { machine.finishSession(); }
                    else { machine.setPhase(Phase.DELIVERING); }
                }
            }
            case SLIPPING -> { if (machine.phaseTicks >= phaseDuration(machine.phase)) { machine.restoreSlippedPrize(); } }
            case DELIVERING -> {
                if (machine.phaseTicks >= phaseDuration(machine.phase) && now >= machine.nextDeliveryAttempt) { machine.deliver(); }
                machine.phaseTicks = Math.min(machine.phaseTicks, phaseDuration(Phase.DELIVERING));
            }
            default -> { }
        }
        machine.setChanged();
        if (machine.phaseTicks % 2 == 0) { machine.sendAnimationUpdate(); }
    }

    private void restoreSlippedPrize() {
        int destination = slipSlot;
        if (destination < 0 || !inventory.getItem(REWARD_START + destination).isEmpty()) { destination = sourceSlot; }
        if (destination < 0 || !inventory.getItem(REWARD_START + destination).isEmpty()) {
            // Only external inventory tampering can fill the reserved source. Keep the prize until room exists.
            destination = -1;
            for (int slot = 0; slot < 9; slot++) { if (inventory.getItem(REWARD_START + slot).isEmpty()) { destination = slot; break; } }
            if (destination < 0) { phaseTicks = phaseDuration(Phase.SLIPPING); return; }
        }
        suppressUpdates = true;
        try { inventory.setItem(REWARD_START + destination, held); held = ItemStack.EMPTY; }
        finally { suppressUpdates = false; }
        phase = Phase.RETURNING; phaseTicks = slipReturnTick;
        setChanged(); sendPublicUpdate();
        level.playSound(null, worldPosition, SoundEvents.DISPENSER_FAIL, SoundSource.BLOCKS, .4F, .8F);
        if (sessionPlayer != null && level.getPlayerByUUID(sessionPlayer) instanceof ServerPlayer player) { tell(player, "slipped"); }
    }

    private void deliver() {
        if (!(level instanceof ServerLevel serverLevel) || deliveryAttempt || held.isEmpty()) { return; }
        deliveryAttempt = true;
        try {
            if (ClawMachineRecovery.spawn(serverLevel, held, chutePosition(), sessionPlayer)) {
                held = ItemStack.EMPTY; playsSinceWin = 0;
                level.playSound(null, worldPosition, SoundEvents.DISPENSER_DISPENSE, SoundSource.BLOCKS, .65F, 1.15F);
                if (sessionPlayer != null && level.getPlayerByUUID(sessionPlayer) instanceof ServerPlayer player) { tell(player, "won"); }
                finishSession();
            } else {
                nextDeliveryAttempt = level.getGameTime() + 100;
                setChanged();
            }
        } finally {
            deliveryAttempt = false;
            if (breakPending) { breakPending = false; dropInventory(); }
        }
    }

    private Vec3 chutePosition() {
        // Clear the front collider by more than the dropped item's 1/8-block half-width.
        return ClawMachineBlock.localToWorld(worldPosition, getBlockState().getValue(ClawMachineBlock.FACING), 40, 7, -4);
    }
    private void setPhase(Phase value) { phase = value; phaseTicks = 0; setChanged(); sendPublicUpdate(); }
    private void finishSession() {
        phase = Phase.IDLE; phaseTicks = 0; sessionPlayer = null; sessionId = null; lastSequence = -1;
        sourceSlot = slipSlot = -1; plannedWin = false;
        setChanged(); sendPublicUpdate();
    }
    public static int phaseDuration(Phase value) {
        return switch (value) {
            case DESCENDING -> 30;
            case GRABBING -> 12;
            case RAISING -> 24;
            case RETURNING -> 36;
            case SLIPPING -> 16;
            case DELIVERING -> 20;
            default -> 0;
        };
    }
    private float progress() { return Math.clamp(phaseTicks / (float)Math.max(1, phaseDuration(phase)), 0, 1); }
    private static float lerp(float from, float to, float progress) { return from + (to - from) * progress; }
    public static float slotX(int slot) { return (2 - slot % 3) * .5F; }
    public static float slotZ(int slot) { return (2 - slot / 3) * .5F; }
    private boolean client() { return level != null && level.isClientSide; }
    public float getClawX() {
        if (client()) { return publicX; }
        return switch (phase) {
            case AIMING -> aimX;
            case DESCENDING, GRABBING, RAISING -> targetX;
            case RETURNING -> lerp(targetX, CHUTE_X, progress());
            case SLIPPING -> slipStartX;
            default -> CHUTE_X;
        };
    }
    public float getClawZ() {
        if (client()) { return publicZ; }
        return switch (phase) {
            case AIMING -> aimZ;
            case DESCENDING, GRABBING, RAISING -> targetZ;
            case RETURNING -> lerp(targetZ, CHUTE_Z, progress());
            case SLIPPING -> slipStartZ;
            default -> CHUTE_Z;
        };
    }
    public float getClawY() {
        if (client()) { return publicY; }
        return switch (phase) { case DESCENDING -> progress(); case GRABBING -> 1; case RAISING -> 1 - progress(); default -> 0; };
    }
    public float getGrip() {
        if (client()) { return publicGrip; }
        return switch (phase) {
            case GRABBING -> progress();
            case RAISING -> 1;
            case RETURNING -> held.isEmpty() ? 0 : 1;
            case SLIPPING, DELIVERING -> 1 - progress();
            default -> 0;
        };
    }
    public float getHeldX() { return client() ? publicHeldX : phase == Phase.SLIPPING ? lerp(slipStartX, slotX(slipSlot), progress()) : getClawX(); }
    public float getHeldZ() { return client() ? publicHeldZ : phase == Phase.SLIPPING ? lerp(slipStartZ, slotZ(slipSlot), progress()) : getClawZ(); }
    public float getHeldY() {
        if (client()) { return publicHeldY; }
        return phase == Phase.SLIPPING ? progress() : phase == Phase.DELIVERING ? progress() * 1.78125F : getClawY();
    }
    public ItemStack getPrice() { return (client() ? publicPrice : inventory.getItem(PRICE_SLOT)).copy(); }
    public ItemStack getRewardDisplay(int slot) {
        if (slot < 0 || slot >= 9) { return ItemStack.EMPTY; }
        if (client()) { return publicRewards[slot].copy(); }
        if (phase == Phase.DESCENDING && slot == sourceSlot) { return held.copy(); }
        return inventory.getItem(REWARD_START + slot).copy();
    }
    public ItemStack getHeldDisplay() {
        return client() ? publicHeld.copy() : phase.ordinal() >= Phase.GRABBING.ordinal() ? held.copy() : ItemStack.EMPTY;
    }

    public void dropInventory() {
        if (!(level instanceof ServerLevel serverLevel) || inventoryDrained) { return; }
        if (deliveryAttempt) { breakPending = true; return; }
        inventoryDrained = true; operator = null;
        List<ItemStack> drops = new ArrayList<>(INVENTORY_SIZE + 1);
        suppressUpdates = true;
        try {
            for (int slot = 0; slot < INVENTORY_SIZE; slot++) { drops.add(inventory.removeItemNoUpdate(slot)); }
            drops.add(held); held = ItemStack.EMPTY;
        } finally { suppressUpdates = false; }
        finishSession();
        ClawMachineRecovery.enqueue(serverLevel, drops, chutePosition(), null);
        ClawMachineRecovery.retry(serverLevel);
    }
    private void inventoryChanged() {
        setChanged();
        if (!suppressUpdates) {
            if (phase == Phase.AIMING) { finishSession(); }
            sendPublicUpdate();
        }
    }
    private void sendPublicUpdate() {
        fullPublicUpdate = true;
        sendAnimationUpdate();
    }
    private void sendAnimationUpdate() {
        if (level != null && !level.isClientSide && !isRemoved()) { level.sendBlockUpdated(worldPosition, getBlockState(), getBlockState(), 2); }
    }
    private static void tell(Player player, String key) { player.displayClientMessage(Component.translatable("message.japanesearcades.claw_machine." + key), true); }

    @Override
    protected void saveAdditional(CompoundTag tag, HolderLookup.Provider registries) {
        super.saveAdditional(tag, registries);
        if (owner != null) { tag.putUUID("Owner", owner); }
        tag.putByteArray("PasswordSalt", passwordSalt); tag.putByteArray("PasswordHash", passwordHash);
        tag.putInt("BaseWinChance", baseWinChance); tag.putInt("GuaranteePlay", guaranteePlay); tag.putInt("PlaysSinceWin", playsSinceWin);
        NonNullList<ItemStack> items = NonNullList.withSize(INVENTORY_SIZE, ItemStack.EMPTY);
        for (int slot = 0; slot < INVENTORY_SIZE; slot++) { items.set(slot, inventory.getItem(slot)); }
        ContainerHelper.saveAllItems(tag, items, registries);
        if (isPaid()) {
            tag.putInt("PaidPhase", phase.ordinal()); tag.putInt("PhaseTicks", phaseTicks);
            if (!held.isEmpty()) { tag.put("HeldPrize", held.save(registries)); }
            if (sessionPlayer != null) { tag.putUUID("Buyer", sessionPlayer); }
            tag.putBoolean("PlannedWin", plannedWin); tag.putInt("SourceSlot", sourceSlot); tag.putInt("SlipSlot", slipSlot);
            tag.putInt("SlipReturnTick", slipReturnTick); tag.putFloat("TargetX", targetX); tag.putFloat("TargetZ", targetZ);
            tag.putFloat("SlipStartX", slipStartX); tag.putFloat("SlipStartZ", slipStartZ);
        }
    }

    @Override
    protected void loadAdditional(CompoundTag tag, HolderLookup.Provider registries) {
        super.loadAdditional(tag, registries);
        owner = tag.hasUUID("Owner") ? tag.getUUID("Owner") : null;
        passwordSalt = tag.getByteArray("PasswordSalt"); passwordHash = tag.getByteArray("PasswordHash"); passwordRevision++;
        baseWinChance = tag.contains("BaseWinChance") ? Math.clamp(tag.getInt("BaseWinChance"), 0, 100) : 25;
        guaranteePlay = tag.contains("GuaranteePlay") ? Math.clamp(tag.getInt("GuaranteePlay"), 0, 1000) : 5;
        playsSinceWin = Math.clamp(tag.getInt("PlaysSinceWin"), 0, 1_000_000);
        NonNullList<ItemStack> items = NonNullList.withSize(INVENTORY_SIZE, ItemStack.EMPTY);
        ContainerHelper.loadAllItems(tag, items, registries);
        suppressUpdates = true;
        try { for (int slot = 0; slot < INVENTORY_SIZE; slot++) { inventory.setItem(slot, items.get(slot)); } }
        finally { suppressUpdates = false; }
        operator = null; sessionId = null; sessionPlayer = null; phase = Phase.IDLE; phaseTicks = 0;
        held = ItemStack.EMPTY; nextDeliveryAttempt = 0; inventoryDrained = deliveryAttempt = breakPending = false;
        fullPublicUpdate = true;
        if (tag.contains("PaidPhase")) {
            phase = Phase.values()[Math.clamp(tag.getInt("PaidPhase"), Phase.DESCENDING.ordinal(), Phase.DELIVERING.ordinal())];
            phaseTicks = Math.clamp(tag.getInt("PhaseTicks"), 0, phaseDuration(phase));
            held = tag.contains("HeldPrize") ? ItemStack.parse(registries, tag.getCompound("HeldPrize")).orElse(ItemStack.EMPTY) : ItemStack.EMPTY;
            sessionPlayer = tag.hasUUID("Buyer") ? tag.getUUID("Buyer") : null;
            plannedWin = tag.getBoolean("PlannedWin"); sourceSlot = Math.clamp(tag.getInt("SourceSlot"), 0, 8);
            slipSlot = Math.clamp(tag.getInt("SlipSlot"), 0, 8); slipReturnTick = Math.clamp(tag.getInt("SlipReturnTick"), 2, 33);
            targetX = slotX(sourceSlot); targetZ = slotZ(sourceSlot);
            slipStartX = tag.getFloat("SlipStartX"); slipStartZ = tag.getFloat("SlipStartZ");
            if (held.isEmpty() && phase != Phase.RETURNING) { phase = Phase.IDLE; phaseTicks = 0; }
        }
    }

    /** Only visible stock/price and pose are public. The payout result is never sent ahead of its animation. */
    @Override
    public CompoundTag getUpdateTag(HolderLookup.Provider registries) {
        CompoundTag tag = new CompoundTag();
        ItemStack price = getPrice(), shownHeld = getHeldDisplay();
        if (!price.isEmpty()) { tag.put("Price", price.save(registries)); }
        if (!shownHeld.isEmpty()) { tag.put("Held", shownHeld.save(registries)); }
        for (int slot = 0; slot < 9; slot++) {
            ItemStack reward = getRewardDisplay(slot);
            if (!reward.isEmpty()) { tag.put("Preview" + slot, reward.save(registries)); }
        }
        writeAnimation(tag);
        return tag;
    }
    private void writeAnimation(CompoundTag tag) {
        tag.putInt("Phase", phase.ordinal()); tag.putInt("PhaseTicks", phaseTicks);
        tag.putFloat("X", getClawX()); tag.putFloat("Z", getClawZ()); tag.putFloat("Y", getClawY()); tag.putFloat("Grip", getGrip());
        tag.putFloat("HeldX", getHeldX()); tag.putFloat("HeldZ", getHeldZ()); tag.putFloat("HeldY", getHeldY());
    }
    @Override public ClientboundBlockEntityDataPacket getUpdatePacket() {
        return ClientboundBlockEntityDataPacket.create(this, (entity, registries) -> {
            if (fullPublicUpdate) {
                fullPublicUpdate = false;
                return getUpdateTag(registries);
            }
            // Chunk/initial tracking still uses the complete getUpdateTag snapshot above.
            CompoundTag tag = new CompoundTag();
            tag.putBoolean("AnimationOnly", true);
            writeAnimation(tag);
            return tag;
        });
    }
    @Override
    public void handleUpdateTag(CompoundTag tag, HolderLookup.Provider registries) {
        if (!tag.getBoolean("AnimationOnly")) {
            publicPrice = tag.contains("Price") ? ItemStack.parse(registries, tag.getCompound("Price")).orElse(ItemStack.EMPTY) : ItemStack.EMPTY;
            publicHeld = tag.contains("Held") ? ItemStack.parse(registries, tag.getCompound("Held")).orElse(ItemStack.EMPTY) : ItemStack.EMPTY;
            for (int slot = 0; slot < 9; slot++) {
                publicRewards[slot] = tag.contains("Preview" + slot) ? ItemStack.parse(registries, tag.getCompound("Preview" + slot)).orElse(ItemStack.EMPTY) : ItemStack.EMPTY;
            }
        }
        phase = Phase.values()[Math.clamp(tag.getInt("Phase"), 0, Phase.values().length - 1)]; phaseTicks = Math.max(0, tag.getInt("PhaseTicks"));
        publicX = tag.getFloat("X"); publicZ = tag.getFloat("Z"); publicY = tag.getFloat("Y"); publicGrip = tag.getFloat("Grip");
        publicHeldX = tag.getFloat("HeldX"); publicHeldZ = tag.getFloat("HeldZ"); publicHeldY = tag.getFloat("HeldY");
    }
    @Override public void onDataPacket(Connection connection, ClientboundBlockEntityDataPacket packet, HolderLookup.Provider registries) {
        handleUpdateTag(packet.getTag(), registries);
    }
    private record Attempt(long afterTick, int failures) {}
}
