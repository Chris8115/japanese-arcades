package local.japanesearcades;

import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.Holder;
import net.minecraft.resources.ResourceKey;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.decoration.PaintingVariant;
import net.minecraft.world.item.Item;
import net.minecraft.world.level.Level;

/** Retains the original collectible's entity ID and saved-world compatibility. */
public final class WaccaPosterEntity extends ArcadePosterEntity {
    public static final ResourceKey<PaintingVariant> VARIANT = variantKey("wacca_poster");

    public WaccaPosterEntity(EntityType<? extends WaccaPosterEntity> type, Level level) {
        super(type, level);
    }

    public WaccaPosterEntity(Level level, BlockPos anchor, Direction facing, Holder<PaintingVariant> variant) {
        this(JapaneseArcades.WACCA_POSTER_ENTITY.get(), level);
        initialize(anchor, facing, variant);
    }

    @Override
    protected Item posterItem() {
        return JapaneseArcades.WACCA_POSTER.get();
    }
}
