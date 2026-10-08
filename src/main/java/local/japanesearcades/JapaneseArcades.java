package local.japanesearcades;

import com.mojang.logging.LogUtils;
import java.util.List;
import net.minecraft.commands.Commands;
import net.minecraft.core.registries.Registries;
import net.minecraft.core.component.DataComponentType;
import net.minecraft.network.chat.Component;
import net.minecraft.world.item.CreativeModeTab;
import net.minecraft.world.item.BlockItem;
import net.minecraft.world.item.DyeColor;
import net.minecraft.world.item.Item;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.MobCategory;
import net.minecraft.world.inventory.MenuType;
import net.minecraft.world.level.block.SoundType;
import net.minecraft.world.level.block.entity.BlockEntityType;
import net.minecraft.world.level.block.state.BlockBehaviour;
import net.minecraft.world.level.material.MapColor;
import net.minecraft.world.level.material.PushReaction;
import net.neoforged.bus.api.IEventBus;
import net.neoforged.fml.common.Mod;
import net.neoforged.fml.ModContainer;
import net.neoforged.fml.config.ModConfig;
import net.neoforged.neoforge.common.NeoForge;
import net.neoforged.neoforge.event.RegisterCommandsEvent;
import net.neoforged.neoforge.common.extensions.IMenuTypeExtension;
import net.neoforged.neoforge.registries.DeferredBlock;
import net.neoforged.neoforge.registries.DeferredHolder;
import net.neoforged.neoforge.registries.DeferredItem;
import net.neoforged.neoforge.registries.DeferredRegister;
import org.slf4j.Logger;

/** Entry point for our pack's custom features. Works on clients and dedicated servers. */
@Mod(JapaneseArcades.MOD_ID)
public final class JapaneseArcades {
    public static final String MOD_ID = "japanesearcades";
    public static final Logger LOGGER = LogUtils.getLogger();

    private static final DeferredRegister.Blocks BLOCKS = DeferredRegister.createBlocks(MOD_ID);
    private static final DeferredRegister.Items ITEMS = DeferredRegister.createItems(MOD_ID);
    private static final DeferredRegister<CreativeModeTab> TABS =
        DeferredRegister.create(Registries.CREATIVE_MODE_TAB, MOD_ID);
    private static final DeferredRegister<BlockEntityType<?>> BLOCK_ENTITIES =
        DeferredRegister.create(Registries.BLOCK_ENTITY_TYPE, MOD_ID);
    private static final DeferredRegister<MenuType<?>> MENUS = DeferredRegister.create(Registries.MENU, MOD_ID);
    private static final DeferredRegister<EntityType<?>> ENTITIES = DeferredRegister.create(Registries.ENTITY_TYPE, MOD_ID);
    private static final DeferredRegister<DataComponentType<?>> COMPONENTS = DeferredRegister.create(Registries.DATA_COMPONENT_TYPE, MOD_ID);
    public static final DeferredHolder<DataComponentType<?>, DataComponentType<ArcadePassData>> PASS_DATA =
        COMPONENTS.register("arcade_pass", () -> DataComponentType.<ArcadePassData>builder()
            .persistent(ArcadePassData.CODEC).networkSynchronized(ArcadePassData.STREAM_CODEC).build());
    public static final DeferredItem<ArcadePassItem> ARCADE_PASS = ITEMS.registerItem("arcade_pass", ArcadePassItem::new,
        new Item.Properties().stacksTo(1));
    public static final DeferredItem<MechSuitItem> MECH_SUIT_ITEM = ITEMS.registerItem(
        "mech_suit", MechSuitItem::new, new Item.Properties().stacksTo(1).rarity(net.minecraft.world.item.Rarity.EPIC).fireResistant());
    public static final DeferredHolder<EntityType<?>, EntityType<MechSuitEntity>> MECH_SUIT =
        ENTITIES.register("mech_suit", () -> EntityType.Builder.<MechSuitEntity>of(
            MechSuitEntity::new, MobCategory.MISC).sized(2F, 5F).clientTrackingRange(10)
            .updateInterval(1).build(MOD_ID + ":mech_suit"));
    public record GlowStickSet(String color, String path, DeferredBlock<GlowStickBlock> block, DeferredItem<BlockItem> item) {}
    public static final List<GlowStickSet> GLOW_STICKS = GlowStickBlock.COLORS.stream().map(JapaneseArcades::glowStick).toList();
    public static final DeferredBlock<ArcadePrizeBlock> HATSUNE_MIKU_FIGURE = prizeBlock("hatsune_miku_figure");
    public static final DeferredBlock<ArcadePrizeBlock> KASANE_TETO_FIGURE = prizeBlock("kasane_teto_figure");
    public static final DeferredItem<?> HATSUNE_MIKU_FIGURE_ITEM = ITEMS.registerSimpleBlockItem("hatsune_miku_figure", HATSUNE_MIKU_FIGURE);
    public static final DeferredItem<?> KASANE_TETO_FIGURE_ITEM = ITEMS.registerSimpleBlockItem("kasane_teto_figure", KASANE_TETO_FIGURE);
    public static final DeferredBlock<HatsuneMikuCutoutBlock> HATSUNE_MIKU_CUTOUT = BLOCKS.registerBlock(
        "hatsune_miku_cutout", HatsuneMikuCutoutBlock::new,
        BlockBehaviour.Properties.of().mapColor(MapColor.COLOR_CYAN).strength(.5F).sound(SoundType.WOOD).noOcclusion());
    public static final DeferredItem<?> HATSUNE_MIKU_CUTOUT_ITEM = ITEMS.registerSimpleBlockItem("hatsune_miku_cutout", HATSUNE_MIKU_CUTOUT);
    public static final DeferredBlock<KasaneTetoCutoutBlock> KASANE_TETO_CUTOUT = BLOCKS.registerBlock(
        "kasane_teto_cutout", KasaneTetoCutoutBlock::new,
        BlockBehaviour.Properties.of().mapColor(MapColor.COLOR_CYAN).strength(.5F).sound(SoundType.WOOD).noOcclusion());
    public static final DeferredItem<?> KASANE_TETO_CUTOUT_ITEM = ITEMS.registerSimpleBlockItem("kasane_teto_cutout", KASANE_TETO_CUTOUT);
    public record MobFigureSet(String mob, DeferredBlock<MobFigureBlock> figure,
            DeferredBlock<MobFigureBlock> emptyBox, DeferredBlock<MobFigureBlock> boxedFigure,
            DeferredItem<MobFigureItem> figureItem, DeferredItem<MobFigureItem> emptyBoxItem,
            DeferredItem<MobFigureItem> boxedFigureItem) {}
    public static final List<MobFigureSet> MOB_FIGURES = MobFigureBlock.MOBS.stream().map(JapaneseArcades::mobFigure).toList();
    public static final DeferredHolder<DataComponentType<?>, DataComponentType<CustomDisplayBoxData>> DISPLAY_BOX_DATA =
        COMPONENTS.register("display_box", () -> DataComponentType.<CustomDisplayBoxData>builder()
            .persistent(CustomDisplayBoxData.CODEC).networkSynchronized(CustomDisplayBoxData.STREAM_CODEC).build());
    public static final DeferredBlock<CustomDisplayBoxBlock> CUSTOM_DISPLAY_BOX = BLOCKS.registerBlock(
        "custom_display_box", CustomDisplayBoxBlock::new,
        BlockBehaviour.Properties.of().mapColor(MapColor.COLOR_BROWN).strength(.5F).sound(SoundType.WOOD).noOcclusion());
    public static final DeferredItem<CustomDisplayBoxItem> CUSTOM_DISPLAY_BOX_ITEM = ITEMS.register("custom_display_box",
        () -> new CustomDisplayBoxItem(CUSTOM_DISPLAY_BOX.get(), new Item.Properties()
            .component(DISPLAY_BOX_DATA.get(), CustomDisplayBoxData.EMPTY)));
    public static final DeferredHolder<BlockEntityType<?>, BlockEntityType<CustomDisplayBoxBlockEntity>> CUSTOM_DISPLAY_BOX_ENTITY =
        BLOCK_ENTITIES.register("custom_display_box", () -> BlockEntityType.Builder.of(
            CustomDisplayBoxBlockEntity::new, CUSTOM_DISPLAY_BOX.get()).build(null));
    public static final DeferredBlock<FigureShelfBlock> FIGURE_DISPLAY_UNIT = BLOCKS.registerBlock(
        "figure_display_unit", properties -> new FigureShelfBlock(2, properties),
        BlockBehaviour.Properties.of().mapColor(MapColor.WOOD).strength(1.5F).sound(SoundType.WOOD).noOcclusion());
    public static final DeferredBlock<FigureShelfBlock> FIGURE_WALL_SHELF = BLOCKS.registerBlock(
        "figure_wall_shelf", properties -> new FigureShelfBlock(1, properties),
        BlockBehaviour.Properties.of().mapColor(MapColor.WOOD).strength(1.5F).sound(SoundType.WOOD).noOcclusion());
    public static final DeferredItem<BlockItem> FIGURE_DISPLAY_UNIT_ITEM = ITEMS.registerSimpleBlockItem("figure_display_unit", FIGURE_DISPLAY_UNIT);
    public static final DeferredItem<BlockItem> FIGURE_WALL_SHELF_ITEM = ITEMS.registerSimpleBlockItem("figure_wall_shelf", FIGURE_WALL_SHELF);
    public static final DeferredHolder<BlockEntityType<?>, BlockEntityType<FigureShelfBlockEntity>> FIGURE_SHELF_ENTITY =
        BLOCK_ENTITIES.register("figure_shelf", () -> BlockEntityType.Builder.of(
            FigureShelfBlockEntity::new, FIGURE_DISPLAY_UNIT.get(), FIGURE_WALL_SHELF.get()).build(null));
    public static final DeferredHolder<MenuType<?>, MenuType<FigureShelfMenu>> FIGURE_SHELF_MENU =
        MENUS.register("figure_shelf", () -> IMenuTypeExtension.create(FigureShelfMenu::new));
    public static final DeferredItem<WaccaPosterItem> WACCA_POSTER = ITEMS.registerItem(
        "wacca_poster", WaccaPosterItem::new, new Item.Properties());
    public static final DeferredHolder<EntityType<?>, EntityType<WaccaPosterEntity>> WACCA_POSTER_ENTITY =
        ENTITIES.register("wacca_poster", () -> EntityType.Builder.<WaccaPosterEntity>of(
            WaccaPosterEntity::new, MobCategory.MISC).sized(.5F, .5F).clientTrackingRange(10)
            .updateInterval(Integer.MAX_VALUE).build(MOD_ID + ":wacca_poster"));
    public record ArcadePosterSet(String path, DeferredItem<ArcadePosterItem> item) {}
    public static final List<ArcadePosterSet> ARCADE_POSTERS = List.of(
        "nostalgia_poster", "nostalgia_op2_poster", "nostalgia_forte_poster",
        "sound_voltex_exceed_gear_poster", "sound_voltex_vivid_wave_poster", "taiko_drum_n_fun_poster",
        "wacca_s_poster", "wacca_reverse_poster", "wacca_lily_poster", "wacca_lily_r_poster", "jubeat_festo_poster",
        "project_diva_arcade_poster", "chunithm_luminous_plus_poster", "sound_voltex_exceed_gear_ensemble_poster",
        "maimai_splash_poster", "sega_cygames_poster", "maimai_universe_poster", "chunithm_paradise_poster",
        "we_love_music_game_poster"
    ).stream().map(path -> new ArcadePosterSet(path,
        ITEMS.registerItem(path, properties -> new ArcadePosterItem(properties, path), new Item.Properties()))).toList();
    public static final DeferredHolder<EntityType<?>, EntityType<ArcadePosterEntity>> ARCADE_POSTER_ENTITY =
        ENTITIES.register("arcade_poster", () -> EntityType.Builder.<ArcadePosterEntity>of(
            ArcadePosterEntity::new, MobCategory.MISC).sized(.5F, .5F).clientTrackingRange(10)
            .updateInterval(Integer.MAX_VALUE).build(MOD_ID + ":arcade_poster"));

    private static GlowStickSet glowStick(String color) {
        String path = color + "_glow_stick";
        var block = BLOCKS.registerBlock(path, GlowStickBlock::new, BlockBehaviour.Properties.of()
            .mapColor(DyeColor.byName(color, DyeColor.WHITE).getMapColor()).instabreak().sound(SoundType.GLASS)
            .noCollission().noOcclusion().pushReaction(PushReaction.DESTROY).lightLevel(state -> 14));
        return new GlowStickSet(color, path, block, ITEMS.registerSimpleBlockItem(path, block));
    }

    private static DeferredBlock<ArcadePrizeBlock> prizeBlock(String name) {
        return BLOCKS.registerBlock(name, ArcadePrizeBlock::new, BlockBehaviour.Properties.of()
            .mapColor(MapColor.COLOR_CYAN).strength(.5F).sound(SoundType.WOOD).noOcclusion());
    }

    private static MobFigureSet mobFigure(String mob) {
        var figure = mobFigureBlock(mob, MobFigureBlock.Form.FIGURE);
        var emptyBox = mobFigureBlock(mob, MobFigureBlock.Form.BOX);
        var boxed = mobFigureBlock(mob, MobFigureBlock.Form.BOXED);
        return new MobFigureSet(mob, figure, emptyBox, boxed,
            ITEMS.register(MobFigureBlock.path(mob, MobFigureBlock.Form.FIGURE), () -> new MobFigureItem(figure.get(), new Item.Properties())),
            ITEMS.register(MobFigureBlock.path(mob, MobFigureBlock.Form.BOX), () -> new MobFigureItem(emptyBox.get(), new Item.Properties())),
            ITEMS.register(MobFigureBlock.path(mob, MobFigureBlock.Form.BOXED), () -> new MobFigureItem(boxed.get(), new Item.Properties())));
    }

    private static DeferredBlock<MobFigureBlock> mobFigureBlock(String mob, MobFigureBlock.Form form) {
        return BLOCKS.registerBlock(MobFigureBlock.path(mob, form), properties -> new MobFigureBlock(mob, form, properties),
            BlockBehaviour.Properties.of().mapColor(MapColor.COLOR_BROWN).strength(.5F).sound(SoundType.WOOD).noOcclusion());
    }

    public static final DeferredBlock<NostalgiaCabinetBlock> NOSTALGIA_OP3 = BLOCKS.registerBlock(
        "nostalgia_op3", NostalgiaCabinetBlock::new,
        BlockBehaviour.Properties.of().mapColor(MapColor.COLOR_BLACK).strength(2.0F, 6.0F)
            .sound(SoundType.METAL).noOcclusion().lightLevel(state -> switch (state.getValue(NostalgiaCabinetBlock.PART)) {
                case BASE -> 5;
                case CONSOLE -> 13;
                case MARQUEE -> 12;
            }));
    public static final DeferredBlock<NostalgiaCabinetBlock> BEATSTREAM = BLOCKS.registerBlock(
        "beatstream", NostalgiaCabinetBlock::new,
        BlockBehaviour.Properties.of().mapColor(MapColor.COLOR_BLACK).strength(2.0F, 6.0F)
            .sound(SoundType.METAL).noOcclusion().lightLevel(state -> switch (state.getValue(NostalgiaCabinetBlock.PART)) {
                case BASE -> 5;
                case CONSOLE -> 13;
                case MARQUEE -> 12;
            }));
    public static final DeferredBlock<SoundVoltexCabinetBlock> SOUND_VOLTEX_VALKYRIE = BLOCKS.registerBlock(
        "sound_voltex_valkyrie", SoundVoltexCabinetBlock::new,
        BlockBehaviour.Properties.of().mapColor(MapColor.COLOR_BLACK).strength(2.0F, 6.0F)
            .sound(SoundType.METAL).noOcclusion().lightLevel(state ->
                state.getValue(NostalgiaCabinetBlock.PART) == NostalgiaCabinetBlock.Part.BASE ? 10 : 13));
    public static final DeferredBlock<SoundVoltexNemsysCabinetBlock> SOUND_VOLTEX_NEMSYS = BLOCKS.registerBlock(
        "sound_voltex_nemsys", SoundVoltexNemsysCabinetBlock::new,
        BlockBehaviour.Properties.of().mapColor(MapColor.COLOR_BLACK).strength(2.0F, 6.0F)
            .sound(SoundType.METAL).noOcclusion().lightLevel(state ->
                state.getValue(NostalgiaCabinetBlock.PART) == NostalgiaCabinetBlock.Part.BASE ? 4 : 13));
    public static final DeferredBlock<WaccaCabinetBlock> WACCA = BLOCKS.registerBlock(
        "wacca", WaccaCabinetBlock::new,
        BlockBehaviour.Properties.of().mapColor(MapColor.COLOR_BLACK).strength(2.0F, 6.0F)
            .sound(SoundType.METAL).noOcclusion().lightLevel(state ->
                state.getValue(NostalgiaCabinetBlock.PART) == NostalgiaCabinetBlock.Part.BASE ? 4 : 13));
    public static final DeferredBlock<ChunithmCabinetBlock> CHUNITHM = BLOCKS.registerBlock(
        "chunithm", ChunithmCabinetBlock::new,
        BlockBehaviour.Properties.of().mapColor(MapColor.COLOR_BLACK).strength(2.0F, 6.0F)
            .sound(SoundType.METAL).noOcclusion().lightLevel(state ->
                state.getValue(NostalgiaCabinetBlock.PART) == NostalgiaCabinetBlock.Part.BASE ? 4 : 13));
    public static final DeferredBlock<OngekiCabinetBlock> ONGEKI = BLOCKS.registerBlock(
        "ongeki", OngekiCabinetBlock::new,
        BlockBehaviour.Properties.of().mapColor(MapColor.SNOW).strength(2.0F, 6.0F)
            .sound(SoundType.METAL).noOcclusion().lightLevel(state ->
                state.getValue(NostalgiaCabinetBlock.PART) == NostalgiaCabinetBlock.Part.BASE ? 4 : 13));
    public static final DeferredBlock<GrooveCoasterCabinetBlock> GROOVE_COASTER = BLOCKS.registerBlock(
        "groove_coaster", GrooveCoasterCabinetBlock::new,
        BlockBehaviour.Properties.of().mapColor(MapColor.COLOR_BLACK).strength(2.0F, 6.0F)
            .sound(SoundType.METAL).noOcclusion().lightLevel(state ->
                state.getValue(NostalgiaCabinetBlock.PART) == NostalgiaCabinetBlock.Part.BASE ? 4 : 13));
    public static final DeferredBlock<MusecaCabinetBlock> MUSECA = BLOCKS.registerBlock(
        "museca", MusecaCabinetBlock::new,
        BlockBehaviour.Properties.of().mapColor(MapColor.COLOR_BLACK).strength(2.0F, 6.0F)
            .sound(SoundType.METAL).noOcclusion().lightLevel(state ->
                state.getValue(NostalgiaCabinetBlock.PART) == NostalgiaCabinetBlock.Part.BASE ? 4 : 13));
    public static final DeferredBlock<ProjectDivaCabinetBlock> PROJECT_DIVA = BLOCKS.registerBlock(
        "project_diva", ProjectDivaCabinetBlock::new,
        BlockBehaviour.Properties.of().mapColor(MapColor.COLOR_BLACK).strength(2.0F, 6.0F)
            .sound(SoundType.METAL).noOcclusion().lightLevel(state ->
                state.getValue(NostalgiaCabinetBlock.PART) == NostalgiaCabinetBlock.Part.BASE ? 4 : 13));
    public static final DeferredBlock<ChronoCircleCabinetBlock> CHRONO_CIRCLE = BLOCKS.registerBlock(
        "chrono_circle", ChronoCircleCabinetBlock::new,
        BlockBehaviour.Properties.of().mapColor(MapColor.COLOR_BLACK).strength(2.0F, 6.0F)
            .sound(SoundType.METAL).noOcclusion().lightLevel(state ->
                state.getValue(NostalgiaCabinetBlock.PART) == NostalgiaCabinetBlock.Part.BASE ? 4 : 13));
    public static final DeferredBlock<MusicDiverCabinetBlock> MUSIC_DIVER = BLOCKS.registerBlock(
        "music_diver", MusicDiverCabinetBlock::new,
        BlockBehaviour.Properties.of().mapColor(MapColor.SNOW).strength(2.0F, 6.0F)
            .sound(SoundType.METAL).noOcclusion().lightLevel(state ->
                state.getValue(NostalgiaCabinetBlock.PART) == NostalgiaCabinetBlock.Part.BASE ? 4 : 13));
    public static final DeferredBlock<PopnMusicCabinetBlock> POPN_MUSIC = BLOCKS.registerBlock(
        "popn_music", PopnMusicCabinetBlock::new,
        BlockBehaviour.Properties.of().mapColor(MapColor.SNOW).strength(2.0F, 6.0F)
            .sound(SoundType.METAL).noOcclusion().lightLevel(state ->
                state.getValue(NostalgiaCabinetBlock.PART) == NostalgiaCabinetBlock.Part.BASE ? 4 : 13));
    public static final DeferredBlock<MaimaiCabinetBlock> MAIMAI = BLOCKS.registerBlock(
        "maimai", MaimaiCabinetBlock::new,
        BlockBehaviour.Properties.of().mapColor(MapColor.SNOW).strength(2.0F, 6.0F)
            .sound(SoundType.METAL).noOcclusion().lightLevel(state ->
                state.getValue(NostalgiaCabinetBlock.PART) == NostalgiaCabinetBlock.Part.BASE ? 4 : 13));
    public static final DeferredBlock<DdrCabinetBlock> DDR_SUPERNOVA = BLOCKS.registerBlock(
        "ddr_supernova", DdrCabinetBlock::new,
        BlockBehaviour.Properties.of().mapColor(MapColor.COLOR_RED).strength(2.0F, 6.0F)
            .sound(SoundType.METAL).noOcclusion().lightLevel(state -> switch (state.getValue(DdrCabinetBlock.SECTION)) {
                case CABINET_CONSOLE, CABINET_MARQUEE -> 12;
                case STAGE_REAR, STAGE_FRONT -> 4;
                default -> 0;
            }));
    public static final DeferredBlock<TaikoCabinetBlock> TAIKO = BLOCKS.registerBlock(
        "taiko", TaikoCabinetBlock::new,
        BlockBehaviour.Properties.of().mapColor(MapColor.COLOR_ORANGE).strength(2.0F, 6.0F)
            .sound(SoundType.METAL).noOcclusion().lightLevel(state -> switch (state.getValue(TaikoCabinetBlock.SECTION)) {
                case REAR_CONSOLE, REAR_MARQUEE -> 12;
                default -> 0;
            }));
    public static final DeferredBlock<BeatmaniaIidxCabinetBlock> BEATMANIA_IIDX_LIGHTNING = BLOCKS.registerBlock(
        "beatmania_iidx_lightning", BeatmaniaIidxCabinetBlock::new,
        BlockBehaviour.Properties.of().mapColor(MapColor.COLOR_BLACK).strength(2.0F, 6.0F)
            .sound(SoundType.METAL).noOcclusion().lightLevel(state -> switch (state.getValue(BeatmaniaIidxCabinetBlock.SECTION)) {
                case CABINET_CONSOLE, CABINET_MARQUEE -> 13;
                case PLATFORM -> 2;
                case CABINET_BASE -> 4;
            }));
    public static final DeferredBlock<InitialDCabinetBlock> INITIAL_D = BLOCKS.registerBlock(
        "initial_d", InitialDCabinetBlock::new,
        BlockBehaviour.Properties.of().mapColor(MapColor.SNOW).strength(2.0F, 6.0F)
            .sound(SoundType.METAL).noOcclusion().lightLevel(state -> switch (state.getValue(InitialDCabinetBlock.SECTION)) {
                case CABINET_CONSOLE, CABINET_MARQUEE -> 12;
                default -> 0;
            }));
    public static final DeferredBlock<JubeatCabinetBlock> JUBEAT = BLOCKS.registerBlock(
        "jubeat", JubeatCabinetBlock::new,
        BlockBehaviour.Properties.of().mapColor(MapColor.COLOR_BLACK).strength(2.0F, 6.0F)
            .sound(SoundType.METAL).noOcclusion().lightLevel(state ->
                state.getValue(NostalgiaCabinetBlock.PART) == NostalgiaCabinetBlock.Part.BASE ? 3 : 12));
    public static final DeferredHolder<EntityType<?>, EntityType<InitialDSeatEntity>> INITIAL_D_SEAT =
        ENTITIES.register("initial_d_seat", () -> EntityType.Builder.<InitialDSeatEntity>of(
            InitialDSeatEntity::new, MobCategory.MISC).sized(.05F, .05F)
            .clientTrackingRange(8).updateInterval(1).noSave().noSummon().build(MOD_ID + ":initial_d_seat"));
    public static final DeferredHolder<BlockEntityType<?>, BlockEntityType<NostalgiaJukeboxBlockEntity>> NOSTALGIA_JUKEBOX =
        BLOCK_ENTITIES.register("nostalgia_jukebox", () -> BlockEntityType.Builder.of(
            NostalgiaJukeboxBlockEntity::new, NOSTALGIA_OP3.get(), BEATSTREAM.get(), SOUND_VOLTEX_VALKYRIE.get(), SOUND_VOLTEX_NEMSYS.get(),
            WACCA.get(), CHUNITHM.get(), ONGEKI.get(), GROOVE_COASTER.get(), MUSECA.get(), PROJECT_DIVA.get(),
            CHRONO_CIRCLE.get(), MUSIC_DIVER.get(), POPN_MUSIC.get(), MAIMAI.get(), DDR_SUPERNOVA.get(), BEATMANIA_IIDX_LIGHTNING.get(), TAIKO.get(), INITIAL_D.get(), JUBEAT.get()).build(null));
    public static final DeferredItem<?> NOSTALGIA_OP3_ITEM =
        ITEMS.registerSimpleBlockItem("nostalgia_op3", NOSTALGIA_OP3, new Item.Properties());
    public static final DeferredItem<?> BEATSTREAM_ITEM =
        ITEMS.registerSimpleBlockItem("beatstream", BEATSTREAM, new Item.Properties());
    public static final DeferredItem<?> SOUND_VOLTEX_VALKYRIE_ITEM =
        ITEMS.registerSimpleBlockItem("sound_voltex_valkyrie", SOUND_VOLTEX_VALKYRIE, new Item.Properties());
    public static final DeferredItem<?> SOUND_VOLTEX_NEMSYS_ITEM =
        ITEMS.registerSimpleBlockItem("sound_voltex_nemsys", SOUND_VOLTEX_NEMSYS, new Item.Properties());
    public static final DeferredItem<?> WACCA_ITEM =
        ITEMS.registerSimpleBlockItem("wacca", WACCA, new Item.Properties());
    public static final DeferredItem<?> CHUNITHM_ITEM =
        ITEMS.registerSimpleBlockItem("chunithm", CHUNITHM, new Item.Properties());
    public static final DeferredItem<?> ONGEKI_ITEM =
        ITEMS.registerSimpleBlockItem("ongeki", ONGEKI, new Item.Properties());
    public static final DeferredItem<?> GROOVE_COASTER_ITEM =
        ITEMS.registerSimpleBlockItem("groove_coaster", GROOVE_COASTER, new Item.Properties());
    public static final DeferredItem<?> MUSECA_ITEM =
        ITEMS.registerSimpleBlockItem("museca", MUSECA, new Item.Properties());
    public static final DeferredItem<?> PROJECT_DIVA_ITEM =
        ITEMS.registerSimpleBlockItem("project_diva", PROJECT_DIVA, new Item.Properties());
    public static final DeferredItem<?> CHRONO_CIRCLE_ITEM =
        ITEMS.registerSimpleBlockItem("chrono_circle", CHRONO_CIRCLE, new Item.Properties());
    public static final DeferredItem<?> MUSIC_DIVER_ITEM =
        ITEMS.registerSimpleBlockItem("music_diver", MUSIC_DIVER, new Item.Properties());
    public static final DeferredItem<?> POPN_MUSIC_ITEM =
        ITEMS.registerSimpleBlockItem("popn_music", POPN_MUSIC, new Item.Properties());
    public static final DeferredItem<?> MAIMAI_ITEM =
        ITEMS.registerSimpleBlockItem("maimai", MAIMAI, new Item.Properties());
    public static final DeferredItem<?> DDR_SUPERNOVA_ITEM =
        ITEMS.registerSimpleBlockItem("ddr_supernova", DDR_SUPERNOVA, new Item.Properties());
    public static final DeferredItem<?> BEATMANIA_IIDX_LIGHTNING_ITEM =
        ITEMS.registerSimpleBlockItem("beatmania_iidx_lightning", BEATMANIA_IIDX_LIGHTNING, new Item.Properties());
    public static final DeferredItem<?> TAIKO_ITEM =
        ITEMS.registerSimpleBlockItem("taiko", TAIKO, new Item.Properties());
    public static final DeferredItem<?> INITIAL_D_ITEM =
        ITEMS.registerSimpleBlockItem("initial_d", INITIAL_D, new Item.Properties());
    public static final DeferredItem<?> JUBEAT_ITEM =
        ITEMS.registerSimpleBlockItem("jubeat", JUBEAT, new Item.Properties());
    public static final DeferredBlock<GachaponBlock> GACHAPON = BLOCKS.registerBlock(
        "gachapon", GachaponBlock::new,
        BlockBehaviour.Properties.of().mapColor(MapColor.SNOW).strength(2.5F, 1200.0F)
            .sound(SoundType.METAL).noOcclusion());
    public static final DeferredItem<?> GACHAPON_ITEM = ITEMS.registerSimpleBlockItem("gachapon", GACHAPON, new Item.Properties());
    public static final DeferredItem<CapsuleItem> GACHAPON_CAPSULE = ITEMS.registerItem(
        "gachapon_capsule", CapsuleItem::new, new Item.Properties().stacksTo(16));
    public static final DeferredHolder<BlockEntityType<?>, BlockEntityType<GachaponBlockEntity>> GACHAPON_ENTITY =
        BLOCK_ENTITIES.register("gachapon", () -> BlockEntityType.Builder.of(GachaponBlockEntity::new, GACHAPON.get()).build(null));
    public static final DeferredHolder<MenuType<?>, MenuType<GachaponMenu>> GACHAPON_MENU =
        MENUS.register("gachapon", () -> IMenuTypeExtension.create(GachaponMenu::new));
    public static final DeferredHolder<MenuType<?>, MenuType<GachaponAccessMenu>> GACHAPON_ACCESS_MENU =
        MENUS.register("gachapon_access", () -> IMenuTypeExtension.create(GachaponAccessMenu::new));
    public static final DeferredBlock<ClawMachineBlock> CLAW_MACHINE = BLOCKS.registerBlock(
        "claw_machine", ClawMachineBlock::new,
        BlockBehaviour.Properties.of().mapColor(MapColor.SNOW).strength(2.5F, 1200.0F)
            .sound(SoundType.METAL).noOcclusion().lightLevel(state -> state.getValue(ClawMachineBlock.PART) >= 12 ? 10 : 4));
    public static final DeferredItem<?> CLAW_MACHINE_ITEM = ITEMS.registerSimpleBlockItem("claw_machine", CLAW_MACHINE, new Item.Properties());
    public static final DeferredHolder<BlockEntityType<?>, BlockEntityType<ClawMachineBlockEntity>> CLAW_MACHINE_ENTITY =
        BLOCK_ENTITIES.register("claw_machine", () -> BlockEntityType.Builder.of(ClawMachineBlockEntity::new, CLAW_MACHINE.get()).build(null));
    public static final DeferredHolder<MenuType<?>, MenuType<ClawMachineMenu>> CLAW_MACHINE_MENU =
        MENUS.register("claw_machine", () -> IMenuTypeExtension.create(ClawMachineMenu::new));
    public static final DeferredHolder<MenuType<?>, MenuType<ClawMachineMenu>> CLAW_MACHINE_PLAY_MENU =
        MENUS.register("claw_machine_play", () -> IMenuTypeExtension.create(ClawMachineMenu::playFromNetwork));
    public static final DeferredHolder<MenuType<?>, MenuType<ClawMachineAccessMenu>> CLAW_MACHINE_ACCESS_MENU =
        MENUS.register("claw_machine_access", () -> IMenuTypeExtension.create(ClawMachineAccessMenu::new));
    public static final DeferredBlock<ArcadeKioskBlock> ARCADE_KIOSK = BLOCKS.registerBlock(
        "arcade_kiosk", ArcadeKioskBlock::new,
        BlockBehaviour.Properties.of().mapColor(MapColor.SNOW).strength(2.5F, 6.0F)
            .sound(SoundType.METAL).noOcclusion().lightLevel(state ->
                state.getValue(ArcadeKioskBlock.HALF) == net.minecraft.world.level.block.state.properties.DoubleBlockHalf.UPPER ? 7 : 0));
    public static final DeferredItem<?> ARCADE_KIOSK_ITEM = ITEMS.registerSimpleBlockItem("arcade_kiosk", ARCADE_KIOSK, new Item.Properties());
    public static final DeferredHolder<MenuType<?>, MenuType<ArcadeKioskMenu>> ARCADE_KIOSK_MENU =
        MENUS.register("arcade_kiosk", () -> IMenuTypeExtension.create(ArcadeKioskMenu::new));
    public static final DeferredHolder<CreativeModeTab, CreativeModeTab> JAPANESE_ARCADES =
        TABS.register("japanese_arcades", () -> CreativeModeTab.builder()
            .title(Component.translatable("itemGroup.japanesearcades.japanese_arcades"))
            .icon(() -> NOSTALGIA_OP3_ITEM.get().getDefaultInstance())
            .displayItems((parameters, output) -> {
                output.accept(NOSTALGIA_OP3_ITEM.get());
                output.accept(BEATSTREAM_ITEM.get());
                output.accept(SOUND_VOLTEX_VALKYRIE_ITEM.get());
                output.accept(SOUND_VOLTEX_NEMSYS_ITEM.get());
                output.accept(WACCA_ITEM.get());
                output.accept(CHUNITHM_ITEM.get());
                output.accept(ONGEKI_ITEM.get());
                output.accept(GROOVE_COASTER_ITEM.get());
                output.accept(MUSECA_ITEM.get());
                output.accept(PROJECT_DIVA_ITEM.get());
                output.accept(CHRONO_CIRCLE_ITEM.get());
                output.accept(MUSIC_DIVER_ITEM.get());
                output.accept(POPN_MUSIC_ITEM.get());
                output.accept(MAIMAI_ITEM.get());
                output.accept(DDR_SUPERNOVA_ITEM.get());
                output.accept(BEATMANIA_IIDX_LIGHTNING_ITEM.get());
                output.accept(TAIKO_ITEM.get());
                output.accept(INITIAL_D_ITEM.get());
                output.accept(JUBEAT_ITEM.get());
                output.accept(GACHAPON_ITEM.get());
                output.accept(CLAW_MACHINE_ITEM.get());
                output.accept(ARCADE_KIOSK_ITEM.get());
                output.accept(ARCADE_PASS.get());
                output.accept(MECH_SUIT_ITEM.get());
                for (GlowStickSet glowStick : GLOW_STICKS) { output.accept(glowStick.item().get()); }
                output.accept(HATSUNE_MIKU_FIGURE_ITEM.get());
                output.accept(KASANE_TETO_FIGURE_ITEM.get());
                output.accept(FIGURE_DISPLAY_UNIT_ITEM.get());
                output.accept(FIGURE_WALL_SHELF_ITEM.get());
                output.accept(HATSUNE_MIKU_CUTOUT_ITEM.get());
                output.accept(KASANE_TETO_CUTOUT_ITEM.get());
                output.accept(WACCA_POSTER.get());
                for (ArcadePosterSet poster : ARCADE_POSTERS) { output.accept(poster.item().get()); }
                for (MobFigureSet figures : MOB_FIGURES) {
                    output.accept(figures.boxedFigureItem().get());
                    output.accept(figures.figureItem().get());
                    output.accept(figures.emptyBoxItem().get());
                }
                output.accept(CUSTOM_DISPLAY_BOX_ITEM.get());
            })
            .build());

    public JapaneseArcades(IEventBus modEventBus, ModContainer modContainer) {
        BLOCKS.register(modEventBus);
        ITEMS.register(modEventBus);
        TABS.register(modEventBus);
        BLOCK_ENTITIES.register(modEventBus);
        MENUS.register(modEventBus);
        ENTITIES.register(modEventBus);
        COMPONENTS.register(modEventBus);
        ArcadeVillagers.register(modEventBus);
        ArcadeWorldgen.register(modEventBus, modContainer);
        modContainer.registerConfig(ModConfig.Type.SERVER, ArcadeEconomyConfig.SPEC, "japanesearcades-arcade-economy.toml");
        modEventBus.addListener(GachaponNetwork::register);
        modEventBus.addListener(ClawMachineNetwork::register);
        modEventBus.addListener(ArcadeKioskNetwork::register);
        modEventBus.addListener(MechSuitNetwork::register);
        NeoForge.EVENT_BUS.register(GachaponProtection.class);
        NeoForge.EVENT_BUS.register(ClawMachineProtection.class);
        NeoForge.EVENT_BUS.register(TaikoDrumInteraction.class);
        NeoForge.EVENT_BUS.register(InitialDSeatEntity.class);
        NeoForge.EVENT_BUS.register(ArcadePlayInteraction.class);
        NeoForge.EVENT_BUS.register(ArcadeKioskMenu.class);
        NeoForge.EVENT_BUS.addListener(ArcadeKioskMenu::protectOverflowPickup);
        NeoForge.EVENT_BUS.addListener(JapaneseArcades::registerCommands);
        LOGGER.info("Japanese Arcades loaded.");
    }

    private static void registerCommands(RegisterCommandsEvent event) {
        event.getDispatcher().register(Commands.literal("japanesearcadesdev")
            .executes(context -> {
                context.getSource().sendSuccess(
                    () -> Component.literal("Japanese Arcades is loaded."),
                    false);
                return 1;
            }));
    }
}
