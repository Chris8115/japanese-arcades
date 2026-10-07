package local.japanesearcades;

import net.minecraft.core.BlockPos;
import net.minecraft.core.HolderLookup;
import net.minecraft.core.component.DataComponentMap;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.nbt.NbtOps;
import net.minecraft.network.Connection;
import net.minecraft.network.protocol.game.ClientboundBlockEntityDataPacket;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.state.BlockState;

/** One persistent displayed item. No ticking or automation inventory is required. */
public final class CustomDisplayBoxBlockEntity extends BlockEntity {
    private CustomDisplayBoxData data = CustomDisplayBoxData.EMPTY;
    private long revision;

    public CustomDisplayBoxBlockEntity(BlockPos pos, BlockState state) {
        super(JapaneseArcades.CUSTOM_DISPLAY_BOX_ENTITY.get(), pos, state);
    }
    public CustomDisplayBoxData data() { return data; }
    public ItemStack containedItem() { return data.containedItem(); }
    public ItemStack retainedItem() { return data.retainedItem(); }
    long revision() { return revision; }

    void setData(CustomDisplayBoxData replacement) {
        data = replacement;
        revision++;
        setChanged();
        if (level != null) { level.sendBlockUpdated(worldPosition, getBlockState(), getBlockState(), 3); }
    }

    @Override protected void saveAdditional(CompoundTag tag, HolderLookup.Provider registries) {
        super.saveAdditional(tag, registries);
        tag.put("DisplayBox", CustomDisplayBoxData.CODEC.encodeStart(
            registries.createSerializationContext(NbtOps.INSTANCE), data).getOrThrow());
    }
    @Override protected void loadAdditional(CompoundTag tag, HolderLookup.Provider registries) {
        super.loadAdditional(tag, registries);
        data = tag.contains("DisplayBox") ? CustomDisplayBoxData.CODEC.parse(
            registries.createSerializationContext(NbtOps.INSTANCE), tag.get("DisplayBox")).result().orElse(CustomDisplayBoxData.EMPTY)
            : CustomDisplayBoxData.EMPTY;
        revision++;
    }
    @Override protected void applyImplicitComponents(DataComponentInput input) {
        super.applyImplicitComponents(input);
        data = input.getOrDefault(JapaneseArcades.DISPLAY_BOX_DATA.get(), CustomDisplayBoxData.EMPTY);
        revision++;
    }
    @Override protected void collectImplicitComponents(DataComponentMap.Builder components) {
        super.collectImplicitComponents(components);
        components.set(JapaneseArcades.DISPLAY_BOX_DATA.get(), data);
    }
    @Override public void removeComponentsFromTag(CompoundTag tag) {
        super.removeComponentsFromTag(tag);
        tag.remove("DisplayBox");
    }
    @Override public CompoundTag getUpdateTag(HolderLookup.Provider registries) { return saveWithoutMetadata(registries); }
    @Override public ClientboundBlockEntityDataPacket getUpdatePacket() { return ClientboundBlockEntityDataPacket.create(this); }
    @Override public void handleUpdateTag(CompoundTag tag, HolderLookup.Provider registries) { loadWithComponents(tag, registries); }
    @Override public void onDataPacket(Connection connection, ClientboundBlockEntityDataPacket packet, HolderLookup.Provider registries) {
        handleUpdateTag(packet.getTag(), registries);
    }
}
