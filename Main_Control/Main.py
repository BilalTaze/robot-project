from Parser import parse_command
from Robot_control import RobotController

ROBOT_IP = "10.220.8.217"


def main():
    robot = RobotController(ROBOT_IP)

    try:
        while True:
            sentence = input("Enter command: ")

            if sentence.lower() in ["quit", "exit"]:
                break

            cmd = parse_command(sentence)
            print("Parsed command:", cmd)

            if cmd is None:
                continue

            robot.execute_command(cmd)

    finally:
        robot.close()


if __name__ == "__main__":
    main()