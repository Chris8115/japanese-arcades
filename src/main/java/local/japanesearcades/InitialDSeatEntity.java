package local.japanesearcades;

import java.util.List;
import javax.annotation.Nullable;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.chat.Component;
import net.minecraft.network.syncher.EntityDataAccessor;
import net.minecraft.network.syncher.EntityDataSerializers;
import net.minecraft.network.syncher.SynchedEntityData;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityDimensions;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.entity.vehicle.DismountHelper;
import net.minecraft.world.level.Level;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.BlockHitResult;
import net.minecraft.world.phys.HitResult;
import net.minecraft.world.phys.Vec3;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.neoforge.event.entity.player.PlayerEvent;

/** Invisible, nonpersistent riding anchor; inventory and ownership never live here. */
public final class InitialDSeatEntity extends Entity {
    private static final EntityDataAccessor<BlockPos> ANCHOR = SynchedEntityData.defineId(InitialDSeatEntity.class, EntityDataSerializers.BLOCK_POS);
    private static final EntityDataAccessor<Integer> FACING = SynchedEntityData.defineId(InitialDSeatEntity.class, EntityDataSerializers.INT);
    private boolean disposing;

    public InitialDSeatEntity(EntityType<? extends InitialDSeatEntity> type, Level level) {
        super(type, level);
        noPhysics = true;
        setNoGravity(true);
        setInvulnerable(true);
        setInvisible(true);
    }
    @Override protected void defineSynchedData(SynchedEntityData.Builder builder) {
        builder.define(ANCHOR, BlockPos.ZERO);
        builder.define(FACING, Direction.NORTH.get3DDataValue());
    }
    public BlockPos getAnchor() { return entityData.get(ANCHOR); }
    public Direction getFacing() { return Direction.from3DDataValue(entityData.get(FACING)); }
    private void configure(BlockPos anchor, Direction facing) {
        entityData.set(ANCHOR, anchor.immutable());
        entityData.set(FACING, facing.get3DDataValue());
        Vec3 hip = hipPosition(anchor, facing);
        setPos(hip.x, hip.y, hip.z);
        setYRot(facing.getOpposite().toYRot());
    }
    static Vec3 hipPosition(BlockPos anchor, Direction facing) {
        // North-facing cabinet: cushion center (8,11.5,-24), with a tiny
        // clearance above its top. Vanilla players attach at their hips (.6).
        return Vec3.atLowerCornerOf(anchor).add(.5, 11.7/16, .5)
            .add(facing.getStepX()*2, 0, facing.getStepZ()*2);
    }
    private static List<InitialDSeatEntity> seats(Level level, BlockPos anchor) {
        return level.getEntitiesOfClass(InitialDSeatEntity.class, new AABB(anchor).inflate(4),
            seat -> !seat.isRemoved() && seat.getAnchor().equals(anchor));
    }
    static void removeFor(Level level, BlockPos anchor) {
        if (!level.isClientSide) { for (InitialDSeatEntity seat : seats(level, anchor)) { seat.discard(); } }
    }

    static boolean mount(Player player, BlockPos clicked) {
        Level level = player.level();
        if (level.isClientSide || !(player instanceof ServerPlayer) || !player.isAlive() || player.isSpectator()
                || player.isPassenger() || player.isShiftKeyDown() || !player.getMainHandItem().isEmpty()
                || !player.canInteractWithBlock(clicked, 0) || !level.hasChunkAt(clicked)) { return false; }
        var state = level.getBlockState(clicked);
        if (!(state.getBlock() instanceof InitialDCabinetBlock block) || state.getValue(InitialDCabinetBlock.SECTION).depth != 2) { return false; }
        BlockPos anchor = block.basePosition(clicked, state);
        Direction facing = state.getValue(InitialDCabinetBlock.FACING);
        if (!block.isComplete(level, anchor, facing)) { return false; }
        HitResult ray = player.pick(player.blockInteractionRange(), 1, false);
        if (!(ray instanceof BlockHitResult visible) || ray.getType() != HitResult.Type.BLOCK) { return false; }
        var visibleState = level.getBlockState(visible.getBlockPos());
        if (!visibleState.is(block) || visibleState.getValue(InitialDCabinetBlock.SECTION).depth != 2
                || !block.basePosition(visible.getBlockPos(), visibleState).equals(anchor)) { return false; }
        for (InitialDSeatEntity existing : seats(level, anchor)) {
            if (!existing.getPassengers().isEmpty()) {
                player.displayClientMessage(Component.translatable("message.japanesearcades.initial_d.occupied"), true);
                return false;
            }
            existing.discard();
        }
        InitialDSeatEntity seat = new InitialDSeatEntity(JapaneseArcades.INITIAL_D_SEAT.get(), level);
        seat.configure(anchor, facing);
        if (!seat.hasHeadroom(player) || seat.findExit(player) == null) {
            player.displayClientMessage(Component.translatable("message.japanesearcades.initial_d.blocked"), true);
            return false;
        }
        if (!level.addFreshEntity(seat)) { return false; }
        if (!block.isComplete(level, anchor, facing) || !player.startRiding(seat)) { seat.discard(); return false; }
        player.setYRot(seat.getYRot());
        player.setYHeadRot(seat.getYRot());
        player.setYBodyRot(seat.getYRot());
        player.setXRot(0);
        seat.positionRider(player);
        player.displayClientMessage(Component.translatable("message.japanesearcades.initial_d.seated"), true);
        return true;
    }

    private boolean hasHeadroom(LivingEntity passenger) {
        Vec3 hip = hipPosition(getAnchor(), getFacing());
        double half = passenger.getBbWidth()/2;
        double top = hip.y - passenger.getVehicleAttachmentPoint(this).y + passenger.getBbHeight();
        AABB torso = new AABB(hip.x-half, hip.y+.05, hip.z-half, hip.x+half, top, hip.z+half);
        if (!level().getWorldBorder().isWithinBounds(torso)) { return false; }
        for (BlockPos pos : BlockPos.betweenClosed(BlockPos.containing(torso.minX, torso.minY, torso.minZ),
                BlockPos.containing(torso.maxX, torso.maxY, torso.maxZ))) {
            var state = level().getBlockState(pos);
            if (state.getBlock() instanceof InitialDCabinetBlock own && own.basePosition(pos, state).equals(getAnchor())) { continue; }
            for (AABB box : state.getCollisionShape(level(), pos).toAabbs()) {
                if (box.move(pos).intersects(torso)) { return false; }
            }
        }
        return true;
    }

    @Override protected boolean canAddPassenger(Entity passenger) { return passenger instanceof Player && getPassengers().isEmpty(); }
    @Override protected Vec3 getPassengerAttachmentPoint(Entity passenger, EntityDimensions dimensions, float partialTick) { return Vec3.ZERO; }
    @Override protected void positionRider(Entity passenger, Entity.MoveFunction callback) {
        super.positionRider(passenger, callback);
        passenger.setYBodyRot(getYRot());
        passenger.resetFallDistance();
    }
    @Override public boolean hurt(DamageSource source, float amount) { return false; }
    @Override public void tick() {
        super.tick();
        setDeltaMovement(Vec3.ZERO);
        if (!level().isClientSide) {
            Vec3 hip = hipPosition(getAnchor(), getFacing());
            setPos(hip.x, hip.y, hip.z);
            if (!level().hasChunkAt(getAnchor())) { discard(); return; }
            var state = level().getBlockState(getAnchor());
            if (!(state.getBlock() instanceof InitialDCabinetBlock block)
                    || !block.isComplete(level(), getAnchor(), getFacing()) || getPassengers().isEmpty()) { discard(); return; }
            Entity rider = getFirstPassenger();
            if (!(rider instanceof Player player) || !player.isAlive() || player.isRemoved() || player.isSpectator()
                    || player.isShiftKeyDown() || !hasHeadroom(player)) { ejectPassengers(); discard(); }
        }
    }
    @Override public void remove(RemovalReason reason) {
        if (!disposing && !level().isClientSide) {
            disposing = true;
            ejectPassengers();
        }
        super.remove(reason);
    }

    @Nullable private Vec3 findExit(LivingEntity passenger) {
        BlockPos seat = getAnchor().relative(getFacing(), 2);
        Direction side = getFacing().getClockWise();
        List<BlockPos> preferred = List.of(seat.relative(side), seat.relative(side.getOpposite()), seat.relative(getFacing()),
            seat.relative(getFacing()).relative(side), seat.relative(getFacing()).relative(side.getOpposite()), seat.relative(getFacing(), 2));
        for (int height : new int[]{0, -1, 1, 2, 3}) {
            for (BlockPos candidate : preferred) {
                Vec3 exit = safeExit(passenger, candidate.above(height));
                if (exit != null) { return exit; }
            }
        }
        // A newly placed obstacle can close the nearest exits while occupied.
        // Search the surrounding floor before falling back above the cabinet.
        for (int radius = 2; radius <= 4; radius++) {
            for (int x = -radius; x <= radius; x++) {
                for (int z = -radius; z <= radius; z++) {
                    if (Math.abs(x) != radius && Math.abs(z) != radius) { continue; }
                    for (int height : new int[]{0, -1, 1, 2, 3}) {
                        Vec3 exit = safeExit(passenger, seat.offset(x, height, z));
                        if (exit != null) { return exit; }
                    }
                }
            }
        }
        return null;
    }
    @Nullable private Vec3 safeExit(LivingEntity passenger, BlockPos candidate) {
        if (!level().hasChunkAt(candidate) || !level().getFluidState(candidate).isEmpty()) { return null; }
        Vec3 exit = DismountHelper.findSafeDismountLocation(passenger.getType(), level(), candidate, true);
        return exit != null && level().noCollision(passenger, passenger.getDimensions(passenger.getPose()).makeBoundingBox(exit)) ? exit : null;
    }
    @Override public Vec3 getDismountLocationForPassenger(LivingEntity passenger) {
        Vec3 exit = findExit(passenger);
        if (exit != null) { return exit; }
        for (int up = 2; up <= 16; up++) {
            Vec3 fallback = position().add(0, up, 0);
            if (level().noCollision(passenger, passenger.getDimensions(passenger.getPose()).makeBoundingBox(fallback))) { return fallback; }
        }
        return position().add(0, 2, 0);
    }

    @SubscribeEvent public static void beforeLogout(PlayerEvent.PlayerLoggedOutEvent event) {
        if (event.getEntity().getVehicle() instanceof InitialDSeatEntity seat) {
            event.getEntity().stopRiding();
            seat.discard();
        }
    }
    @Override protected void readAdditionalSaveData(CompoundTag tag) {
        // noSave() prevents world persistence; reading stale/manual data cannot
        // create an occupied or cross-world ride after a restart.
        entityData.set(ANCHOR, BlockPos.of(tag.getLong("Anchor")));
        Direction facing = Direction.from3DDataValue(tag.getInt("Facing"));
        entityData.set(FACING, facing.getAxis().isHorizontal() ? facing.get3DDataValue() : Direction.NORTH.get3DDataValue());
    }
    @Override protected void addAdditionalSaveData(CompoundTag tag) {
        tag.putLong("Anchor", getAnchor().asLong());
        tag.putInt("Facing", getFacing().get3DDataValue());
    }
}
