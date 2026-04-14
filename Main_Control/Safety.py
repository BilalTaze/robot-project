import math


class SafetyManager:
    def __init__(self):
        # Workspace limits (meters)
        self.x_min = -0.45
        self.x_max = 0.45

        self.y_min = -0.45
        self.y_max = -0.19

        self.z_min = 0.10
        self.z_max = 0.40

        # Max motion per command
        self.max_translation_step = 0.10           # 10 cm
        self.max_rotation_step = math.radians(30)  # 30 degrees

        # Reach safety
        # Distance from robot base to TCP must stay below this value.
        # Adjust experimentally for your URSim setup.
        self.max_reach = 0.55  # meters

    def is_pose_safe(self, target_pose):
        x, y, z = target_pose[0], target_pose[1], target_pose[2]

        if not (self.x_min <= x <= self.x_max):
            return False
        if not (self.y_min <= y <= self.y_max):
            return False
        if not (self.z_min <= z <= self.z_max):
            return False

        return True

    def is_translation_step_safe(self, distance):
        return abs(distance) <= self.max_translation_step

    def is_rotation_step_safe(self, rotation):
        if rotation is None or len(rotation) != 3:
            return False
        return all(abs(r) <= self.max_rotation_step for r in rotation)

    def is_joint_configuration_safe(self, joints):
        """
        Simple heuristics to avoid risky configurations.
        This is not a full singularity detector.
        joints = [q1, q2, q3, q4, q5, q6] in radians
        """
        if joints is None or len(joints) != 6:
            return False

        shoulder = joints[1]
        elbow = joints[2]
        wrist2 = joints[4]

        # Heuristic 1: wrist2 near 0 can be risky
        if abs(wrist2) < math.radians(5):
            return False

        # Heuristic 2: arm too aligned / stretched
        if abs(shoulder) < math.radians(5) and abs(elbow) < math.radians(5):
            return False

        return True

    def compute_reach(self, pose):
        """
        Compute TCP distance from robot base origin.
        pose = [x, y, z, rx, ry, rz]
        """
        x, y, z = pose[0], pose[1], pose[2]
        return math.sqrt(x * x + y * y + z * z)

    def is_reach_safe(self, pose):
        """
        Returns True if TCP is not too far from the base.
        """
        return self.compute_reach(pose) <= self.max_reach