import re
from Commands import COMMANDS
from Distance_parser import extract_distance, extract_angle


def parse_command(sentence):
    """
    Convert a natural language sentence into a structured robot command.

    Example:
        "move x plus ten centimeters"
        → {'action': 'move', 'direction': [1,0,0], 'distance': 0.1, 'frame': 'base/tool'}
    """

    # Normalize input sentence (lowercase + remove hyphens)
    s = sentence.lower().replace("-", " ").replace(".","").strip()
    words = s.split()

    # -------- FRAME MODE --------
    # Set global reference frame
    if s == "frame base":
        return {"action": "set_frame", "frame": "base"}

    if s == "frame tool":
        return {"action": "set_frame", "frame": "tool"}

    # -------- SEQUENCE COMMANDS --------
    # Start recording a sequence of commands
    if s == "sequence mode":
        return {"action": "sequence_mode"}

    # Execute stored sequence
    if s == "run sequence":
        return {"action": "run_sequence"}

    # Clear stored sequence
    if s == "clear sequence":
        return {"action": "clear_sequence"}
    
    # -------- SHOW SEQUENCE --------
    if s == "show sequence":
        return {"action": "show_sequence"}

    # -------- INITIAL VARIABLES --------
    action = None
    axis = None
    sign = None
    frame = None

    qualitative_distance = None
    qualitative_angle = None

    # Extract numeric values from sentence (if present)
    numeric_distance = extract_distance(sentence)
    numeric_angle = extract_angle(sentence)

    # Detect forbidden case: digits present (only text allowed)
    has_digit = bool(re.search(r"\d+", sentence))

    # -------- KEYWORD EXTRACTION --------
    # Loop through each word and match with command dictionary
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

    # Reject command if digits are used
    if has_digit:
        return None

    # Missing essential components → invalid command
    if axis is None or sign is None or action is None:
        return None

    # -------- ROTATION --------
    if action == "rotate":

        # Prevent mixing numeric and qualitative values
        if numeric_angle is not None and qualitative_angle is not None:
            return None

        # Choose value (numeric or qualitative)
        value = numeric_angle if numeric_angle is not None else qualitative_angle
        if value is None:
            return None

        # Initialize rotation vector [Rx, Ry, Rz]
        rotation = [0, 0, 0]

        # Assign rotation to correct axis
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

        # Prevent mixing numeric and qualitative values
        if numeric_distance is not None and qualitative_distance is not None:
            return None

        # Choose value (numeric or qualitative)
        value = numeric_distance if numeric_distance is not None else qualitative_distance
        if value is None:
            return None

        # Initialize direction vector [dx, dy, dz]
        direction = [0, 0, 0]

        # Assign direction based on axis
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

    # If no valid command found
    return None