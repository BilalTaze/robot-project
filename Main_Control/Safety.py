import math


class SafetyManager:
    """
    Safety layer for the robot controller.

    This class is responsible for validating commands before execution
    in order to prevent:
    - collisions
    - unreachable positions
    - singular configurations
    - unsafe joint configurations
    """

    def __init__(self):

        # -------- WORKSPACE LIMITS --------
        # Defines a 3D bounding box in which the TCP is allowed to move (in meters)
        self.x_min = -0.45
        self.x_max = 0.45

        self.y_min = -0.45
        self.y_max = -0.19

        self.z_min = 0.10
        self.z_max = 0.40

        # -------- MOTION LIMITS --------
        # Maximum allowed displacement per command
        self.max_translation_step = 0.10           # 10 cm

        # Maximum allowed rotation per command (converted from degrees to radians)
        self.max_rotation_step = math.radians(30)  # 30°

        # -------- REACH LIMIT --------
        # Maximum allowed distance from robot base to TCP
        # Prevents the arm from being fully stretched (singularity risk)
        self.max_reach = 0.55  # meters

    # -------- WORKSPACE CHECK --------

    def is_pose_safe(self, target_pose):
        """
        Check if the target position is inside the allowed workspace.

        target_pose = [x, y, z, rx, ry, rz]
        """

        x, y, z = target_pose[0], target_pose[1], target_pose[2]

        # Check each axis independently
        if not (self.x_min <= x <= self.x_max):
            return False

        if not (self.y_min <= y <= self.y_max):
            return False

        if not (self.z_min <= z <= self.z_max):
            return False

        return True

    # -------- TRANSLATION LIMIT --------

    def is_translation_step_safe(self, distance):
        """
        Check if the translation distance is within allowed limits.
        """
        return abs(distance) <= self.max_translation_step

    # -------- ROTATION LIMIT --------

    def is_rotation_step_safe(self, rotation):
        """
        Check if the rotation is within allowed limits.

        rotation = [Rx, Ry, Rz] (in radians)
        """
        if rotation is None or len(rotation) != 3:
            return False

        return all(abs(r) <= self.max_rotation_step for r in rotation)

    # -------- JOINT SAFETY --------

    def is_joint_configuration_safe(self, joints):
        """
        Avoid risky joint configurations.

        joints = [q1, q2, q3, q4, q5, q6] in radians
        """

        if joints is None or len(joints) != 6:
            return False

        shoulder = joints[1]
        elbow = joints[2]
        wrist2 = joints[4]

        # Heuristic 1:
        # Avoid wrist alignment (near 0 rad → unstable configuration)
        if abs(wrist2) < math.radians(5):
            return False

        # Heuristic 2:
        # Avoid fully stretched or aligned arm (singularity risk)
        if abs(shoulder) < math.radians(5) and abs(elbow) < math.radians(5):
            return False

        return True

    # -------- REACH COMPUTATION --------

    def compute_reach(self, pose):
        """
        Compute the Euclidean distance from robot base to TCP.

        pose = [x, y, z, rx, ry, rz]
        """

        x, y, z = pose[0], pose[1], pose[2]

        return math.sqrt(x * x + y * y + z * z)

    # -------- REACH SAFETY --------

    def is_reach_safe(self, pose):
        """
        Check if the TCP is within safe reach distance.

        Prevents the robot from reaching too far,
        which could lead to instability or singularity.
        """
        return self.compute_reach(pose) <= self.max_reach