from Parser import parse_command
from Robot_control import RobotController
from Sequence_manager import SequenceManager
import threading

ROBOT_IP = "192.168.1.109"


def main():
    robot = RobotController(ROBOT_IP)
    sequence = SequenceManager()

    current_frame = "tool"

    try:
        while True:
            sentence = input("Enter command: ").strip().lower()

            if sentence in ["quit", "exit"]:
                break

            # -------- STOP (handled ONLY here) --------
            if sentence == "stop":
                robot.stop_requested = True
                continue

            cmd = parse_command(sentence)

            if cmd is None:
                print("Invalid or incomplete command")
                continue

            action = cmd.get("action")

            # -------- FRAME --------
            if action == "set_frame":
                current_frame = cmd.get("frame")
                print("Parsed command:", cmd)
                print(f"Frame set to: {current_frame}")
                continue

            # -------- SEQUENCE --------
            if action == "sequence_mode":
                print("Parsed command:", cmd)
                sequence.start_sequence_mode()
                print("Sequence mode activated")
                continue

            if action == "clear_sequence":
                print("Parsed command:", cmd)
                sequence.clear()
                print("Sequence cleared")
                continue

            if action == "show_sequence":
                commands = sequence.get_commands()
                if not commands:
                    print("Sequence is empty")
                else:
                    print("Current sequence:")
                    for i, c in enumerate(commands, 1):
                        print(f"{i}. {c}")
                continue

            if action == "run_sequence":
                print("Parsed command:", cmd)
                commands = sequence.get_commands()
                print(f"Running sequence with {len(commands)} commands")

                def worker():
                    for c in commands:
                        # Stop before next command starts
                        if robot.stop_requested:
                            robot.stop_requested = False
                            print("Sequence interrupted")
                            break

                        completed = robot.execute_command(c)

                        # Stop or interruption during current command
                        if not completed:
                            print("Sequence interrupted")
                            break

                    sequence.stop_sequence_mode()
                    print("Sequence finished")

                threading.Thread(target=worker, daemon=True).start()
                continue

            # -------- APPLY FRAME --------
            if cmd.get("frame") is None:
                cmd["frame"] = current_frame

            print("Parsed command:", cmd)

            # -------- EXECUTE --------
            if sequence.is_active():
                sequence.add_command(cmd)
                print("Command added to sequence")
            else:
                if robot.is_moving:
                    print("Robot already moving")
                    continue

                threading.Thread(
                    target=robot.execute_command,
                    args=(cmd,),
                    daemon=True
                ).start()

    finally:
        robot.close()


if __name__ == "__main__":
    main()