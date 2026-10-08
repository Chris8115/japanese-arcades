package local.japanesearcades;

import javax.annotation.Nullable;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.Holder;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.ResourceKey;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.decoration.Painting;
import net.minecraft.world.entity.decoration.PaintingVariant;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.GameRules;
import net.minecraft.world.level.Level;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;

/** Shared wall-poster geometry; vanilla painting data synchronizes and saves the chosen print. */
public class ArcadePosterEntity extends Painting {
    public static final double WIDTH = 1.0;
    public static final double HEIGHT = 4096.0 / 2979.0;

    public ArcadePosterEntity(EntityType<? extends ArcadePosterEntity> type, Level level) {
        super(type, level);
    }

    public ArcadePosterEntity(Level level, BlockPos anchor, Direction facing, Holder<PaintingVariant> variant) {
        this(JapaneseArcades.ARCADE_POSTER_ENTITY.get(), level);
        initialize(anchor, facing, variant);
    }

    protected final void initialize(BlockPos anchor, Direction facing, Holder<PaintingVariant> variant) {
        this.pos = anchor.immutable();
        setVariant(variant);
        setDirection(facing);
    }

    public static ResourceKey<PaintingVariant> variantKey(String path) {
        return ResourceKey.create(Registries.PAINTING_VARIANT,
            ResourceLocation.fromNamespaceAndPath(JapaneseArcades.MOD_ID, path));
    }

    @Override
    protected AABB calculateBoundingBox(BlockPos anchor, Direction facing) {
        Vec3 center = Vec3.atCenterOf(anchor).relative(facing, -.46875).add(0, (HEIGHT - 1) / 2, 0);
        return AABB.ofSize(center, facing.getAxis() == Direction.Axis.X ? DEPTH : WIDTH,
            HEIGHT, facing.getAxis() == Direction.Axis.Z ? DEPTH : WIDTH);
    }

    @Override
    protected AABB calculateSupportBox() {
        // Keep the original WACCA print dimensions while requiring both occupied wall cells.
        return super.calculateBoundingBox(pos, direction).move(direction.step().mul(-.5F)).deflate(1.0E-7);
    }

    protected Item posterItem() {
        return JapaneseArcades.ARCADE_POSTERS.stream()
            .filter(poster -> getVariant().is(variantKey(poster.path())))
            .map(poster -> (Item) poster.item().get()).findFirst().orElse(JapaneseArcades.WACCA_POSTER.get());
    }

    @Override
    public void dropItem(@Nullable Entity breaker) {
        if (!level().getGameRules().getBoolean(GameRules.RULE_DOENTITYDROPS)) { return; }
        playSound(SoundEvents.PAINTING_BREAK, 1, 1);
        if (breaker instanceof Player player && player.hasInfiniteMaterials()) { return; }
        spawnAtLocation(posterItem());
    }

    @Override
    public ItemStack getPickResult() {
        return new ItemStack(posterItem());
    }
}
