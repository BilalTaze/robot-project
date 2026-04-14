class SequenceManager:
    def __init__(self):
        self.sequence_mode = False
        self.commands = []

    def start_sequence_mode(self):
        self.sequence_mode = True
        self.commands = []

    def stop_sequence_mode(self):
        self.sequence_mode = False

    def add_command(self, cmd):
        if cmd is not None:
            self.commands.append(cmd)

    def clear(self):
        self.commands = []

    def get_commands(self):
        return self.commands.copy()

    def is_active(self):
        return self.sequence_mode