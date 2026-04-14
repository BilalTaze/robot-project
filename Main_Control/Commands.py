# Dictionary mapping words to robot command parameters
COMMANDS = {

    # Type of command
    "action": {
        "move": "move",
        "go": "move",
        "rotate": "rotate",
        "turn": "rotate",
        "stop": "stop",
        "sequence": "sequence",
        "run": "run",
        "clear": "clear"
    },

    # Axis definitions (Cartesian axes)
    "axis": {
        "x": "x",
        "y": "y",
        "z": "z"
    },

    # Direction sign (positive or negative movement)
    "sign": {
        "plus": 1,
        "positive": 1,
        "+": 1,
        "minus": -1,
        "negative": -1,
        "-": -1
    },

    # Predefined translation distances (in meters)
    "distance": {
        "small": 0.02,
        "medium": 0.05,
        "far": 0.10
    },

    # Predefined rotation angles (in radians)
    "angle": {
        "small": 0.1,
        "medium": 0.3,
        "far": 0.6
    },

    # Reference frames
    "frame": {
        "base": "base",   # world reference frame
        "tool": "tool",   # end-effector frame
        "tcp": "tool"
    }
}