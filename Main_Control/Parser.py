import re
from Commands import COMMANDS
from Distance_parser import extract_distance, extract_angle


def parse_command(sentence):
    s = sentence.lower().replace("-", " ").strip()
    words = s.split()

    # -------- FRAME MODE --------
    if s == "frame base":
        return {"action": "set_frame", "frame": "base"}

    if s == "frame tool":
        return {"action": "set_frame", "frame": "tool"}

    # -------- SEQUENCE COMMANDS --------
    if s == "sequence mode":
        return {"action": "sequence_mode"}

    if s == "run sequence":
        return {"action": "run_sequence"}

    if s == "clear sequence":
        return {"action": "clear_sequence"}

    action = None
    axis = None
    sign = None
    frame = None  # ⚠️ IMPORTANT : plus de valeur par défaut

    qualitative_distance = None
    qualitative_angle = None

    numeric_distance = extract_distance(sentence)
    numeric_angle = extract_angle(sentence)

    has_digit = bool(re.search(r"\d+", sentence))

    for word in words:
        if word in COMMANDS["action"]:
            action = COMMANDS["action"][word]

        if word in COMMANDS["axis"]:
            axis = word

        if word in COMMANDS["sign"]:
            sign = COMMANDS["sign"][word]

        if word in COMMANDS["frame"]:
            frame = COMMANDS["frame"][word]

        if word in COMMANDS["distance"]:
            qualitative_distance = COMMANDS["distance"][word]

        if word in COMMANDS["angle"]:
            qualitative_angle = COMMANDS["angle"][word]

    if has_digit:
        return None

    if axis is None or sign is None or action is None:
        return None

    # -------- ROTATION --------
    if action == "rotate":
        if numeric_angle is not None and qualitative_angle is not None:
            return None

        value = numeric_angle if numeric_angle is not None else qualitative_angle
        if value is None:
            return None

        rotation = [0, 0, 0]

        if axis == "x":
            rotation = [sign * value, 0, 0]
        elif axis == "y":
            rotation = [0, sign * value, 0]
        elif axis == "z":
            rotation = [0, 0, sign * value]

        return {
            "action": "rotate",
            "rotation": rotation,
            "frame": frame
        }

    # -------- TRANSLATION --------
    if action == "move":
        if numeric_distance is not None and qualitative_distance is not None:
            return None

        value = numeric_distance if numeric_distance is not None else qualitative_distance
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