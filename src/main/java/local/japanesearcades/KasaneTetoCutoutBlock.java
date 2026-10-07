package local.japanesearcades;

import com.mojang.serialization.MapCodec;

/** Teto's matching collectible cardboard standee. */
public final class KasaneTetoCutoutBlock extends CardboardCutoutBlock {
    public static final MapCodec<KasaneTetoCutoutBlock> CODEC = simpleCodec(KasaneTetoCutoutBlock::new);
    public static final double MODEL_WIDTH = 12.94458291;
    public static final double MODEL_HEIGHT = 25.64449438;

    public KasaneTetoCutoutBlock(Properties properties) { super(properties, MODEL_WIDTH, MODEL_HEIGHT); }
    @Override protected MapCodec<KasaneTetoCutoutBlock> codec() { return CODEC; }
}
