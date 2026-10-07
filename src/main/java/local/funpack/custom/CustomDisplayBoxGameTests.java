package local.funpack.custom;

import static local.funpack.custom.GachaponTransactionGameTests.aimAt;
import static local.funpack.custom.GachaponTransactionGameTests.createPlayer;

import java.util.List;
import java.util.function.Consumer;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.component.DataComponents;
import net.minecraft.gametest.framework.GameTest;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.item.ItemEntity;
import net.minecraft.world.item.BlockItem;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.item.component.CustomData;
import net.minecraft.world.item.component.ItemContainerContents;
import net.minecraft.world.item.context.BlockPlaceContext;
import net.minecraft.world.level.GameType;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.phys.BlockHitResult;
import net.minecraft.world.phys.Vec3;
import net.neoforged.neoforge.common.NeoForge;
import net.neoforged.neoforge.event.entity.EntityJoinLevelEvent;
import net.neoforged.neoforge.gametest.GameTestHolder;
import net.neoforged.neoforge.gametest.PrefixGameTestTemplate;

/** Component-preserving placement, unpacking, persistence, and atomic delivery. */
@GameTestHolder(FunPackCustom.MOD_ID)
@PrefixGameTestTemplate(false)
public final class CustomDisplayBoxGameTests {
    private static final BlockPos BASE = new BlockPos(3, 1, 3);

    private static ItemStack marked(ItemStack stack, String name) {
        stack.set(DataComponents.CUSTOM_NAME, Component.literal(name));
        CompoundTag tag = new CompoundTag();
        tag.putString("collector", "museum-original");
        tag.putInt("serial", 731);
        stack.set(DataComponents.CUSTOM_DATA, CustomData.of(tag));
        return stack;
    }

    private static List<ItemStack> payloads() {
        ItemStack sword = marked(new ItemStack(Items.DIAMOND_SWORD), "Worn ceremonial sword");
        sword.setDamageValue(73);
        sword.set(DataComponents.ENCHANTMENT_GLINT_OVERRIDE, true);
        ItemStack diamonds = marked(new ItemStack(Items.DIAMOND, 3), "Exhibit diamond");
        ItemStack container = marked(new ItemStack(Items.BARREL, 2), "Supply barrel");
        container.set(DataComponents.CONTAINER, ItemContainerContents.fromItems(List.of(diamonds.copy())));
        ItemStack figure = marked(new ItemStack(FunPackCustom.MOB_FIGURES.getFirst().figureItem().get(), 2), "Collector creeper");
        return List.of(sword, diamonds, container, figure);
    }

    private static ItemStack box(CustomDisplayBoxData data, int count) {
        ItemStack stack = new ItemStack(FunPackCustom.CUSTOM_DISPLAY_BOX_ITEM.get(), count);
        stack.set(FunPackCustom.DISPLAY_BOX_DATA.get(), data);
        return stack;
    }

    private static CustomDisplayBoxBlockEntity entity(GameTestHelper helper) {
        return (CustomDisplayBoxBlockEntity)helper.getBlockEntity(BASE);
    }

    private static void place(GameTestHelper helper, ServerPlayer player, ItemStack stack, Direction facing) {
        helper.setBlock(BASE.below(), Blocks.STONE);
        aimAt(player, helper.absolutePos(BASE));
        player.setYRot(facing.getOpposite().toYRot());
        player.setItemInHand(InteractionHand.MAIN_HAND, stack.copy());
        BlockPos floor = helper.absolutePos(BASE.below());
        var hit = new BlockHitResult(Vec3.atCenterOf(floor).add(0, .5, 0), Direction.UP, floor, false);
        helper.assertTrue(((BlockItem)stack.getItem()).place(new BlockPlaceContext(player, InteractionHand.MAIN_HAND,
            player.getMainHandItem(), hit)).consumesAction(), "Custom display box failed to place");
        helper.assertBlockPresent(FunPackCustom.CUSTOM_DISPLAY_BOX.get(), BASE);
        helper.assertBlockProperty(BASE, CustomDisplayBoxBlock.FACING, facing);
    }

    private static void use(GameTestHelper helper, ServerPlayer player, InteractionHand hand) {
        BlockPos pos = helper.absolutePos(BASE);
        var state = helper.getLevel().getBlockState(pos);
        FunPackCustom.CUSTOM_DISPLAY_BOX.get().useItemOn(player.getItemInHand(hand), state, helper.getLevel(), pos,
            player, hand, new BlockHitResult(Vec3.atCenterOf(pos), Direction.NORTH, pos, false));
    }

    private static void full(ServerPlayer player) {
        player.getInventory().clearContent();
        for (int slot = 0; slot < 36; slot++) player.getInventory().setItem(slot, new ItemStack(Items.COBBLESTONE, 64));
    }

    private static int exactInventory(ServerPlayer player, ItemStack expected) {
        int total = 0;
        for (int slot = 0; slot < player.getInventory().getContainerSize(); slot++) {
            ItemStack stack = player.getInventory().getItem(slot);
            if (ItemStack.isSameItemSameComponents(stack, expected)) total += stack.getCount();
        }
        return total;
    }

    private static int exactDelivered(GameTestHelper helper, ServerPlayer player, ItemStack expected) {
        return exactInventory(player, expected) + helper.getEntities(EntityType.ITEM, BASE, 6).stream()
            .filter(drop -> ItemStack.isSameItemSameComponents(drop.getItem(), expected)).mapToInt(drop -> drop.getItem().getCount()).sum();
    }

    private static void noDrops(GameTestHelper helper) {
        helper.assertTrue(helper.getEntities(EntityType.ITEM, BASE, 6).isEmpty(), "Display box leaked an unexpected or partial output");
    }

    private static void dataMatches(GameTestHelper helper, CustomDisplayBoxData actual, CustomDisplayBoxData expected, String message) {
        helper.assertTrue(actual.isEmpty() == expected.isEmpty()
            && ItemStack.matches(actual.containedItem(), expected.containedItem())
            && ItemStack.matches(actual.retainedItem(), expected.retainedItem()), message);
    }

    @GameTest(template = "nostalgia_test")
    public static void customDisplayBoxPreservesOneArbitraryItemAndRetainsItsIdentityAfterUnpacking(GameTestHelper helper) {
        for (GameType mode : new GameType[]{GameType.SURVIVAL, GameType.CREATIVE}) {
            ServerPlayer player = createPlayer(helper, "DisplayInsert" + mode.getName(), mode);
            for (ItemStack sample : payloads()) {
                place(helper, player, new ItemStack(FunPackCustom.CUSTOM_DISPLAY_BOX_ITEM.get()), Direction.EAST);
                player.getInventory().clearContent();
                player.setItemInHand(InteractionHand.MAIN_HAND, sample.copy());
                ItemStack expected = sample.copyWithCount(1);
                use(helper, player, InteractionHand.MAIN_HAND);
                helper.assertTrue(player.getMainHandItem().getCount() == sample.getCount()-1,
                    "Insertion must consume one source item, including creative");
                helper.assertTrue(ItemStack.matches(entity(helper).containedItem(), expected)
                    && ItemStack.matches(entity(helper).retainedItem(), expected),
                    "Insertion changed the item's name, damage, nested contents, or other components");
                if (!player.getMainHandItem().isEmpty()) player.getMainHandItem().set(DataComponents.CUSTOM_NAME, Component.literal("Changed remainder"));
                helper.assertTrue(ItemStack.matches(entity(helper).containedItem(), expected), "Stored payload aliases the source stack");

                player.setItemInHand(InteractionHand.MAIN_HAND, new ItemStack(Items.DIRT, 2));
                use(helper, player, InteractionHand.MAIN_HAND);
                helper.assertTrue(player.getMainHandItem().getCount() == 2 && ItemStack.matches(entity(helper).containedItem(), expected),
                    "An occupied box accepted a replacement item");
                player.getInventory().clearContent();
                use(helper, player, InteractionHand.MAIN_HAND);
                helper.assertTrue(entity(helper).data().isEmpty() && ItemStack.matches(entity(helper).retainedItem(), expected),
                    "Unpacking erased the display identity or kept a second live item");
                helper.assertTrue(exactInventory(player, expected) == 1, "Unpacking lost components or delivered more than one item");
                player.getInventory().clearContent();
                use(helper, player, InteractionHand.MAIN_HAND);
                helper.assertTrue(entity(helper).data().isEmpty() && exactInventory(player, expected) == 0,
                    "An empty labeled box regenerated its retained item");
                noDrops(helper);
                helper.getLevel().destroyBlock(helper.absolutePos(BASE), false, player);
            }
        }
        helper.succeed();
    }

    @GameTest(template = "nostalgia_test")
    public static void customDisplayBoxContentsAndRetainedIdentitySurviveSaveLootAndReplacementInEveryFacing(GameTestHelper helper) {
        ServerPlayer player = createPlayer(helper, "DisplaySave", GameType.SURVIVAL);
        CustomDisplayBoxData filled = CustomDisplayBoxData.filled(payloads().getFirst());
        for (CustomDisplayBoxData expected : List.of(filled, filled.emptied())) {
            for (Direction facing : Direction.Plane.HORIZONTAL) {
                ItemStack source = box(expected, 1);
                // Exercise item component serialization before normal placement as well as block-entity persistence.
                source = ItemStack.parse(helper.getLevel().registryAccess(), source.save(helper.getLevel().registryAccess())).orElseThrow();
                place(helper, player, source, facing);
                helper.assertTrue(player.getMainHandItem().isEmpty(), "Survival placement did not consume its display box");
                dataMatches(helper, entity(helper).data(), expected, "Placed item components were not applied to its block entity");
                var registry = helper.getLevel().registryAccess();
                var original = entity(helper);
                var restored = (CustomDisplayBoxBlockEntity)BlockEntity.loadStatic(original.getBlockPos(), original.getBlockState(),
                    original.saveWithFullMetadata(registry), registry);
                helper.assertTrue(restored != null, "Saved custom display box did not reload");
                helper.getLevel().setBlockEntity(restored);
                dataMatches(helper, entity(helper).data(), expected, "Reloading changed payload components or retained label identity");
                helper.assertBlockProperty(BASE, CustomDisplayBoxBlock.FACING, facing);
                helper.getLevel().destroyBlock(helper.absolutePos(BASE), true, player);
                helper.assertBlockPresent(Blocks.AIR, BASE);
                var drops = helper.getEntities(EntityType.ITEM, BASE, 6);
                helper.assertTrue(drops.size() == 1 && drops.getFirst().getItem().is(FunPackCustom.CUSTOM_DISPLAY_BOX_ITEM.get())
                    && drops.getFirst().getItem().getCount() == 1, "Breaking a display box lost it or separately duplicated its content");
                ItemStack dropped = drops.getFirst().getItem().copy();
                dataMatches(helper, CustomDisplayBoxData.from(dropped), expected, "Display box loot lost its saved data");
                drops.forEach(ItemEntity::discard);
                place(helper, player, dropped, facing.getOpposite());
                dataMatches(helper, entity(helper).data(), expected, "Re-placing the recovered box changed its display data");
                helper.getLevel().destroyBlock(helper.absolutePos(BASE), false, player);
            }
        }
        helper.succeed();
    }

    @GameTest(template = "nostalgia_test")
    public static void creativeBreakingPreservesStoredDisplayItemsWithoutDuplicatingEmptyCases(GameTestHelper helper) {
        ServerPlayer player = createPlayer(helper, "DisplayCreative", GameType.CREATIVE);
        CustomDisplayBoxData filled = CustomDisplayBoxData.filled(payloads().getFirst());
        for (Direction facing : Direction.Plane.HORIZONTAL) {
            for (CustomDisplayBoxData expected : List.of(filled, filled.emptied())) {
                place(helper, player, box(expected, 1), facing);
                player.getInventory().clearContent();
                BlockPos pos = helper.absolutePos(BASE);
                var state = helper.getLevel().getBlockState(pos);
                state.getBlock().playerWillDestroy(helper.getLevel(), pos, state, player);
                helper.getLevel().destroyBlock(pos, false, player);
                helper.assertBlockPresent(Blocks.AIR, BASE);
                if (expected.isEmpty()) {
                    noDrops(helper);
                } else {
                    var drops = helper.getEntities(EntityType.ITEM, BASE, 6);
                    helper.assertTrue(drops.size() == 1 && drops.getFirst().getItem().is(FunPackCustom.CUSTOM_DISPLAY_BOX_ITEM.get())
                        && drops.getFirst().getItem().getCount() == 1,
                        "Creative destruction deleted the stored display item or duplicated its package");
                    dataMatches(helper, CustomDisplayBoxData.from(drops.getFirst().getItem()), expected,
                        "Creative destruction changed the stored item's components or retained identity");
                    drops.forEach(ItemEntity::discard);
                }
            }
        }
        helper.succeed();
    }

    @GameTest(template = "nostalgia_test")
    public static void heldCustomDisplayBoxesOpenOnePreservingOuterAndInnerComponentsInBothHands(GameTestHelper helper) {
        ItemStack payload = payloads().getFirst();
        CustomDisplayBoxData data = CustomDisplayBoxData.filled(payload);
        for (GameType mode : new GameType[]{GameType.SURVIVAL, GameType.CREATIVE}) {
            ServerPlayer player = createPlayer(helper, "DisplayHeld" + mode.getName(), mode);
            for (InteractionHand hand : InteractionHand.values()) {
                player.getInventory().clearContent();
                ItemStack source = marked(box(data, 2), "My display case");
                ItemStack empty = source.copyWithCount(1);
                empty.set(FunPackCustom.DISPLAY_BOX_DATA.get(), data.emptied());
                player.setItemInHand(hand, source.copy());
                player.setShiftKeyDown(false);
                FunPackCustom.CUSTOM_DISPLAY_BOX_ITEM.get().use(helper.getLevel(), player, hand);
                helper.assertTrue(ItemStack.matches(player.getItemInHand(hand), source), "Display box opened without sneaking");
                player.setShiftKeyDown(true);
                FunPackCustom.CUSTOM_DISPLAY_BOX_ITEM.get().use(helper.getLevel(), player, hand);
                helper.assertTrue(exactInventory(player, source) == 1 && exactInventory(player, empty) == 1
                    && exactInventory(player, payload) == 1,
                    "Held opening failed to preserve both payload and labeled outer box, or consumed the wrong count");
                player.getInventory().clearContent();
                player.setItemInHand(hand, empty.copy());
                FunPackCustom.CUSTOM_DISPLAY_BOX_ITEM.get().use(helper.getLevel(), player, hand);
                helper.assertTrue(ItemStack.matches(player.getItemInHand(hand), empty) && exactInventory(player, payload) == 0,
                    "An empty held box regenerated its retained display item");
                noDrops(helper);
            }
            player.setShiftKeyDown(false);
        }
        helper.succeed();
    }

    @GameTest(template = "nostalgia_test")
    public static void customDisplayBoxesRejectDirectNestingAndLeavePresetBoxesIndependent(GameTestHelper helper) {
        ServerPlayer player = createPlayer(helper, "DisplayReject", GameType.SURVIVAL);
        var preset = FunPackCustom.MOB_FIGURES.getFirst();
        helper.setBlock(BASE.east(), preset.boxedFigure().get());
        place(helper, player, new ItemStack(FunPackCustom.CUSTOM_DISPLAY_BOX_ITEM.get()), Direction.SOUTH);
        for (ItemStack nested : List.of(new ItemStack(FunPackCustom.CUSTOM_DISPLAY_BOX_ITEM.get(), 2),
                box(CustomDisplayBoxData.filled(payloads().getFirst()), 2))) {
            player.setItemInHand(InteractionHand.MAIN_HAND, nested.copy());
            use(helper, player, InteractionHand.MAIN_HAND);
            helper.assertTrue(ItemStack.matches(player.getMainHandItem(), nested) && entity(helper).data().isEmpty(),
                "A display box accepted another custom display box as its direct content");
        }
        helper.assertBlockPresent(preset.boxedFigure().get(), BASE.east());
        BlockPos neighbor = helper.absolutePos(BASE.east());
        aimAt(player, neighbor);
        player.getInventory().clearContent();
        var state = helper.getLevel().getBlockState(neighbor);
        preset.boxedFigure().get().useWithoutItem(state, helper.getLevel(), neighbor, player,
            new BlockHitResult(Vec3.atCenterOf(neighbor), Direction.NORTH, neighbor, false));
        helper.assertBlockPresent(preset.emptyBox().get(), BASE.east());
        helper.assertTrue(ArcadeOrderCatalog.count(player, preset.figureItem().get()) == 1,
            "Adding custom boxes changed preset mob-box unpacking");
        helper.assertBlockPresent(FunPackCustom.CUSTOM_DISPLAY_BOX.get(), BASE);
        helper.assertTrue(entity(helper).data().isEmpty(), "Unpacking a preset neighbor modified the custom box");
        noDrops(helper);
        helper.succeed();
    }

    @GameTest(template = "nostalgia_test")
    public static void customDisplayBoxCanceledOrSubstitutedOverflowKeepsTheExactPlacedPayload(GameTestHelper helper) {
        ServerPlayer player = createPlayer(helper, "DisplayOverflow", GameType.SURVIVAL);
        ItemStack payload = payloads().getFirst();
        CustomDisplayBoxData data = CustomDisplayBoxData.filled(payload);
        place(helper, player, box(data, 1), Direction.WEST);
        for (int action = 0; action < 3; action++) {
            full(player);
            int failure = action;
            Consumer<EntityJoinLevelEvent> callback = event -> {
                if (event.getLevel() == helper.getLevel() && event.getEntity() instanceof ItemEntity item
                    && item.getItem().is(payload.getItem()) && item.distanceToSqr(player) < 16) {
                    if (failure == 0) event.setCanceled(true);
                    if (failure == 1) item.setItem(new ItemStack(Items.DIRT));
                }
            };
            NeoForge.EVENT_BUS.addListener(callback);
            try { use(helper, player, InteractionHand.OFF_HAND); }
            finally { NeoForge.EVENT_BUS.unregister(callback); }
            helper.assertTrue(ArcadeOrderCatalog.count(player, Items.COBBLESTONE) == 36*64 && player.getOffhandItem().isEmpty(),
                "Placed extraction overwrote an unrelated full inventory slot");
            if (action < 2) {
                dataMatches(helper, entity(helper).data(), data, "Rejected ground output consumed or changed the placed payload");
                noDrops(helper);
            } else {
                dataMatches(helper, entity(helper).data(), data.emptied(), "Successful overflow failed to retain the empty display's identity");
                helper.assertTrue(exactDelivered(helper, player, payload) == 1, "Successful overflow lost payload components or duplicated it");
            }
        }
        helper.succeed();
    }

    @GameTest(template = "nostalgia_test")
    public static void heldCustomDisplayBoxRollsBackBothOutputsIfReturningTheEmptyCaseFails(GameTestHelper helper) {
        ItemStack payload = payloads().getFirst();
        CustomDisplayBoxData data = CustomDisplayBoxData.filled(payload);
        for (GameType mode : new GameType[]{GameType.SURVIVAL, GameType.CREATIVE}) {
            ServerPlayer player = createPlayer(helper, "DisplayFull" + mode.getName(), mode);
            player.setShiftKeyDown(true);
            for (int sourceCount : new int[]{1, 2}) {
                for (int action = 0; action < 3; action++) {
                    full(player);
                    ItemStack source = marked(box(data, sourceCount), "Original case");
                    ItemStack empty = source.copyWithCount(1);
                    empty.set(FunPackCustom.DISPLAY_BOX_DATA.get(), data.emptied());
                    player.setItemInHand(InteractionHand.MAIN_HAND, source.copy());
                    int failure = action;
                    Consumer<EntityJoinLevelEvent> callback = event -> {
                        if (event.getLevel() == helper.getLevel() && event.getEntity() instanceof ItemEntity item
                            && item.getItem().is(FunPackCustom.CUSTOM_DISPLAY_BOX_ITEM.get()) && item.distanceToSqr(player) < 16) {
                            if (failure == 0) event.setCanceled(true);
                            if (failure == 1) item.setItem(new ItemStack(Items.DIRT));
                        }
                    };
                    NeoForge.EVENT_BUS.addListener(callback);
                    try { FunPackCustom.CUSTOM_DISPLAY_BOX_ITEM.get().use(helper.getLevel(), player, InteractionHand.MAIN_HAND); }
                    finally { NeoForge.EVENT_BUS.unregister(callback); }
                    helper.assertTrue(ArcadeOrderCatalog.count(player, Items.COBBLESTONE) == 35*64,
                        "Held opening overwrote an unrelated full inventory slot");
                    if (action < 2) {
                        helper.assertTrue(ItemStack.matches(player.getMainHandItem(), source)
                            && exactInventory(player, payload) == 0 && exactInventory(player, empty) == 0,
                            "Canceled second output lost the original filled box or committed a partial inventory delivery");
                        noDrops(helper);
                    } else {
                        helper.assertTrue(exactInventory(player, source) == sourceCount-1
                            && exactDelivered(helper, player, payload) == 1 && exactDelivered(helper, player, empty) == 1,
                            "Successful held overflow lost or duplicated a component-preserving output");
                    }
                    helper.getEntities(EntityType.ITEM, BASE, 6).forEach(ItemEntity::discard);
                }
            }
            player.setShiftKeyDown(false);
        }
        helper.succeed();
    }
}
