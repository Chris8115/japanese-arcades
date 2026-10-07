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

/** Exercises actual item placement and the inherited hanging-entity lifecycle. */
@GameTestHolder(JapaneseArcades.MOD_ID)
@PrefixGameTestTemplate(false)
public final class WaccaPosterGameTests {
    private static final BlockPos WALL = new BlockPos(3, 3, 3);

    private static ServerPlayer player(GameTestHelper helper, String name, GameType mode) {
        var player = createPlayer(helper, name, mode);
        player.setPos(Vec3.atCenterOf(helper.absolutePos(new BlockPos(6, 1, 6))));
        player.setItemInHand(InteractionHand.MAIN_HAND, new ItemStack(JapaneseArcades.WACCA_POSTER.get(), 2));
        return player;
    }

    private static void wall(GameTestHelper helper, Direction facing, boolean present) {
        for (int y = 0; y < 2; y++) {
            helper.setBlock(WALL.offset(0, y, 0), present ? Blocks.STONE : Blocks.AIR);
        }
    }

    private static InteractionResult place(GameTestHelper helper, ServerPlayer player, Direction facing) {
        return place(helper, player, facing, WALL);
    }

    private static InteractionResult place(GameTestHelper helper, ServerPlayer player, Direction facing, BlockPos wall) {
        BlockPos absolute = helper.absolutePos(wall);
        var hit = new BlockHitResult(Vec3.atCenterOf(absolute).relative(facing, .5), facing, absolute, false);
        return JapaneseArcades.WACCA_POSTER.get().useOn(new UseOnContext(player, InteractionHand.MAIN_HAND, hit));
    }

    private static List<WaccaPosterEntity> posters(GameTestHelper helper) {
        return helper.getEntities(JapaneseArcades.WACCA_POSTER_ENTITY.get(), WALL, 5);
    }

    private static WaccaPosterEntity onlyPoster(GameTestHelper helper) {
        var posters = posters(helper);
        helper.assertTrue(posters.size() == 1, "Expected exactly one dedicated poster, found " + posters.size());
        return posters.getFirst();
    }

    @GameTest(template = "nostalgia_test")
    public static void posterAllFacingsPersistAndRecoverTheSamePrize(GameTestHelper helper) {
        ServerPlayer player = player(helper, "PosterFacing", GameType.SURVIVAL);
        for (Direction facing : Direction.Plane.HORIZONTAL) {
            wall(helper, facing, true);
            player.setItemInHand(InteractionHand.MAIN_HAND, new ItemStack(JapaneseArcades.WACCA_POSTER.get(), 2));
            helper.assertTrue(place(helper, player, facing).consumesAction(), "Poster placement failed: " + facing);
            helper.assertTrue(player.getMainHandItem().getCount() == 1, "Placement must consume exactly one poster");
            var poster = onlyPoster(helper);
            helper.assertTrue(poster.getDirection() == facing && poster.getVariant().is(WaccaPosterEntity.VARIANT)
                && poster.getVariant().value().width() == 1 && poster.getVariant().value().height() == 2,
                "Poster direction, artwork or occupied wall cells differ from the purchased item");
            var bounds = poster.getBoundingBox();
            double width = facing.getAxis() == Direction.Axis.X ? bounds.getZsize() : bounds.getXsize();
            helper.assertTrue(Math.abs(width - WaccaPosterEntity.WIDTH) < 1.0E-7
                && Math.abs(bounds.getYsize() - WaccaPosterEntity.HEIGHT) < 1.0E-7
                && Math.abs(bounds.minY - helper.absolutePos(WALL).getY()) < 1.0E-7,
                "Poster must be exactly one block wide, retain the artwork aspect and start at the clicked cell's bottom");
            helper.assertTrue(!poster.getVariant().is(PaintingVariantTags.PLACEABLE), "Ordinary paintings must not randomly select prize artwork");
            helper.assertTrue(poster.getPickResult().is(JapaneseArcades.WACCA_POSTER.get()), "Pick block returned an ordinary painting");
            CompoundTag saved = new CompoundTag();
            helper.assertTrue(poster.save(saved), "Poster entity must support world saving");
            poster.discard();
            var restored = JapaneseArcades.WACCA_POSTER_ENTITY.get().create(helper.getLevel());
            helper.assertTrue(restored != null, "Poster factory failed");
            restored.load(saved);
            helper.assertTrue(restored.getDirection() == facing && restored.getVariant().is(WaccaPosterEntity.VARIANT)
                && restored.getPos().equals(helper.absolutePos(WALL.relative(facing)))
                && restored.getBoundingBox().equals(bounds), "Reload changed poster placement, artwork or dimensions");
            helper.assertTrue(helper.getLevel().addFreshEntity(restored), "Saved poster could not be restored");
            BlockPos neighborWall = WALL.relative(facing.getClockWise());
            helper.setBlock(neighborWall, Blocks.STONE);
            helper.setBlock(neighborWall.above(), Blocks.STONE);
            helper.assertTrue(place(helper, player, facing, neighborWall).consumesAction() && posters(helper).size() == 2,
                "One-block-wide posters must fit directly beside each other");
            var neighbor = posters(helper).stream().filter(value -> value != restored).findFirst().orElseThrow();
            helper.assertTrue(!restored.getBoundingBox().intersects(neighbor.getBoundingBox()), "Adjacent poster hitboxes overlap");
            restored.hurt(helper.getLevel().damageSources().playerAttack(player), 1);
            helper.assertTrue(posters(helper).size() == 1 && !neighbor.isRemoved(), "Breaking one poster affected its neighbor");
            helper.assertItemEntityCountIs(JapaneseArcades.WACCA_POSTER.get(), WALL, 5, 1);
            neighbor.hurt(helper.getLevel().damageSources().playerAttack(player), 1);
            helper.assertTrue(posters(helper).isEmpty(), "Survival attack did not remove the poster");
            helper.assertItemEntityCountIs(JapaneseArcades.WACCA_POSTER.get(), WALL, 5, 2);
            helper.assertItemEntityCountIs(Items.PAINTING, WALL, 5, 0);
            helper.getEntities(EntityType.ITEM, WALL, 5).forEach(ItemEntity::discard);
            helper.setBlock(neighborWall, Blocks.AIR);
            helper.setBlock(neighborWall.above(), Blocks.AIR);
            wall(helper, facing, false);
        }
        helper.succeed();
    }

    @GameTest(template = "nostalgia_test")
    public static void posterInvalidPlacementAndCanceledSpawnNeverConsumeThePrize(GameTestHelper helper) {
        ServerPlayer player = player(helper, "PosterInvalid", GameType.SURVIVAL);
        Direction facing = Direction.NORTH;
        wall(helper, facing, true);
        helper.assertTrue(place(helper, player, Direction.UP) == InteractionResult.FAIL
            && place(helper, player, Direction.DOWN) == InteractionResult.FAIL, "A wall poster accepted a floor or ceiling");
        helper.setBlock(WALL.above(), Blocks.AIR);
        helper.assertTrue(place(helper, player, facing) == InteractionResult.FAIL, "An unsupported poster was placed");
        wall(helper, facing, true);
        helper.setBlock(WALL.relative(facing), Blocks.STONE);
        helper.assertTrue(place(helper, player, facing) == InteractionResult.FAIL, "A poster intersected a solid block");
        helper.setBlock(WALL.relative(facing), Blocks.AIR);
        Consumer<EntityJoinLevelEvent> veto = event -> {
            if (event.getEntity() instanceof WaccaPosterEntity poster
                && poster.getPos().equals(helper.absolutePos(WALL.relative(facing)))) { event.setCanceled(true); }
        };
        NeoForge.EVENT_BUS.addListener(veto);
        try {
            helper.assertTrue(place(helper, player, facing) == InteractionResult.FAIL, "A canceled entity spawn reported placement success");
        } finally { NeoForge.EVENT_BUS.unregister(veto); }
        helper.assertTrue(player.getMainHandItem().getCount() == 2 && posters(helper).isEmpty(),
            "A failed placement consumed a prize or left a poster behind");
        helper.assertTrue(place(helper, player, facing).consumesAction(), "Valid placement after failures did not recover");
        helper.assertTrue(place(helper, player, facing) == InteractionResult.FAIL
            && player.getMainHandItem().getCount() == 1 && posters(helper).size() == 1, "Overlapping posters consumed an item or duplicated artwork");
        helper.succeed();
    }

    @GameTest(template = "nostalgia_test")
    public static void posterCreativeUseDoesNotDuplicateAndItemDataCannotReplaceTheArt(GameTestHelper helper) {
        ServerPlayer player = player(helper, "PosterCreative", GameType.CREATIVE);
        wall(helper, Direction.NORTH, true);
        CompoundTag forged = new CompoundTag();
        forged.putString("variant", "minecraft:kebab");
        forged.putBoolean("Invulnerable", true);
        player.getMainHandItem().set(DataComponents.ENTITY_DATA, CustomData.of(forged));
        helper.assertTrue(place(helper, player, Direction.NORTH).consumesAction(), "Creative poster placement failed");
        var poster = onlyPoster(helper);
        helper.assertTrue(player.getMainHandItem().getCount() == 2 && poster.getVariant().is(WaccaPosterEntity.VARIANT)
            && !poster.isInvulnerable(), "Creative use consumed the item or copied arbitrary entity data");
        poster.hurt(helper.getLevel().damageSources().playerAttack(player), 1);
        helper.assertTrue(posters(helper).isEmpty() && helper.getEntities(EntityType.ITEM, WALL, 5).isEmpty(),
            "Creative removal duplicated a collectible");
        helper.succeed();
    }

    @GameTest(template = "nostalgia_test", timeoutTicks = 140)
    public static void posterSupportLossDropsTheDedicatedPrize(GameTestHelper helper) {
        ServerPlayer player = player(helper, "PosterSupport", GameType.SURVIVAL);
        wall(helper, Direction.NORTH, true);
        helper.assertTrue(place(helper, player, Direction.NORTH).consumesAction(), "Supported poster placement failed");
        helper.setBlock(WALL.above(), Blocks.AIR);
        helper.runAfterDelay(110, () -> {
            helper.assertTrue(posters(helper).isEmpty(), "Poster survived removal of a supporting wall block");
            helper.assertItemEntityCountIs(JapaneseArcades.WACCA_POSTER.get(), WALL, 5, 1);
            helper.assertItemEntityCountIs(Items.PAINTING, WALL, 5, 0);
            helper.succeed();
        });
    }
}
