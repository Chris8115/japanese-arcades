package local.japanesearcades;

import static local.japanesearcades.GachaponTransactionGameTests.aimAt;
import static local.japanesearcades.GachaponTransactionGameTests.createPlayer;

import java.util.List;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.gametest.framework.GameTest;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.item.ItemEntity;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.GameType;
import net.minecraft.world.level.LightLayer;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.material.Fluids;
import net.minecraft.world.phys.BlockHitResult;
import net.minecraft.world.phys.Vec3;
import net.neoforged.neoforge.gametest.GameTestHolder;
import net.neoforged.neoforge.gametest.PrefixGameTestTemplate;

/** Real block-item use, support updates, water buckets, and asynchronous block-light propagation. */
@GameTestHolder(JapaneseArcades.MOD_ID)
@PrefixGameTestTemplate(false)
public final class GlowStickGameTests {
    private static final BlockPos BASE = new BlockPos(3, 2, 3);
    private static final List<Direction> MOUNTS = List.of(Direction.UP, Direction.NORTH, Direction.SOUTH, Direction.EAST, Direction.WEST);

    private static boolean use(GameTestHelper helper, ServerPlayer player, InteractionHand hand, Direction face) {
        BlockPos support = helper.absolutePos(BASE.relative(face.getOpposite()));
        aimAt(player, helper.absolutePos(BASE));
        Vec3 hitPos = Vec3.atCenterOf(support).add(face.getStepX() * .5, face.getStepY() * .5, face.getStepZ() * .5);
        return player.gameMode.useItemOn(player, helper.getLevel(), player.getItemInHand(hand), hand,
            new BlockHitResult(hitPos, face, support, false)).consumesAction();
    }

    private static void clear(GameTestHelper helper) {
        helper.setBlock(BASE, Blocks.AIR);
        for (Direction direction : Direction.values()) { helper.setBlock(BASE.relative(direction), Blocks.AIR); }
        helper.getEntities(EntityType.ITEM, BASE, 4).forEach(ItemEntity::discard);
    }

    @GameTest(template = "nostalgia_test")
    public static void bothHandsMountEachColorOnFloorsAndWallsAndDropExactlyOnce(GameTestHelper helper) {
        ServerPlayer player = createPlayer(helper, "GlowBothHands", GameType.SURVIVAL);
        for (var glow : JapaneseArcades.GLOW_STICKS) {
            for (InteractionHand hand : InteractionHand.values()) {
                for (Direction facing : MOUNTS) {
                    clear(helper);
                    helper.setBlock(BASE.relative(facing.getOpposite()), Blocks.STONE);
                    InteractionHand other = hand == InteractionHand.MAIN_HAND ? InteractionHand.OFF_HAND : InteractionHand.MAIN_HAND;
                    var otherColor = JapaneseArcades.GLOW_STICKS.get((JapaneseArcades.GLOW_STICKS.indexOf(glow) + 1) % 7);
                    player.setItemInHand(hand, new ItemStack(glow.item().get(), 2));
                    ItemStack untouched = new ItemStack(otherColor.item().get(), 3);
                    player.setItemInHand(other, untouched.copy());
                    helper.assertTrue(use(helper, player, hand, facing), "Native " + hand + " placement failed for " + glow.path() + " facing " + facing);
                    helper.assertBlockPresent(glow.block().get(), BASE);
                    helper.assertBlockProperty(BASE, GlowStickBlock.FACING, facing);
                    helper.assertTrue(player.getItemInHand(hand).getCount() == 1
                        && ItemStack.matches(player.getItemInHand(other), untouched), "Placement consumed the wrong hand or quantity");
                    var state = helper.getBlockState(BASE);
                    var pos = helper.absolutePos(BASE);
                    helper.assertTrue(state.getCollisionShape(helper.getLevel(), pos).isEmpty()
                        && !state.getShape(helper.getLevel(), pos).isEmpty(), "Glow stick must be selectable without blocking movement");
                    helper.assertTrue(glow.block().get().getCloneItemStack(helper.getLevel(), pos, state).is(glow.item().get()),
                        "Pick-block changed the glow-stick color");
                    helper.getLevel().destroyBlock(pos, true, player);
                    helper.assertItemEntityCountIs(glow.item().get(), BASE, 4, 1);
                    helper.assertTrue(helper.getEntities(EntityType.ITEM, BASE, 4).size() == 1, "Breaking glow stick produced extra drops");
                    helper.getEntities(EntityType.ITEM, BASE, 4).forEach(ItemEntity::discard);
                    player.setItemInHand(hand, new ItemStack(glow.item().get(), 2));
                    helper.assertTrue(use(helper, player, hand, facing), "Replacement failed before support-removal test");
                    helper.getLevel().destroyBlock(helper.absolutePos(BASE.relative(facing.getOpposite())), false);
                    helper.assertBlockPresent(Blocks.AIR, BASE);
                    helper.assertItemEntityCountIs(glow.item().get(), BASE, 4, 1);
                    helper.assertTrue(helper.getEntities(EntityType.ITEM, BASE, 4).size() == 1, "Support loss duplicated or changed the drop");
                }
            }
        }
        clear(helper);
        player.setGameMode(GameType.CREATIVE);
        for (InteractionHand hand : InteractionHand.values()) {
            var glow = JapaneseArcades.GLOW_STICKS.getFirst();
            helper.setBlock(BASE.below(), Blocks.STONE);
            player.setItemInHand(hand, new ItemStack(glow.item().get(), 2));
            helper.assertTrue(use(helper, player, hand, Direction.UP) && player.getItemInHand(hand).getCount() == 2,
                "Creative placement consumed a held glow stick");
            helper.assertTrue(player.gameMode.destroyBlock(helper.absolutePos(BASE)), "Native creative break failed");
            helper.assertItemEntityCountIs(glow.item().get(), BASE, 4, 0);
        }
        helper.succeed();
    }

    @GameTest(template = "nostalgia_test")
    public static void ceilingsUnsupportedSurfacesAndLavaRejectWithoutConsumption(GameTestHelper helper) {
        ServerPlayer player = createPlayer(helper, "GlowInvalid", GameType.SURVIVAL);
        var glow = JapaneseArcades.GLOW_STICKS.getFirst();
        for (InteractionHand hand : InteractionHand.values()) {
            clear(helper);
            player.setItemInHand(hand, new ItemStack(glow.item().get(), 2));
            helper.setBlock(BASE.above(), Blocks.STONE);
            helper.assertFalse(use(helper, player, hand, Direction.DOWN), "Glow stick attached to a ceiling");
            helper.assertBlockPresent(Blocks.AIR, BASE);
            helper.assertTrue(player.getItemInHand(hand).getCount() == 2, "Ceiling rejection consumed an item");
            clear(helper);
            helper.setBlock(BASE.south(), Blocks.OAK_FENCE);
            helper.assertFalse(use(helper, player, hand, Direction.NORTH), "Glow stick attached to an unsupported fence side");
            helper.assertBlockPresent(Blocks.AIR, BASE);
            helper.assertTrue(player.getItemInHand(hand).getCount() == 2, "Unsupported wall consumed an item");
            clear(helper);
            helper.setBlock(BASE.below(), Blocks.STONE);
            helper.setBlock(BASE, Blocks.LAVA);
            helper.assertFalse(use(helper, player, hand, Direction.UP), "Glow stick replaced lava");
            helper.assertBlockPresent(Blocks.LAVA, BASE);
            helper.assertTrue(player.getItemInHand(hand).getCount() == 2, "Lava rejection consumed an item");
        }
        clear(helper);
        helper.succeed();
    }

    @GameTest(template = "nostalgia_test")
    public static void waterloggedColorsRemainLitAndReleaseWaterWhenRemoved(GameTestHelper helper) {
        ServerPlayer player = createPlayer(helper, "GlowWater", GameType.SURVIVAL);
        for (var glow : JapaneseArcades.GLOW_STICKS) {
            for (Direction facing : List.of(Direction.UP, Direction.NORTH)) {
                clear(helper);
                helper.setBlock(BASE.relative(facing.getOpposite()), Blocks.STONE);
                helper.setBlock(BASE, Blocks.WATER);
                player.setItemInHand(InteractionHand.OFF_HAND, new ItemStack(glow.item().get(), 2));
                helper.assertTrue(use(helper, player, InteractionHand.OFF_HAND, facing), "Underwater glow-stick placement failed");
                var pos = helper.absolutePos(BASE);
                var state = helper.getBlockState(BASE);
                helper.assertTrue(state.getValue(GlowStickBlock.WATERLOGGED)
                    && state.getFluidState().isSourceOfType(Fluids.WATER)
                    && state.getLightEmission(helper.getLevel(), pos) == 14, "Water extinguished or removed the glow stick's source water");
                ItemStack bucket = glow.block().get().pickupBlock(player, helper.getLevel(), pos, state);
                helper.assertTrue(bucket.is(Items.WATER_BUCKET) && !helper.getBlockState(BASE).getValue(GlowStickBlock.WATERLOGGED),
                    "Water bucket pickup failed");
                helper.assertTrue(glow.block().get().placeLiquid(helper.getLevel(), pos, helper.getBlockState(BASE), Fluids.WATER.getSource(false)),
                    "Replacing bucket water failed");
                helper.assertBlockProperty(BASE, GlowStickBlock.WATERLOGGED, true);
                helper.getLevel().destroyBlock(pos, true, player);
                helper.assertBlockPresent(Blocks.WATER, BASE);
                helper.assertItemEntityCountIs(glow.item().get(), BASE, 4, 1);
                helper.getEntities(EntityType.ITEM, BASE, 4).forEach(ItemEntity::discard);
                helper.assertTrue(use(helper, player, InteractionHand.OFF_HAND, facing), "Waterlogged replacement failed");
                helper.getLevel().destroyBlock(helper.absolutePos(BASE.relative(facing.getOpposite())), false);
                helper.assertBlockPresent(Blocks.WATER, BASE);
                helper.assertItemEntityCountIs(glow.item().get(), BASE, 4, 1);
                helper.assertTrue(helper.getEntities(EntityType.ITEM, BASE, 4).size() == 1, "Waterlogged support loss created extra drops");
            }
        }
        clear(helper);
        helper.succeed();
    }

    @GameTest(template = "nostalgia_test", timeoutTicks = 160)
    public static void placedGlowActuallyLightsNearbyAirAndRemovalDarkensIt(GameTestHelper helper) {
        // Opaque shell isolates the light engine assertion from daylight and nearby test fixtures.
        for (int x = 0; x <= 6; x++) {
            for (int y = 0; y <= 5; y++) {
                for (int z = 0; z <= 6; z++) {
                    boolean wall = x == 0 || x == 6 || y == 0 || y == 5 || z == 0 || z == 6;
                    helper.setBlock(new BlockPos(x, y, z), wall ? Blocks.STONE : Blocks.AIR);
                }
            }
        }
        helper.setBlock(BASE.below(), Blocks.STONE);
        ServerPlayer player = createPlayer(helper, "GlowLighting", GameType.SURVIVAL);
        player.setItemInHand(InteractionHand.MAIN_HAND, new ItemStack(JapaneseArcades.GLOW_STICKS.getFirst().item().get()));
        helper.assertTrue(use(helper, player, InteractionHand.MAIN_HAND, Direction.UP), "Light fixture placement failed");
        BlockPos source = helper.absolutePos(BASE);
        helper.startSequence().thenWaitUntil(() -> {
            helper.assertTrue(helper.getLevel().getBrightness(LightLayer.BLOCK, source) == 14
                && helper.getLevel().getBrightness(LightLayer.BLOCK, source.east()) == 13
                && helper.getLevel().getBrightness(LightLayer.BLOCK, source.east(2)) == 12,
                "Glow-stick light did not propagate into adjacent air with vanilla attenuation");
        }).thenExecute(() -> helper.getLevel().destroyBlock(source, false)).thenWaitUntil(() -> {
            helper.assertTrue(helper.getLevel().getBrightness(LightLayer.BLOCK, source) == 0
                && helper.getLevel().getBrightness(LightLayer.BLOCK, source.east()) == 0,
                "Removed glow stick left stale block light");
        }).thenSucceed();
    }
}
