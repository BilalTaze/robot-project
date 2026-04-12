import re
from Commands import COMMANDS
from Distance_parser import extract_distance


def parse_command(sentence: str) -> dict | None:
    words = sentence.lower().replace("-", " ").split()

    action = None
    axis = None
    sign = None
    frame = "tool"

    qualitative_distance = None
    numeric_distance = extract_distance(sentence)

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

    if has_digit:
        return None

    if numeric_distance is not None and qualitative_distance is not None:
        return None

    if numeric_distance is not None:
        distance = numeric_distance
    elif qualitative_distance is not None:
        distance = qualitative_distance
    else:
        return None

    if not axis or sign is None:
        return None

    if axis == "x":
        direction = [sign, 0, 0]
    elif axis == "y":
        direction = [0, sign, 0]
    elif axis == "z":
        direction = [0, 0, sign]
    else:
        return None

    if action is None:
        return None

    return {
        "action": action,
        "direction": direction,
        "distance": distance,
        "frame": frame
    }