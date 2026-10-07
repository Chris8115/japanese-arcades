package local.japanesearcades;

import java.util.Map;
import java.util.WeakHashMap;
import javax.annotation.Nullable;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.ClipContext;
import net.minecraft.world.level.Level;
import net.minecraft.world.phys.BlockHitResult;
import net.minecraft.world.phys.HitResult;
import net.minecraft.world.phys.Vec3;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.neoforge.event.entity.player.PlayerInteractEvent;

/** Server-validated tilted drum faces; no client-supplied hit region or sound. */
public final class TaikoDrumInteraction {
    private static final double SIN = Math.sin(Math.toRadians(35));
    private static final double COS = Math.cos(Math.toRadians(35));
    static final double OUTWARD_YAW = Math.toRadians(8);
    private static final Map<Player, Cooldown> LAST_HIT = new WeakHashMap<>();
    private record Cooldown(Level level, long tick) {}
    enum Region { HEAD, RIM }
    record Hit(Region region, Vec3 point) {}
    private TaikoDrumInteraction() {}

    static Vec3 modelPoint(BlockPos anchor, Direction facing, double x, double y, double z) {
        x /= 16; y /= 16; z /= 16;
        Vec3 rotated = switch (facing) {
            case EAST -> new Vec3(1-z, y, x);
            case SOUTH -> new Vec3(1-x, y, 1-z);
            case WEST -> new Vec3(z, y, 1-x);
            default -> new Vec3(x, y, z);
        };
        return Vec3.atLowerCornerOf(anchor).add(rotated);
    }

    static Vec3 headCenter(BlockPos anchor, Direction facing, TaikoCabinetBlock.Side side) {
        return modelPoint(anchor, facing, side == TaikoCabinetBlock.Side.PRIMARY ? 8 : 24, 24, -9);
    }

    static Vec3 drumNormal(Direction facing, TaikoCabinetBlock.Side side) {
        Direction across = facing.getClockWise();
        double outward = side == TaikoCabinetBlock.Side.PRIMARY ? -1 : 1;
        double lateral = outward * COS * Math.sin(OUTWARD_YAW);
        double forward = COS * Math.cos(OUTWARD_YAW);
        return new Vec3(across.getStepX()*lateral + facing.getStepX()*forward, SIN,
            across.getStepZ()*lateral + facing.getStepZ()*forward);
    }

    /** Across the tilted face, following its eight-degree outward turn. */
    static Vec3 drumAcross(Direction facing, TaikoCabinetBlock.Side side) {
        Direction across = facing.getClockWise();
        double outward = side == TaikoCabinetBlock.Side.PRIMARY ? -1 : 1;
        double lateral = Math.cos(OUTWARD_YAW), forward = -outward * Math.sin(OUTWARD_YAW);
        return new Vec3(across.getStepX()*lateral + facing.getStepX()*forward, 0,
            across.getStepZ()*lateral + facing.getStepZ()*forward);
    }

    @Nullable
    static Hit target(Player player, BlockPos pos) {
        if (!player.isAlive() || player.isSpectator() || !player.level().hasChunkAt(pos)
                || !player.canInteractWithBlock(pos, .05)) { return null; }
        var held = player.getMainHandItem();
        if (!held.isEmpty() && !held.is(Items.STICK)) { return null; }
        var state = player.level().getBlockState(pos);
        if (!(state.getBlock() instanceof TaikoCabinetBlock block)
                || state.getValue(TaikoCabinetBlock.SECTION) != TaikoCabinetBlock.Section.DRUMS) { return null; }
        Direction facing = state.getValue(TaikoCabinetBlock.FACING);
        Vec3 center = headCenter(block.basePosition(pos, state), facing, state.getValue(TaikoCabinetBlock.SIDE));
        Vec3 normal = drumNormal(facing, state.getValue(TaikoCabinetBlock.SIDE));
        Vec3 eye = player.getEyePosition();
        Vec3 ray = player.getViewVector(1);
        double incidence = ray.dot(normal);
        if (incidence >= -.001) { return null; }
        double distance = center.subtract(eye).dot(normal) / incidence;
        if (distance < 0 || distance > player.blockInteractionRange()+.05) { return null; }
        Vec3 point = eye.add(ray.scale(distance));
        double radius = point.distanceTo(center)*16;
        if (radius > 6.8) { return null; }
        // The ordinary block outline ray must reach this same drum first, so a
        // forged interaction through a wall cannot play the hidden drum.
        BlockHitResult obstruction = player.level().clip(new ClipContext(eye, point.add(ray.scale(.13)),
            ClipContext.Block.OUTLINE, ClipContext.Fluid.NONE, player));
        if (obstruction.getType() != HitResult.Type.BLOCK || !obstruction.getBlockPos().equals(pos)) { return null; }
        return new Hit(radius <= 6.1 ? Region.HEAD : Region.RIM, point);
    }

    static boolean tryHit(Player player, BlockPos pos) {
        Hit hit = target(player, pos);
        if (hit == null) { return false; }
        Level level = player.level();
        if (!level.isClientSide) {
            long tick = level.getGameTime();
            Cooldown previous = LAST_HIT.get(player);
            if (previous != null && previous.level == level && tick >= previous.tick && tick-previous.tick < 2) { return true; }
            LAST_HIT.put(player, new Cooldown(level, tick));
            var sound = hit.region == Region.HEAD ? SoundEvents.NOTE_BLOCK_BASEDRUM.value() : SoundEvents.NOTE_BLOCK_HAT.value();
            level.playSound(null, hit.point.x, hit.point.y, hit.point.z, sound, SoundSource.BLOCKS,
                1.0F, hit.region == Region.HEAD ? .8F : 1.2F);
        }
        return true;
    }

    @SubscribeEvent
    public static void leftClick(PlayerInteractEvent.LeftClickBlock event) {
        if (event.getEntity().isShiftKeyDown()) { return; }
        if (target(event.getEntity(), event.getPos()) == null) { return; }
        // NeoForge still forwards START to the server when the client cancels
        // mining. Cancel both sides to prevent damage or creative prediction.
        event.setCanceled(true);
        if (event.getAction() == PlayerInteractEvent.LeftClickBlock.Action.START) {
            tryHit(event.getEntity(), event.getPos());
        }
    }
}
