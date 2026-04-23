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

# Constants
MODEL_NAME = "mistral-medium-latest"  # Default AI model for parsing commands
VALID_FRAMES = {"base", "tool"}  # Supported reference frames for robot movements
VALID_SEQUENCE_ACTIONS = {  # Supported sequence-related actions
    "sequence_mode",
    "show_sequence",
    "run_sequence",
    "clear_sequence",
}


# ---------------------------------------------------------------------------
# Basic helpers
# ---------------------------------------------------------------------------

def _load_api_key(filepath: str = "api_key.json") -> str:
    """Load the API key from a JSON file.

    Args:
        filepath: Path to the JSON file containing the API key.

    Returns:
        The API key string.

    Raises:
        ValueError: If the API key is missing from the file.
    """
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)

    api_key = data.get("api_key")
    if not api_key:
        raise ValueError("Missing 'api_key' in api_key.json")
    return api_key


def _extract_json_object(text: str) -> dict[str, Any]:
    """Extract a JSON object from the AI model's response text.

    Attempts to parse the entire text as JSON first, then tries to extract
    the JSON object from within the text if direct parsing fails.

    Args:
        text: The raw response text from the AI model.

    Returns:
        The parsed JSON object as a dictionary.

    Raises:
        ValueError: If no valid JSON object can be found or parsed.
    """
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
    """Extract and validate a required string field from a dictionary.

    Args:
        data: The dictionary to extract from.
        key: The key of the required field.

    Returns:
        The stripped string value.

    Raises:
        ValueError: If the field is missing or not a valid string.
    """
    value = data.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"Missing or invalid '{key}'")
    return value.strip()


def _normalize_frame(frame: Any, default_frame: str | None = None) -> str:
    """Normalize and validate a frame value.

    Converts 'tcp' to 'tool' and ensures the frame is in VALID_FRAMES.

    Args:
        frame: The frame value to normalize.
        default_frame: Default frame to use if frame is None or empty.

    Returns:
        The normalized frame string.

    Raises:
        ValueError: If frame is invalid and no default is provided.
    """
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
    """Normalize and validate an axis value.

    Args:
        axis: The axis value ('x', 'y', or 'z').

    Returns:
        The normalized axis string in lowercase.

    Raises:
        ValueError: If axis is not 'x', 'y', or 'z'.
    """
    if not isinstance(axis, str):
        raise ValueError("Missing or invalid axis")
    axis = axis.strip().lower()
    if axis not in {"x", "y", "z"}:
        raise ValueError(f"Invalid axis: {axis}")
    return axis


def _normalize_sign(sign: Any) -> int:
    """Normalize a sign string to an integer.

    Args:
        sign: The sign string ('plus' or 'minus').

    Returns:
        1 for 'plus', -1 for 'minus'.

    Raises:
        ValueError: If sign is not 'plus' or 'minus'.
    """
    if not isinstance(sign, str):
        raise ValueError("Missing or invalid sign")
    sign = sign.strip().lower()
    if sign == "plus":
        return 1
    if sign == "minus":
        return -1
    raise ValueError(f"Invalid sign: {sign}")


def _normalize_non_negative_number(name: str, value: Any) -> float:
    """Validate and convert a value to a non-negative float.

    Args:
        name: Name of the value for error messages.
        value: The numeric value to validate.

    Returns:
        The value as a float.

    Raises:
        ValueError: If value is not numeric or negative.
    """
    if not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be numeric")
    value = float(value)
    if value < 0:
        raise ValueError(f"{name} must be >= 0")
    return value


def _axis_sign_to_direction(axis: str, sign: int) -> list[int]:
    """Convert axis and sign to a direction vector.

    Args:
        axis: The axis ('x', 'y', or 'z').
        sign: The sign (1 or -1).

    Returns:
        A 3-element list representing the direction vector.
    """
    if axis == "x":
        return [sign, 0, 0]
    if axis == "y":
        return [0, sign, 0]
    return [0, 0, sign]


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def validate_command(command: dict[str, Any], default_frame: str = "base") -> dict[str, Any]:
    """Validate and normalize a parsed command from the AI model.

    Converts the AI's output into the standardized format used by the robot project.

    Args:
        command: The command dictionary from the AI.
        default_frame: Default frame to use if not specified.

    Returns:
        The validated and normalized command dictionary.

    Raises:
        ValueError: If the command is invalid or incomplete.
    """
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
    """Build the prompt for the AI model to parse a command sentence.

    Args:
        sentence: The input sentence to parse.
        default_frame: The default frame to use in instructions.

    Returns:
        The complete prompt string for the AI model.
    """
    return f"""
You must correct and interpret a robot command sentence.
Respond only with valid JSON. No additional text.

Mandatory behavior:
- You can correct spelling mistakes, mispronounced words, and small errors.
- You can rephrase a poorly worded command into a correct one.
- You must never invent missing information.
- If mandatory information is missing, the command is invalid.

Example of allowed correction:
- "More x plus ten centim" -> "move x plus ten centimeters"

Forbidden examples:
- "move x" must NOT become "move x plus small"
- "rotate z" must NOT become "rotate z plus ten degrees"

Supported commands:
1. move [axis] [plus/minus] [distance]
2. rotate [axis] [plus/minus] [angle]
3. frame base | frame tool | frame tcp
4. sequence mode
5. show sequence
6. run sequence
7. clear sequence

Rules:
- axis must be x, y or z
- sign must be plus or minus
- if frame is not given for move or rotate, use "{default_frame}"
- tcp is equivalent to tool
- small, medium, far are valid magnitudes
- an explicit distance in centimeters or meters is valid
- an explicit angle in degrees or radians is valid

The output JSON must have one of the following formats.

1. move:
{{
  "action": "move",
  "normalized_input": "move x plus ten centimeters",
  "axis": "x",
  "sign": "plus",
  "distance": 0.1,
  "frame": "base"
}}

2. rotate:
{{
  "action": "rotate",
  "normalized_input": "rotate z minus twenty degrees",
  "axis": "z",
  "sign": "minus",
  "angle": 20,
  "unit": "deg",
  "frame": "tool"
}}

3. set frame:
{{
  "action": "set_frame",
  "normalized_input": "frame tool",
  "frame": "tool"
}}

4. sequence:
{{"action": "sequence_mode", "normalized_input": "sequence mode"}}
{{"action": "show_sequence", "normalized_input": "show sequence"}}
{{"action": "run_sequence", "normalized_input": "run sequence"}}
{{"action": "clear_sequence", "normalized_input": "clear sequence"}}

5. invalid:
{{
  "action": "invalid",
  "normalized_input": "move x",
  "reason": "incomplete_move_command"
}}

Important:
- If the command is incomplete, you must return action="invalid".
- Never invent axis, sign, distance, angle or frame if they are absent.
- Respond with a single JSON object.

Sentence to analyze:
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
    """Parse a robot command sentence using AI and validate the result.

    This is the main public function for parsing commands.

    Args:
        sentence: The command sentence to parse.
        default_frame: Default reference frame for movements.
        api_key_path: Path to the API key file.
        model: The AI model to use.

    Returns:
        The validated command dictionary.

    Raises:
        ValueError: If the sentence is invalid or parsing fails.
    """
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
    # Test examples when running the script directly
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
