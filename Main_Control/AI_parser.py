"""
Module for recognize commads with AI
"""

import json
from mistralai.client import Mistral

def parse_commands(sentence):
    with open("api_key.json", "r") as f:
        api_key_data = json.load(f)

    api_key = api_key_data["api_key"]
    model = "mistral-medium-latest"

    client = Mistral(api_key=api_key)

    question = """
        voici le dictionnaire des commandes que le robot peut comprendre, et les mots associés à chaque paramètre de commande.
        COMMANDS = {

            Type of command
            "action": {
                "move": "move",
                "go": "move",
                "rotate": "rotate",
                "turn": "rotate",
                "sequence": "sequence",
                "run": "run",
                "clear": "clear"
            },

            Axis definitions (Cartesian axes)
            "axis": {
                "x": "x",
                "y": "y",
                "z": "z"
            },

            Direction sign (positive or negative movement)
            "sign": {
                "plus": 1,
                "positive": 1,
                "+": 1,
                "minus": -1,
                "negative": -1,
                "-": -1
            },

            Predefined translation distances (in meters)
            "distance": {
                "small": 0.02,
                "medium": 0.05,
                "far": 0.10
            },

            Predefined rotation angles (in radians)
            "angle": {
                "small": 0.1,
                "medium": 0.3,
                "far": 0.6
            },

            Reference frames
            "frame": {
                "base": "base",    world reference frame
                "tool": "tool",    end-effector frame
                "tcp": "tool"
            }
        }

        En utilisant ce dictionnaire, je veux en sorti le dictionnaire suivant : {'action': 'move', 'direction': [1,0,0], 'distance': 0.1, 'frame': 'base/tool'}
        Par défault, le frame doit être 'tool' si aucune indication n'est donnée.
        Répondre uniquement avec le dictionnaire de sortie, sans explication ni texte supplémentaire.
        Voici la phrase à analyser : 
        """
    question += sentence
    chat_response = client.chat.complete(
        model= model,
        messages = [
            {
                "role": "user",
                "content": question,
            },
        ]
    )
    response =  chat_response.choices[0].message.content
    json_response = json.loads(response.replace("'",'"'))
    return json_response


if __name__ == "__main__":
    sentence = "Unix plus small"
    result = parse_commands(sentence)
    print(type(result))
    print(result)