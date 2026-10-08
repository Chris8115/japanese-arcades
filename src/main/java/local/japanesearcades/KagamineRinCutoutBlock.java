package local.japanesearcades;

import com.mojang.serialization.MapCodec;

/** Rin's collectible standee shares the other characters' sixteen-angle placement. */
public final class KagamineRinCutoutBlock extends CardboardCutoutBlock {
    public static final MapCodec<KagamineRinCutoutBlock> CODEC = simpleCodec(KagamineRinCutoutBlock::new);
    public static final double MODEL_WIDTH = 12.965510264711481;
    public static final double MODEL_HEIGHT = 25.64449438;

    public KagamineRinCutoutBlock(Properties properties) { super(properties, MODEL_WIDTH, MODEL_HEIGHT); }
    @Override protected MapCodec<KagamineRinCutoutBlock> codec() { return CODEC; }
}
