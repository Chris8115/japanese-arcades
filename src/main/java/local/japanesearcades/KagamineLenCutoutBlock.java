package local.japanesearcades;

import com.mojang.serialization.MapCodec;

/** Len's collectible standee shares the other characters' sixteen-angle placement. */
public final class KagamineLenCutoutBlock extends CardboardCutoutBlock {
    public static final MapCodec<KagamineLenCutoutBlock> CODEC = simpleCodec(KagamineLenCutoutBlock::new);
    public static final double MODEL_WIDTH = 12.853664859626276;
    public static final double MODEL_HEIGHT = 25.64449438;

    public KagamineLenCutoutBlock(Properties properties) { super(properties, MODEL_WIDTH, MODEL_HEIGHT); }
    @Override protected MapCodec<KagamineLenCutoutBlock> codec() { return CODEC; }
}
