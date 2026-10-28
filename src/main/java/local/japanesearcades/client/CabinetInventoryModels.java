package local.japanesearcades.client;

import com.mojang.blaze3d.vertex.PoseStack;
import java.util.List;
import local.japanesearcades.JapaneseArcades;
import net.minecraft.client.Minecraft;
import net.minecraft.client.multiplayer.ClientLevel;
import net.minecraft.client.renderer.MultiBufferSource;
import net.minecraft.client.renderer.block.model.ItemOverrides;
import net.minecraft.client.renderer.texture.MissingTextureAtlasSprite;
import net.minecraft.client.resources.model.BakedModel;
import net.minecraft.client.resources.model.ModelBakery;
import net.minecraft.client.resources.model.ModelResourceLocation;
import net.minecraft.core.Direction;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.util.RandomSource;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.item.ItemDisplayContext;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;
import net.neoforged.api.distmarker.Dist;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.client.event.ModelEvent;
import net.neoforged.neoforge.client.model.BakedModelWrapper;
import org.jetbrains.annotations.Nullable;

/** Native model snapshots keep tiny GUI icons from resubmitting detailed static meshes. */
@EventBusSubscriber(modid = JapaneseArcades.MOD_ID, value = Dist.CLIENT, bus = EventBusSubscriber.Bus.MOD)
public final class CabinetInventoryModels {
    // Snapshot assets are deliberately explicit: a new item keeps its native model until
    // an icon has been captured and checked. No live registries are touched on the bake worker.
    private static final List<ResourceLocation> CABINETS = List.of(
        "nostalgia_op3", "beatstream", "sound_voltex_valkyrie", "sound_voltex_nemsys",
        "wacca", "chunithm", "ongeki", "groove_coaster", "museca", "project_diva",
        "chrono_circle", "music_diver", "popn_music", "maimai", "ddr_supernova",
        "beatmania_iidx_lightning", "taiko", "initial_d", "jubeat",
        "arcade_kiosk", "gachapon", "hatsune_miku_figure", "kasane_teto_figure", "sleeping_fox_plush",
        "bombergirl", "gitadora_guitarfreaks", "gitadora_drummania", "claw_machine", "compact_claw_machine").stream()
        .map(name -> ResourceLocation.fromNamespaceAndPath(JapaneseArcades.MOD_ID, name)).toList();

    private CabinetInventoryModels() {}

    private static ModelResourceLocation iconLocation(ResourceLocation cabinet) {
        return ModelResourceLocation.standalone(cabinet.withPrefix("item/gui/"));
    }

    @SubscribeEvent
    public static void additionalModels(ModelEvent.RegisterAdditional event) {
        CABINETS.forEach(id -> event.register(iconLocation(id)));
    }

    @SubscribeEvent
    public static void modelsBaked(ModelEvent.ModifyBakingResult event) {
        var models = event.getModels();
        BakedModel missing = models.get(ModelBakery.MISSING_MODEL_VARIANT);
        for (ResourceLocation id : CABINETS) {
            ModelResourceLocation location = ModelResourceLocation.inventory(id);
            BakedModel detailed = models.get(location);
            BakedModel icon = models.get(iconLocation(id));
            if (eligible(detailed, missing) && eligible(icon, missing)) {
                models.put(location, new InventoryModel(detailed, icon));
            }
        }
    }

    private static boolean eligible(@Nullable BakedModel model, @Nullable BakedModel missing) {
        if (model == null || model == missing || model.isCustomRenderer()
            || model.getOverrides() != ItemOverrides.EMPTY) {
            return false;
        }
        RandomSource random = RandomSource.create(42);
        int count = 0;
        for (int side = -1; side < Direction.values().length; side++) {
            random.setSeed(42);
            for (var quad : model.getQuads(null, side < 0 ? null : Direction.values()[side], random)) {
                if (quad.isTinted() || quad.getSprite().contents().name().equals(MissingTextureAtlasSprite.getLocation())) {
                    return false;
                }
                count++;
            }
        }
        return count > 0;
    }

    /** World prize renderers also use the GUI viewing angle, but need the actual 3D cabinet. */
    public static BakedModel full(BakedModel model) {
        return model instanceof InventoryModel inventory ? inventory.detailedModel() : model;
    }

    /** Flat printed machine displays can reuse the same verified snapshot as GUI slots. */
    static boolean renderFlatIcon(ItemStack stack, int light, int overlay, PoseStack pose,
                                  MultiBufferSource buffers, @Nullable Level level) {
        if (stack.isEmpty() || stack.hasFoil()) { return false; }
        var renderer = Minecraft.getInstance().getItemRenderer();
        BakedModel model = renderer.getModel(stack, level, null, 0);
        if (!(model instanceof InventoryModel)) { return false; }
        renderer.render(stack, ItemDisplayContext.GUI, false, pose, buffers, light, overlay, model);
        return true;
    }

    /** Equivalent to ItemRenderer.renderStatic, retaining native overrides and foil handling. */
    static void renderFull(ItemStack stack, ItemDisplayContext context, int light, int overlay,
                           PoseStack pose, MultiBufferSource buffers, @Nullable Level level, int seed) {
        if (!stack.isEmpty()) {
            var renderer = Minecraft.getInstance().getItemRenderer();
            BakedModel model = full(renderer.getModel(stack, level, null, seed));
            renderer.render(stack, context, false, pose, buffers, light, overlay, model);
        }
    }

    private static final class InventoryModel extends BakedModelWrapper<BakedModel> {
        private final BakedModel icon;
        private final ItemOverrides overrides = new ItemOverrides() {
            @Override
            public BakedModel resolve(BakedModel model, ItemStack stack, @Nullable ClientLevel level,
                                      @Nullable LivingEntity entity, int seed) {
                // Glint follows the original model surface. Ordinary inventory icons use the
                // snapshot; special enchanted stacks retain the existing native rendering.
                return stack.hasFoil() ? originalModel : model;
            }
        };

        private InventoryModel(BakedModel detailed, BakedModel icon) {
            super(detailed);
            this.icon = icon;
        }

        private BakedModel detailedModel() { return originalModel; }

        @Override
        public ItemOverrides getOverrides() { return overrides; }

        @Override
        public boolean usesBlockLight() {
            // GuiGraphics chooses lighting before applyTransform selects the snapshot.
            // The capture already contains the detailed model's directional shading.
            return icon.usesBlockLight();
        }

        @Override
        public BakedModel applyTransform(ItemDisplayContext context, PoseStack pose, boolean leftHand) {
            return (context == ItemDisplayContext.GUI ? icon : originalModel).applyTransform(context, pose, leftHand);
        }
    }
}
