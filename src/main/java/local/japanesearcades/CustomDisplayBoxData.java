package local.japanesearcades;

import com.mojang.serialization.Codec;
import com.mojang.serialization.codecs.RecordCodecBuilder;
import java.util.List;
import java.util.Objects;
import net.minecraft.network.RegistryFriendlyByteBuf;
import net.minecraft.network.codec.ByteBufCodecs;
import net.minecraft.network.codec.StreamCodec;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.component.ItemContainerContents;

/** Immutable contents and the last displayed item; returned stacks are always defensive copies. */
public final class CustomDisplayBoxData {
    public static final CustomDisplayBoxData EMPTY = new CustomDisplayBoxData(ItemStack.EMPTY, ItemStack.EMPTY);
    public static final Codec<CustomDisplayBoxData> CODEC = RecordCodecBuilder.create(instance -> instance.group(
        ItemStack.OPTIONAL_CODEC.optionalFieldOf("contained", ItemStack.EMPTY).forGetter(CustomDisplayBoxData::containedItem),
        ItemStack.OPTIONAL_CODEC.optionalFieldOf("retained", ItemStack.EMPTY).forGetter(CustomDisplayBoxData::retainedItem),
        Codec.BOOL.optionalFieldOf("straight_on", false).forGetter(CustomDisplayBoxData::straightOn)
    ).apply(instance, CustomDisplayBoxData::new));
    public static final StreamCodec<RegistryFriendlyByteBuf, CustomDisplayBoxData> STREAM_CODEC = StreamCodec.composite(
        ItemStack.OPTIONAL_STREAM_CODEC, CustomDisplayBoxData::containedItem,
        ItemStack.OPTIONAL_STREAM_CODEC, CustomDisplayBoxData::retainedItem,
        ByteBufCodecs.BOOL, CustomDisplayBoxData::straightOn,
        CustomDisplayBoxData::new);
    private final ItemContainerContents contents;
    private final ItemContainerContents reference;
    private final boolean straightOn;

    public CustomDisplayBoxData(ItemStack contained, ItemStack retained) {
        this(contained, retained, false);
    }
    public CustomDisplayBoxData(ItemStack contained, ItemStack retained, boolean straightOn) {
        contents = single(contained);
        reference = contents.equals(ItemContainerContents.EMPTY) ? single(retained) : contents;
        this.straightOn = straightOn;
    }

    private static ItemContainerContents single(ItemStack item) {
        if (item.isEmpty() || item.getItem() instanceof CustomDisplayBoxItem) { return ItemContainerContents.EMPTY; }
        return ItemContainerContents.fromItems(List.of(item.copyWithCount(1)));
    }
    public static CustomDisplayBoxData from(ItemStack stack) {
        return stack.getOrDefault(JapaneseArcades.DISPLAY_BOX_DATA.get(), EMPTY);
    }
    public static CustomDisplayBoxData filled(ItemStack item) { return new CustomDisplayBoxData(item, item); }
    public CustomDisplayBoxData filledWith(ItemStack item) { return new CustomDisplayBoxData(item, item, straightOn); }
    public ItemStack containedItem() { return contents.copyOne(); }
    public ItemStack retainedItem() { return reference.copyOne(); }
    public boolean isEmpty() { return contents.equals(ItemContainerContents.EMPTY); }
    public boolean straightOn() { return straightOn; }
    public CustomDisplayBoxData emptied() { return new CustomDisplayBoxData(ItemStack.EMPTY, retainedItem(), straightOn); }
    public CustomDisplayBoxData withStraightOn(boolean value) {
        return value == straightOn ? this : new CustomDisplayBoxData(containedItem(), retainedItem(), value);
    }
    public CustomDisplayBoxData toggledOrientation() { return withStraightOn(!straightOn); }

    @Override public boolean equals(Object other) {
        return other instanceof CustomDisplayBoxData data && contents.equals(data.contents) && reference.equals(data.reference)
            && straightOn == data.straightOn;
    }
    @Override public int hashCode() { return Objects.hash(contents, reference, straightOn); }
}
