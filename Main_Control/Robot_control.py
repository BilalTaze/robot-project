import math
import time
from rtde_control import RTDEControlInterface
from rtde_receive import RTDEReceiveInterface
from Safety import SafetyManager


class RobotController:
    def __init__(self, robot_ip: str):
        self.robot_ip = robot_ip
        self.rtde_c = RTDEControlInterface(robot_ip)
        self.rtde_r = RTDEReceiveInterface(robot_ip)
        self.safety = SafetyManager()

    @staticmethod
    def mat_mul(A, B):
        return [
            [sum(A[i][k] * B[k][j] for k in range(3)) for j in range(3)]
            for i in range(3)
        ]

    @staticmethod
    def mat_vec_mul(R, v):
        return [
            R[0][0] * v[0] + R[0][1] * v[1] + R[0][2] * v[2],
            R[1][0] * v[0] + R[1][1] * v[1] + R[1][2] * v[2],
            R[2][0] * v[0] + R[2][1] * v[1] + R[2][2] * v[2],
        ]

    @staticmethod
    def rotvec_to_matrix(rx, ry, rz):
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
        cr = math.cos(roll)
        sr = math.sin(roll)
        cp = math.cos(pitch)
        sp = math.sin(pitch)
        cy = math.cos(yaw)
        sy = math.sin(yaw)

        Rx = [
            [1, 0, 0],
            [0, cr, -sr],
            [0, sr, cr],
        ]
        Ry = [
            [cp, 0, sp],
            [0, 1, 0],
            [-sp, 0, cp],
        ]
        Rz = [
            [cy, -sy, 0],
            [sy, cy, 0],
            [0, 0, 1],
        ]

        return RobotController.mat_mul(Rz, RobotController.mat_mul(Ry, Rx))

    @staticmethod
    def matrix_to_rpy(R):
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
        R = cls.rotvec_to_matrix(rx, ry, rz)
        return cls.matrix_to_rpy(R)

    @classmethod
    def rpy_to_rotvec(cls, roll, pitch, yaw):
        R = cls.rpy_to_matrix(roll, pitch, yaw)
        return cls.matrix_to_rotvec(R)

    @staticmethod
    def rad_to_deg(rad_value):
        return rad_value * 180.0 / math.pi

    def print_rpy_deg(self, label, pose):
        roll, pitch, yaw = self.rotvec_to_rpy(pose[3], pose[4], pose[5])
        print(f"\n--- {label} RPY (deg) ---")
        print(
            f"Roll: {self.rad_to_deg(roll):.2f}, "
            f"Pitch: {self.rad_to_deg(pitch):.2f}, "
            f"Yaw: {self.rad_to_deg(yaw):.2f}"
        )

    def execute_command(self, cmd: dict):
        if cmd is None:
            return

        action = cmd.get("action")
        current_joints = self.rtde_r.getActualQ()

        if action == "stop":
            self.rtde_c.speedStop()
            print("Robot stopped")
            return

        if not self.safety.is_joint_configuration_safe(current_joints):
            print("Unsafe joint configuration: command cancelled")
            return

        if action == "rotate":
            rotation = cmd.get("rotation")

            if rotation is None or len(rotation) != 3:
                return

            if not self.safety.is_rotation_step_safe(rotation):
                print("Rotation step too large: command cancelled")
                return

            pose_before = self.rtde_r.getActualTCPPose()

            print("\n--- BEFORE ROTATION (rotvec) ---")
            print(
                f"Rx: {pose_before[3]:.4f}, "
                f"Ry: {pose_before[4]:.4f}, "
                f"Rz: {pose_before[5]:.4f}"
            )
            self.print_rpy_deg("BEFORE", pose_before)

            target_pose = pose_before.copy()

            roll, pitch, yaw = self.rotvec_to_rpy(
                pose_before[3], pose_before[4], pose_before[5]
            )

            roll += rotation[0]
            pitch += rotation[1]
            yaw += rotation[2]

            rv = self.rpy_to_rotvec(roll, pitch, yaw)

            target_pose[3] = rv[0]
            target_pose[4] = rv[1]
            target_pose[5] = rv[2]

            if not self.safety.is_pose_safe(target_pose):
                print("Target pose outside safety workspace: rotation cancelled")
                return

            if not self.safety.is_reach_safe(target_pose):
                print("Target pose exceeds safe reach: rotation cancelled")
                return

            print("\n--- TARGET ROTATION (rotvec) ---")
            print(
                f"Rx: {target_pose[3]:.4f}, "
                f"Ry: {target_pose[4]:.4f}, "
                f"Rz: {target_pose[5]:.4f}"
            )
            self.print_rpy_deg("TARGET", target_pose)

            self.rtde_c.moveL(target_pose, 0.10, 0.10)
            time.sleep(0.5)

            pose_after = self.rtde_r.getActualTCPPose()

            print("\n--- AFTER ROTATION (rotvec) ---")
            print(
                f"Rx: {pose_after[3]:.4f}, "
                f"Ry: {pose_after[4]:.4f}, "
                f"Rz: {pose_after[5]:.4f}"
            )
            self.print_rpy_deg("AFTER", pose_after)

            print("\n--- DELTA ROTATION (rotvec) ---")
            print(
                f"dRx: {pose_after[3] - pose_before[3]:.4f}, "
                f"dRy: {pose_after[4] - pose_before[4]:.4f}, "
                f"dRz: {pose_after[5] - pose_before[5]:.4f}"
            )

            roll_before, pitch_before, yaw_before = self.rotvec_to_rpy(
                pose_before[3], pose_before[4], pose_before[5]
            )
            roll_after, pitch_after, yaw_after = self.rotvec_to_rpy(
                pose_after[3], pose_after[4], pose_after[5]
            )

            print("\n--- DELTA RPY (deg) ---")
            print(
                f"dRoll: {self.rad_to_deg(roll_after - roll_before):.2f}, "
                f"dPitch: {self.rad_to_deg(pitch_after - pitch_before):.2f}, "
                f"dYaw: {self.rad_to_deg(yaw_after - yaw_before):.2f}"
            )
            return

        if action != "move":
            return

        direction = cmd.get("direction")
        distance = cmd.get("distance")
        frame = cmd.get("frame", "tool")

        if direction is None or len(direction) != 3:
            return

        if distance is None:
            return

        if not self.safety.is_translation_step_safe(distance):
            print("Translation step too large: command cancelled")
            return

        pose_before = self.rtde_r.getActualTCPPose()

        print("\n--- BEFORE ---")
        print(
            f"X: {pose_before[0]:.4f}, "
            f"Y: {pose_before[1]:.4f}, "
            f"Z: {pose_before[2]:.4f}"
        )

        dx = direction[0] * distance
        dy = direction[1] * distance
        dz = direction[2] * distance

        target_pose = pose_before.copy()

        if frame == "base":
            target_pose[0] += dx
            target_pose[1] += dy
            target_pose[2] += dz
        else:
            rx, ry, rz = pose_before[3], pose_before[4], pose_before[5]
            R = self.rotvec_to_matrix(rx, ry, rz)

            v_tool = [dx, dy, dz]
            v_base = self.mat_vec_mul(R, v_tool)

            target_pose[0] += v_base[0]
            target_pose[1] += v_base[1]
            target_pose[2] += v_base[2]

        if not self.safety.is_pose_safe(target_pose):
            print("Target pose outside safety workspace: movement cancelled")
            return

        if not self.safety.is_reach_safe(target_pose):
            print("Target pose exceeds safe reach: movement cancelled")
            return

        print("\n--- TARGET ---")
        print(
            f"X: {target_pose[0]:.4f}, "
            f"Y: {target_pose[1]:.4f}, "
            f"Z: {target_pose[2]:.4f}"
        )

        self.rtde_c.moveL(target_pose, 0.10, 0.10)
        time.sleep(0.5)

        pose_after = self.rtde_r.getActualTCPPose()

        print("\n--- AFTER ---")
        print(
            f"X: {pose_after[0]:.4f}, "
            f"Y: {pose_after[1]:.4f}, "
            f"Z: {pose_after[2]:.4f}"
        )

        dx_real = pose_after[0] - pose_before[0]
        dy_real = pose_after[1] - pose_before[1]
        dz_real = pose_after[2] - pose_before[2]

        print("\n--- DELTA ---")
        print(
            f"dX: {dx_real:.4f}, "
            f"dY: {dy_real:.4f}, "
            f"dZ: {dz_real:.4f}"
        )

    def close(self):
        self.rtde_c.stopScript()