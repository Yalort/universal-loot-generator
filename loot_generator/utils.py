import json
import os
import random
import re
from dataclasses import dataclass
from typing import List, Optional

@dataclass
class LootItem:
    name: str
    rarity: int
    description: str
    point_value: int
    tags: List[str]


@dataclass
class Material:
    """A material that can be inserted into item names."""

    name: str
    modifier: float
    type: str

BASE_DIR = os.path.dirname(__file__)


def _resolve(path: str) -> str:
    """Return absolute path relative to this module."""
    return os.path.join(BASE_DIR, path)


def load_materials(filepath=_resolve('data/materials.json')) -> List[Material]:
    """Load material definitions from json file."""
    path = _resolve(filepath) if isinstance(filepath, str) and not os.path.isabs(filepath) else filepath
    if not os.path.exists(path):
        return []
    with open(path, 'r') as file:
        data = json.load(file)
    materials_data = data.get("materials", data)
    return [Material(**m) for m in materials_data]


def save_materials(materials: List[Material], filepath=_resolve('data/materials.json')) -> None:
    """Save material definitions to json file."""
    path = _resolve(filepath) if isinstance(filepath, str) and not os.path.isabs(filepath) else filepath
    with open(path, 'w') as file:
        json.dump({"materials": [m.__dict__ for m in materials]}, file, indent=4)


def load_loot_items(filepath=_resolve('data/loot_items.json')):
    """Load loot items from json file.

    The file may contain either a list of items or an object with
    ``items`` and ``tags`` keys. Only the item data is returned here.
    """
    with open(_resolve(filepath) if isinstance(filepath, str) and not os.path.isabs(filepath) else filepath, 'r') as file:
        data = json.load(file)

    if isinstance(data, dict):
        items_data = data.get("items", [])
    else:
        items_data = data

    return [LootItem(**item) for item in items_data]

def load_all_tags(filepath=_resolve('data/loot_items.json')):
    """Return the list of all tags stored in ``loot_items.json``.

    For backward compatibility, if the file does not contain a ``tags``
    key the tags are derived from the items.
    """
    with open(_resolve(filepath) if isinstance(filepath, str) and not os.path.isabs(filepath) else filepath, 'r') as file:
        data = json.load(file)

    if isinstance(data, dict) and "tags" in data:
        return data.get("tags", [])

    # Older format: derive tags from items list
    items = data if not isinstance(data, dict) else data.get("items", [])
    tags = sorted({tag for item in items for tag in item.get("tags", [])})
    return tags

def load_presets(filepath=_resolve('data/presets.json')):
    with open(_resolve(filepath) if isinstance(filepath, str) and not os.path.isabs(filepath) else filepath, 'r') as file:
        return json.load(file)

def save_presets(presets, filepath=_resolve('data/presets.json')):
    with open(_resolve(filepath) if isinstance(filepath, str) and not os.path.isabs(filepath) else filepath, 'w') as file:
        json.dump(presets, file, indent=4)

def generate_loot(
    items: List[LootItem],
    points: int,
    include_tags: Optional[List[str]] = None,
    exclude_tags: Optional[List[str]] = None,
    min_rarity: Optional[int] = None,
    max_rarity: Optional[int] = None,
    materials: Optional[List[Material]] = None,
):
    if points <= 0:
        raise ValueError("points must be positive")
    filtered_items = [
        item
        for item in items
        if (not include_tags or set(include_tags).intersection(item.tags))
        and (not exclude_tags or not set(exclude_tags).intersection(item.tags))
        and (min_rarity is None or item.rarity >= min_rarity)
        and (max_rarity is None or item.rarity <= max_rarity)
    ]

    # Validate rarities and skip items with non-positive values
    invalid_items = [item for item in filtered_items if item.rarity <= 0]
    if invalid_items:
        filtered_items = [item for item in filtered_items if item.rarity > 0]
        if not filtered_items:
            invalid_names = ", ".join(item.name for item in invalid_items)
            raise ValueError(
                f"All filtered items have non-positive rarity: {invalid_names}"
            )

    # Filter out items with invalid or zero point values
    invalid_value_items = [item for item in filtered_items if item.point_value <= 0]
    if invalid_value_items:
        filtered_items = [item for item in filtered_items if item.point_value > 0]
        if not filtered_items:
            invalid_names = ", ".join(item.name for item in invalid_value_items)
            raise ValueError(
                f"All filtered items have non-positive point value: {invalid_names}"
            )

    loot = []
    total_points = 0

    if not filtered_items:
        return loot

    while total_points < points:
        remaining = points - total_points
        available_items = [i for i in filtered_items if i.point_value <= remaining]
        if not available_items:
            break
        weights = [1 / i.rarity for i in available_items]
        item = random.choices(available_items, weights=weights, k=1)[0]
        if materials:
            name, value = resolve_material_placeholders(item.name, item.point_value, materials)
            item = LootItem(name, item.rarity, item.description, value, item.tags)
        loot.append(item)
        total_points += item.point_value

    return loot


def resolve_material_placeholders(name: str, value: int, materials: List[Material]) -> (str, int):
    """Replace material placeholders in ``name`` using provided materials.

    Placeholders are of the form ``[Metal]`` or ``[Metal/o]``. Multiple material
    types can be provided by separating them with ``/`` such as
    ``[Wood/Metal/Stone]``. The optional variant (``/o``) may be combined with
    multiple types (e.g. ``[Wood/Metal/o]``) and may be replaced with an empty
    string with 50% probability. ``value`` is modified by each material's
    ``modifier``.
    """
    pattern = re.compile(r"\[([A-Za-z/]+?)(?:(/o))?\]")
    modifiers = 1.0

    def repl(match: re.Match) -> str:
        nonlocal modifiers
        types_str, optional = match.group(1), match.group(2)
        if optional:
            if random.random() < 0.5:
                return ""
        types = [t.strip() for t in types_str.split("/") if t.strip()]
        options = [m for m in materials if m.type.lower() in {t.lower() for t in types}]
        if not options:
            return ""
        mat = random.choice(options)
        modifiers *= mat.modifier
        return mat.name

    new_name = pattern.sub(repl, name)
    new_value = int(round(value * modifiers))
    return new_name.strip(), new_value


def parse_items_text(text: str) -> List[LootItem]:
    """Parse a bulk text string into ``LootItem`` objects.

    Each non-empty line should contain five ``|`` separated fields in the
    order ``name|rarity|description|point_value|tag1,tag2``. Tags are
    comma-separated. Whitespace around fields is ignored.
    """

    items: List[LootItem] = []
    for line in text.splitlines():
        if not line.strip():
            continue
        parts = [p.strip() for p in line.split("|")]
        if len(parts) != 5:
            raise ValueError("Each line must contain five '|' separated fields")
        name, rarity_str, description, value_str, tags_str = parts
        rarity = int(rarity_str)
        point_value = int(value_str)
        tags = [t.strip() for t in tags_str.split(",") if t.strip()]
        items.append(LootItem(name, rarity, description, point_value, tags))

    return items


def parse_materials_text(text: str) -> List[Material]:
    """Parse a bulk text string into ``Material`` objects.

    Each non-empty line should contain three ``|`` separated fields in the
    order ``name|modifier|type``. Whitespace around fields is ignored.
    """

    materials: List[Material] = []
    for line in text.splitlines():
        if not line.strip():
            continue
        parts = [p.strip() for p in line.split("|")]
        if len(parts) != 3:
            raise ValueError("Each line must contain three '|' separated fields")
        name, modifier_str, type_str = parts
        modifier = float(modifier_str)
        materials.append(Material(name, modifier, type_str))

    return materials
