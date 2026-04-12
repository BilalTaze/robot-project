import re
import math
from text_to_num import text2num

ANGLE_UNITS = {
    "degree": math.pi / 180,
    "degrees": math.pi / 180
}

DISTANCE_UNITS = {
    "cm": 0.01,
    "centimeter": 0.01,
    "centimeters": 0.01
}

NUMBER_WORDS = {
    "one","two","three","four","five","six","seven","eight","nine",
    "ten","eleven","twelve","thirteen","fourteen","fifteen",
    "sixteen","seventeen","eighteen","nineteen",
    "twenty","thirty","forty","fifty"
}


def extract_value(sentence, units):
    s = sentence.lower().replace("-", " ")
    words = s.split()

    # interdit chiffres
    if re.search(r"\d+", s):
        return None

    unit = None
    idx = None

    for i, w in enumerate(words):
        if w in units:
            unit = w
            idx = i
            break

    if unit is None:
        return None

    number_tokens = []
    i = idx - 1

    while i >= 0 and words[i] in NUMBER_WORDS:
        number_tokens.insert(0, words[i])
        i -= 1

    if not number_tokens:
        return None

    try:
        number = text2num(" ".join(number_tokens), "en")
        return number * units[unit]
    except:
        return None


def extract_distance(sentence):
    return extract_value(sentence, DISTANCE_UNITS)


def extract_angle(sentence):
    return extract_value(sentence, ANGLE_UNITS)