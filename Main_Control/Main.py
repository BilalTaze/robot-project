from Parser import parse_command
from Robot_control import RobotController
from Sequence_manager import SequenceManager

ROBOT_IP = "10.220.8.217"


def main():
    robot = RobotController(ROBOT_IP)
    sequence = SequenceManager()

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

            if sequence.is_active():
                sequence.add_command(cmd)
                print("Command added to sequence")
            else:
                robot.execute_command(cmd)

    finally:
        robot.close()


if __name__ == "__main__":
    main()