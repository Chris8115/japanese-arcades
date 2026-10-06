package local.funpack.custom;

import net.minecraft.core.BlockPos;
import net.minecraft.core.Holder;
import net.minecraft.core.HolderLookup;
import net.minecraft.core.component.DataComponents;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.world.Container;
import net.minecraft.world.entity.item.ItemEntity;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.JukeboxSong;
import net.minecraft.world.item.JukeboxSongPlayer;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.gameevent.GameEvent;
import net.minecraft.world.phys.Vec3;
import net.minecraft.world.ticks.ContainerSingleItem;

/** One saved disc per cabinet, using Minecraft's normal jukebox playback. */
public final class NostalgiaJukeboxBlockEntity extends BlockEntity implements ContainerSingleItem.BlockContainerSingleItem {
    private ItemStack disc = ItemStack.EMPTY;
    private final JukeboxSongPlayer songPlayer = new JukeboxSongPlayer(this::songChanged, worldPosition);

    public NostalgiaJukeboxBlockEntity(BlockPos pos, BlockState state) {
        super(FunPackCustom.NOSTALGIA_JUKEBOX.get(), pos, state);
    }

    public JukeboxSongPlayer getSongPlayer() { return songPlayer; }

    private void songChanged() {
        setChanged();
        if (level != null) {
            level.updateNeighborsAt(worldPosition, getBlockState().getBlock());
        }
    }

    @Override
    public ItemStack getTheItem() { return disc; }

    @Override
    public void setTheItem(ItemStack stack) {
        disc = stack.isEmpty() ? ItemStack.EMPTY : stack.copyWithCount(1);
        if (level != null) {
            BlockState current = level.getBlockState(worldPosition);
            if (current.is(FunPackCustom.NOSTALGIA_OP3.get())
                    && current.getValue(NostalgiaCabinetBlock.PART) == NostalgiaCabinetBlock.Part.BASE) {
                level.setBlock(worldPosition, current.setValue(NostalgiaCabinetBlock.HAS_RECORD, !disc.isEmpty()), 2);
                level.gameEvent(GameEvent.BLOCK_CHANGE, worldPosition, GameEvent.Context.of(current));
            }
            var song = JukeboxSong.fromStack(level.registryAccess(), disc);
            if (song.isPresent()) {
                songPlayer.play(level, song.get());
            } else {
                songPlayer.stop(level, getBlockState());
            }
        }
        setChanged();
    }

    @Override
    public ItemStack splitTheItem(int amount) {
        if (amount <= 0 || disc.isEmpty()) { return ItemStack.EMPTY; }
        ItemStack result = disc;
        setTheItem(ItemStack.EMPTY);
        return result;
    }

    public void ejectDisc() {
        if (level == null || level.isClientSide || disc.isEmpty()) { return; }
        var facing = getBlockState().getValue(NostalgiaCabinetBlock.FACING);
        ItemStack ejected = removeTheItem();
        // Eject in front of the footwell rather than inside the console above it.
        Vec3 point = Vec3.atCenterOf(worldPosition).add(facing.getStepX() * .9, .35, facing.getStepZ() * .9);
        ItemEntity entity = new ItemEntity(level, point.x, point.y, point.z, ejected);
        entity.setDefaultPickUpDelay();
        level.addFreshEntity(entity);
    }

    public int comparatorOutput() {
        return level == null ? 0 : JukeboxSong.fromStack(level.registryAccess(), disc)
            .map(Holder::value).map(JukeboxSong::comparatorOutput).orElse(0);
    }

    public static void tick(Level level, BlockPos pos, BlockState state, NostalgiaJukeboxBlockEntity cabinet) {
        cabinet.songPlayer.tick(level, state);
    }

    @Override
    protected void saveAdditional(CompoundTag tag, HolderLookup.Provider registries) {
        super.saveAdditional(tag, registries);
        if (!disc.isEmpty()) { tag.put("RecordItem", disc.save(registries)); }
        if (songPlayer.isPlaying()) { tag.putLong("ticks_since_song_started", songPlayer.getTicksSinceSongStarted()); }
    }

    @Override
    protected void loadAdditional(CompoundTag tag, HolderLookup.Provider registries) {
        super.loadAdditional(tag, registries);
        disc = tag.contains("RecordItem", CompoundTag.TAG_COMPOUND)
            ? ItemStack.parse(registries, tag.getCompound("RecordItem")).orElse(ItemStack.EMPTY) : ItemStack.EMPTY;
        if (!disc.isEmpty()) { disc.setCount(1); }
        if (tag.contains("ticks_since_song_started", CompoundTag.TAG_LONG)) {
            JukeboxSong.fromStack(registries, disc).ifPresent(song ->
                songPlayer.setSongWithoutPlaying(song, tag.getLong("ticks_since_song_started")));
        }
    }

    @Override
    public int getMaxStackSize() { return 1; }

    @Override
    public BlockEntity getContainerBlockEntity() { return this; }

    @Override
    public boolean canPlaceItem(int slot, ItemStack stack) {
        return slot == 0 && disc.isEmpty() && stack.has(DataComponents.JUKEBOX_PLAYABLE)
            && level != null && JukeboxSong.fromStack(level.registryAccess(), stack).isPresent();
    }

    @Override
    public boolean canTakeItem(Container target, int slot, ItemStack stack) {
        return target.hasAnyMatching(ItemStack::isEmpty);
    }
}
