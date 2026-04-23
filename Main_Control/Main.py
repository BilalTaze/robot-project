import threading
import time
from Parser import parse_command
from Robot_control import RobotController
from Sequence_manager import SequenceManager
from robot_voice_app import RobotVoiceApp
from AI_parser import parse_commands_with_AI

# Robot IP address
ROBOT_IP = "192.168.8.200"


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
    # Security stop loop
        def stop_loop():
            while True:
                if robot.stop_requested:
                    robot._stop_motion()
                    app.reset()
                    robot.stop_requested = False
        threading.Thread(target=stop_loop)

    # Main interactive loop
        while True:
        # Launch the Tkinter main loop to wait for user input and confirmation
            app.root.mainloop()

            # if app.stop_robot:
            #     print("in stop condition")
            #     robot._stop_motion()
            #     robot.stop_requested = True
            #     app.stop_robot = False
            #     app.reset()
            #     app.display_information(information="Stop command sent to robot.")
            #     continue

        # while waiting for input, continue the loop without doing anything
            if app.text is None:continue

            app.display_information(information=f"Received input: {app.text}", delete_previous=True)

        # End program if user says "exit"
            if "exit" in app.text.lower(): break

        # Parse natural language command into structured dict
            try:
            # First try standard parsing
                cmd = parse_command(app.text)
            # If standard parsing fails, try AI parsing
                if cmd is None: cmd = parse_commands_with_AI(app.text, default_frame=current_frame)

            except Exception as e:
            # Invalid command handling
                app.display_information(information = "Invalid or incomplete command, please try again.")
                app.reset()
                continue
            else:
                app.enable_record_button()

        # Display parsed command for confirmation
            info = cmd.get("normalized_input", cmd)
            app.display_information(information = f"Parsed command: {info}")

        # Command gestion after confirmation
            # Extract action type
            action = cmd.get("action")

            # -------- FRAME MANAGEMENT --------
            # Set global reference frame (base or tool)
            if action == "set_frame":
                current_frame = cmd.get("frame")
                robot.execution_status += f"Reference frame set to {current_frame}"

            # -------- SEQUENCE MODE --------
            # Activate sequence recording mode
            elif action == "sequence_mode":
                sequence.start_sequence_mode()
                robot.execution_status += "Sequence mode activated. Next commands will be added to the sequence until you say 'run sequence'."

            # Clear stored sequence
            elif action == "clear_sequence":
                sequence.clear()
                robot.execution_status += "Sequence cleared."

            # Display stored sequence
            elif action == "show_sequence":
                commands = sequence.get_commands()
                if not commands: robot.execution_status += "Current sequence is empty."
                else:
                    robot.execution_status += "Current sequence:\n"
                    for i, c in enumerate(commands, 1):
                        robot.execution_status += f"{i}. {c.get('normalized_input', c)}\n"

            # -------- RUN SEQUENCE --------
            # Execute stored sequence asynchronously
            elif action == "run_sequence":
                print("Running sequence")
                commands = sequence.get_commands()
                robot.execution_status += f"Running sequence with {len(commands)} commands"

                def worker():
                    """
                    Thread worker executing the sequence step by step.
                    Handles stop and interruption.
                    """
                    for c in commands:
                        # Stop requested before starting next command
                        robot.execution_status += f"Executing command: {c}"
                        print(f'stop requested: {robot.stop_requested}')

                        # Execute command
                        if not robot.stop_requested: completed = robot.execute_command(c)
                        else:
                            app.reset()
                            robot.stop_requested = False
                            robot.execution_status += "Sequence execution stopped by user."

                        # If command failed or was interrupted → stop sequence
                        if not completed:
                            robot.execution_status += "Sequence interrupted during execution."
                            break

                    # Exit sequence mode after execution
                    sequence.stop_sequence_mode()
                    # sequence.clear()
                    robot.execution_status += "Sequence execution finished."

                # Run sequence in separate thread (non-blocking)
                threading.Thread(target=worker, daemon=True).start()

            # -------- APPLY FRAME --------
            # Apply global frame if not specified in command
            elif cmd.get("frame") is None: cmd["frame"] = current_frame

            # -------- EXECUTION --------
            elif sequence.is_active():
                # Add command to sequence instead of executing
                sequence.add_command(cmd)
                robot.execution_status += "Command added to sequence."
            else:
                app.display_information(information=f"Executing command immediately")
                # Prevent concurrent motion
                if robot.is_moving: robot.execution_status += "Robot already moving."
                elif robot.stop_requested: robot.execution_status += "Stop requested, cannot execute new command."
                else:
                # Execute command in separate thread (non-blocking)
                    threading.Thread(
                        target=robot.execute_command,
                        args=(cmd,),
                        daemon=True
                    ).start()
                    robot.execution_status += "Command executed"
            
        # After execution, reset app state for next command
            app.reset()
        # And display that command was executed (for user feedback)
            app.display_information(information = robot.execution_status)
            robot.execution_status = ""

    finally:
        # Ensure robot is properly stopped when exiting program
        robot.close()


# Entry point
if __name__ == "__main__":
    main()