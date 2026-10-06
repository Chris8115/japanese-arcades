package local.funpack.custom;

import java.util.List;
import java.util.UUID;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.gametest.framework.GameTest;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.nbt.NbtOps;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.util.RandomSource;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.item.BlockItem;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.item.context.BlockPlaceContext;
import net.minecraft.world.level.GameType;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.phys.BlockHitResult;
import net.minecraft.world.phys.HitResult;
import net.minecraft.world.phys.Vec3;
import net.neoforged.neoforge.gametest.GameTestHolder;
import net.neoforged.neoforge.gametest.PrefixGameTestTemplate;
import static local.funpack.custom.NostalgiaCabinetGameTests.BASE;
import static local.funpack.custom.GachaponTransactionGameTests.createPlayer;

@GameTestHolder(FunPackCustom.MOD_ID)
@PrefixGameTestTemplate(false)
public final class ArcadePlayGameTests {
    private static void floor(GameTestHelper helper) {
        for (int x = 0; x < 8; x++) for (int z = 0; z < 8; z++) helper.setBlock(new BlockPos(x, 0, z), Blocks.STONE);
    }
    private static void place(GameTestHelper helper, ServerPlayer player, ItemStack item) {
        floor(helper);
        player.setYRot(0);
        player.setItemInHand(InteractionHand.MAIN_HAND, item);
        BlockPos ground = helper.absolutePos(BASE.below());
        var hit = new BlockHitResult(Vec3.atCenterOf(ground).add(0,.5,0), Direction.UP, ground, false);
        helper.assertTrue(((BlockItem)item.getItem()).place(new BlockPlaceContext(player, InteractionHand.MAIN_HAND, item, hit)).consumesAction(),
            "Cabinet failed to place for arcade play");
    }
    private static void aim(GameTestHelper helper, ServerPlayer player) {
        Vec3 target = Vec3.atLowerCornerOf(helper.absolutePos(BASE)).add(.5, 1.7, .6);
        Vec3 eye = target.add(-2, 0, 0);
        player.setPos(eye.x, eye.y-player.getEyeHeight(), eye.z);
        player.setYRot(-90); player.setYHeadRot(-90); player.setXRot(0);
        player.setOldPosAndRot();
    }
    private static ItemStack funded(long credits, long points) {
        ItemStack item = ArcadePassItem.createPass();
        ArcadePassItem.setData(item, ArcadePassItem.data(item).withBalances(credits, points));
        return item;
    }
    private static ServerPlayer setup(GameTestHelper helper, String name) {
        ServerPlayer player = createPlayer(helper, name, GameType.SURVIVAL);
        place(helper, player, new ItemStack(FunPackCustom.NOSTALGIA_OP3_ITEM.get()));
        aim(helper, player);
        return player;
    }
    @GameTest(template="nostalgia_test")
    public static void arcadeEveryCabinetConsumesCreditsAwardsRankAndPreservesIdleModelAndDisc(GameTestHelper helper) {
        for (var entry : ArcadeOrderCatalog.entries(ArcadeOrderCatalog.MACHINES)) {
            ItemStack item = entry.output();
            if (!(item.getItem() instanceof BlockItem bi) || !(bi.getBlock() instanceof NostalgiaCabinetBlock)) continue;
            ServerPlayer player = createPlayer(helper, "ArcadePlay", GameType.SURVIVAL);
            place(helper, player, item);
            player.setItemInHand(InteractionHand.MAIN_HAND, new ItemStack(Items.MUSIC_DISC_13));
            helper.useBlock(BASE.above(), player);
            var jukebox = (NostalgiaJukeboxBlockEntity)helper.getBlockEntity(BASE);
            helper.assertTrue(jukebox.getSongPlayer().isPlaying(), "Fixture music was not started");
            var anchorBefore = helper.getBlockState(BASE);
            var consoleBefore = helper.getBlockState(BASE.above());
            var profile = ArcadeEconomyConfig.profile(entry.id());
            ItemStack pass = funded(profile.credits()+100, 37);
            var before = ArcadePassItem.data(pass);
            player.setItemInHand(InteractionHand.MAIN_HAND, pass);
            aim(helper, player);
            helper.assertTrue(ArcadePlayInteraction.play(player, helper.absolutePos(BASE.above()), InteractionHand.MAIN_HAND), "Paid play rejected: "+entry.id());
            var after = ArcadePassItem.data(pass);
            helper.assertTrue(after.credits()==100 && profile.ranks().stream().anyMatch(rank -> after.prizePoints()==37+rank.points()), "Wrong debit/reward for "+entry.id());
            helper.assertTrue(after.id().equals(before.id()) && after.revision()==before.revision()+1, "Play replaced identity or failed to revise pass");
            helper.assertTrue(anchorBefore.equals(helper.getBlockState(BASE)) && consoleBefore.equals(helper.getBlockState(BASE.above())), "Play changed idle blockstate");
            helper.assertTrue(jukebox.getTheItem().is(Items.MUSIC_DISC_13) && jukebox.getSongPlayer().isPlaying(), "Pass interrupted music disc");
            helper.getLevel().destroyBlock(helper.absolutePos(BASE), false);
            helper.getLevel().getServer().getPlayerList().remove(player);
        }
        helper.succeed();
    }
    @GameTest(template="nostalgia_test", timeoutTicks=1300)
    public static void arcadeRepeatedPacketAndChangedPassCannotBypassCooldown(GameTestHelper helper) {
        ServerPlayer player = setup(helper, "ArcadeRepeat");
        ItemStack a=funded(500,0), b=funded(500,0);
        player.setItemInHand(InteractionHand.MAIN_HAND,a);
        helper.assertTrue(ArcadePlayInteraction.play(player,helper.absolutePos(BASE),InteractionHand.MAIN_HAND),"Initial play failed");
        var paid=ArcadePassItem.data(a);
        helper.assertFalse(ArcadePlayInteraction.play(player,helper.absolutePos(BASE.above()),InteractionHand.MAIN_HAND),"Repeat charged another play");
        helper.assertTrue(paid.equals(ArcadePassItem.data(a)),"Repeated packet changed wallet");
        player.setItemInHand(InteractionHand.MAIN_HAND,ItemStack.EMPTY);
        player.setItemInHand(InteractionHand.OFF_HAND,b);
        helper.assertFalse(ArcadePlayInteraction.play(player,helper.absolutePos(BASE),InteractionHand.OFF_HAND),"Switching pass bypassed player cooldown");
        helper.assertTrue(ArcadePassItem.data(b).credits()==500 && ArcadePassItem.data(b).prizePoints()==0,"Blocked offhand pass was charged");
        helper.runAfterDelay(ArcadeEconomyConfig.cooldownTicks()+1,()->{
            aim(helper,player);
            helper.assertTrue(ArcadePlayInteraction.play(player,helper.absolutePos(BASE),InteractionHand.OFF_HAND),"Offhand pass failed after cooldown");
            helper.assertTrue(paid.equals(ArcadePassItem.data(a)) && ArcadePassItem.data(b).prizePoints()>0,"Reward reached the wrong pass");
            helper.succeed();
        });
    }
    @GameTest(template="nostalgia_test")
    public static void arcadeInsufficientCreditAndFullWalletNeverConsumeValue(GameTestHelper helper) {
        ServerPlayer player=setup(helper,"ArcadePoor");
        ItemStack pass=funded(0,30); player.setItemInHand(InteractionHand.MAIN_HAND,pass);
        var before=ArcadePassItem.data(pass);
        helper.assertFalse(ArcadePlayInteraction.play(player,helper.absolutePos(BASE),InteractionHand.MAIN_HAND),"Unfunded pass played");
        helper.assertTrue(before.equals(ArcadePassItem.data(pass)),"Failed play changed wallet");
        ArcadePassItem.setData(pass,before.withBalances(100,ArcadePassData.MAX_BALANCE));
        before=ArcadePassItem.data(pass);
        helper.assertFalse(ArcadePlayInteraction.play(player,helper.absolutePos(BASE),InteractionHand.MAIN_HAND),"Overflowing points accepted");
        helper.assertTrue(before.equals(ArcadePassItem.data(pass)),"Full-wallet rejection consumed credits");
        pass.setCount(2);
        helper.assertFalse(ArcadePlayInteraction.play(player,helper.absolutePos(BASE),InteractionHand.MAIN_HAND),"Stacked malformed pass accepted");
        helper.succeed();
    }
    @GameTest(template="nostalgia_test")
    public static void arcadeSpectatorRangeWallAndPrizeDecorationRejectPaidPlay(GameTestHelper helper) {
        ServerPlayer player=setup(helper,"ArcadeReach");
        ItemStack pass=funded(100,10); player.setItemInHand(InteractionHand.MAIN_HAND,pass);
        var before=ArcadePassItem.data(pass);
        player.setGameMode(GameType.SPECTATOR);
        helper.assertFalse(ArcadePlayInteraction.play(player,helper.absolutePos(BASE),InteractionHand.MAIN_HAND),"Spectator played");
        player.setGameMode(GameType.SURVIVAL);
        aim(helper,player); player.setPos(player.getX()-10,player.getY(),player.getZ());
        helper.assertFalse(ArcadePlayInteraction.play(player,helper.absolutePos(BASE),InteractionHand.MAIN_HAND),"Remote play accepted");
        aim(helper,player); helper.setBlock(BASE.west().above(),Blocks.STONE);
        helper.assertFalse(ArcadePlayInteraction.play(player,helper.absolutePos(BASE),InteractionHand.MAIN_HAND),"Play passed through a wall");
        helper.setBlock(BASE.west().above(),Blocks.AIR);
        helper.getLevel().destroyBlock(helper.absolutePos(BASE),false);
        helper.setBlock(BASE,FunPackCustom.HATSUNE_MIKU_FIGURE.get());
        helper.assertFalse(ArcadePlayInteraction.play(player,helper.absolutePos(BASE),InteractionHand.MAIN_HAND),"Collectible figure gave points");
        helper.assertTrue(before.equals(ArcadePassItem.data(pass)),"Rejected play changed pass");
        helper.succeed();
    }
    @GameTest(template="nostalgia_test")
    public static void arcadePassComponentPersistsBalancesAndFutureDesignAndRejectsInvalidMoney(GameTestHelper helper) {
        ItemStack pass=funded(123456789,876543210);
        var old=ArcadePassItem.data(pass);
        ArcadePassItem.setData(pass,new ArcadePassData(1,old.id(),ResourceLocation.parse("future:rare_dungeon"),old.credits(),old.prizePoints(),old.revision()));
        var saved=pass.save(helper.getLevel().registryAccess());
        ItemStack restored=ItemStack.parseOptional(helper.getLevel().registryAccess(),(CompoundTag)saved);
        helper.assertTrue(ArcadePassItem.data(restored).equals(ArcadePassItem.data(pass)),"Persisted pass lost balances, ID or skin");
        CompoundTag invalid=new CompoundTag(); invalid.putLong("credits",-1);
        helper.assertTrue(ArcadePassData.CODEC.parse(NbtOps.INSTANCE,invalid).error().isPresent(),"Negative credits decoded");
        invalid.putLong("credits",ArcadePassData.MAX_BALANCE+1);
        helper.assertTrue(ArcadePassData.CODEC.parse(NbtOps.INSTANCE,invalid).error().isPresent(),"Overflow balance decoded");
        CompoundTag found=new CompoundTag(); found.putLong("credits",75); found.putString("design","future:rare_dungeon");
        var loot=ArcadePassData.CODEC.parse(NbtOps.INSTANCE,found).getOrThrow();
        helper.assertTrue(loot.credits()==75 && loot.prizePoints()==0 && loot.version()==1,"Minimal future loot data did not load");
        helper.succeed();
    }
    @GameTest(template="nostalgia_test")
    public static void arcadeWeightedRanksRespectConfiguredWeightsAndRewards(GameTestHelper helper) {
        var profile=new ArcadeEconomyConfig.PlayProfile(7,"test",List.of(
            new ArcadeEconomyConfig.Rank("low",1,3),new ArcadeEconomyConfig.Rank("high",3,19)));
        RandomSource random=RandomSource.create(1234567);
        int high=0;
        for(int i=0;i<4000;i++){
            var rank=ArcadeEconomyConfig.roll(profile,random);
            helper.assertTrue(rank.points()==3 || rank.points()==19,"Rank used a hardcoded reward");
            if(rank.label().equals("high"))high++;
        }
        helper.assertTrue(high>2700 && high<3300,"Weighted draw does not favor configured 3:1 result");
        helper.succeed();
    }
}
