import socket

HOST = "10.49.212.217"  # URSim IP
PORT = 30001             # Interface port

# Socket creation
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Robot connection
s.connect((HOST, PORT))

# URScript command to display a popup on the robot's teach pendant
command = 'popup("Connection test", title="Popup", blocking=True)\n'

# Send the command to the robot
s.send(command.encode('utf-8'))

# Close the socket connection
s.close()

print("Commande envoyée.")