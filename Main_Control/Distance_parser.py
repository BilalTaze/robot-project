import re
import math
from text_to_num import text2num


# -------- UNIT DEFINITIONS --------

# Conversion factors for angle units (degrees → radians)
ANGLE_UNITS = {
    "degree": math.pi / 180,
    "degrees": math.pi / 180
}

# Conversion factors for distance units (centimeters → meters)
DISTANCE_UNITS = {
    "cm": 0.01,
    "centimeter": 0.01,
    "centimeters": 0.01
}

# Supported number words for parsing spoken values
NUMBER_WORDS = {
    "one","two","three","four","five","six","seven","eight","nine",
    "ten","eleven","twelve","thirteen","fourteen","fifteen",
    "sixteen","seventeen","eighteen","nineteen",
    "twenty","thirty","forty","fifty"
}


# -------- GENERIC VALUE EXTRACTION --------

def extract_value(sentence, units):
    """
    Extract a numeric value from a sentence based on a given unit dictionary.

    Example:
        "move ten centimeters" → 0.10
        "rotate twenty degrees" → 0.35 (rad)

    Steps:
    1. Normalize text (lowercase, remove '-')
    2. Detect unit (cm, degree, etc.)
    3. Extract number words before the unit
    4. Convert text → number using text2num
    5. Apply unit conversion
    """

    # Normalize sentence
    s = sentence.lower().replace("-", " ")
    words = s.split()

    # Reject if digits are present (only text allowed)
    if re.search(r"\d+", s):
        return None

    unit = None
    idx = None

    # Find the unit in the sentence
    for i, w in enumerate(words):
        if w in units:
            unit = w
            idx = i
            break

    # No unit found → cannot extract value
    if unit is None:
        return None

    # Extract number words located before the unit
    number_tokens = []
    i = idx - 1

    while i >= 0 and words[i] in NUMBER_WORDS:
        number_tokens.insert(0, words[i])
        i -= 1

    # No number found → invalid command
    if not number_tokens:
        return None

    try:
        # Convert text (e.g. "twenty four") → numeric value (24)
        number = text2num(" ".join(number_tokens), "en")

        # Apply unit conversion (cm → m, degree → rad)
        return number * units[unit]

    except:
        # If parsing fails → return None safely
        return None


# -------- DISTANCE EXTRACTION --------

def extract_distance(sentence):
    """
    Extract a distance in meters from a sentence.

    Example:
        "move ten centimeters" → 0.10
    """
    return extract_value(sentence, DISTANCE_UNITS)


# -------- ANGLE EXTRACTION --------

def extract_angle(sentence):
    """
    Extract an angle in radians from a sentence.

    Example:
        "rotate twenty degrees" → ~0.35 rad
    """
    return extract_value(sentence, ANGLE_UNITS)