from Commands import COMMANDS
from Distance_parser import extract_distance, extract_angle
import re


def parse_command(sentence):

    words = sentence.lower().replace("-", " ").split()

    action = None
    axis = None
    sign = None
    frame = "tool"

    dist = extract_distance(sentence)
    angle = extract_angle(sentence)

    q_dist = None
    q_angle = None

    for w in words:
        if w in COMMANDS["action"]:
            action = COMMANDS["action"][w]

        if w in COMMANDS["axis"]:
            axis = w

        if w in COMMANDS["sign"]:
            sign = COMMANDS["sign"][w]

        if w in COMMANDS["frame"]:
            frame = COMMANDS["frame"][w]

        if w in COMMANDS["distance"]:
            q_dist = COMMANDS["distance"][w]

        if w in COMMANDS["angle"]:
            q_angle = COMMANDS["angle"][w]

    if re.search(r"\d+", sentence):
        return None

    if axis is None or sign is None or action is None:
        return None

    # -------- ROTATION --------
    if action == "rotate":

        if angle is not None and q_angle is not None:
            return None

        value = angle if angle is not None else q_angle

        if value is None:
            return None

        rot = [0, 0, 0]

        if axis == "x":
            rot = [sign * value, 0, 0]
        elif axis == "y":
            rot = [0, sign * value, 0]
        elif axis == "z":
            rot = [0, 0, sign * value]

        return {
            "action": "rotate",
            "rotation": rot,
            "frame": frame
        }

    # -------- TRANSLATION --------
    if action == "move":

        if dist is not None and q_dist is not None:
            return None

        value = dist if dist is not None else q_dist

        if value is None:
            return None

        direction = [0, 0, 0]

        if axis == "x":
            direction = [sign, 0, 0]
        elif axis == "y":
            direction = [0, sign, 0]
        elif axis == "z":
            direction = [0, 0, sign]

        return {
            "action": "move",
            "direction": direction,
            "distance": value,
            "frame": frame
        }

    return None