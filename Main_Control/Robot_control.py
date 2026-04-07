import math
import time
from rtde_control import RTDEControlInterface
from rtde_receive import RTDEReceiveInterface


class RobotController:
    def __init__(self, robot_ip: str):
        self.robot_ip = robot_ip
        self.rtde_c = RTDEControlInterface(robot_ip)
        self.rtde_r = RTDEReceiveInterface(robot_ip)

    # ---------- ROTATION TOOL -> BASE ----------
    @staticmethod
    def rotvec_to_matrix(rx, ry, rz):
        theta = math.sqrt(rx*rx + ry*ry + rz*rz)

        if theta < 1e-12:
            return [
                [1, 0, 0],
                [0, 1, 0],
                [0, 0, 1]
            ]

        kx = rx / theta
        ky = ry / theta
        kz = rz / theta

        c = math.cos(theta)
        s = math.sin(theta)
        v = 1 - c

        return [
            [kx*kx*v + c,     kx*ky*v - kz*s, kx*kz*v + ky*s],
            [ky*kx*v + kz*s,  ky*ky*v + c,    ky*kz*v - kx*s],
            [kz*kx*v - ky*s,  kz*ky*v + kx*s, kz*kz*v + c]
        ]

    @staticmethod
    def mat_vec_mul(R, v):
        return [
            R[0][0]*v[0] + R[0][1]*v[1] + R[0][2]*v[2],
            R[1][0]*v[0] + R[1][1]*v[1] + R[1][2]*v[2],
            R[2][0]*v[0] + R[2][1]*v[1] + R[2][2]*v[2]
        ]

    # ---------- EXECUTION ----------
    def execute_command(self, cmd: dict):

        action = cmd.get("action")

        if action == "stop":
            self.rtde_c.speedStop()
            print("Robot stopped")
            return

        if action != "move":
            print("Unknown or missing action")
            return

        direction = cmd.get("direction")
        distance = cmd.get("distance")
        frame = cmd.get("frame", "tool")

        if direction is None:
            print("Missing direction")
            return

        if distance is None:
            print("Missing distance")
            return

        # ---------- BEFORE ----------
        pose_before = self.rtde_r.getActualTCPPose()

        print("\n--- BEFORE ---")
        print(f"X: {pose_before[0]:.4f}, Y: {pose_before[1]:.4f}, Z: {pose_before[2]:.4f}")

        # ---------- CALCUL ----------
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

        # ---------- TARGET ----------
        print("\n--- TARGET ---")
        print(f"X: {target_pose[0]:.4f}, Y: {target_pose[1]:.4f}, Z: {target_pose[2]:.4f}")

        # ---------- MOVE ----------
        self.rtde_c.moveL(target_pose, 0.10, 0.10)

        time.sleep(0.5)

        # ---------- AFTER ----------
        pose_after = self.rtde_r.getActualTCPPose()

        print("\n--- AFTER ---")
        print(f"X: {pose_after[0]:.4f}, Y: {pose_after[1]:.4f}, Z: {pose_after[2]:.4f}")

        # ---------- DELTA ----------
        dx_real = pose_after[0] - pose_before[0]
        dy_real = pose_after[1] - pose_before[1]
        dz_real = pose_after[2] - pose_before[2]

        print("\n--- DELTA ---")
        print(f"dX: {dx_real:.4f}, dY: {dy_real:.4f}, dZ: {dz_real:.4f}")

    # ---------- CLOSE ----------
    def close(self):
        self.rtde_c.stopScript()