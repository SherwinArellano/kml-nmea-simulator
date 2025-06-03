import random
import string


def generate_code_trailer():
    """
    Generates a trailer code in the format: 2 letters - 3 digits - 2 letters
    Example: 'TA487PZ'
    """
    letters = string.ascii_uppercase
    part1 = "".join(random.choices(letters, k=2))
    part2 = "".join(random.choices(string.digits, k=3))
    part3 = "".join(random.choices(letters, k=2))
    return f"{part1}{part2}{part3}"


def generate_code_container():
    """
    Generates a container code in the format: 3 letters - 4 digits
    Example: 'BSE1212'
    """
    letters = string.ascii_uppercase
    part1 = "".join(random.choices(letters, k=3))
    part2 = "".join(random.choices(string.digits, k=4))
    return f"{part1}{part2}"
