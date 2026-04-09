from rtde_receive import RTDEReceiveInterface as RTDEReceive

ROBOT_IP = "172.20.10.2"

rtde_r = RTDEReceive(ROBOT_IP)

print("Joints :", rtde_r.getActualQ())
print("TCP pose :", rtde_r.getActualTCPPose())