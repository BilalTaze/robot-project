import re
from text_to_num import text2num

UNITS = {
    "mm": 0.001,
    "millimeter": 0.001,
    "millimeters": 0.001,
    "cm": 0.01,
    "centimeter": 0.01,
    "centimeters": 0.01,
    "m": 1.0,
    "meter": 1.0,
    "meters": 1.0,
}

NUMBER_WORDS = {
    "zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine",
    "ten", "eleven", "twelve", "thirteen", "fourteen", "fifteen", "sixteen",
    "seventeen", "eighteen", "nineteen", "twenty", "thirty", "forty", "fifty",
    "sixty", "seventy", "eighty", "ninety", "hundred", "thousand"
}


def extract_distance(sentence: str):
    s = sentence.lower().replace("-", " ")

    # chiffres interdits
    if re.search(r"\d+", s):
        return None

    words = s.split()

    unit = None
    unit_index = None

    for i, word in enumerate(words):
        if word in UNITS:
            unit = word
            unit_index = i
            break

    if unit is None:
        return None

    # on récupère seulement les mots de nombre juste avant l’unité
    number_tokens = []
    i = unit_index - 1

    while i >= 0 and words[i] in NUMBER_WORDS:
        number_tokens.insert(0, words[i])
        i -= 1

    if not number_tokens:
        return None

    number_text = " ".join(number_tokens)

    try:
        number = text2num(number_text, "en")
        return number * UNITS[unit]
    except Exception:
        return None