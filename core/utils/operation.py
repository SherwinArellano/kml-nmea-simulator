from pathlib import Path
import json
import random
import string
import re


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


project_root = Path(__file__).resolve().parent.parent.parent

with open(
    project_root / "assets" / "lista-province.json", "r", encoding="utf-8"
) as f_prov:
    # province_map: { "AG": "Agrigento", "AL": "Alessandria", ... }
    province_map: dict[str, str] = json.load(f_prov)

with open(
    project_root / "assets" / "lista-comuni.json", "r", encoding="utf-8"
) as f_com:
    # comuni_list: [ ["A001", "PD", "ABANO BAGNI", 0], ["A001", "PD", "ABANO TERME", 1], ... ]
    comuni_list: list[tuple[str, str, str, int]] = json.load(f_com)

# Build reverse-lookup maps
# province_name_to_code: {"Agrigento": "AG", ...}
province_name_to_code = {name.upper(): code for code, name in province_map.items()}
# include code-to-code mapping so that if user passes "AG", we still return "AG"
for code in province_map:
    province_name_to_code[code.upper()] = code

# comune_name_to_code: {"ABANO BAGNI": "A001", "ABANO TERME": "A001", ...}
comune_name_to_code = {}
# Also allow code-to-code: {"A001": "A001", ...}
for entry in comuni_list:
    code, prov_code, comune_name, _ = entry
    comune_name_to_code[comune_name.upper()] = code
    comune_name_to_code[code.upper()] = code  # if option is already a code


def get_cod_prov(pm_name: str | None, prov_option: str | None) -> str | None:
    """
    Determines cod_prov from the KML's Placemark <name> or optional prov option.
    1. If pm_name contains a province name or code, returns that code. (pm = placemark)
    2. Else if prov is provided (either name or code) and valid, returns that code.
    3. Otherwise, returns None.
    """
    name_upper = (pm_name or "").upper()
    # 1. Check if any province name/code appears in the KML name
    for prov_name_upper, prov_code in province_name_to_code.items():
        # We match whole words to avoid partial collisions
        if re.search(rf"\b{re.escape(prov_name_upper)}\b", name_upper):
            return prov_code

    # 2. Fallback to prov_option if given
    if prov_option:
        prov_opt_upper = prov_option.strip().upper()
        if prov_opt_upper in province_name_to_code:
            return province_name_to_code[prov_opt_upper]

    # 3. No province found
    return None


def get_cod_comune(pm_name: str | None, comune_option: str | None) -> str | None:
    """
    Determines cod_comune from the KML's Placemark <name> or optional comune option.
    1. If pm_name contains a municipality name or code, returns that code. (pm = placemark)
    2. Else if comune is provided (either name or code) and valid, returns that code.
    3. Otherwise, returns None.
    """
    name_upper = (pm_name or "").upper()
    # 1. Check if any comune name appears in the KML name
    for comune_name_upper, comune_code in comune_name_to_code.items():
        # Only match municipality names (ignore code-to-code here)
        # If comune_name_upper is exactly a numeric/alphanumeric code, skip in this loop
        if comune_name_upper.isalpha() or " " in comune_name_upper:
            if re.search(rf"\b{re.escape(comune_name_upper)}\b", name_upper):
                return comune_code

    # 2. Fallback to comune_option if given
    if comune_option:
        comune_opt_upper = comune_option.strip().upper()
        if comune_opt_upper in comune_name_to_code:
            return comune_name_to_code[comune_opt_upper]

    # 3. No municipality found
    return None
