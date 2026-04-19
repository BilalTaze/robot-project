"""AI parser compatible with the existing robot project.

Goals:
- The LLM may correct misspelled / badly pronounced commands.
- The LLM must never complete missing mandatory information.
- Python validates the structure strictly and rejects incomplete commands.
- Output format matches the rest of the current project:
    * move       -> {"action": "move", "direction": [...], "distance": ..., "frame": ...}
    * rotate     -> {"action": "rotate", "rotation": [...], "frame": ...}
    * set_frame  -> {"action": "set_frame", "frame": ...}
    * sequence   -> {"action": "sequence_mode" | "show_sequence" | ...}
"""

import json
import math
from typing import Any

from mistralai.client import Mistral


MODEL_NAME = "mistral-medium-latest"
VALID_FRAMES = {"base", "tool"}
VALID_SEQUENCE_ACTIONS = {
    "sequence_mode",
    "show_sequence",
    "run_sequence",
    "clear_sequence",
}


# ---------------------------------------------------------------------------
# Basic helpers
# ---------------------------------------------------------------------------

def _load_api_key(filepath: str = "api_key.json") -> str:
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)

    api_key = data.get("api_key")
    if not api_key:
        raise ValueError("Missing 'api_key' in api_key.json")
    return api_key


def _extract_json_object(text: str) -> dict[str, Any]:
    if not text or not text.strip():
        raise ValueError("Empty response from model")

    text = text.strip()

    try:
        parsed = json.loads(text)
        if isinstance(parsed, dict):
            return parsed
    except json.JSONDecodeError:
        pass

    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError(f"Model response does not contain a JSON object: {text}")

    candidate = text[start : end + 1]
    try:
        parsed = json.loads(candidate)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON returned by model: {candidate}") from exc

    if not isinstance(parsed, dict):
        raise ValueError("Model output must be a JSON object")

    return parsed


def _require_string_field(data: dict[str, Any], key: str) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"Missing or invalid '{key}'")
    return value.strip()


def _normalize_frame(frame: Any, default_frame: str | None = None) -> str:
    if not isinstance(frame, str) or not frame.strip():
        if default_frame is None:
            raise ValueError("Missing frame")
        frame = default_frame

    frame = frame.strip().lower()
    if frame == "tcp":
        frame = "tool"

    if frame not in VALID_FRAMES:
        raise ValueError(f"Invalid frame: {frame}")
    return frame


def _normalize_axis(axis: Any) -> str:
    if not isinstance(axis, str):
        raise ValueError("Missing or invalid axis")
    axis = axis.strip().lower()
    if axis not in {"x", "y", "z"}:
        raise ValueError(f"Invalid axis: {axis}")
    return axis


def _normalize_sign(sign: Any) -> int:
    if not isinstance(sign, str):
        raise ValueError("Missing or invalid sign")
    sign = sign.strip().lower()
    if sign == "plus":
        return 1
    if sign == "minus":
        return -1
    raise ValueError(f"Invalid sign: {sign}")


def _normalize_non_negative_number(name: str, value: Any) -> float:
    if not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be numeric")
    value = float(value)
    if value < 0:
        raise ValueError(f"{name} must be >= 0")
    return value


def _axis_sign_to_direction(axis: str, sign: int) -> list[int]:
    if axis == "x":
        return [sign, 0, 0]
    if axis == "y":
        return [0, sign, 0]
    return [0, 0, sign]


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def validate_command(command: dict[str, Any], default_frame: str = "base") -> dict[str, Any]:
    if not isinstance(command, dict):
        raise ValueError("Command must be a dictionary")

    default_frame = _normalize_frame(default_frame)
    action = _require_string_field(command, "action").lower()

    if action == "invalid":
        reason = command.get("reason", "invalid_command")
        raise ValueError(f"Command rejected: {reason}")

    normalized_input = _require_string_field(command, "normalized_input")
    normalized: dict[str, Any] = {
        "action": action,
        "normalized_input": normalized_input,
    }

    if action == "move":
        axis = _normalize_axis(command.get("axis"))
        sign = _normalize_sign(command.get("sign"))
        distance = _normalize_non_negative_number("distance", command.get("distance"))
        frame = _normalize_frame(command.get("frame"), default_frame)

        normalized.update({
            "direction": _axis_sign_to_direction(axis, sign),
            "distance": distance,
            "frame": frame,
        })
        return normalized

    if action == "rotate":
        axis = _normalize_axis(command.get("axis"))
        sign = _normalize_sign(command.get("sign"))
        angle = _normalize_non_negative_number("angle", command.get("angle"))
        unit = _require_string_field(command, "unit").lower()
        frame = _normalize_frame(command.get("frame"), default_frame)

        if unit == "deg":
            angle = math.radians(angle)
        elif unit != "rad":
            raise ValueError("unit must be 'rad' or 'deg'")

        normalized.update({
            "rotation": [v * angle for v in _axis_sign_to_direction(axis, sign)],
            "frame": frame,
        })
        return normalized

    if action == "set_frame":
        normalized.update({
            "frame": _normalize_frame(command.get("frame"))
        })
        return normalized

    if action in VALID_SEQUENCE_ACTIONS:
        return normalized

    raise ValueError(f"Unsupported action: {action}")


# ---------------------------------------------------------------------------
# Prompt
# ---------------------------------------------------------------------------

def _build_prompt(sentence: str, default_frame: str) -> str:
    return f"""
Tu dois corriger et interpréter une phrase de commande robot.
Réponds uniquement avec un JSON valide. Aucun texte supplémentaire.

Comportement obligatoire :
- Tu peux corriger les fautes, les mots mal prononcés et les petites erreurs.
- Tu peux reformuler une commande mal dite vers une commande correcte.
- Tu ne dois jamais inventer une information absente.
- Si une information obligatoire manque, la commande est invalide.

Exemple de correction autorisée :
- "More x plus ten centim" -> "move x plus ten centimeters"

Exemples interdits :
- "move x" ne doit PAS devenir "move x plus small"
- "rotate z" ne doit PAS devenir "rotate z plus ten degrees"

Commandes supportées :
1. move [axis] [plus/minus] [distance]
2. rotate [axis] [plus/minus] [angle]
3. frame base | frame tool | frame tcp
4. sequence mode
5. show sequence
6. run sequence
7. clear sequence

Règles :
- axis doit être x, y ou z
- sign doit être plus ou minus
- si le frame n'est pas donné pour move ou rotate, utiliser "{default_frame}"
- tcp équivaut à tool
- small, medium, far sont des magnitudes valides
- une distance explicite en centimeters ou meters est valide
- un angle explicite en degrees ou radians est valide

Le JSON de sortie doit avoir l'un des formats suivants.

1. move :
{{
  "action": "move",
  "normalized_input": "move x plus ten centimeters",
  "axis": "x",
  "sign": "plus",
  "distance": 0.1,
  "frame": "base"
}}

2. rotate :
{{
  "action": "rotate",
  "normalized_input": "rotate z minus twenty degrees",
  "axis": "z",
  "sign": "minus",
  "angle": 20,
  "unit": "deg",
  "frame": "tool"
}}

3. set frame :
{{
  "action": "set_frame",
  "normalized_input": "frame tool",
  "frame": "tool"
}}

4. sequence :
{{"action": "sequence_mode", "normalized_input": "sequence mode"}}
{{"action": "show_sequence", "normalized_input": "show sequence"}}
{{"action": "run_sequence", "normalized_input": "run sequence"}}
{{"action": "clear_sequence", "normalized_input": "clear sequence"}}

5. invalid :
{{
  "action": "invalid",
  "normalized_input": "move x",
  "reason": "incomplete_move_command"
}}

Important :
- Si la commande est incomplète, retourne obligatoirement action="invalid".
- N'invente jamais axis, sign, distance, angle ou frame s'ils sont absents.
- Réponds avec un seul objet JSON.

Phrase à analyser :
{sentence}
""".strip()


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def parse_commands_with_AI(
    sentence: str,
    default_frame: str = "base",
    api_key_path: str = "api_key.json",
    model: str = MODEL_NAME,
) -> dict[str, Any]:
    if not isinstance(sentence, str) or not sentence.strip():
        raise ValueError("sentence must be a non-empty string")

    default_frame = _normalize_frame(default_frame)
    api_key = _load_api_key(api_key_path)
    client = Mistral(api_key=api_key)

    prompt = _build_prompt(sentence.strip(), default_frame)
    chat_response = client.chat.complete(
        model=model,
        messages=[{"role": "user", "content": prompt}],
    )

    response_text = chat_response.choices[0].message.content
    parsed = _extract_json_object(response_text)
    return validate_command(parsed, default_frame=default_frame)


if __name__ == "__main__":
    examples = [
        "move x plus small",
        "More x plus ten centim",
        "move x",
        "rotate z minus",
        "frame tool",
        "run sequence",
    ]

    for sentence in examples:
        try:
            result = parse_commands_with_AI(sentence)
            print(f"Input  : {sentence}")
            print(f"Output : {result}")
        except Exception as exc:
            print(f"Input  : {sentence}")
            print(f"Error  : {exc}")
        print("-" * 60)
