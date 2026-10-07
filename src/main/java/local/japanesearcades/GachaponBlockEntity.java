package local.japanesearcades;

import java.security.GeneralSecurityException;
import java.security.MessageDigest;
import java.security.SecureRandom;
import java.util.ArrayList;
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
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.Container;
import net.minecraft.world.ContainerHelper;
import net.minecraft.world.Containers;
import net.minecraft.world.SimpleContainer;
import net.minecraft.world.SimpleMenuProvider;
import net.minecraft.world.entity.item.ItemEntity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.BlockHitResult;
import net.minecraft.world.phys.HitResult;
import net.minecraft.world.phys.Vec3;

/** Server-owned stock and transactions; deliberately not a Container, so hoppers cannot bypass access. */
public final class GachaponBlockEntity extends BlockEntity {
    public static final int PRICE_SLOT = 0;
    public static final int REWARD_START = 1;
    public static final int PAYMENT_START = 10;
    public static final int INVENTORY_SIZE = 19;
    public static final int CRANK_DURATION = 40;
    public static final int CRANK_RESET_DELAY = 100;
    private static final SecureRandom PASSWORD_RANDOM = new SecureRandom();
    private final SimpleContainer inventory = new SimpleContainer(INVENTORY_SIZE) {
        @Override public int getMaxStackSize() { return 64; }
        @Override public void setChanged() { super.setChanged(); inventoryChanged(); }
    };
    private final ItemStack[] publicRewards = new ItemStack[9];
    private final Map<UUID, Attempt> attempts = new HashMap<>();
    private final Map<UUID, Long> awaitingRelease = new HashMap<>();
    @Nullable private UUID owner;
    private byte[] passwordSalt = new byte[0];
    private byte[] passwordHash = new byte[0];
    private int passwordRevision;
    private int dispenseAmount = 1;
    private ItemStack publicPrice = ItemStack.EMPTY;
    @Nullable private UUID crankingPlayer;
    private long lastHeartbeat;
    private long pausedSince = -1;
    private boolean holdingCrank;
    private boolean crankActive;
    private int crankTicks;
    private boolean suppressUpdates;

    public GachaponBlockEntity(BlockPos pos, BlockState state) {
        super(JapaneseArcades.GACHAPON_ENTITY.get(), pos, state);
        java.util.Arrays.fill(publicRewards, ItemStack.EMPTY);
    }

    public void assignOwner(ServerPlayer player) {
        if (owner == null) { owner = player.getUUID(); setChanged(); }
    }

    public boolean isOwnerOrCreative(Player player) { return player.isCreative() || player.getUUID().equals(owner); }
    public boolean hasPassword() { return passwordSalt.length == 16 && passwordHash.length == 32; }
    public int getDispenseAmount() { return dispenseAmount; }
    public int getCrankTicks() { return crankTicks; }
    public boolean isCranking() { return crankActive; }
    boolean hasPendingCrank() { return crankingPlayer != null; }
    public ItemStack getPrice() { return (level != null && level.isClientSide ? publicPrice : inventory.getItem(PRICE_SLOT)).copy(); }
    public ItemStack getPriceDisplay() { return getPrice(); }
    public ItemStack getRewardDisplay(int slot) {
        if (slot < 0 || slot >= 9) { return ItemStack.EMPTY; }
        return level != null && level.isClientSide ? publicRewards[slot].copy() : inventory.getItem(REWARD_START + slot).copyWithCount(1);
    }
    Container operatorInventory() { return inventory; }
    int passwordRevision() { return passwordRevision; }

    public boolean canReach(Player player) {
        return level != null && !isRemoved() && player.level() == level && player.isAlive() && !player.isSpectator()
            && level.getBlockEntity(worldPosition) == this && player.canInteractWithBlock(worldPosition, 0);
    }

    public void openOperatorAccess(ServerPlayer player) {
        if (!canReach(player)) { return; }
        if (isOwnerOrCreative(player)) { openOperator(player, false); }
        else { openAccess(player, false); }
    }

    public void openAccess(ServerPlayer player, boolean setup) {
        if (!canReach(player)) { return; }
        boolean initialSetup = setup && isOwnerOrCreative(player) && !hasPassword();
        player.openMenu(new SimpleMenuProvider((id, inv, viewer) -> new GachaponAccessMenu(id, inv, this, initialSetup),
            Component.translatable(initialSetup ? "menu.japanesearcades.gachapon.setup" : "menu.japanesearcades.gachapon.access")),
            buffer -> buffer.writeBlockPos(worldPosition).writeBoolean(initialSetup));
    }

    void openOperator(ServerPlayer player, boolean authenticated) {
        if (!canReach(player) || (!authenticated && !isOwnerOrCreative(player))) { return; }
        cancelCrank();
        player.openMenu(new SimpleMenuProvider((id, inv, viewer) -> new GachaponMenu(id, inv, this, authenticated),
            Component.translatable("menu.japanesearcades.gachapon")),
            buffer -> buffer.writeBlockPos(worldPosition).writeBoolean(isOwnerOrCreative(player)));
    }

    public static boolean validPassword(String password) {
        return password != null && password.length() >= 4 && password.length() <= 32
            && !password.isBlank() && password.chars().noneMatch(Character::isISOControl);
    }

    /** Returns GUI status (zero means authenticated). A password is never put in a menu data slot. */
    int authenticate(ServerPlayer player, String password) {
        if (!canReach(player)) { return 6; }
        long now = level.getGameTime();
        Attempt previous = attempts.get(player.getUUID());
        if (previous != null && previous.afterTick > now) { return 2; }
        if (!hasPassword() || !validPassword(password)
                || !MessageDigest.isEqual(passwordHash, derive(password, passwordSalt))) {
            int failures = previous == null ? 1 : Math.min(6, previous.failures + 1);
            if (attempts.size() >= 128) { attempts.entrySet().removeIf(entry -> entry.getValue().afterTick <= now); }
            if (attempts.size() >= 128) { return 2; }
            attempts.put(player.getUUID(), new Attempt(now + 40L * failures, failures));
            return 1;
        }
        attempts.remove(player.getUUID());
        return 0;
    }

    boolean setPassword(Player player, String password) {
        if (!isOwnerOrCreative(player) || !validPassword(password)) { return false; }
        byte[] salt = new byte[16];
        PASSWORD_RANDOM.nextBytes(salt);
        byte[] hash = derive(password, salt);
        passwordSalt = salt;
        passwordHash = hash;
        passwordRevision++;
        attempts.clear();
        cancelCrank();
        setChanged();
        return true;
    }

    private static byte[] derive(String password, byte[] salt) {
        PBEKeySpec spec = new PBEKeySpec(password.toCharArray(), salt, 120_000, 256);
        try { return SecretKeyFactory.getInstance("PBKDF2WithHmacSHA256").generateSecret(spec).getEncoded(); }
        catch (GeneralSecurityException exception) { throw new IllegalStateException("Password hashing unavailable", exception); }
        finally { spec.clearPassword(); }
    }

    void setDispenseAmount(int amount) {
        int clamped = Math.clamp(amount, 1, 64);
        if (dispenseAmount != clamped) { cancelCrank(); dispenseAmount = clamped; setChanged(); }
    }

    public boolean startCrank(ServerPlayer player) {
        if (!canReach(player) || !isLookingAt(player) || player.containerMenu != player.inventoryMenu) { return false; }
        long now = level.getGameTime();
        if (pausedSince >= 0 && now - pausedSince >= CRANK_RESET_DELAY) { cancelCrank(); }
        awaitingRelease.entrySet().removeIf(entry -> now - entry.getValue() > 10);
        if (awaitingRelease.containsKey(player.getUUID())) { return false; }
        if (crankingPlayer != null) {
            if (!crankingPlayer.equals(player.getUUID())) { tell(player, "busy"); return false; }
            holdingCrank = true;
            lastHeartbeat = now;
            pausedSince = -1;
            return true;
        }
        String error = transactionError(player);
        if (error != null) { tell(player, error); return false; }
        crankingPlayer = player.getUUID();
        lastHeartbeat = now;
        pausedSince = -1;
        holdingCrank = true;
        crankActive = true;
        crankTicks = 0;
        sendPublicUpdate();
        return true;
    }

    public void heartbeat(ServerPlayer player, boolean held) {
        if (pausedSince >= 0 && level.getGameTime() - pausedSince >= CRANK_RESET_DELAY) { cancelCrank(); }
        if (awaitingRelease.containsKey(player.getUUID())) {
            if (held) { awaitingRelease.put(player.getUUID(), level.getGameTime()); }
            else { awaitingRelease.remove(player.getUUID()); }
        }
        if (!player.getUUID().equals(crankingPlayer)) { return; }
        if (!held || !canReach(player) || !isLookingAt(player) || player.containerMenu != player.inventoryMenu) { pauseCrank(); return; }
        holdingCrank = true;
        pausedSince = -1;
        lastHeartbeat = level.getGameTime();
    }

    private boolean isLookingAt(ServerPlayer player) {
        HitResult hit = player.pick(player.blockInteractionRange(), 1.0F, false);
        return hit instanceof BlockHitResult blockHit && hit.getType() == HitResult.Type.BLOCK
            && blockHit.getBlockPos().equals(worldPosition);
    }

    public static void serverTick(Level level, BlockPos pos, BlockState state, GachaponBlockEntity machine) {
        if (machine.crankingPlayer == null) { return; }
        Player candidate = level.getPlayerByUUID(machine.crankingPlayer);
        if (!(candidate instanceof ServerPlayer player) || !machine.canReach(player) || !machine.isLookingAt(player)
                || player.containerMenu != player.inventoryMenu || !machine.holdingCrank
                || level.getGameTime() - machine.lastHeartbeat > 10) {
            machine.pauseCrank();
            if (level.getGameTime() - machine.pausedSince >= CRANK_RESET_DELAY) { machine.cancelCrank(); }
            return;
        }
        machine.pausedSince = -1;
        if (!machine.crankActive) { machine.crankActive = true; machine.sendPublicUpdate(); }
        machine.crankTicks++;
        if (machine.crankTicks % 8 == 0) {
            level.playSound(null, pos, SoundEvents.TRIPWIRE_CLICK_ON, SoundSource.BLOCKS, .28F, 1.1F + machine.crankTicks / 100F);
        }
        if (machine.crankTicks >= CRANK_DURATION) {
            machine.completeRoll(player);
            machine.awaitingRelease.put(player.getUUID(), level.getGameTime());
            machine.cancelCrank();
        } else if (machine.crankTicks % 2 == 0) { machine.sendPublicUpdate(); }
    }

    private void cancelCrank() {
        if (crankingPlayer != null || crankTicks != 0) {
            crankingPlayer = null;
            crankTicks = 0;
            pausedSince = -1;
            holdingCrank = false;
            crankActive = false;
            sendPublicUpdate();
        }
    }

    private void pauseCrank() {
        if (crankingPlayer == null) { return; }
        holdingCrank = false;
        if (pausedSince < 0) { pausedSince = level.getGameTime(); }
        if (crankActive) { crankActive = false; sendPublicUpdate(); }
    }

    @Nullable private String transactionError(ServerPlayer player) {
        if (!hasPassword()) { return "not_configured"; }
        ItemStack price = inventory.getItem(PRICE_SLOT);
        if (price.isEmpty()) { return "no_price"; }
        if (rewardSlots().isEmpty()) { return "out_of_stock"; }
        if (currencyCount(player, price) < price.getCount()) { return "insufficient_currency"; }
        if (simulateDeposit(price) == null) { return "payment_full"; }
        return null;
    }

    private List<Integer> rewardSlots() {
        List<Integer> choices = new ArrayList<>(9);
        for (int slot = REWARD_START; slot < PAYMENT_START; slot++) {
            if (!inventory.getItem(slot).isEmpty()) { choices.add(slot); }
        }
        return choices;
    }

    private static boolean currencySlot(int slot) { return slot < 36 || slot == 40; }
    private static int currencyCount(ServerPlayer player, ItemStack price) {
        int count = 0;
        for (int slot = 0; slot < player.getInventory().getContainerSize(); slot++) {
            ItemStack held = player.getInventory().getItem(slot);
            if (currencySlot(slot) && ItemStack.isSameItemSameComponents(held, price)) { count += held.getCount(); }
        }
        return count;
    }

    @Nullable private List<ItemStack> simulateDeposit(ItemStack price) {
        List<ItemStack> result = new ArrayList<>(9);
        for (int slot = PAYMENT_START; slot < INVENTORY_SIZE; slot++) { result.add(inventory.getItem(slot).copy()); }
        int remaining = price.getCount();
        for (int pass = 0; pass < 2; pass++) {
            for (int index = 0; index < result.size() && remaining > 0; index++) {
                ItemStack existing = result.get(index);
                if (pass == 0 && !existing.isEmpty() && ItemStack.isSameItemSameComponents(existing, price)) {
                    int add = Math.min(remaining, Math.max(0, Math.min(64, existing.getMaxStackSize()) - existing.getCount()));
                    existing.grow(add); remaining -= add;
                } else if (pass == 1 && existing.isEmpty()) {
                    int add = Math.min(remaining, Math.min(64, price.getMaxStackSize()));
                    result.set(index, price.copyWithCount(add)); remaining -= add;
                }
            }
        }
        return remaining == 0 ? result : null;
    }

    /** Everything is planned before the first mutation; server ticks serialize simultaneous buyers and operators. */
    private void completeRoll(ServerPlayer player) {
        String error = transactionError(player);
        if (error != null) { tell(player, error); return; }
        ItemStack price = inventory.getItem(PRICE_SLOT).copy();
        List<ItemStack> deposited = simulateDeposit(price);
        List<Integer> choices = rewardSlots();
        int selected = choices.get(level.random.nextInt(choices.size()));
        ItemStack reward = inventory.getItem(selected);
        int count = Math.min(dispenseAmount, reward.getCount());
        ItemStack capsule = CapsuleItem.create(reward.copyWithCount(count));
        ItemStack expectedCapsule = capsule.copy();
        List<ItemStack> before = new ArrayList<>(INVENTORY_SIZE);
        for (int slot = 0; slot < INVENTORY_SIZE; slot++) { before.add(inventory.getItem(slot).copy()); }
        int quotedAmount = dispenseAmount;
        int quotedRevision = passwordRevision;
        Direction front = getBlockState().getValue(GachaponBlock.FACING);
        Direction across = front.getClockWise();
        Vec3 exit = Vec3.atLowerCornerOf(worldPosition).add(.5 + across.getStepX() * .16375 + front.getStepX() * .65,
            .18, .5 + across.getStepZ() * .16375 + front.getStepZ() * .65);
        ItemEntity drop = new ItemEntity(level, exit.x, exit.y, exit.z, capsule);
        drop.setDeltaMovement(front.getStepX() * .07, .07, front.getStepZ() * .07);
        drop.setDefaultPickUpDelay();
        drop.setTarget(player.getUUID());
        // An event handler may refuse the entity. Do not take payment for a capsule
        // that the world has rejected. Check again after that potentially reentrant event.
        if (!level.addFreshEntity(drop)) { tell(player, "dispense_failed"); return; }
        boolean unchanged = canReach(player) && player.getUUID().equals(crankingPlayer)
            && dispenseAmount == quotedAmount && passwordRevision == quotedRevision
            && currencyCount(player, price) >= price.getCount() && !drop.isRemoved()
            && ItemStack.matches(drop.getItem(), expectedCapsule);
        for (int slot = 0; slot < INVENTORY_SIZE && unchanged; slot++) {
            unchanged = ItemStack.matches(before.get(slot), inventory.getItem(slot));
        }
        if (!unchanged) { drop.discard(); tell(player, "dispense_failed"); return; }
        suppressUpdates = true;
        try {
            int remaining = price.getCount();
            for (int slot = 0; slot < player.getInventory().getContainerSize() && remaining > 0; slot++) {
                ItemStack held = player.getInventory().getItem(slot);
                if (currencySlot(slot) && ItemStack.isSameItemSameComponents(held, price)) {
                    int used = Math.min(remaining, held.getCount());
                    held.shrink(used); remaining -= used;
                }
            }
            for (int slot = 0; slot < 9; slot++) { inventory.setItem(PAYMENT_START + slot, deposited.get(slot)); }
            inventory.removeItem(selected, count);
        } finally { suppressUpdates = false; }
        inventoryChanged();
        player.getInventory().setChanged();
        player.inventoryMenu.broadcastChanges();
        level.playSound(null, worldPosition, SoundEvents.DISPENSER_DISPENSE, SoundSource.BLOCKS, .7F, 1.15F);
        tell(player, "dispensed");
    }

    private static void tell(Player player, String key) { player.displayClientMessage(Component.translatable("message.japanesearcades.gachapon." + key), true); }

    public void dropInventory() {
        if (level == null || level.isClientSide) { return; }
        cancelCrank();
        Containers.dropContents(level, worldPosition, inventory);
        inventory.clearContent();
    }

    private void inventoryChanged() {
        setChanged();
        if (!suppressUpdates) {
            // Any operator edit invalidates an in-flight quote before money can be taken.
            cancelCrank();
            sendPublicUpdate();
        }
    }

    private void sendPublicUpdate() {
        if (level != null && !level.isClientSide) { level.sendBlockUpdated(worldPosition, getBlockState(), getBlockState(), 2); }
    }

    @Override
    protected void saveAdditional(CompoundTag tag, HolderLookup.Provider registries) {
        super.saveAdditional(tag, registries);
        if (owner != null) { tag.putUUID("Owner", owner); }
        tag.putByteArray("PasswordSalt", passwordSalt);
        tag.putByteArray("PasswordHash", passwordHash);
        tag.putInt("DispenseAmount", dispenseAmount);
        NonNullList<ItemStack> items = NonNullList.withSize(INVENTORY_SIZE, ItemStack.EMPTY);
        for (int slot = 0; slot < INVENTORY_SIZE; slot++) { items.set(slot, inventory.getItem(slot)); }
        ContainerHelper.saveAllItems(tag, items, registries);
    }

    @Override
    protected void loadAdditional(CompoundTag tag, HolderLookup.Provider registries) {
        super.loadAdditional(tag, registries);
        owner = tag.hasUUID("Owner") ? tag.getUUID("Owner") : null;
        passwordSalt = tag.getByteArray("PasswordSalt");
        passwordHash = tag.getByteArray("PasswordHash");
        dispenseAmount = Math.clamp(tag.getInt("DispenseAmount"), 1, 64);
        NonNullList<ItemStack> items = NonNullList.withSize(INVENTORY_SIZE, ItemStack.EMPTY);
        ContainerHelper.loadAllItems(tag, items, registries);
        suppressUpdates = true;
        try { for (int slot = 0; slot < INVENTORY_SIZE; slot++) { inventory.setItem(slot, items.get(slot)); } }
        finally { suppressUpdates = false; }
        crankingPlayer = null;
        awaitingRelease.clear();
        crankTicks = 0;
        pausedSince = -1;
        holdingCrank = false;
        crankActive = false;
        passwordRevision++;
    }

    /** Explicit allow-list: no ownership, credentials, collected money, or hidden inventory is sent to nearby clients. */
    @Override
    public CompoundTag getUpdateTag(HolderLookup.Provider registries) {
        CompoundTag tag = new CompoundTag();
        if (!inventory.getItem(PRICE_SLOT).isEmpty()) { tag.put("Price", inventory.getItem(PRICE_SLOT).save(registries)); }
        for (int slot = 0; slot < 9; slot++) {
            ItemStack item = inventory.getItem(REWARD_START + slot);
            if (!item.isEmpty()) { tag.put("Preview" + slot, item.copyWithCount(1).save(registries)); }
        }
        tag.putInt("CrankTicks", crankTicks);
        tag.putBoolean("CrankActive", crankActive);
        return tag;
    }

    @Override
    public ClientboundBlockEntityDataPacket getUpdatePacket() { return ClientboundBlockEntityDataPacket.create(this); }

    @Override
    public void handleUpdateTag(CompoundTag tag, HolderLookup.Provider registries) {
        publicPrice = tag.contains("Price") ? ItemStack.parse(registries, tag.getCompound("Price")).orElse(ItemStack.EMPTY) : ItemStack.EMPTY;
        for (int slot = 0; slot < 9; slot++) {
            publicRewards[slot] = tag.contains("Preview" + slot)
                ? ItemStack.parse(registries, tag.getCompound("Preview" + slot)).orElse(ItemStack.EMPTY) : ItemStack.EMPTY;
        }
        crankTicks = Math.clamp(tag.getInt("CrankTicks"), 0, CRANK_DURATION);
        crankActive = tag.getBoolean("CrankActive");
    }

    @Override
    public void onDataPacket(Connection connection, ClientboundBlockEntityDataPacket packet, HolderLookup.Provider registries) {
        handleUpdateTag(packet.getTag(), registries);
    }

    private record Attempt(long afterTick, int failures) {}
}
