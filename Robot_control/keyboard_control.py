import time
import keyboard
from rtde_control import RTDEControlInterface

ROBOT_IP = "10.159.202.217"

rtde_c = RTDEControlInterface(ROBOT_IP)

speed = 0.05  # m/s
acc = 0.5

print("Contrôle clavier actif")
print("W/S = X+, X-")
print("A/D = Y-, Y+")
print("R/F = Z+, Z-")
print("Q = Quitter")

try:
    while True:
        vx = 0
        vy = 0
        vz = 0

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

        rtde_c.speedL([vx, vy, vz, 0, 0, 0], acc, 0.1)

        if keyboard.is_pressed("q"):
            break

        time.sleep(0.02)

except KeyboardInterrupt:
    pass

finally:
    rtde_c.speedStop()
    rtde_c.stopScript()
    print("Arrêt")