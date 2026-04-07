from Commands import COMMANDS


def parse_command(sentence: str) -> dict:
    words = sentence.lower().split()

    action = None
    direction = None
    distance = None
    frame = "tool"

    for word in words:
        if word in COMMANDS["action"]:
            action = COMMANDS["action"][word]

        if word in COMMANDS["direction"]:
            direction = COMMANDS["direction"][word]

        if word in COMMANDS["distance"]:
            distance = COMMANDS["distance"][word]

        if word in COMMANDS["frame"]:
            frame = COMMANDS["frame"][word]

    return {
        "action": action,
        "direction": direction,
        "distance": distance,
        "frame": frame
    }