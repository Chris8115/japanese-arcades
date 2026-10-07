package local.japanesearcades;

import com.mojang.serialization.MapCodec;

/** Miku artwork retains its original proportions while sharing the standee lifecycle. */
public final class HatsuneMikuCutoutBlock extends CardboardCutoutBlock {
    public static final MapCodec<HatsuneMikuCutoutBlock> CODEC = simpleCodec(HatsuneMikuCutoutBlock::new);
    public static final double MODEL_WIDTH = 15.2;
    public static final double MODEL_HEIGHT = 25.64449438;

    public HatsuneMikuCutoutBlock(Properties properties) { super(properties, MODEL_WIDTH, MODEL_HEIGHT); }
    @Override protected MapCodec<HatsuneMikuCutoutBlock> codec() { return CODEC; }
}
