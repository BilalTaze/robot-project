import threading
from Parser import parse_command
from Robot_control import RobotController
from Sequence_manager import SequenceManager
from robot_voice_app import RobotVoiceApp
from AI_parser import parse_commands_with_AI

# Robot IP address
ROBOT_IP = "192.168.8.184"


def main():
    """
    Main entry point of the application.
    Handles:
    - user input
    - command parsing
    - sequence management
    - robot execution
    """
    print("Starting robot control application")
    # Initialize robot controller and sequence manager
    robot = RobotController(ROBOT_IP)
    sequence = SequenceManager()
    app = RobotVoiceApp()
    # Default reference frame (tool frame)
    current_frame = "tool"

    try:
        # Main interactive loop
        while True:
            # Read user input
            app.main()  # Get the recognized command from the voice app

            if app.text is None:
                continue

            print(f"Received input: {app.text}")
            # Exit condition
            if "exit" in app.text.lower() or "quit" in app.text.lower() or "close" in app.text.lower():
                break

            # -------- STOP (handled ONLY here) --------
            # Immediate stop command (interrupts current motion)
            if app.command == "stop":
                robot.stop_requested = True
                continue

            # Parse natural language command into structured dict
            try:
                cmd = parse_commands_with_AI(app.text)
            except Exception as e:
                cmd = parse_command(app.text)  # Fallback to rule-based parser if AI parsing fails

            # Invalid command handling
            if cmd is None:
                app.update_ui(activateButton=False, result="Invalid or incomplete command, please try again.")
                continue
            else:
                app.update_ui(activateButton=True, result=f"Parsed command: {cmd}")

            if not app.command_confirmed:
                continue

            # Extract action type
            action = cmd.get("action")

            # -------- FRAME MANAGEMENT --------
            # Set global reference frame (base or tool)
            if action == "set_frame":
                current_frame = cmd.get("frame")
                print("Parsed command:", cmd)
                print(f"Frame set to: {current_frame}")
                continue

            # -------- SEQUENCE MODE --------
            # Activate sequence recording mode
            if action == "sequence_mode":
                print("Parsed command:", cmd)
                sequence.start_sequence_mode()
                print("Sequence mode activated")
                continue

            # Clear stored sequence
            if action == "clear_sequence":
                print("Parsed command:", cmd)
                sequence.clear()
                print("Sequence cleared")
                continue

            # Display stored sequence
            if action == "show_sequence":
                commands = sequence.get_commands()
                if not commands:
                    print("Sequence is empty")
                else:
                    print("Current sequence:")
                    for i, c in enumerate(commands, 1):
                        print(f"{i}. {c}")
                continue

            # -------- RUN SEQUENCE --------
            # Execute stored sequence asynchronously
            if action == "run_sequence":
                print("Parsed command:", cmd)
                commands = sequence.get_commands()
                print(f"Running sequence with {len(commands)} commands")

                def worker():
                    """
                    Thread worker executing the sequence step by step.
                    Handles stop and interruption.
                    """
                    for c in commands:
                        # Stop requested before starting next command
                        if robot.stop_requested:
                            robot.stop_requested = False
                            print("Sequence interrupted")
                            break

                        # Execute command
                        completed = robot.execute_command(c)

                        # If command failed or was interrupted → stop sequence
                        if not completed:
                            print("Sequence interrupted")
                            break

                    # Exit sequence mode after execution
                    sequence.stop_sequence_mode()
                    print("Sequence finished")

                # Run sequence in separate thread (non-blocking)
                threading.Thread(target=worker, daemon=True).start()
                continue

            # -------- APPLY FRAME --------
            # Apply global frame if not specified in command
            if cmd.get("frame") is None:
                cmd["frame"] = current_frame

            # -------- EXECUTION --------
            if sequence.is_active():
                # Add command to sequence instead of executing
                sequence.add_command(cmd)
                print("Command added to sequence")
            else:
                print(f"Executing command {cmd} immediately")
                # Prevent concurrent motion
                if robot.is_moving:
                    print("Robot already moving")
                    continue

                # Execute command in separate thread (non-blocking)
                threading.Thread(
                    target=robot.execute_command,
                    args=(cmd,),
                    daemon=True
                ).start()
                app.reset()

            app.update_ui(activateButton=False, result="Command executed")
            


    finally:
        # Ensure robot is properly stopped when exiting program
        robot.close()


# Entry point
if __name__ == "__main__":
    main()