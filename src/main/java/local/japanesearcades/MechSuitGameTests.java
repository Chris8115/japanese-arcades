package local.japanesearcades;

import static local.japanesearcades.GachaponTransactionGameTests.aimAt;
import static local.japanesearcades.GachaponTransactionGameTests.createPlayer;

import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.component.DataComponents;
import net.minecraft.gametest.framework.GameTest;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.util.Mth;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.animal.Cow;
import net.minecraft.world.entity.animal.Wolf;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.item.context.UseOnContext;
import net.minecraft.world.level.GameType;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.BlockHitResult;
import net.minecraft.world.phys.Vec3;
import net.neoforged.neoforge.gametest.GameTestHolder;
import net.neoforged.neoforge.gametest.PrefixGameTestTemplate;

/** Native deployment, collisions, rider input, sword damage and recoverable reward lifecycle. */
@GameTestHolder(JapaneseArcades.MOD_ID)
@PrefixGameTestTemplate(false)
public final class MechSuitGameTests {
    private static final BlockPos BASE = new BlockPos(12, 1, 12);

    private static void floor(GameTestHelper helper) {
        for (int x = 3; x < 29; x++) { for (int z = 3; z < 29; z++) { helper.setBlock(new BlockPos(x, 0, z), Blocks.STONE); } }
    }
    private static ServerPlayer player(GameTestHelper helper, String name) {
        ServerPlayer player = createPlayer(helper, name, GameType.SURVIVAL);
        aimAt(player, helper.absolutePos(BASE));
        player.setYRot(0);
        player.setXRot(0);
        return player;
    }
    private static boolean deploy(GameTestHelper helper, ServerPlayer player) {
        BlockPos support = helper.absolutePos(BASE.below());
        return JapaneseArcades.MECH_SUIT_ITEM.get().useOn(new UseOnContext(player, InteractionHand.MAIN_HAND,
            new BlockHitResult(Vec3.atCenterOf(support).add(0, .5, 0), Direction.UP, support, false))).consumesAction();
    }
    private static MechSuitEntity mech(GameTestHelper helper, ServerPlayer owner) {
        floor(helper);
        MechSuitEntity suit = new MechSuitEntity(JapaneseArcades.MECH_SUIT.get(), helper.getLevel());
        Vec3 at = Vec3.atBottomCenterOf(helper.absolutePos(BASE));
        suit.moveTo(at.x, at.y, at.z, 0, 0);
        suit.configure(owner.getUUID(), MechSuitEntity.MAX_HULL);
        helper.assertTrue(helper.getLevel().addFreshEntity(suit), "Could not add mech fixture");
        return suit;
    }
    private static MechSuitNetwork.InputPayload input(float forward, float strafe, boolean up, boolean down, boolean left, boolean right) {
        return new MechSuitNetwork.InputPayload(forward, strafe, up, down, left, right, 0, 0);
    }
    private static void ticks(MechSuitEntity mech, int count) {
        for (int tick = 0; tick < count; tick++) { mech.tickCount++; mech.tick(); }
    }
    private static void drive(MechSuitEntity mech, ServerPlayer player, int count, MechSuitNetwork.InputPayload input) {
        for (int tick = 0; tick < count; tick++) { MechSuitNetwork.handleInput(player, input); ticks(mech, 1); }
    }
    private static long packedCount(ServerPlayer player) {
        return player.getInventory().items.stream().filter(stack -> stack.is(JapaneseArcades.MECH_SUIT_ITEM.get())).mapToInt(ItemStack::getCount).sum();
    }

    @GameTest(template = "arcade_test")
    public static void deployRequiresClearanceConsumesOnceAndPreservesRewardData(GameTestHelper helper) {
        floor(helper);
        ServerPlayer owner = player(helper, "MechDeploy");
        ItemStack reward = MechSuitItem.packed(71);
        reward.set(DataComponents.CUSTOM_NAME, Component.literal("Festival champion"));
        owner.setItemInHand(InteractionHand.MAIN_HAND, reward);
        helper.setBlock(BASE.above(4), Blocks.STONE);
        helper.assertFalse(deploy(helper, owner), "Five-block suit deployed through a ceiling");
        helper.assertTrue(owner.getMainHandItem().getCount() == 1, "Blocked deployment consumed high-tier reward");
        helper.setBlock(BASE.above(4), Blocks.AIR);
        helper.setBlock(BASE, Blocks.WATER);
        helper.assertFalse(deploy(helper, owner), "Suit deployed inside fluid");
        helper.setBlock(BASE, Blocks.AIR);
        helper.assertTrue(deploy(helper, owner) && owner.getMainHandItem().isEmpty(), "Clear deployment failed or retained the spent item");
        var suits = helper.getLevel().getEntitiesOfClass(MechSuitEntity.class, new AABB(helper.absolutePos(BASE)).inflate(4));
        helper.assertTrue(suits.size() == 1, "Deployment produced an incorrect entity count");
        MechSuitEntity mech = suits.getFirst();
        helper.assertTrue(mech.getHullHealth() == 71 && owner.getUUID().equals(mech.getOwnerUUID())
            && "Festival champion".equals(mech.getCustomName().getString()), "Deployment lost hull, name or owner");
        owner.setItemInHand(InteractionHand.MAIN_HAND, new ItemStack(JapaneseArcades.MECH_SUIT_ITEM.get()));
        helper.assertFalse(deploy(helper, owner), "A second suit deployed inside the first");
        helper.assertTrue(owner.getMainHandItem().getCount() == 1, "Overlap rejection consumed an item");
        mech.discard();
        helper.succeed();
    }

    @GameTest(template = "arcade_test")
    public static void ownerMountsFliesHoversAndStaleOrForeignInputsStop(GameTestHelper helper) {
        ServerPlayer owner = player(helper, "MechPilot");
        MechSuitEntity mech = mech(helper, owner);
        ServerPlayer stranger = player(helper, "MechStranger");
        helper.assertFalse(mech.interact(stranger, InteractionHand.MAIN_HAND).consumesAction(), "Foreign player stole an owned suit");
        helper.assertTrue(mech.interact(owner, InteractionHand.MAIN_HAND).consumesAction() && owner.getVehicle() == mech, "Owner could not mount");
        helper.assertTrue(mech.getControllingPassenger() == null, "Vanilla vehicle position packets can bypass server control");
        Vec3 start = mech.position();
        drive(mech, owner, 10, input(0, 0, true, false, false, false));
        helper.assertTrue(mech.isFlying() && mech.getY() > start.y + 3, "Ascend did not launch the mech");
        double hover = mech.getY();
        drive(mech, owner, 8, input(1, 0, false, false, false, false));
        helper.assertTrue(Math.abs(mech.getY() - hover) < .001 && mech.getZ() > start.z + 3, "Flight did not move horizontally at fixed hover height");
        ticks(mech, 8);
        Vec3 stopped = mech.position();
        MechSuitNetwork.handleInput(stranger, input(1, 1, true, false, true, true));
        ticks(mech, 4);
        helper.assertTrue(mech.position().distanceToSqr(stopped) < .00001, "Stale/foreign input moved an occupied hovering suit");
        MechSuitNetwork.handleInput(owner, new MechSuitNetwork.InputPayload(Float.NaN, 1, true, false, true, true, 0, 0));
        ticks(mech, 1);
        helper.assertTrue(mech.position().distanceToSqr(stopped) < .00001, "Nonfinite input changed flight state");
        owner.stopRiding();
        helper.assertTrue(owner.hasEffect(MobEffects.SLOW_FALLING) && owner.fallDistance == 0, "Airborne dismount omitted descent protection");
        double emptyHeight = mech.getY();
        ticks(mech, 5);
        helper.assertTrue(mech.getY() < emptyHeight && mech.getZ() == stopped.z, "Empty suit kept pilot input instead of settling vertically");
        mech.discard();
        helper.succeed();
    }

    @GameTest(template = "arcade_test")
    public static void turningConvergesAcrossYawWrapAndMovementAndSwordsFollowTheAim(GameTestHelper helper) {
        ServerPlayer owner = player(helper, "MechSteering");
        MechSuitEntity mech = mech(helper, owner);
        helper.assertTrue(mech.interact(owner, InteractionHand.MAIN_HAND).consumesAction(), "Could not mount steering fixture");
        var east = new MechSuitNetwork.InputPayload(0, 0, false, false, false, false, 90, 0);
        drive(mech, owner, 8, east);
        helper.assertTrue(Math.abs(Mth.wrapDegrees(mech.getYRot() - 90)) < .001,
            "Body did not converge onto a90-degree aim; steering retained an angular dead zone");
        Vec3 before = mech.position();
        drive(mech, owner, 4, new MechSuitNetwork.InputPayload(1, 0, false, false, false, false, 90, 0));
        helper.assertTrue(mech.getX() < before.x - .9 && Math.abs(mech.getZ() - before.z) < .001,
            "Forward movement did not follow the settled nonzero body yaw");
        mech.setYRot(170);
        var wrap = new MechSuitNetwork.InputPayload(0, 0, false, false, false, false, -170, 0);
        drive(mech, owner, 1, wrap);
        helper.assertTrue(Math.abs(Mth.wrapDegrees(mech.getYRot() - 170) - 18) < .001,
            "Crossing the yaw wrap turned the long way around or exceeded the18-degree step");
        drive(mech, owner, 3, wrap);
        helper.assertTrue(Math.abs(Mth.wrapDegrees(mech.getYRot() + 170)) < .001,
            "Body did not converge across the positive/negative180-degree boundary");
        Vec3 facing = Vec3.directionFromRotation(0, -170);
        Cow front = EntityType.COW.create(helper.getLevel());
        Cow behind = EntityType.COW.create(helper.getLevel());
        for (Cow target : new Cow[]{front, behind}) {
            target.getAttribute(Attributes.MAX_HEALTH).setBaseValue(100);
            target.setHealth(100); target.setNoAi(true); target.setNoGravity(true);
            Vec3 at = mech.position().add(0, 2.4, 0).add(facing.scale(target == front ? 3.5 : -3.5));
            target.setPos(at.x, at.y, at.z);
            helper.getLevel().addFreshEntity(target);
        }
        drive(mech, owner, 1, new MechSuitNetwork.InputPayload(0, 0, false, false, true, false, -170, 0));
        helper.assertTrue(front.getHealth() == 88 && behind.getHealth() == 100,
            "Sword damage did not follow the settled wrapped body yaw");
        front.discard(); behind.discard();
        drive(mech, owner, 16, wrap);
        Cow above = EntityType.COW.create(helper.getLevel());
        above.getAttribute(Attributes.MAX_HEALTH).setBaseValue(100);
        above.setHealth(100); above.setNoAi(true); above.setNoGravity(true);
        Vec3 raisedTarget = mech.position().add(0, 3.5, 0).add(Vec3.directionFromRotation(-70, -170).scale(4));
        above.setPos(raisedTarget.x, raisedTarget.y - .7, raisedTarget.z);
        helper.getLevel().addFreshEntity(above);
        drive(mech, owner, 1, new MechSuitNetwork.InputPayload(0, 0, false, false, false, true, -170, -70));
        helper.assertTrue(above.getHealth() == 88 && mech.getXRot() == -70,
            "Sword could not reach a nearby airborne target along the pilot's elevated pitch");
        above.discard(); owner.stopRiding(); mech.discard(); helper.succeed();
    }

    @GameTest(template = "arcade_test")
    public static void groundedAndFlyingMotionRespectsWallsCeilingsAndBounds(GameTestHelper helper) {
        ServerPlayer owner = player(helper, "MechCollision");
        MechSuitEntity mech = mech(helper, owner);
        helper.assertTrue(mech.interact(owner, InteractionHand.MAIN_HAND).consumesAction(), "Could not mount collision fixture");
        for (int x = 10; x <= 14; x++) { for (int y = 1; y <= 10; y++) { helper.setBlock(new BlockPos(x, y, 16), Blocks.STONE); } }
        drive(mech, owner, 30, input(1, 0, false, false, false, false));
        helper.assertTrue(mech.getBoundingBox().maxZ <= helper.absolutePos(new BlockPos(12, 1, 16)).getZ() + .001,
            "Ground movement passed through a wall");
        for (int x = 10; x <= 14; x++) { for (int z = 11; z <= 17; z++) { helper.setBlock(new BlockPos(x, 9, z), Blocks.STONE); } }
        drive(mech, owner, 30, input(0, 0, true, false, false, false));
        helper.assertTrue(mech.getBoundingBox().maxY <= helper.absolutePos(new BlockPos(12, 9, 12)).getY() + .001,
            "Flight passed through a ceiling");
        helper.assertFalse(MechSuitEntity.loadedAndWithinBounds(helper.getLevel(), mech.getBoundingBox().move(0, 2000, 0)),
            "Movement guard accepted coordinates above the build limit");
        helper.assertFalse(MechSuitEntity.loadedAndWithinBounds(helper.getLevel(), mech.getBoundingBox().move(30_000_000, 0, 0)),
            "Movement guard accepted an unloaded/border-exceeding destination");
        owner.stopRiding(); mech.discard(); helper.succeed();
    }

    @GameTest(template = "arcade_test")
    public static void damagedAndWreckedSuitsSaveRecoverRepairAndCannotDuplicate(GameTestHelper helper) {
        ServerPlayer owner = player(helper, "MechRecovery");
        MechSuitEntity mech = mech(helper, owner);
        helper.assertTrue(mech.hurt(helper.getLevel().damageSources().generic(), 31) && mech.getHullHealth() == 89,
            "Environmental damage was ignored on an unoccupied suit");
        mech.setCustomName(Component.literal("Lucky prize"));
        CompoundTag saved = mech.saveWithoutId(new CompoundTag());
        MechSuitEntity restored = new MechSuitEntity(JapaneseArcades.MECH_SUIT.get(), helper.getLevel());
        restored.load(saved);
        helper.assertTrue(restored.getHullHealth() == 89 && owner.getUUID().equals(restored.getOwnerUUID())
            && "Lucky prize".equals(restored.getCustomName().getString()), "Entity save/load lost reward identity or condition");
        for (int slot = 0; slot < 36; slot++) { owner.getInventory().setItem(slot, new ItemStack(Items.STONE, 64)); }
        owner.setShiftKeyDown(true);
        helper.assertFalse(mech.interact(owner, InteractionHand.MAIN_HAND).consumesAction(), "Full inventory recovery reported success");
        helper.assertTrue(!mech.isRemoved(), "Full inventory destroyed the paid reward");
        owner.getInventory().setItem(0, ItemStack.EMPTY);
        helper.assertTrue(mech.interact(owner, InteractionHand.MAIN_HAND).consumesAction() && mech.isRemoved(), "Recovery failed");
        helper.assertFalse(mech.interact(owner, InteractionHand.MAIN_HAND).consumesAction(), "Removed suit accepted duplicate recovery");
        helper.assertTrue(packedCount(owner) == 1 && MechSuitItem.hull(owner.getMainHandItem()) == 89
            && "Lucky prize".equals(owner.getMainHandItem().getHoverName().getString()), "Recovery duplicated, healed or renamed the reward");
        owner.setShiftKeyDown(false);
        helper.assertTrue(deploy(helper, owner), "Recovered suit failed to redeploy");
        MechSuitEntity redeployed = helper.getLevel().getEntitiesOfClass(MechSuitEntity.class, new AABB(helper.absolutePos(BASE)).inflate(3)).getFirst();
        helper.assertTrue(redeployed.hurt(helper.getLevel().damageSources().generic(), 200) && redeployed.getHullHealth() == 0 && !redeployed.isRemoved(),
            "Exhausted hull did not leave a repairable wreck");
        helper.assertFalse(redeployed.interact(owner, InteractionHand.MAIN_HAND).consumesAction(), "Wrecked suit could be piloted");
        owner.setItemInHand(InteractionHand.MAIN_HAND, new ItemStack(Items.IRON_INGOT, 2));
        helper.assertTrue(redeployed.interact(owner, InteractionHand.MAIN_HAND).consumesAction() && redeployed.getHullHealth() == 20
            && owner.getMainHandItem().getCount() == 1, "Repair did not consume exactly one iron ingot for 20 hull");
        redeployed.discard(); helper.succeed();
    }

    @GameTest(template = "arcade_test")
    public static void dualSwordsUseIndependentCooldownsAndRespectWallsAndPets(GameTestHelper helper) {
        ServerPlayer owner = player(helper, "MechSwords");
        MechSuitEntity mech = mech(helper, owner);
        helper.assertTrue(mech.interact(owner, InteractionHand.MAIN_HAND).consumesAction(), "Could not mount sword fixture");
        Cow target = EntityType.COW.create(helper.getLevel());
        target.setNoAi(true); target.setNoGravity(true);
        target.setPos(mech.getX(), mech.getY() + 2.4, mech.getZ() + 3.5);
        helper.getLevel().addFreshEntity(target);
        Wolf pet = EntityType.WOLF.create(helper.getLevel());
        pet.setNoAi(true); pet.setNoGravity(true); pet.setOwnerUUID(owner.getUUID()); pet.setTame(true, false);
        pet.setPos(mech.getX() + 1, mech.getY() + 2.4, mech.getZ() + 3.5);
        helper.getLevel().addFreshEntity(pet);
        float petHealth = pet.getHealth();
        drive(mech, owner, 1, input(0, 0, false, false, true, false));
        helper.assertTrue(target.getHealth() < target.getMaxHealth() && mech.getLeftSwingTicks() == MechSuitEntity.SWING_TICKS
            && mech.getRightSwingTicks() == 0, "Left sword did not damage a reachable target or animated the wrong arm");
        helper.assertTrue(pet.getHealth() == petHealth, "Sword damaged the pilot's pet");
        target.discard();
        Cow second = EntityType.COW.create(helper.getLevel());
        second.setNoAi(true); second.setNoGravity(true);
        second.setPos(mech.getX(), mech.getY() + 2.4, mech.getZ() + 3.5);
        helper.getLevel().addFreshEntity(second);
        drive(mech, owner, 1, input(0, 0, false, false, false, true));
        helper.assertTrue(second.getHealth() < second.getMaxHealth() && mech.getRightSwingTicks() == MechSuitEntity.SWING_TICKS,
            "Right sword shared the left sword's cooldown or dealt no damage");
        second.discard();
        drive(mech, owner, 16, input(0, 0, false, false, false, false));
        Cow dual = EntityType.COW.create(helper.getLevel());
        dual.getAttribute(Attributes.MAX_HEALTH).setBaseValue(100);
        dual.setHealth(100); dual.setNoAi(true); dual.setNoGravity(true);
        dual.setPos(mech.getX(), mech.getY() + 2.4, mech.getZ() + 3.5);
        helper.getLevel().addFreshEntity(dual);
        drive(mech, owner, 1, input(0, 0, false, false, true, true));
        helper.assertTrue(dual.getHealth() == 76 && mech.getLeftSwingTicks() == MechSuitEntity.SWING_TICKS
            && mech.getRightSwingTicks() == MechSuitEntity.SWING_TICKS, "Simultaneous blades lost one strike to immunity frames");
        dual.invulnerableTime = 0;
        drive(mech, owner, 1, input(0, 0, false, false, true, true));
        helper.assertTrue(dual.getHealth() == 76, "Held attack bypassed server cooldown");
        dual.discard();
        Cow blocked = EntityType.COW.create(helper.getLevel());
        blocked.setNoAi(true); blocked.setNoGravity(true);
        blocked.setPos(mech.getX(), mech.getY() + 2.4, mech.getZ() + 3.5);
        helper.getLevel().addFreshEntity(blocked);
        for (int x = 11; x <= 13; x++) { for (int y = 2; y <= 6; y++) { helper.setBlock(new BlockPos(x, y, 14), Blocks.STONE); } }
        drive(mech, owner, 30, input(0, 0, false, false, true, true));
        helper.assertTrue(blocked.getHealth() == blocked.getMaxHealth(), "Swords hit a target through a solid wall");
        blocked.discard(); pet.discard(); owner.stopRiding(); mech.discard(); helper.succeed();
    }

    @GameTest(template = "arcade_test", timeoutTicks = 160)
    public static void cockpitAbsorbsDamageAndVanillaAttackCannotBypassSwordCooldown(GameTestHelper helper) {
        ServerPlayer owner = player(helper, "MechArmor");
        owner.setInvulnerable(false);
        MechSuitEntity mech = mech(helper, owner);
        helper.assertTrue(mech.interact(owner, InteractionHand.MAIN_HAND).consumesAction(), "Could not mount armor fixture");
        // Real connections retain vanilla's 60-tick login invulnerability before damage events are emitted.
        helper.runAfterDelay(65, () -> {
            float pilotHealth = owner.getHealth();
            owner.hurt(helper.getLevel().damageSources().generic(), 10);
            helper.assertTrue(owner.getHealth() == pilotHealth && mech.getHullHealth() == MechSuitEntity.MAX_HULL - 10,
                "Incoming pilot damage did not transfer to the suit hull: pilot=" + owner.getHealth() + ", hull=" + mech.getHullHealth());
            Cow target = EntityType.COW.create(helper.getLevel());
            target.setNoAi(true); target.setNoGravity(true);
            target.setPos(mech.getX(), mech.getY() + 2.4, mech.getZ() + 2);
            helper.getLevel().addFreshEntity(target);
            owner.setItemInHand(InteractionHand.MAIN_HAND, new ItemStack(Items.NETHERITE_SWORD));
            owner.attack(target);
            helper.assertTrue(target.getHealth() == target.getMaxHealth(), "Mounted vanilla attack bypassed suit cooldown/weapon rules");
            target.discard(); owner.stopRiding(); mech.discard(); helper.succeed();
        });
    }
}
