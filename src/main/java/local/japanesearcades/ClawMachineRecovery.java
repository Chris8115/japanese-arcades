package local.japanesearcades;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import javax.annotation.Nullable;
import net.minecraft.core.BlockPos;
import net.minecraft.core.HolderLookup;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.nbt.ListTag;
import net.minecraft.nbt.Tag;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.entity.item.ItemEntity;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.saveddata.SavedData;
import net.minecraft.world.phys.Vec3;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.event.tick.LevelTickEvent;

/** Preserves stock from removed claw machines when another mod vetoes world-item delivery. */
@EventBusSubscriber(modid = JapaneseArcades.MOD_ID)
public final class ClawMachineRecovery extends SavedData {
    static final String NAME = JapaneseArcades.MOD_ID + "_claw_returns";
    private static final Factory<ClawMachineRecovery> FACTORY = new Factory<>(ClawMachineRecovery::new, ClawMachineRecovery::load);
    private final Map<UUID, Pending> pending = new LinkedHashMap<>();
    private boolean retrying;

    static ClawMachineRecovery get(ServerLevel level) { return level.getDataStorage().computeIfAbsent(FACTORY, NAME); }

    static void enqueue(ServerLevel level, List<ItemStack> items, Vec3 position, @Nullable UUID recipient) {
        var data = get(level);
        for (ItemStack item : items) {
            if (!item.isEmpty()) { data.pending.put(UUID.randomUUID(), new Pending(item.copy(), position, recipient)); }
        }
        data.setDirty();
    }

    static void retry(ServerLevel level) {
        var data = level.getDataStorage().get(FACTORY, NAME);
        if (data == null || data.retrying || data.pending.isEmpty()) { return; }
        data.retrying = true;
        try {
            // Snapshot the keys: a delivery callback may remove another machine and append returns.
            for (UUID id : new ArrayList<>(data.pending.keySet())) {
                Pending entry = data.pending.get(id);
                if (entry != null && level.hasChunkAt(BlockPos.containing(entry.position))
                    && spawn(level, entry.item, entry.position, entry.recipient)) {
                    data.pending.remove(id);
                    data.setDirty();
                }
            }
        } finally { data.retrying = false; }
    }

    /** Does not mutate the source stack. Caller retains it until the exact entity is accepted. */
    static boolean spawn(ServerLevel level, ItemStack item, Vec3 position, @Nullable UUID recipient) {
        if (item.isEmpty()) { return true; }
        ItemEntity entity = new ItemEntity(level, position.x, position.y, position.z, item.copy());
        entity.getPersistentData().putBoolean(ArcadeKioskMenu.OVERFLOW_MARKER, true);
        entity.setDefaultPickUpDelay();
        if (recipient != null) { entity.setTarget(recipient); }
        entity.setDeltaMovement(0, .05, 0);
        boolean accepted = level.addFreshEntity(entity);
        if (!accepted || entity.isRemoved() || !ItemStack.matches(item, entity.getItem())) {
            entity.discard();
            return false;
        }
        return true;
    }

    @SubscribeEvent
    public static void afterLevelTick(LevelTickEvent.Post event) {
        if (event.getLevel() instanceof ServerLevel level && level.getGameTime() % 100 == 0) { retry(level); }
    }

    @Override
    public CompoundTag save(CompoundTag tag, HolderLookup.Provider registries) {
        ListTag entries = new ListTag();
        pending.forEach((id, entry) -> {
            CompoundTag value = new CompoundTag();
            value.putUUID("Id", id);
            value.put("Item", entry.item.save(registries));
            value.putDouble("X", entry.position.x); value.putDouble("Y", entry.position.y); value.putDouble("Z", entry.position.z);
            if (entry.recipient != null) { value.putUUID("Recipient", entry.recipient); }
            entries.add(value);
        });
        tag.put("Returns", entries);
        return tag;
    }

    static ClawMachineRecovery load(CompoundTag tag, HolderLookup.Provider registries) {
        var result = new ClawMachineRecovery();
        ListTag entries = tag.getList("Returns", Tag.TAG_COMPOUND);
        for (int index = 0; index < entries.size(); index++) {
            CompoundTag value = entries.getCompound(index);
            ItemStack item = ItemStack.parse(registries, value.getCompound("Item")).orElse(ItemStack.EMPTY);
            if (!item.isEmpty()) {
                UUID id = value.hasUUID("Id") ? value.getUUID("Id") : UUID.randomUUID();
                result.pending.put(id, new Pending(item, new Vec3(value.getDouble("X"), value.getDouble("Y"), value.getDouble("Z")),
                    value.hasUUID("Recipient") ? value.getUUID("Recipient") : null));
            }
        }
        return result;
    }

    private record Pending(ItemStack item, Vec3 position, @Nullable UUID recipient) {}
}
