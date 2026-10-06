package local.funpack.custom;

import com.mojang.logging.LogUtils;
import net.minecraft.commands.Commands;
import net.minecraft.core.registries.Registries;
import net.minecraft.network.chat.Component;
import net.minecraft.world.item.CreativeModeTab;
import net.minecraft.world.item.Item;
import net.minecraft.world.level.block.SoundType;
import net.minecraft.world.level.block.entity.BlockEntityType;
import net.minecraft.world.level.block.state.BlockBehaviour;
import net.minecraft.world.level.material.MapColor;
import net.neoforged.bus.api.IEventBus;
import net.neoforged.fml.common.Mod;
import net.neoforged.neoforge.common.NeoForge;
import net.neoforged.neoforge.event.RegisterCommandsEvent;
import net.neoforged.neoforge.registries.DeferredBlock;
import net.neoforged.neoforge.registries.DeferredHolder;
import net.neoforged.neoforge.registries.DeferredItem;
import net.neoforged.neoforge.registries.DeferredRegister;
import org.slf4j.Logger;

/** Entry point for our pack's custom features. Works on clients and dedicated servers. */
@Mod(FunPackCustom.MOD_ID)
public final class FunPackCustom {
    public static final String MOD_ID = "funpackcustom";
    public static final Logger LOGGER = LogUtils.getLogger();

    private static final DeferredRegister.Blocks BLOCKS = DeferredRegister.createBlocks(MOD_ID);
    private static final DeferredRegister.Items ITEMS = DeferredRegister.createItems(MOD_ID);
    private static final DeferredRegister<CreativeModeTab> TABS =
        DeferredRegister.create(Registries.CREATIVE_MODE_TAB, MOD_ID);
    private static final DeferredRegister<BlockEntityType<?>> BLOCK_ENTITIES =
        DeferredRegister.create(Registries.BLOCK_ENTITY_TYPE, MOD_ID);

    public static final DeferredBlock<NostalgiaCabinetBlock> NOSTALGIA_OP3 = BLOCKS.registerBlock(
        "nostalgia_op3", NostalgiaCabinetBlock::new,
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
    public static final DeferredHolder<BlockEntityType<?>, BlockEntityType<NostalgiaJukeboxBlockEntity>> NOSTALGIA_JUKEBOX =
        BLOCK_ENTITIES.register("nostalgia_jukebox", () -> BlockEntityType.Builder.of(
            NostalgiaJukeboxBlockEntity::new, NOSTALGIA_OP3.get(), SOUND_VOLTEX_VALKYRIE.get()).build(null));
    public static final DeferredItem<?> NOSTALGIA_OP3_ITEM =
        ITEMS.registerSimpleBlockItem("nostalgia_op3", NOSTALGIA_OP3, new Item.Properties());
    public static final DeferredItem<?> SOUND_VOLTEX_VALKYRIE_ITEM =
        ITEMS.registerSimpleBlockItem("sound_voltex_valkyrie", SOUND_VOLTEX_VALKYRIE, new Item.Properties());
    public static final DeferredHolder<CreativeModeTab, CreativeModeTab> JAPANESE_ARCADES =
        TABS.register("japanese_arcades", () -> CreativeModeTab.builder()
            .title(Component.translatable("itemGroup.funpackcustom.japanese_arcades"))
            .icon(() -> NOSTALGIA_OP3_ITEM.get().getDefaultInstance())
            .displayItems((parameters, output) -> {
                output.accept(NOSTALGIA_OP3_ITEM.get());
                output.accept(SOUND_VOLTEX_VALKYRIE_ITEM.get());
            })
            .build());

    public FunPackCustom(IEventBus modEventBus) {
        BLOCKS.register(modEventBus);
        ITEMS.register(modEventBus);
        TABS.register(modEventBus);
        BLOCK_ENTITIES.register(modEventBus);
        NeoForge.EVENT_BUS.addListener(FunPackCustom::registerCommands);
        LOGGER.info("Fun Pack Custom loaded. Development environment is ready.");
    }

    private static void registerCommands(RegisterCommandsEvent event) {
        event.getDispatcher().register(Commands.literal("funpackdev")
            .executes(context -> {
                context.getSource().sendSuccess(
                    () -> Component.literal("Fun Pack Custom is loaded. Ready to build our own mods!"),
                    false);
                return 1;
            }));
    }
}
