from lxml import etree as ET
from lxml.etree import CDATA
from core.models import TrackInfo
import re

_NS = {"k": "http://www.opengis.net/kml/2.2"}
_RE = re.compile(r"^([A-Za-z0-9]+-)(\d+)(.*)")

parser = ET.XMLParser(remove_blank_text=True)


def _increment_name_if_exists(name: str) -> str | None:
    match = _RE.match(name)
    if not match:
        return None

    prefix, number_str, suffix = match.groups()
    new_number = int(number_str) + 1
    return f"{prefix}{new_number}{suffix}"


def increment_all_track_numbers(path: str, output_path: str):
    tree = ET.parse(path, parser)
    root = tree.getroot()

    for folder in root.findall(".//k:Folder", _NS):
        name_el = folder.find("k:name", _NS)
        placemark = folder.find("k:Placemark", _NS)
        if placemark is None:
            continue

        pm_name_el = placemark.find("k:name", _NS)
        if pm_name_el is None:
            continue

        # lxml wants explicit None‐check hence `if name_el is not None`
        old_name = (name_el if name_el is not None else pm_name_el).text or ""
        new_name = _increment_name_if_exists(old_name)
        if not new_name:
            continue

        # Ships have their own layer
        if name_el is not None and _RE.match(name_el.text or ""):
            name_el.text = CDATA(new_name)

        # While driving routes (trucks) only have one layer
        pm_name_el.text = CDATA(new_name)

    tree.write(output_path, encoding="utf-8", xml_declaration=True, pretty_print=True)


def increment_track_number(ti: TrackInfo):
    tree = ET.parse(ti.path, parser)
    root: ET._Element = tree.getroot()

    matches = root.xpath(
        ".//k:name[starts-with(text(), $name)]", namespaces=_NS, name=ti.name
    )

    for name_el in matches:
        print(f"[increment] {ti.name}: {name_el.text}")
        new_name = _increment_name_if_exists(name_el.text)

        if not new_name:
            continue

        ti.name = new_name
        name_el.text = CDATA(new_name)

    tree.write(ti.path, encoding="utf-8", xml_declaration=True, pretty_print=True)
