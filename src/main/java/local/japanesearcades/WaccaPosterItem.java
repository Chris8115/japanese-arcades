package local.japanesearcades;

import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.Holder;
import net.minecraft.world.entity.decoration.PaintingVariant;
import net.minecraft.world.level.Level;

/** Keeps the original WACCA item's dedicated entity while sharing poster placement behavior. */
public final class WaccaPosterItem extends ArcadePosterItem {
    public WaccaPosterItem(Properties properties) { super(properties, "wacca_poster"); }

    @Override
    protected ArcadePosterEntity createPoster(Level level, BlockPos anchor, Direction facing,
                                               Holder<PaintingVariant> artwork) {
        return new WaccaPosterEntity(level, anchor, facing, artwork);
    }
}
