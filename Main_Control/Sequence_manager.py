class SequenceManager:
    """
    Manages a sequence of robot commands.

    This class allows:
    - activating sequence mode
    - storing commands
    - clearing commands
    - executing them later (handled externally)

    Used to create multi-step robot behaviors.
    """

    def __init__(self):
        # Indicates whether sequence mode is active
        self.sequence_mode = False

        # List of stored commands
        self.commands = []

    def start_sequence_mode(self):
        """
        Activate sequence mode and reset stored commands.
        """
        self.sequence_mode = True
        self.commands = []

    def stop_sequence_mode(self):
        """
        Deactivate sequence mode.
        """
        self.sequence_mode = False

    def add_command(self, cmd):
        """
        Add a command to the sequence.

        Only valid commands (not None) are stored.
        """
        if cmd is not None:
            self.commands.append(cmd)

    def clear(self):
        """
        Remove all stored commands from the sequence.
        """
        self.commands = []

    def get_commands(self):
        """
        Return a copy of the stored commands.

        Using a copy prevents accidental modification
        of the internal list.
        """
        return self.commands.copy()

    def is_active(self):
        """
        Check if sequence mode is currently active.
        """
        return self.sequence_mode