package local.funpack.custom;

import com.mojang.logging.LogUtils;
import net.minecraft.commands.Commands;
import net.minecraft.network.chat.Component;
import net.neoforged.fml.common.Mod;
import net.neoforged.neoforge.common.NeoForge;
import net.neoforged.neoforge.event.RegisterCommandsEvent;
import org.slf4j.Logger;

/** Entry point for our pack's custom features. Works on clients and dedicated servers. */
@Mod(FunPackCustom.MOD_ID)
public final class FunPackCustom {
    public static final String MOD_ID = "funpackcustom";
    public static final Logger LOGGER = LogUtils.getLogger();

    public FunPackCustom() {
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
