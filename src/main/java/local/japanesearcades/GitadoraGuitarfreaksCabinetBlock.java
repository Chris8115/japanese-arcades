package local.japanesearcades;

import com.mojang.serialization.MapCodec;
import net.minecraft.world.level.block.HorizontalDirectionalBlock;

/** GuitarFreaks with static controller hardware and one persistent music-disc inventory. */
public final class GitadoraGuitarfreaksCabinetBlock extends CompactMusicCabinetBlock {
    public static final MapCodec<GitadoraGuitarfreaksCabinetBlock> CODEC = simpleCodec(GitadoraGuitarfreaksCabinetBlock::new);
    public GitadoraGuitarfreaksCabinetBlock(Properties properties) {
        super(properties, new double[][] {
            {-1.7, 0, 2, 17.7, 1.3, 15.5}, {-1, 1.3, 2.2, 17, 23, 15.3},
            {-1, 23, 5, 17, 38.2, 15.3}, {-1.9, 38.2, 7.3, 17.9, 46.8, 14.7},
            {10.8, 17, .9, 15.8, 39.7, 2.6}, {-.85, 1.4, .5, 3.45, 22.2, 5.8}
        });
    }
    @Override protected MapCodec<? extends HorizontalDirectionalBlock> codec() { return CODEC; }
}
