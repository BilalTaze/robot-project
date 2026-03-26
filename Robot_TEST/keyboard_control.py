# import time
# import keyboard
# from rtde_control import RTDEControlInterface

# ROBOT_IP = "10.49.212.217"

# rtde_c = RTDEControlInterface(ROBOT_IP)

# speed = 0.05  # m/s
# acc = 0.5

# print("Contrôle clavier actif")
# print("W/S = X+, X-")
# print("A/D = Y-, Y+")
# print("R/F = Z+, Z-")
# print("Q = Quitter")

# try:
#     while True:
#         vx = 0
#         vy = 0
#         vz = 0

#         if keyboard.is_pressed("w"):
#             vx = speed
#         if keyboard.is_pressed("s"):
#             vx = -speed
#         if keyboard.is_pressed("a"):
#             vy = -speed
#         if keyboard.is_pressed("d"):
#             vy = speed
#         if keyboard.is_pressed("r"):
#             vz = speed
#         if keyboard.is_pressed("f"):
#             vz = -speed

#         rtde_c.speedL([vx, vy, vz, 0, 0, 0], acc, 0.1)

#         if keyboard.is_pressed("q"):
#             break

#         time.sleep(0.02)

# except KeyboardInterrupt:
#     pass

# finally:
#     rtde_c.speedStop()
#     rtde_c.stopScript()
#     print("Arrêt")

import time
import math
import keyboard
from rtde_control import RTDEControlInterface
from rtde_receive import RTDEReceiveInterface


ROBOT_IP = "10.49.212.217"

rtde_c = RTDEControlInterface(ROBOT_IP)
rtde_r = RTDEReceiveInterface(ROBOT_IP)

speed = 0.05   # m/s
acc = 0.5
dt = 0.02      # 50 Hz

mode = "base"
toggle_pressed = False


def rotvec_to_matrix(rx, ry, rz):
    """Convert axis-angle rotation vector to 3x3 rotation matrix."""
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


def mat_vec_mul(R, v):
    return [
        R[0][0] * v[0] + R[0][1] * v[1] + R[0][2] * v[2],
        R[1][0] * v[0] + R[1][1] * v[1] + R[1][2] * v[2],
        R[2][0] * v[0] + R[2][1] * v[1] + R[2][2] * v[2],
    ]


print("Contrôle clavier actif")
print("W/S = X+ / X-")
print("A/D = Y- / Y+")
print("R/F = Z+ / Z-")
print("T = changer Base/Tool")
print("Q = quitter")
print(f"Mode actuel : {mode.upper()}")

try:
    while True:
        vx = 0.0
        vy = 0.0
        vz = 0.0

        if keyboard.is_pressed("w"):
            vx = speed
        if keyboard.is_pressed("s"):
            vx = -speed
        if keyboard.is_pressed("a"):
            vy = -speed
        if keyboard.is_pressed("d"):
            vy = speed
        if keyboard.is_pressed("r"):
            vz = speed
        if keyboard.is_pressed("f"):
            vz = -speed

        # Toggle mode with T
        if keyboard.is_pressed("t"):
            if not toggle_pressed:
                mode = "tool" if mode == "base" else "base"
                print(f"Mode changé : {mode.upper()}")
                toggle_pressed = True
        else:
            toggle_pressed = False

        if mode == "base":
            v_cmd = [vx, vy, vz]
        else:
            # Convert tool-frame linear velocity into base-frame linear velocity
            tcp_pose = rtde_r.getActualTCPPose()   # [x, y, z, rx, ry, rz]
            rx, ry, rz = tcp_pose[3], tcp_pose[4], tcp_pose[5]
            R = rotvec_to_matrix(rx, ry, rz)
            v_cmd = mat_vec_mul(R, [vx, vy, vz])

        rtde_c.speedL([v_cmd[0], v_cmd[1], v_cmd[2], 0, 0, 0], acc, 0.1)

        if keyboard.is_pressed("q"):
            break

        time.sleep(dt)

except KeyboardInterrupt:
    pass

finally:
    rtde_c.speedStop()
    rtde_c.stopScript()
    print("Arrêt")