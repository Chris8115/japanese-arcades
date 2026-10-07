package local.japanesearcades;

import com.mojang.datafixers.util.Pair;
import com.mojang.serialization.JsonOps;
import java.util.List;
import java.util.Optional;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Holder;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.registries.Registries;
import net.minecraft.gametest.framework.GameTest;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.nbt.Tag;
import net.minecraft.resources.ResourceKey;
import net.minecraft.util.RandomSource;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.level.ChunkPos;
import net.minecraft.world.level.LevelHeightAccessor;
import net.minecraft.world.level.biome.Biomes;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.Mirror;
import net.minecraft.world.level.block.Rotation;
import net.minecraft.world.level.chunk.ChunkGenerator;
import net.minecraft.world.level.levelgen.FlatLevelSource;
import net.minecraft.world.level.levelgen.Heightmap;
import net.minecraft.world.level.levelgen.flat.FlatLayerInfo;
import net.minecraft.world.level.levelgen.flat.FlatLevelGeneratorSettings;
import net.minecraft.world.level.levelgen.structure.BoundingBox;
import net.minecraft.world.level.levelgen.structure.PoolElementStructurePiece;
import net.minecraft.world.level.levelgen.structure.Structure;
import net.minecraft.world.level.levelgen.structure.pools.DimensionPadding;
import net.minecraft.world.level.levelgen.structure.pools.EmptyPoolElement;
import net.minecraft.world.level.levelgen.structure.pools.JigsawPlacement;
import net.minecraft.world.level.levelgen.structure.pools.StructurePoolElement;
import net.minecraft.world.level.levelgen.structure.pools.StructureTemplatePool;
import net.minecraft.world.level.levelgen.structure.pools.alias.PoolAliasLookup;
import net.minecraft.world.level.levelgen.structure.templatesystem.LiquidSettings;
import net.minecraft.world.level.levelgen.structure.templatesystem.StructurePlaceSettings;
import net.minecraft.world.level.levelgen.structure.templatesystem.StructureTemplate;
import net.neoforged.neoforge.gametest.GameTestHolder;
import net.neoforged.neoforge.gametest.PrefixGameTestTemplate;

/** Native pool selection, rotated furniture/entity placement, and safe generation sites. */
@GameTestHolder(JapaneseArcades.MOD_ID)
@PrefixGameTestTemplate(false)
public final class ArcadeWorldgenGameTests {
    private static final String TEMPLATE = "arcade/japanese_arcade";

    @GameTest(template = "nostalgia_test")
    public static void poolReloadPreservesOtherEntriesAndNeverDuplicates(GameTestHelper helper) {
        var registry = helper.getLevel().registryAccess().registryOrThrow(Registries.TEMPLATE_POOL);
        var fallback = registry.getHolderOrThrow(ResourceKey.create(Registries.TEMPLATE_POOL,
            net.minecraft.resources.ResourceLocation.withDefaultNamespace("empty")));
        var original = Pair.<StructurePoolElement, Integer>of(EmptyPoolElement.INSTANCE, 7);
        var pool = new StructureTemplatePool(fallback, List.of(original));
        var arcade = StructurePoolElement.single("japanesearcades:arcade/japanese_arcade_village")
            .apply(StructureTemplatePool.Projection.RIGID);
        var additions = List.of(Pair.<StructurePoolElement, Integer>of(arcade, 1));
        var ops = helper.getLevel().registryAccess().createSerializationContext(JsonOps.INSTANCE);
        pool.getMaxSize(helper.getLevel().getStructureManager());
        ArcadeWorldgen.updatePool(pool, additions, 2, ops);
        helper.assertTrue(pool.size() == 9 && pool.rawTemplates.getFirst() == original,
            "Village injection changed pre-existing entries or their weights");
        helper.assertTrue(pool.getMaxSize(helper.getLevel().getStructureManager()) >= 18,
            "Pool height cache did not include the tall arcade");
        ArcadeWorldgen.updatePool(pool, additions, 2, ops);
        helper.assertTrue(pool.size() == 9 && pool.rawTemplates.size() == 2,
            "A resource reload duplicated the arcade weight");

        // Emulate an independent mod adding a distinct weighted entry after our first reload.
        var other = StructurePoolElement.single("minecraft:village/plains/houses/plains_small_house_1")
            .apply(StructureTemplatePool.Projection.RIGID);
        var otherEntry = Pair.<StructurePoolElement, Integer>of(other, 3);
        pool.rawTemplates.add(otherEntry);
        for (int i = 0; i < 3; i++) { pool.templates.add(other); }
        ArcadeWorldgen.updatePool(pool, additions, 4, ops);
        helper.assertTrue(pool.size() == 14 && pool.rawTemplates.contains(otherEntry),
            "Changing arcade weight discarded another mod's subsequent pool entry");
        ArcadeWorldgen.updatePool(pool, additions, 0, ops);
        helper.assertTrue(pool.size() == 10 && pool.rawTemplates.equals(List.of(original, otherEntry)),
            "Disabling village integration removed something other than our own addition");
        helper.assertTrue(pool.getShuffledTemplates(RandomSource.create(1)).stream().filter(element -> element == other).count() == 3,
            "Other mod's weighted runtime selection changed");

        // A fresh server registry is independent; a datapack-provided arcade keeps its own weight.
        var authored = Pair.<StructurePoolElement, Integer>of(arcade, 5);
        var fresh = new StructureTemplatePool(fallback, List.of(original, authored));
        ArcadeWorldgen.updatePool(fresh, additions, 2, ops);
        ArcadeWorldgen.updatePool(fresh, additions, 0, ops);
        helper.assertTrue(fresh.size() == 12 && fresh.rawTemplates.get(1) == authored,
            "An independently authored arcade entry was duplicated or removed");
        helper.succeed();
    }

    @GameTest(template = "arcade_test", timeoutTicks = 120)
    public static void northArcadePlacesUsableMachinesAndSupportedDecor(GameTestHelper helper) {
        placeAndCheck(helper, Rotation.NONE);
    }

    @GameTest(template = "arcade_test", timeoutTicks = 120)
    public static void eastArcadePlacesUsableMachinesAndSupportedDecor(GameTestHelper helper) {
        placeAndCheck(helper, Rotation.CLOCKWISE_90);
    }

    @GameTest(template = "arcade_test", timeoutTicks = 120)
    public static void southArcadePlacesUsableMachinesAndSupportedDecor(GameTestHelper helper) {
        placeAndCheck(helper, Rotation.CLOCKWISE_180);
    }

    @GameTest(template = "arcade_test", timeoutTicks = 120)
    public static void westArcadePlacesUsableMachinesAndSupportedDecor(GameTestHelper helper) {
        placeAndCheck(helper, Rotation.COUNTERCLOCKWISE_90);
    }

    private static void placeAndCheck(GameTestHelper helper, Rotation rotation) {
        var level = helper.getLevel();
        var manager = level.getStructureManager();
        var template = manager.get(ArcadeWorldgen.id(TEMPLATE)).orElseThrow();
        var element = level.registryAccess().registryOrThrow(Registries.TEMPLATE_POOL)
            .get(ArcadeWorldgen.id("arcade/start")).getRandomTemplate(RandomSource.create(42));
        BlockPos origin = template.getZeroPositionWithTransform(helper.absolutePos(new BlockPos(4, 2, 4)), Mirror.NONE, rotation);
        BoundingBox bounds = element.getBoundingBox(manager, origin, rotation);
        var placement = new StructurePlaceSettings().setRotation(rotation);
        List<BlockPos> surroundingGround = List.of(new BlockPos(0, 0, 0), new BlockPos(0, 1, 0),
            new BlockPos(18, 0, 0), new BlockPos(18, 1, 0), new BlockPos(0, 0, 18), new BlockPos(0, 1, 18),
            new BlockPos(18, 0, 18), new BlockPos(18, 1, 18)).stream()
            .map(pos -> StructureTemplate.calculateRelativePosition(placement, pos).offset(origin)).toList();
        for (BlockPos ground : surroundingGround) { level.setBlock(ground, Blocks.DEEPSLATE.defaultBlockState(), 18); }
        helper.assertTrue(element.place(manager, level, level.structureManager(), level.getChunkSource().getGenerator(),
            origin, origin, rotation, bounds, RandomSource.create(42), LiquidSettings.IGNORE_WATERLOGGING, false),
            "Native single-pool element failed to place the arcade");
        for (BlockPos ground : surroundingGround) {
            helper.assertTrue(level.getBlockState(ground).is(Blocks.DEEPSLATE),
                "Arcade excavated surrounding ground instead of preserving it at " + ground);
        }
        checkContents(helper, template, origin, rotation);
        // Exercise normal neighbor validation rather than relying on template placement's known-shape flag.
        for (Block block : contentBlocks()) {
            for (var info : template.filterBlocks(origin, new StructurePlaceSettings().setRotation(rotation), block)) {
                level.updateNeighborsAt(info.pos(), block);
            }
        }
        helper.runAfterDelay(4, () -> {
            checkContents(helper, template, origin, rotation);
            helper.succeed();
        });
    }

    private static List<Block> contentBlocks() {
        return List.of(JapaneseArcades.JUBEAT.get(), JapaneseArcades.WACCA.get(), JapaneseArcades.CHUNITHM.get(),
            JapaneseArcades.TAIKO.get(), JapaneseArcades.PROJECT_DIVA.get(), JapaneseArcades.NOSTALGIA_OP3.get(),
            JapaneseArcades.ARCADE_KIOSK.get());
    }

    static void checkContents(GameTestHelper helper, StructureTemplate template, BlockPos origin, Rotation rotation) {
        var level = helper.getLevel();
        var settings = new StructurePlaceSettings().setRotation(rotation);
        int machines = 0;
        for (Block block : contentBlocks()) {
            var sections = template.filterBlocks(origin, settings, block);
            helper.assertFalse(sections.isEmpty(), "Arcade is missing " + BuiltInRegistries.BLOCK.getKey(block));
            for (var section : sections) {
                helper.assertTrue(level.getBlockState(section.pos()).equals(section.state()),
                    "Missing/incorrect rotated machine section at " + section.pos() + ": " + section.state());
                if (section.nbt() != null) {
                    var entity = level.getBlockEntity(section.pos());
                    helper.assertTrue(entity != null, "Generated machine did not create its functional block entity");
                    helper.assertTrue(entity.saveWithFullMetadata(level.registryAccess()).getString("id").equals(section.nbt().getString("id")),
                        "Template's machine block entity type was lost");
                    machines++;
                }
            }
        }
        helper.assertTrue(machines == 6, "Arcade did not initialize its six rhythm machine inventories");
        helper.assertTrue(helper.getEntities(EntityType.PAINTING).size() == 4, "Arcade's four wall artworks did not spawn");
        var templateEntities = template.save(new CompoundTag()).getList("entities", Tag.TAG_COMPOUND);
        for (var painting : helper.getEntities(EntityType.PAINTING)) {
            var variant = painting.getVariant().unwrapKey().orElseThrow().location();
            helper.assertTrue(painting.survives(), "Painting " + variant + " at " + painting.getPos()
                + " facing " + painting.getDirection() + " lacks support or overlaps another entity; collision-free="
                + level.noCollision(painting) + ", bounds=" + painting.getBoundingBox());
            helper.assertTrue(variant.getNamespace().equals(JapaneseArcades.MOD_ID),
                "Structure lost its custom wall artwork variant");
            boolean matched = false;
            for (int i = 0; i < templateEntities.size(); i++) {
                var raw = templateEntities.getCompound(i);
                var nbt = raw.getCompound("nbt");
                if (!variant.toString().equals(nbt.getString("variant"))) { continue; }
                var coordinates = raw.getList("blockPos", Tag.TAG_INT);
                var expectedAnchor = StructureTemplate.calculateRelativePosition(settings,
                    new BlockPos(coordinates.getInt(0), coordinates.getInt(1), coordinates.getInt(2))).offset(origin);
                helper.assertTrue(painting.getPos().equals(expectedAnchor), "Painting's native attachment anchor shifted after template rotation");
                helper.assertTrue(painting.getDirection() == rotation.rotate(net.minecraft.core.Direction.from2DDataValue(nbt.getByte("facing"))),
                    "Painting facing was transformed incorrectly");
                var saved = new CompoundTag();
                painting.save(saved);
                helper.assertTrue(saved.getInt("TileX") == expectedAnchor.getX() && saved.getInt("TileY") == expectedAnchor.getY()
                    && saved.getInt("TileZ") == expectedAnchor.getZ(), "Painting persisted a local rather than world-space attachment");
                matched = true;
            }
            helper.assertTrue(matched, "Spawned painting is not one of the template's authored entities");
        }
        helper.assertEntityPresent(EntityType.VILLAGER);
        for (var jigsaw : template.filterBlocks(origin, settings, Blocks.JIGSAW)) {
            helper.assertFalse(level.getBlockState(jigsaw.pos()).is(Blocks.JIGSAW), "Worldgen left an exposed jigsaw block");
        }
    }

    @GameTest(template = "arcade_test", timeoutTicks = 120)
    public static void nativeRoadJigsawActuallyAttachesTheFullArcade(GameTestHelper helper) {
        var level = helper.getLevel();
        var pools = level.registryAccess().registryOrThrow(Registries.TEMPLATE_POOL);
        var road = pools.getHolderOrThrow(ResourceKey.create(Registries.TEMPLATE_POOL, ArcadeWorldgen.id("arcade/test_road")));
        var context = context(helper, level.getChunkSource().getGenerator(), level, 7331);
        var generated = JigsawPlacement.addPieces(context, road, Optional.empty(), 1,
            helper.absolutePos(new BlockPos(15, 3, 15)), false, Optional.empty(), 32,
            PoolAliasLookup.EMPTY, DimensionPadding.ZERO, LiquidSettings.IGNORE_WATERLOGGING).orElseThrow();
        var builder = generated.getPiecesBuilder();
        var pieces = builder.build().pieces();
        helper.assertTrue(pieces.size() == 2, "Native road generation did not attach the village arcade as its child");
        var bounds = builder.getBoundingBox();
        BlockPos target = helper.absolutePos(new BlockPos(4, 2, 4));
        for (var piece : pieces) { piece.move(target.getX() - bounds.minX(), target.getY() - bounds.minY(), target.getZ() - bounds.minZ()); }
        var placedBounds = builder.getBoundingBox();
        PoolElementStructurePiece arcade = null;
        for (var piece : pieces) {
            var poolPiece = (PoolElementStructurePiece) piece;
            poolPiece.place(level, level.structureManager(), level.getChunkSource().getGenerator(), RandomSource.create(3),
                placedBounds, poolPiece.getPosition(), false);
            if (poolPiece.getBoundingBox().getYSpan() >= 18) { arcade = poolPiece; }
        }
        helper.assertTrue(arcade != null, "Jigsaw child was not the full-height arcade");
        var template = level.getStructureManager().get(ArcadeWorldgen.id("arcade/japanese_arcade_village")).orElseThrow();
        var placedArcade = arcade;
        checkContents(helper, template, placedArcade.getPosition(), placedArcade.getRotation());
        var connector = template.filterBlocks(placedArcade.getPosition(),
            new StructurePlaceSettings().setRotation(placedArcade.getRotation()), Blocks.JIGSAW).getFirst();
        helper.assertTrue(level.getBlockState(connector.pos()).is(Blocks.DIRT_PATH), "Entrance connector did not become a walkable path");
        helper.assertTrue(level.getBlockState(connector.pos().relative(
            net.minecraft.world.level.block.JigsawBlock.getFrontFacing(connector.state()))).is(Blocks.DIRT_PATH),
            "Arcade's floor-height connector did not align with its neighboring road");
        helper.runAfterDelay(4, () -> {
            checkContents(helper, template, placedArcade.getPosition(), placedArcade.getRotation());
            helper.succeed();
        });
    }

    @GameTest(template = "nostalgia_test")
    public static void standaloneUsesDryGroundAndRejectsWaterAndLowCeilings(GameTestHelper helper) {
        var level = helper.getLevel();
        var structure = (ArcadeStructure) level.registryAccess().registryOrThrow(Registries.STRUCTURE)
            .get(ArcadeWorldgen.id("japanese_arcade"));
        var dryGenerator = flat(helper, Blocks.GRASS_BLOCK);
        for (long seed = 1; seed <= 4; seed++) {
            var dry = context(helper, dryGenerator, level, seed);
            var start = structure.findValidGenerationPoint(dry);
            helper.assertTrue(start.isPresent(), "Standalone arcade rejected valid flat dry terrain");
            var pieces = start.orElseThrow().getPiecesBuilder();
            helper.assertTrue(pieces.build().pieces().size() == 1, "Standalone did not generate exactly its own full building");
            var bounds = pieces.getBoundingBox();
            int surface = dryGenerator.getFirstFreeHeight(bounds.getCenter().getX(), bounds.getCenter().getZ(),
                Heightmap.Types.WORLD_SURFACE_WG, level, level.getChunkSource().randomState());
            helper.assertTrue(bounds.minY() + 2 == surface, "Walking floor was buried or raised above the projected ground");
            var lowCeiling = LevelHeightAccessor.create(level.getMinBuildHeight(), bounds.maxY() - level.getMinBuildHeight() + 1);
            helper.assertFalse(ArcadeStructure.suitableTerrain(context(helper, dryGenerator, lowCeiling, seed), bounds, 3),
                "Arcade accepted a site without enough upward build clearance");
        }
        helper.assertTrue(structure.findValidGenerationPoint(context(helper, flat(helper, Blocks.WATER), level, 5)).isEmpty(),
            "Standalone arcade accepted a water surface");
        helper.succeed();
    }

    private static FlatLevelSource flat(GameTestHelper helper, Block surface) {
        var biome = helper.getLevel().registryAccess().registryOrThrow(Registries.BIOME).getHolderOrThrow(Biomes.PLAINS);
        var settings = new FlatLevelGeneratorSettings(Optional.empty(), biome, List.of());
        settings.getLayersInfo().add(new FlatLayerInfo(1, Blocks.BEDROCK));
        settings.getLayersInfo().add(new FlatLayerInfo(2, Blocks.DIRT));
        settings.getLayersInfo().add(new FlatLayerInfo(1, surface));
        settings.updateLayers();
        return new FlatLevelSource(settings);
    }

    private static Structure.GenerationContext context(GameTestHelper helper, ChunkGenerator generator, LevelHeightAccessor height, long seed) {
        var level = helper.getLevel();
        return new Structure.GenerationContext(level.registryAccess(), generator, generator.getBiomeSource(),
            level.getChunkSource().randomState(), level.getStructureManager(), seed,
            new ChunkPos(helper.absolutePos(new BlockPos(8, 1, 8))), height, holder -> true);
    }
}
