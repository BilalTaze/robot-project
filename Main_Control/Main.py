from Parser import parse_command
from Robot_control import RobotController
from Sequence_manager import SequenceManager

ROBOT_IP = "10.220.8.217"


def main():
    robot = RobotController(ROBOT_IP)
    sequence = SequenceManager()

    current_frame = "tool"  # mode par défaut

    try:
        while True:
            sentence = input("Enter command: ")

            if sentence.lower() in ["quit", "exit"]:
                break

            cmd = parse_command(sentence)
            print("Parsed command:", cmd)

            if cmd is None:
                continue

            action = cmd.get("action")

            # -------- FRAME MODE --------
            if action == "set_frame":
                current_frame = cmd.get("frame")
                print(f"Frame set to: {current_frame}")
                continue

            # -------- SEQUENCE --------
            if action == "sequence_mode":
                sequence.start_sequence_mode()
                print("Sequence mode activated")
                continue

            if action == "clear_sequence":
                sequence.clear()
                print("Sequence cleared")
                continue

            if action == "run_sequence":
                commands = sequence.get_commands()
                print(f"Running sequence with {len(commands)} commands")

                for seq_cmd in commands:
                    robot.execute_command(seq_cmd)

                sequence.stop_sequence_mode()
                print("Sequence finished")
                continue

            # -------- APPLY GLOBAL FRAME --------
            if cmd.get("frame") is None:
                cmd["frame"] = current_frame

            # -------- EXECUTION --------
            if sequence.is_active():
                sequence.add_command(cmd)
                print("Command added to sequence")
            else:
                robot.execute_command(cmd)

    finally:
        robot.close()


if __name__ == "__main__":
    main()