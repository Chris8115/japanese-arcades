package local.japanesearcades;

import static local.japanesearcades.GachaponTransactionGameTests.createPlayer;

import java.util.List;
import java.util.function.Consumer;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.component.DataComponents;
import net.minecraft.gametest.framework.GameTest;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.tags.PaintingVariantTags;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.item.ItemEntity;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.item.component.CustomData;
import net.minecraft.world.item.context.UseOnContext;
import net.minecraft.world.level.GameType;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.phys.BlockHitResult;
import net.minecraft.world.phys.Vec3;
import net.neoforged.neoforge.common.NeoForge;
import net.neoforged.neoforge.event.entity.EntityJoinLevelEvent;
import net.neoforged.neoforge.gametest.GameTestHolder;
import net.neoforged.neoforge.gametest.PrefixGameTestTemplate;

/** Runs every new artwork through the actual shared hanging-entity lifecycle. */
@GameTestHolder(JapaneseArcades.MOD_ID)
@PrefixGameTestTemplate(false)
public final class ArcadePosterGameTests {
    private static final BlockPos WALL = new BlockPos(3, 3, 3);

    private static ServerPlayer player(GameTestHelper helper, String name, GameType mode) {
        var player = createPlayer(helper, name, mode);
        player.setPos(Vec3.atCenterOf(helper.absolutePos(new BlockPos(6, 1, 6))));
        return player;
    }

    private static void wall(GameTestHelper helper, BlockPos wall, boolean present) {
        for (int y = 0; y < 2; y++) { helper.setBlock(wall.above(y), present ? Blocks.STONE : Blocks.AIR); }
    }

    private static InteractionResult place(GameTestHelper helper, ServerPlayer player, Direction facing, BlockPos wall) {
        BlockPos absolute = helper.absolutePos(wall);
        var hit = new BlockHitResult(Vec3.atCenterOf(absolute).relative(facing, .5), facing, absolute, false);
        return player.getMainHandItem().getItem().useOn(new UseOnContext(player, InteractionHand.MAIN_HAND, hit));
    }

    private static List<ArcadePosterEntity> posters(GameTestHelper helper) {
        return helper.getEntities(JapaneseArcades.ARCADE_POSTER_ENTITY.get(), WALL, 5);
    }

    private static ArcadePosterEntity onlyPoster(GameTestHelper helper) {
        var posters = posters(helper);
        helper.assertTrue(posters.size() == 1, "Expected one arcade poster, found " + posters.size());
        return posters.getFirst();
    }

    @GameTest(template = "nostalgia_test")
    public static void everyArtworkKeepsItsDimensionsPickAndDropAfterReloadOnAllFacings(GameTestHelper helper) {
        var player = player(helper, "PosterCollection", GameType.SURVIVAL);
        for (var print : JapaneseArcades.ARCADE_POSTERS) {
            for (Direction facing : Direction.Plane.HORIZONTAL) {
                wall(helper, WALL, true);
                player.setItemInHand(InteractionHand.MAIN_HAND, new ItemStack(print.item().get(), 2));
                helper.assertTrue(place(helper, player, facing, WALL).consumesAction(), "Placement failed: " + print.path() + " " + facing);
                var poster = onlyPoster(helper);
                var bounds = poster.getBoundingBox();
                double width = facing.getAxis() == Direction.Axis.X ? bounds.getZsize() : bounds.getXsize();
                helper.assertTrue(player.getMainHandItem().getCount() == 1 && poster.getPickResult().is(print.item().get()),
                    "Placement consumed the wrong count or pick block changed artwork: " + print.path());
                helper.assertTrue(poster.getVariant().is(ArcadePosterEntity.variantKey(print.path()))
                    && !poster.getVariant().is(PaintingVariantTags.PLACEABLE), "Wrong or randomly placeable artwork: " + print.path());
                helper.assertTrue(Math.abs(width - WaccaPosterEntity.WIDTH) < 1.0E-7
                    && Math.abs(bounds.getYsize() - WaccaPosterEntity.HEIGHT) < 1.0E-7
                    && Math.abs(bounds.minY - helper.absolutePos(WALL).getY()) < 1.0E-7,
                    "Print changed the original WACCA dimensions: " + print.path());
                CompoundTag saved = new CompoundTag();
                helper.assertTrue(poster.save(saved), "Poster refused world saving");
                poster.discard();
                var loaded = EntityType.loadEntityRecursive(saved, helper.getLevel(), entity -> entity);
                helper.assertTrue(loaded instanceof ArcadePosterEntity && !(loaded instanceof WaccaPosterEntity),
                    "Saved poster loaded as the wrong registered entity");
                var restored = (ArcadePosterEntity) loaded;
                helper.assertTrue(restored.getDirection() == facing && restored.getBoundingBox().equals(bounds)
                    && restored.getVariant().is(ArcadePosterEntity.variantKey(print.path()))
                    && restored.getPickResult().is(print.item().get()) && restored.survives(),
                    "Reload changed artwork, item, support, facing or dimensions: " + print.path());
                helper.assertTrue(helper.getLevel().addFreshEntity(restored), "Saved poster refused reinsertion");
                restored.hurt(helper.getLevel().damageSources().playerAttack(player), 1);
                helper.assertTrue(posters(helper).isEmpty(), "Survival attack did not remove the poster");
                helper.assertItemEntityCountIs(print.item().get(), WALL, 5, 1);
                helper.assertTrue(helper.getEntities(EntityType.ITEM, WALL, 5).size() == 1, "Breaking a poster duplicated or changed its prize");
                helper.getEntities(EntityType.ITEM, WALL, 5).forEach(ItemEntity::discard);
                wall(helper, WALL, false);
            }
        }
        helper.succeed();
    }

    @GameTest(template = "nostalgia_test")
    public static void everyArtworkRejectsUnsupportedObstructedOverlappingAndCanceledPlacement(GameTestHelper helper) {
        var player = player(helper, "PosterFailures", GameType.SURVIVAL);
        Direction facing = Direction.NORTH;
        for (var print : JapaneseArcades.ARCADE_POSTERS) {
            player.setItemInHand(InteractionHand.MAIN_HAND, new ItemStack(print.item().get(), 2));
            wall(helper, WALL, true);
            helper.assertTrue(place(helper, player, Direction.UP, WALL) == InteractionResult.FAIL
                && place(helper, player, Direction.DOWN, WALL) == InteractionResult.FAIL, "Poster accepted a floor or ceiling");
            helper.setBlock(WALL.above(), Blocks.AIR);
            helper.assertTrue(place(helper, player, facing, WALL) == InteractionResult.FAIL, "Poster accepted one missing wall cell");
            wall(helper, WALL, true);
            helper.setBlock(WALL.relative(facing), Blocks.STONE);
            helper.assertTrue(place(helper, player, facing, WALL) == InteractionResult.FAIL, "Poster entered a solid block");
            helper.setBlock(WALL.relative(facing), Blocks.AIR);
            Consumer<EntityJoinLevelEvent> veto = event -> {
                if (event.getEntity() instanceof ArcadePosterEntity poster
                    && poster.getPos().equals(helper.absolutePos(WALL.relative(facing)))) { event.setCanceled(true); }
            };
            NeoForge.EVENT_BUS.addListener(veto);
            try {
                helper.assertTrue(place(helper, player, facing, WALL) == InteractionResult.FAIL, "Canceled spawn reported success");
            } finally { NeoForge.EVENT_BUS.unregister(veto); }
            helper.assertTrue(player.getMainHandItem().getCount() == 2 && posters(helper).isEmpty(), "Failed placement consumed a prize or created a poster");
            helper.assertTrue(place(helper, player, facing, WALL).consumesAction(), "Valid placement failed after rejected attempts");
            helper.assertTrue(place(helper, player, facing, WALL) == InteractionResult.FAIL
                && player.getMainHandItem().getCount() == 1 && posters(helper).size() == 1, "Overlapping identical artwork consumed or duplicated a prize");
            onlyPoster(helper).discard();
        }
        helper.succeed();
    }

    @GameTest(template = "nostalgia_test")
    public static void differentPrintsAndLegacyWaccaShareWallSpacingAndOverlapRules(GameTestHelper helper) {
        var player = player(helper, "PosterNeighbors", GameType.SURVIVAL);
        var first = JapaneseArcades.ARCADE_POSTERS.getFirst();
        var second = JapaneseArcades.ARCADE_POSTERS.get(1);
        Direction facing = Direction.NORTH;
        BlockPos neighbor = WALL.relative(facing.getClockWise());
        BlockPos original = WALL.relative(facing.getCounterClockWise());
        wall(helper, WALL, true);
        wall(helper, neighbor, true);
        wall(helper, original, true);
        player.setItemInHand(InteractionHand.MAIN_HAND, new ItemStack(first.item().get()));
        helper.assertTrue(place(helper, player, facing, WALL).consumesAction(), "First poster failed");
        var center = onlyPoster(helper);
        player.setItemInHand(InteractionHand.MAIN_HAND, new ItemStack(second.item().get(), 2));
        helper.assertTrue(place(helper, player, facing, WALL) == InteractionResult.FAIL
            && player.getMainHandItem().getCount() == 2, "Different print overlapped an occupied poster");
        helper.assertTrue(place(helper, player, facing, neighbor).consumesAction(), "Different print could not fit immediately beside its neighbor");
        player.setItemInHand(InteractionHand.MAIN_HAND, new ItemStack(JapaneseArcades.WACCA_POSTER.get(), 2));
        helper.assertTrue(place(helper, player, facing, WALL) == InteractionResult.FAIL
            && player.getMainHandItem().getCount() == 2, "Legacy WACCA overlapped a new print");
        helper.assertTrue(place(helper, player, facing, original).consumesAction(), "Legacy WACCA could not fit beside a new print");
        var legacy = helper.getEntities(JapaneseArcades.WACCA_POSTER_ENTITY.get(), WALL, 5).getFirst();
        player.setItemInHand(InteractionHand.MAIN_HAND, new ItemStack(first.item().get(), 2));
        helper.assertTrue(place(helper, player, facing, original) == InteractionResult.FAIL
            && player.getMainHandItem().getCount() == 2, "New print overlapped legacy WACCA");
        helper.assertTrue(posters(helper).stream().filter(poster -> poster != center)
            .noneMatch(poster -> poster.getBoundingBox().intersects(center.getBoundingBox()))
            && !legacy.getBoundingBox().intersects(center.getBoundingBox()), "Adjacent print hitboxes overlap");
        center.hurt(helper.getLevel().damageSources().playerAttack(player), 1);
        helper.assertItemEntityCountIs(first.item().get(), WALL, 5, 1);
        helper.assertTrue(posters(helper).size() == 1 && !legacy.isRemoved()
            && posters(helper).getFirst().getPickResult().is(second.item().get()), "Breaking one artwork changed its neighbor");
        helper.succeed();
    }

    @GameTest(template = "nostalgia_test")
    public static void everyCreativePosterIgnoresForgedArtworkAndDoesNotDuplicate(GameTestHelper helper) {
        var player = player(helper, "PosterCreative", GameType.CREATIVE);
        wall(helper, WALL, true);
        for (var print : JapaneseArcades.ARCADE_POSTERS) {
            ItemStack stack = new ItemStack(print.item().get(), 2);
            CompoundTag forged = new CompoundTag();
            forged.putString("id", "minecraft:painting");
            forged.putString("variant", "japanesearcades:wacca_poster");
            forged.putBoolean("Invulnerable", true);
            stack.set(DataComponents.ENTITY_DATA, CustomData.of(forged));
            player.setItemInHand(InteractionHand.MAIN_HAND, stack);
            helper.assertTrue(place(helper, player, Direction.NORTH, WALL).consumesAction(), "Creative poster placement failed");
            var poster = onlyPoster(helper);
            helper.assertTrue(stack.getCount() == 2 && !poster.isInvulnerable()
                && poster.getVariant().is(ArcadePosterEntity.variantKey(print.path()))
                && poster.getPickResult().is(print.item().get()), "Item data replaced artwork or creative use consumed a poster");
            poster.hurt(helper.getLevel().damageSources().playerAttack(player), 1);
            helper.assertTrue(posters(helper).isEmpty() && helper.getEntities(EntityType.ITEM, WALL, 5).isEmpty(),
                "Creative poster removal duplicated a prize");
        }
        helper.succeed();
    }

    @GameTest(template = "nostalgia_test", timeoutTicks = 260)
    public static void everyUnsupportedArtworkDropsItsOwnCollectible(GameTestHelper helper) {
        var player = player(helper, "PosterSupport", GameType.SURVIVAL);
        unsupportedBatch(helper, player, 0);
    }

    private static void unsupportedBatch(GameTestHelper helper, ServerPlayer player, int first) {
        int end = Math.min(first + 12, JapaneseArcades.ARCADE_POSTERS.size());
        for (int index = first; index < end; index++) {
            var print = JapaneseArcades.ARCADE_POSTERS.get(index);
            int slot = index - first;
            // Reuse two rows inside the seven-block fixture instead of reaching into neighboring tests.
            var wall = new BlockPos(slot % 6, 3, 2 + (slot / 6) * 3);
            wall(helper, wall, true);
            player.setItemInHand(InteractionHand.MAIN_HAND, new ItemStack(print.item().get()));
            helper.assertTrue(place(helper, player, Direction.NORTH, wall).consumesAction(), "Supported gallery placement failed");
            helper.setBlock(wall.above(), Blocks.AIR);
        }
        helper.runAfterDelay(110, () -> {
            helper.assertTrue(posters(helper).isEmpty(), "Unsupported gallery poster survived");
            for (var print : JapaneseArcades.ARCADE_POSTERS.subList(first, end)) {
                helper.assertItemEntityCountIs(print.item().get(), WALL, 5, 1);
            }
            helper.assertItemEntityCountIs(Items.PAINTING, WALL, 5, 0);
            helper.getEntities(EntityType.ITEM, WALL, 5).forEach(ItemEntity::discard);
            if (end < JapaneseArcades.ARCADE_POSTERS.size()) { unsupportedBatch(helper, player, end); }
            else { helper.succeed(); }
        });
    }
}
