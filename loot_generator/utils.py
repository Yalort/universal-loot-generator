import json
import os
import random
import re
import shutil
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

# Root directory where user game system data is stored
DATASET_ROOT = os.path.join(os.path.expanduser("~"), "documents", "UniversalLootGen")

# Currently selected game system directory
_current_system_dir: Optional[str] = None


def get_dataset_root() -> str:
    """Return the base directory for all game system datasets."""
    return DATASET_ROOT


def list_game_systems() -> List[str]:
    """Return available game system names."""
    if not os.path.isdir(DATASET_ROOT):
        return []
    return [name for name in os.listdir(DATASET_ROOT) if os.path.isdir(os.path.join(DATASET_ROOT, name))]


def ensure_game_system(name: str) -> str:
    """Ensure the named game system directory exists with default data."""
    system_dir = os.path.join(DATASET_ROOT, name)
    if not os.path.isdir(system_dir):
        os.makedirs(system_dir, exist_ok=True)
        for fname in ("loot_items.json", "materials.json", "presets.json"):
            shutil.copy(_resolve(f"data/{fname}"), os.path.join(system_dir, fname))
    return system_dir


def rename_game_system(old: str, new: str) -> None:
    """Rename a game system directory."""
    old_path = os.path.join(DATASET_ROOT, old)
    new_path = os.path.join(DATASET_ROOT, new)
    if os.path.isdir(old_path) and old != new:
        os.rename(old_path, new_path)


def set_game_system(name: Optional[str]) -> None:
    """Set the currently active game system."""
    global _current_system_dir
    if name:
        _current_system_dir = ensure_game_system(name)
    else:
        _current_system_dir = None


def get_current_system_dir() -> Optional[str]:
    return _current_system_dir


def get_data_path(filename: str) -> str:
    """Return absolute path for ``filename`` within the active dataset."""
    if _current_system_dir:
        return os.path.join(_current_system_dir, filename)
    return _resolve(f"data/{filename}")


def _resolve(path: str) -> str:
    """Return absolute path relative to this module."""
    return os.path.join(BASE_DIR, path)


def load_materials(filepath: Optional[str] = None) -> List[Material]:
    """Load material definitions from json file."""
    path = filepath or get_data_path('materials.json')
    if not os.path.isabs(path):
        path = _resolve(path)
    if not os.path.exists(path):
        return []
    with open(path, 'r') as file:
        data = json.load(file)
    materials_data = data.get("materials", data)
    return [Material(**m) for m in materials_data]


def save_materials(materials: List[Material], filepath: Optional[str] = None) -> None:
    """Save material definitions to json file."""
    path = filepath or get_data_path('materials.json')
    if not os.path.isabs(path):
        path = _resolve(path)
    with open(path, 'w') as file:
        json.dump({"materials": [m.__dict__ for m in materials]}, file, indent=4)


def load_loot_items(filepath: Optional[str] = None):
    """Load loot items from json file.

    The file may contain either a list of items or an object with
    ``items`` and ``tags`` keys. Only the item data is returned here.
    """
    path = filepath or get_data_path('loot_items.json')
    if not os.path.isabs(path):
        path = _resolve(path)
    with open(path, 'r') as file:
        data = json.load(file)

    if isinstance(data, dict):
        items_data = data.get("items", [])
    else:
        items_data = data

    return [LootItem(**item) for item in items_data]

def load_all_tags(filepath: Optional[str] = None):
    """Return the list of all tags stored in ``loot_items.json``.

    For backward compatibility, if the file does not contain a ``tags``
    key the tags are derived from the items.
    """
    path = filepath or get_data_path('loot_items.json')
    if not os.path.isabs(path):
        path = _resolve(path)
    with open(path, 'r') as file:
        data = json.load(file)

    if isinstance(data, dict) and "tags" in data:
        return data.get("tags", [])

    # Older format: derive tags from items list
    items = data if not isinstance(data, dict) else data.get("items", [])
    tags = sorted({tag for item in items for tag in item.get("tags", [])})
    return tags

def load_presets(filepath: Optional[str] = None):
    path = filepath or get_data_path('presets.json')
    if not os.path.isabs(path):
        path = _resolve(path)
    with open(path, 'r') as file:
        return json.load(file)

def save_presets(presets, filepath: Optional[str] = None):
    path = filepath or get_data_path('presets.json')
    if not os.path.isabs(path):
        path = _resolve(path)
    with open(path, 'w') as file:
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
