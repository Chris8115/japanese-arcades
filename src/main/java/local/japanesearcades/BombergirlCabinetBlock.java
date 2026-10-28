package local.japanesearcades;

import com.mojang.serialization.MapCodec;
import net.minecraft.world.level.block.HorizontalDirectionalBlock;

/** Bombergirl cabinet with the shared persistent music-disc behavior. */
public final class BombergirlCabinetBlock extends CompactMusicCabinetBlock {
    public static final MapCodec<BombergirlCabinetBlock> CODEC = simpleCodec(BombergirlCabinetBlock::new);
    public BombergirlCabinetBlock(Properties properties) {
        super(properties, new double[][] {
            {.8, 0, .6, 15.2, 1.52, 15.2}, {1.15, 1.5, 4.06, 14.85, 13.4, 15.1},
            {.2, 13.4, .45, 15.8, 16, 12.05}, {.2, 16, 2.8, 15.8, 17.2, 12.05},
            {.75, 17.2, 8.4, 15.25, 35, 15.51}, {.25, 34.9, 9.42, 15.75, 38.28, 11},
            {1.15, 38.28, 10.42, 14.85, 47.5, 10.68}
        });
    }
    @Override protected MapCodec<? extends HorizontalDirectionalBlock> codec() { return CODEC; }
}
