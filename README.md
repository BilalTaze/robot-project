# robot-project

The project aims to develop a voice-controlled system for operating a UR3 robot.
It is divide in two main parts:
- Voice app
- Robot control

Linked by the file Main.py and the two comand's parser. 

The voice recognition is manage by the Python's class "RobotVoiceApp" in the file robot_voice_app.py the robot control is manage by the class "RobotController" in Robot_control.py.

### How to use this application

To launch this small tkinter app, you need to be connected to the robot and can access to its ip address. In the file Main.py you need to replace "0.0.0.0" by your robot's ip address. You also need to have a Mistral AI api key in a json file named "api_key.json" (follow this link to create your api key: https://admin.mistral.ai/organization/api-keys, you will need to create an account (free)).

Then, you can create en python virtual environment and install the requirements (see requirements.txt)

To launch the project, execute Main.py

A "Tkinter" window will apeare with a button "record", and the instruction to move the robots.

The following section present the supported commands

### Supported Commands

The robot can be controlled using voice commands. Here is the list of supported commands:

#### Movement Commands
- **move [axis] [plus/minus] [distance]**: Move the robot along a specific axis.
  - axis: x, y, or z
  - sign: plus or minus
  - distance: small, medium, far, or a specific value in centimeters/meters (e.g., "ten centimeters")
  - Example: "move x plus ten centimeters"

- **rotate [axis] [plus/minus] [angle]**: Rotate the robot around a specific axis.
  - axis: x, y, or z
  - sign: plus or minus
  - angle: a specific value in degrees or radians (e.g., "twenty degrees")
  - Example: "rotate z minus twenty degrees"

#### Frame Commands
- **frame base**: Set the reference frame to the robot's base.
- **frame tool**: Set the reference frame to the tool (TCP).
- **frame tcp**: Same as "frame tool".

#### Sequence Commands
- **sequence mode**: Enter sequence mode to record a series of commands.
- **show sequence**: Display the current sequence of commands.
- **run sequence**: Execute the recorded sequence.
- **clear sequence**: Clear the recorded sequence.

#### To close the app
- **exit**: Exit the application.