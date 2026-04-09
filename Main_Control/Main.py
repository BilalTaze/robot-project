from Parser import parse_command
from Robot_control import RobotController


ROBOT_IP = "172.20.10.2"


def main():
    robot = RobotController(ROBOT_IP)

    try:
        while True:
            sentence = input("Enter command: ")

            if sentence.lower() in ["quit", "exit"]:
                break

            cmd = parse_command(sentence)
            print("Parsed command:", cmd)

            robot.execute_command(cmd)

    finally:
        robot.close()


if __name__ == "__main__":
    main()