from Parser import parse_command
from Robot_control import RobotController
from Sequence_manager import SequenceManager

# Robot IP address
ROBOT_IP = "10.220.8.217"


def main():
    # Initialize robot controller and sequence manager
    robot = RobotController(ROBOT_IP)
    sequence = SequenceManager()

    # Default reference frame (tool or base)
    current_frame = "tool"

    try:
        while True:
            # Get user input command
            sentence = input("Enter command: ")

            # Exit condition
            if sentence.lower() in ["quit", "exit"]:
                break

            # Parse the input sentence into a structured command
            cmd = parse_command(sentence)

            # Ignore invalid commands
            cmd = parse_command(sentence)

            if cmd is None:
                print("Unrecognized or incomplete command")
                continue

            action = cmd.get("action")

            # -------- FRAME MODE --------
            # Change the global reference frame (base or tool)
            if action == "set_frame":
                current_frame = cmd.get("frame")
                print("Parsed command:", cmd)
                print(f"Frame set to: {current_frame}")
                continue

            # -------- SEQUENCE MODE --------
            # Start recording a sequence of commands
            if action == "sequence_mode":
                print("Parsed command:", cmd)
                sequence.start_sequence_mode()
                print("Sequence mode activated")
                continue

            # Clear all stored commands in the sequence
            if action == "clear_sequence":
                print("Parsed command:", cmd)
                sequence.clear()
                print("Sequence cleared")
                continue

            # Execute all stored commands sequentially
            if action == "run_sequence":
                print("Parsed command:", cmd)
                commands = sequence.get_commands()
                print(f"Running sequence with {len(commands)} commands")

                for seq_cmd in commands:
                    robot.execute_command(seq_cmd)

                sequence.stop_sequence_mode()
                print("Sequence finished")
                continue
            
            if action == "show_sequence":
                commands = sequence.get_commands()
                if not commands:
                    print("Sequence is empty")
                else:
                    print("Current sequence:")
                for i, cmd in enumerate(commands, 1):
                    print(f"{i}. {cmd}")
                continue

            # -------- APPLY GLOBAL FRAME --------
            # If no frame is specified in the command, use the current global frame
            if cmd.get("frame") is None:
                cmd["frame"] = current_frame

            # Debug: show the final interpreted command
            print("Parsed command:", cmd)

            # -------- EXECUTION --------
            # If sequence mode is active → store command
            # Otherwise → execute immediately
            if sequence.is_active():
                sequence.add_command(cmd)
                print("Command added to sequence")
            else:
                robot.execute_command(cmd)

    finally:
        # Ensure robot script is properly stopped on exit
        robot.close()


if __name__ == "__main__":
    main()