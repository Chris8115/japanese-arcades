package local.funpack.custom;

import com.google.gson.JsonElement;
import com.mojang.datafixers.util.Pair;
import com.mojang.serialization.DynamicOps;
import com.mojang.serialization.JsonOps;
import it.unimi.dsi.fastutil.objects.ObjectArrayList;
import java.util.ArrayList;
import java.util.Collections;
import java.util.IdentityHashMap;
import java.util.List;
import java.util.Set;
import java.util.WeakHashMap;
import net.minecraft.core.RegistryAccess;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.level.levelgen.structure.StructureType;
import net.minecraft.world.level.levelgen.structure.pools.StructurePoolElement;
import net.minecraft.world.level.levelgen.structure.pools.StructureTemplatePool;
import net.minecraft.world.level.levelgen.structure.templatesystem.StructureProcessorType;
import net.neoforged.bus.api.IEventBus;
import net.neoforged.fml.ModContainer;
import net.neoforged.fml.config.ModConfig;
import net.neoforged.neoforge.common.NeoForge;
import net.neoforged.neoforge.event.TagsUpdatedEvent;
import net.neoforged.neoforge.registries.DeferredHolder;
import net.neoforged.neoforge.registries.DeferredRegister;

/** Additive village integration; no vanilla or other-mod datapack files are replaced. */
public final class ArcadeWorldgen {
    private static final DeferredRegister<StructureType<?>> TYPES =
        DeferredRegister.create(Registries.STRUCTURE_TYPE, FunPackCustom.MOD_ID);
    public static final DeferredHolder<StructureType<?>, StructureType<ArcadeStructure>> ARCADE =
        TYPES.register("japanese_arcade", () -> () -> ArcadeStructure.CODEC);
    private static final DeferredRegister<StructureProcessorType<?>> PROCESSORS =
        DeferredRegister.create(Registries.STRUCTURE_PROCESSOR, FunPackCustom.MOD_ID);
    public static final DeferredHolder<StructureProcessorType<?>, StructureProcessorType<ArcadePaintingProcessor>> PAINTING_ANCHOR =
        PROCESSORS.register("arcade_painting_anchor", () -> () -> ArcadePaintingProcessor.CODEC);
    public static final ResourceLocation VILLAGE_POOL = id("arcade/village");
    public static final ResourceLocation INTEGRATED_VILLAGE_POOL = id("arcade/integrated_village");
    static final List<ResourceLocation> VILLAGE_HOUSES = List.of("plains", "desert", "savanna", "snowy", "taiga")
        .stream().map(style -> ResourceLocation.withDefaultNamespace("village/" + style + "/houses")).toList();
    // These ground-level villages use the same air-at-feet house connector. Elevated and water villages need separate foundations.
    static final List<ResourceLocation> INTEGRATED_VILLAGE_HOUSES = List.of(
        "tavern_village/house", "cabin_village/house/house", "clockwork_village/house/house1",
        "clockwork_village/house/house2", "kutcha_village/house/house", "marketstead_village/house/house1",
        "marketstead_village/house/house2", "mediterranean_village/house/house")
        .stream().map(path -> ResourceLocation.fromNamespaceAndPath("integrated_villages", path)).toList();
    // Registry objects belong to individual server loads. Weak keys never retain closed worlds.
    private static final WeakHashMap<StructureTemplatePool, List<Pair<StructurePoolElement, Integer>>> INSERTED =
        new WeakHashMap<>();

    private ArcadeWorldgen() {}

    public static ResourceLocation id(String path) {
        return ResourceLocation.fromNamespaceAndPath(FunPackCustom.MOD_ID, path);
    }

    public static void register(IEventBus modBus, ModContainer container) {
        TYPES.register(modBus);
        PROCESSORS.register(modBus);
        container.registerConfig(ModConfig.Type.COMMON, ArcadeWorldgenConfig.SPEC, "funpackcustom-arcade-worldgen.toml");
        NeoForge.EVENT_BUS.addListener(ArcadeWorldgen::tagsUpdated);
    }

    private static void tagsUpdated(TagsUpdatedEvent event) {
        if (event.getUpdateCause() == TagsUpdatedEvent.UpdateCause.SERVER_DATA_LOAD) {
            injectVillagePools(event.getRegistryAccess(), ArcadeWorldgenConfig.villageWeight());
        }
    }

    static void injectVillagePools(RegistryAccess access, int weight) {
        injectVillagePools(access, weight, VILLAGE_POOL, VILLAGE_HOUSES);
        injectVillagePools(access, weight, INTEGRATED_VILLAGE_POOL, INTEGRATED_VILLAGE_HOUSES);
    }

    private static void injectVillagePools(RegistryAccess access, int weight, ResourceLocation sourceId,
            List<ResourceLocation> targets) {
        var pools = access.registryOrThrow(Registries.TEMPLATE_POOL);
        var source = pools.get(sourceId);
        List<Pair<StructurePoolElement, Integer>> additions = source == null ? List.of() : List.copyOf(source.rawTemplates);
        DynamicOps<JsonElement> ops = access.createSerializationContext(JsonOps.INSTANCE);
        for (ResourceLocation target : targets) {
            var pool = pools.get(target);
            if (pool != null) { updatePool(pool, additions, weight, ops); }
        }
    }

    /** Reconcile only entries inserted by this class, including reloads of the same registry. */
    static synchronized void updatePool(StructureTemplatePool pool, List<Pair<StructurePoolElement, Integer>> additions,
            int multiplier, DynamicOps<JsonElement> ops) {
        List<Pair<StructurePoolElement, Integer>> raw = new ArrayList<>(pool.rawTemplates);
        ObjectArrayList<StructurePoolElement> weighted = new ObjectArrayList<>(pool.templates);
        List<Pair<StructurePoolElement, Integer>> previous = INSERTED.remove(pool);
        if (previous != null) {
            Set<Pair<StructurePoolElement, Integer>> owned = Collections.newSetFromMap(new IdentityHashMap<>());
            owned.addAll(previous);
            raw.removeIf(owned::contains);
            for (var entry : previous) {
                int remaining = entry.getSecond();
                for (int i = weighted.size() - 1; i >= 0 && remaining > 0; i--) {
                    if (weighted.get(i) == entry.getFirst()) { weighted.remove(i); remaining--; }
                }
            }
        }
        List<Pair<StructurePoolElement, Integer>> inserted = new ArrayList<>();
        if (multiplier > 0) {
            for (var addition : additions) {
                JsonElement encoded = encode(addition.getFirst(), ops);
                // A datapack may already have added this exact element; retain its chosen weight.
                if (encoded != null && raw.stream().anyMatch(existing -> encoded.equals(encode(existing.getFirst(), ops)))) {
                    continue;
                }
                int weight = Math.min(150, Math.multiplyExact(addition.getSecond(), multiplier));
                var entry = Pair.of(addition.getFirst(), weight);
                raw.add(entry);
                inserted.add(entry);
                for (int i = 0; i < weight; i++) { weighted.add(entry.getFirst()); }
            }
        }
        if (previous != null || !inserted.isEmpty()) {
            // Copy instead of clearing a collection that another generation task may already hold.
            pool.rawTemplates = raw;
            pool.templates = weighted;
            pool.maxSize = Integer.MIN_VALUE;
        }
        if (!inserted.isEmpty()) { INSERTED.put(pool, inserted); }
    }

    private static JsonElement encode(StructurePoolElement element, DynamicOps<JsonElement> ops) {
        return StructurePoolElement.CODEC.encodeStart(ops, element).result().orElse(null);
    }
}
