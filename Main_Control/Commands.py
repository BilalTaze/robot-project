COMMANDS = {
    "action": {
        "move": "move",
        "go": "move",
        "stop": "stop"
    },

    "direction": {
        "forward":  [1, 0, 0],
        "backward": [-1, 0, 0],
        "left":     [0, 1, 0],
        "right":    [0, -1, 0],
        "up":       [0, 0, 1],
        "down":     [0, 0, -1]
    },

    "distance": {
        "little": 0.02,
        "small": 0.02,
        "more": 0.05,
        "medium": 0.05,
        "far": 0.1,
        "big": 0.1
    },

    "frame": {
        "base": "base",
        "robot": "base",
        "tool": "tool",
        "tcp": "tool"
    }
}