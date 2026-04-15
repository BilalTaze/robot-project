import math
import time
import threading
from rtde_control import RTDEControlInterface
from rtde_receive import RTDEReceiveInterface
from Safety import SafetyManager


class RobotController:
    """
    Robot controller using RTDE.

    Features:
    - translation control
    - rotation control
    - base/tool frame support
    - safety checks
    - interruptible motion with speedL
    """

    def __init__(self, robot_ip: str):
        # Initialize RTDE interfaces (control + feedback)
        self.robot_ip = robot_ip
        self.rtde_c = RTDEControlInterface(robot_ip)
        self.rtde_r = RTDEReceiveInterface(robot_ip)

        # Safety manager (workspace, reach, joints)
        self.safety = SafetyManager()

        # Flag used to stop motion from outside (main thread)
        self.stop_requested = False

        # Lock to prevent multiple simultaneous motions
        self.motion_lock = threading.Lock()

        # Indicates if robot is currently moving
        self.is_moving = False

    # ------------------------------------------------------------------
    # Basic math helpers
    # ------------------------------------------------------------------

    @staticmethod
    def mat_mul(A, B):
        # Multiply two 3x3 matrices
        return [
            [sum(A[i][k] * B[k][j] for k in range(3)) for j in range(3)]
            for i in range(3)
        ]

    @staticmethod
    def mat_transpose(A):
        # Transpose a 3x3 matrix
        return [list(row) for row in zip(*A)]

    @staticmethod
    def mat_vec_mul(R, v):
        # Multiply a matrix with a 3D vector
        return [
            R[0][0] * v[0] + R[0][1] * v[1] + R[0][2] * v[2],
            R[1][0] * v[0] + R[1][1] * v[1] + R[1][2] * v[2],
            R[2][0] * v[0] + R[2][1] * v[1] + R[2][2] * v[2],
        ]

    # ------------------------------------------------------------------
    # Rotation conversions
    # ------------------------------------------------------------------

    @staticmethod
    def rotvec_to_matrix(rx, ry, rz):
        # Convert rotation vector (axis-angle) to rotation matrix
        theta = math.sqrt(rx * rx + ry * ry + rz * rz)

        if theta < 1e-12:
            return [
                [1.0, 0.0, 0.0],
                [0.0, 1.0, 0.0],
                [0.0, 0.0, 1.0],
            ]

        kx = rx / theta
        ky = ry / theta
        kz = rz / theta

        c = math.cos(theta)
        s = math.sin(theta)
        v = 1.0 - c

        return [
            [kx * kx * v + c,      kx * ky * v - kz * s, kx * kz * v + ky * s],
            [ky * kx * v + kz * s, ky * ky * v + c,      ky * kz * v - kx * s],
            [kz * kx * v - ky * s, kz * ky * v + kx * s, kz * kz * v + c],
        ]

    @staticmethod
    def matrix_to_rotvec(R):
        # Convert rotation matrix to rotation vector
        trace = R[0][0] + R[1][1] + R[2][2]
        cos_theta = max(-1.0, min(1.0, (trace - 1.0) / 2.0))
        theta = math.acos(cos_theta)

        if theta < 1e-12:
            return [0.0, 0.0, 0.0]

        denom = 2.0 * math.sin(theta)
        kx = (R[2][1] - R[1][2]) / denom
        ky = (R[0][2] - R[2][0]) / denom
        kz = (R[1][0] - R[0][1]) / denom

        return [kx * theta, ky * theta, kz * theta]

    @staticmethod
    def rpy_to_matrix(roll, pitch, yaw):
        # Convert roll-pitch-yaw to rotation matrix
        cr = math.cos(roll)
        sr = math.sin(roll)
        cp = math.cos(pitch)
        sp = math.sin(pitch)
        cy = math.cos(yaw)
        sy = math.sin(yaw)

        Rx = [[1, 0, 0], [0, cr, -sr], [0, sr, cr]]
        Ry = [[cp, 0, sp], [0, 1, 0], [-sp, 0, cp]]
        Rz = [[cy, -sy, 0], [sy, cy, 0], [0, 0, 1]]

        return RobotController.mat_mul(Rz, RobotController.mat_mul(Ry, Rx))

    @staticmethod
    def matrix_to_rpy(R):
        # Convert rotation matrix to roll-pitch-yaw
        pitch = math.asin(-R[2][0])

        if abs(math.cos(pitch)) > 1e-9:
            roll = math.atan2(R[2][1], R[2][2])
            yaw = math.atan2(R[1][0], R[0][0])
        else:
            roll = 0.0
            yaw = math.atan2(-R[0][1], R[1][1])

        return [roll, pitch, yaw]

    @classmethod
    def rotvec_to_rpy(cls, rx, ry, rz):
        # Convert rotation vector → RPY
        return cls.matrix_to_rpy(cls.rotvec_to_matrix(rx, ry, rz))

    @classmethod
    def rpy_to_rotvec(cls, roll, pitch, yaw):
        # Convert RPY → rotation vector
        return cls.matrix_to_rotvec(cls.rpy_to_matrix(roll, pitch, yaw))

    # ------------------------------------------------------------------
    # Stop
    # ------------------------------------------------------------------

    def _stop_motion(self):
        # Stop robot immediately
        try:
            self.rtde_c.speedStop()
        except Exception:
            pass

        try:
            self.rtde_c.stopL(1.0)
        except Exception:
            pass

        self.stop_requested = False
        print("Robot stopped")

    # ------------------------------------------------------------------
    # Safety helpers
    # ------------------------------------------------------------------

    def _is_target_safe(self, target_pose, motion_name="movement"):
        # Check workspace limits
        if not self.safety.is_pose_safe(target_pose):
            print(f"Target outside workspace: {motion_name} cancelled")
            return False

        # Check reach limits
        if not self.safety.is_reach_safe(target_pose):
            print(f"Reach limit exceeded: {motion_name} cancelled")
            return False

        return True

    # ------------------------------------------------------------------
    # Target builders
    # ------------------------------------------------------------------

    def _build_translation_target(self, pose, direction, distance, frame):
        # Compute target position depending on frame (base or tool)
        target_pose = pose.copy()

        dx = direction[0] * distance
        dy = direction[1] * distance
        dz = direction[2] * distance

        if frame == "base":
            # Direct movement in base frame
            target_pose[0] += dx
            target_pose[1] += dy
            target_pose[2] += dz
        else:
            # Convert movement from tool frame to base frame
            rx, ry, rz = pose[3], pose[4], pose[5]
            R = self.rotvec_to_matrix(rx, ry, rz)
            v_base = self.mat_vec_mul(R, [dx, dy, dz])

            target_pose[0] += v_base[0]
            target_pose[1] += v_base[1]
            target_pose[2] += v_base[2]

        return target_pose

    def _build_rotation_target(self, pose, rotation):
        # Compute target orientation
        target_pose = pose.copy()

        roll, pitch, yaw = self.rotvec_to_rpy(
            pose[3], pose[4], pose[5]
        )

        roll += rotation[0]
        pitch += rotation[1]
        yaw += rotation[2]

        rv = self.rpy_to_rotvec(roll, pitch, yaw)
        target_pose[3] = rv[0]
        target_pose[4] = rv[1]
        target_pose[5] = rv[2]

        return target_pose

    # ------------------------------------------------------------------
    # Motion execution
    # ------------------------------------------------------------------

    def _speedL_move_to_target(
        self,
        target_pose,
        speed=0.08,
        acc=0.30,
        dt=0.02,
        pos_tolerance=0.002,
    ):
        # Move to target position using speedL loop (interruptible)
        max_iters = 1000

        for _ in range(max_iters):
            if self.stop_requested:
                self._stop_motion()
                return False

            current_pose = self.rtde_r.getActualTCPPose()

            # Compute position error
            ex = target_pose[0] - current_pose[0]
            ey = target_pose[1] - current_pose[1]
            ez = target_pose[2] - current_pose[2]

            dist = math.sqrt(ex * ex + ey * ey + ez * ez)

            # Stop if close enough
            if dist < pos_tolerance:
                self.rtde_c.speedStop()
                return True

            # Normalize direction
            ux = ex / dist
            uy = ey / dist
            uz = ez / dist

            # Compute velocity
            vx = ux * speed
            vy = uy * speed
            vz = uz * speed

            # Send speed command (translation only)
            self.rtde_c.speedL([vx, vy, vz, 0.0, 0.0, 0.0], acc, dt)
            time.sleep(dt)

        self.rtde_c.speedStop()
        print("Target not reached within iteration limit")
        return False

    def _speedL_rotate_to_target(
        self,
        target_pose,
        angular_speed=0.5,
        acc=1.0,
        dt=0.02,
        angle_tolerance=0.01,
    ):
        # Rotate to target orientation using speedL loop
        max_iters = 1000

        for _ in range(max_iters):
            if self.stop_requested:
                self._stop_motion()
                return False

            current_pose = self.rtde_r.getActualTCPPose()

            # Compute rotation matrices
            Rc = self.rotvec_to_matrix(
                current_pose[3], current_pose[4], current_pose[5]
            )
            Rt = self.rotvec_to_matrix(
                target_pose[3], target_pose[4], target_pose[5]
            )

            # Compute rotation error
            Re = self.mat_mul(Rt, self.mat_transpose(Rc))
            err_vec = self.matrix_to_rotvec(Re)

            ex, ey, ez = err_vec
            angle_error = math.sqrt(ex * ex + ey * ey + ez * ez)

            # Stop if angle is small enough
            if angle_error < angle_tolerance:
                self.rtde_c.speedStop()
                return True

            # Normalize rotation axis
            ux = ex / angle_error
            uy = ey / angle_error
            uz = ez / angle_error

            # Angular velocity
            wx = ux * angular_speed
            wy = uy * angular_speed
            wz = uz * angular_speed

            # Send speed command (rotation only)
            self.rtde_c.speedL([0.0, 0.0, 0.0, wx, wy, wz], acc, dt)
            time.sleep(dt)

        self.rtde_c.speedStop()
        print("Rotation target not reached within iteration limit")
        return False

    # ------------------------------------------------------------------
    # Public command execution
    # ------------------------------------------------------------------

    def execute_command(self, cmd: dict):
        # Execute parsed command (move or rotate)
        if cmd is None:
            return False

        with self.motion_lock:
            self.is_moving = True
            try:
                action = cmd.get("action")
                current_joints = self.rtde_r.getActualQ()

                # Check joint safety before motion
                if not self.safety.is_joint_configuration_safe(current_joints):
                    print("Unsafe joint configuration: command cancelled")
                    return False

                # -------- ROTATION --------
                if action == "rotate":
                    rotation = cmd.get("rotation")

                    if rotation is None or len(rotation) != 3:
                        return False

                    if not self.safety.is_rotation_step_safe(rotation):
                        print("Rotation too large: command cancelled")
                        return False

                    pose = self.rtde_r.getActualTCPPose()
                    target_pose = self._build_rotation_target(pose, rotation)

                    if not self._is_target_safe(target_pose, "rotation"):
                        return False

                    return self._speedL_rotate_to_target(target_pose)

                # -------- TRANSLATION --------
                if action != "move":
                    return False

                direction = cmd.get("direction")
                distance = cmd.get("distance")
                frame = cmd.get("frame", "tool")

                if direction is None or len(direction) != 3:
                    return False

                if distance is None:
                    return False

                if not self.safety.is_translation_step_safe(distance):
                    print("Translation too large: command cancelled")
                    return False

                pose = self.rtde_r.getActualTCPPose()
                target_pose = self._build_translation_target(
                    pose, direction, distance, frame
                )

                if not self._is_target_safe(target_pose, "movement"):
                    return False

                return self._speedL_move_to_target(target_pose)

            finally:
                self.is_moving = False

    def close(self):
        # Stop RTDE script properly
        try:
            self.rtde_c.stopScript()
        except Exception:
            pass