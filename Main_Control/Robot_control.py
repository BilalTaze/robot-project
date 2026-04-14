import math
import time
from rtde_control import RTDEControlInterface
from rtde_receive import RTDEReceiveInterface
from Safety import SafetyManager


class RobotController:
    """
    Main class responsible for controlling the robot using RTDE.
    Handles:
    - motion execution (move / rotate)
    - coordinate transformations (tool ↔ base)
    - safety checks before execution
    """

    def __init__(self, robot_ip: str):
        # Initialize robot communication interfaces
        self.robot_ip = robot_ip
        self.rtde_c = RTDEControlInterface(robot_ip)   # Control interface (commands)
        self.rtde_r = RTDEReceiveInterface(robot_ip)   # Feedback interface (state)
        self.safety = SafetyManager()                  # Safety system

    # -------- MATRIX OPERATIONS --------

    @staticmethod
    def mat_mul(A, B):
        """Multiply two 3x3 matrices"""
        return [
            [sum(A[i][k] * B[k][j] for k in range(3)) for j in range(3)]
            for i in range(3)
        ]

    @staticmethod
    def mat_vec_mul(R, v):
        """Multiply a 3x3 matrix with a 3D vector"""
        return [
            R[0][0] * v[0] + R[0][1] * v[1] + R[0][2] * v[2],
            R[1][0] * v[0] + R[1][1] * v[1] + R[1][2] * v[2],
            R[2][0] * v[0] + R[2][1] * v[1] + R[2][2] * v[2],
        ]

    # -------- ROTATION CONVERSIONS --------

    @staticmethod
    def rotvec_to_matrix(rx, ry, rz):
        """
        Convert a rotation vector (axis-angle) to a rotation matrix.
        Used to transform tool-frame movements into base-frame coordinates.
        """
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
        """
        Convert a rotation matrix back to a rotation vector.
        Used after modifying orientation in RPY.
        """
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
        """
        Convert Roll-Pitch-Yaw angles to a rotation matrix.
        """
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
        """
        Convert a rotation matrix to Roll-Pitch-Yaw angles.
        Used for intuitive rotation manipulation.
        """
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
        """Convert rotation vector → RPY"""
        return cls.matrix_to_rpy(cls.rotvec_to_matrix(rx, ry, rz))

    @classmethod
    def rpy_to_rotvec(cls, roll, pitch, yaw):
        """Convert RPY → rotation vector"""
        return cls.matrix_to_rotvec(cls.rpy_to_matrix(roll, pitch, yaw))

    # -------- COMMAND EXECUTION --------

    def execute_command(self, cmd: dict):
        """
        Execute a parsed command:
        - move → translation
        - rotate → orientation change
        - stop → emergency stop
        """

        if cmd is None:
            return

        action = cmd.get("action")
        current_joints = self.rtde_r.getActualQ()

        # -------- STOP COMMAND --------
        if action == "stop":
            self.rtde_c.speedStop()
            print("Robot stopped")
            return

        # -------- SAFETY CHECK (JOINTS) --------
        if not self.safety.is_joint_configuration_safe(current_joints):
            print("Unsafe joint configuration: command cancelled")
            return

        # -------- ROTATION --------
        if action == "rotate":
            rotation = cmd.get("rotation")

            if rotation is None or len(rotation) != 3:
                return

            # Check rotation limits
            if not self.safety.is_rotation_step_safe(rotation):
                print("Rotation too large: command cancelled")
                return

            # Get current pose
            pose = self.rtde_r.getActualTCPPose()
            target_pose = pose.copy()

            # Convert to RPY for intuitive manipulation
            roll, pitch, yaw = self.rotvec_to_rpy(
                pose[3], pose[4], pose[5]
            )

            # Apply rotation
            roll += rotation[0]
            pitch += rotation[1]
            yaw += rotation[2]

            # Convert back to rotation vector
            rv = self.rpy_to_rotvec(roll, pitch, yaw)

            target_pose[3] = rv[0]
            target_pose[4] = rv[1]
            target_pose[5] = rv[2]

            # Safety checks
            if not self.safety.is_pose_safe(target_pose):
                print("Target outside workspace: rotation cancelled")
                return

            if not self.safety.is_reach_safe(target_pose):
                print("Reach limit exceeded: rotation cancelled")
                return

            # Execute movement
            self.rtde_c.moveL(target_pose, 0.10, 0.10)
            time.sleep(0.3)
            return

        # -------- TRANSLATION --------
        if action != "move":
            return

        direction = cmd.get("direction")
        distance = cmd.get("distance")
        frame = cmd.get("frame", "tool")

        if direction is None or len(direction) != 3:
            return

        if distance is None:
            return

        # Check translation limits
        if not self.safety.is_translation_step_safe(distance):
            print("Translation too large: command cancelled")
            return

        # Get current pose
        pose = self.rtde_r.getActualTCPPose()
        target_pose = pose.copy()

        dx = direction[0] * distance
        dy = direction[1] * distance
        dz = direction[2] * distance

        # -------- FRAME HANDLING --------
        if frame == "base":
            # Direct movement in world frame
            target_pose[0] += dx
            target_pose[1] += dy
            target_pose[2] += dz
        else:
            # Movement relative to tool orientation
            rx, ry, rz = pose[3], pose[4], pose[5]
            R = self.rotvec_to_matrix(rx, ry, rz)

            v_base = self.mat_vec_mul(R, [dx, dy, dz])

            target_pose[0] += v_base[0]
            target_pose[1] += v_base[1]
            target_pose[2] += v_base[2]

        # Safety checks
        if not self.safety.is_pose_safe(target_pose):
            print("Target outside workspace: movement cancelled")
            return

        if not self.safety.is_reach_safe(target_pose):
            print("Reach limit exceeded: movement cancelled")
            return

        # Execute movement
        self.rtde_c.moveL(target_pose, 0.10, 0.10)
        time.sleep(0.3)

    def close(self):
        """Stop robot script properly"""
        self.rtde_c.stopScript()