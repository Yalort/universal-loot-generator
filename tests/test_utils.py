import os
import json
import random
import tempfile
import pytest
from loot_generator import utils


OLD_FORMAT_ITEMS = [
    {
        "name": "Sword",
        "rarity": 1,
        "description": "A sword",
        "point_value": 10,
        "tags": ["weapon", "melee"]
    },
    {
        "name": "Potion",
        "rarity": 2,
        "description": "Heals",
        "point_value": 5,
        "tags": ["consumable"]
    }
]


def test_resolve_returns_module_relative_path():
    path = utils._resolve('data/loot_items.json')
    expected = os.path.join(os.path.dirname(utils.__file__), 'data/loot_items.json')
    assert path == expected


def test_load_loot_items_returns_empty_list():
    items = utils.load_loot_items()
    assert isinstance(items, list)
    assert items == []


def test_load_all_tags_from_tags_key():
    tags = utils.load_all_tags()
    assert tags == []
    assert isinstance(tags, list)


def test_load_all_tags_fallback(tmp_path):
    tmp_file = tmp_path / 'items.json'
    with open(tmp_file, 'w') as fh:
        json.dump(OLD_FORMAT_ITEMS, fh)
    tags = utils.load_all_tags(str(tmp_file))
    assert set(tags) == {'weapon', 'melee', 'consumable'}


def test_load_and_save_presets_roundtrip(tmp_path):
    presets = {'Test': {'loot_points': 5, 'include_tags': ['weapon'], 'exclude_tags': []}}
    tmp_file = tmp_path / 'presets.json'
    utils.save_presets(presets, str(tmp_file))
    loaded = utils.load_presets(str(tmp_file))
    assert presets == loaded


def test_generate_loot_include_tags():
    items = [
        utils.LootItem('Sword', 1, '', 10, ['weapon']),
        utils.LootItem('Axe', 1, '', 10, ['weapon']),
        utils.LootItem('Potion', 1, '', 5, ['consumable']),
    ]
    random.seed(1)
    loot = utils.generate_loot(items, points=15, include_tags=['weapon'])
    assert loot
    assert all('weapon' in item.tags for item in loot)


def test_generate_loot_exclude_tags():
    items = [
        utils.LootItem('Wand', 1, '', 10, ['magic']),
        utils.LootItem('Sword', 1, '', 10, ['weapon']),
    ]
    random.seed(0)
    loot = utils.generate_loot(items, points=15, exclude_tags=['magic'])
    assert loot
    assert all('magic' not in item.tags for item in loot)


def test_generate_loot_rarity_filters():
    items = [
        utils.LootItem('Common', 1, '', 5, ['misc']),
        utils.LootItem('Uncommon', 2, '', 5, ['misc']),
        utils.LootItem('Rare', 3, '', 5, ['misc']),
    ]
    random.seed(0)
    loot = utils.generate_loot(items, points=15, min_rarity=2, max_rarity=3)
    assert loot
    assert all(2 <= item.rarity <= 3 for item in loot)


def test_generate_loot_no_items_when_filtered_out():
    items = [utils.LootItem('Sword', 1, '', 10, ['weapon'])]
    random.seed(0)
    loot = utils.generate_loot(items, points=10, include_tags=['nonexistent'])
    assert loot == []


def test_generate_loot_invalid_point_values_raise():
    items = [
        utils.LootItem('Bad1', 1, '', 0, []),
        utils.LootItem('Bad2', 1, '', -5, []),
    ]
    with pytest.raises(ValueError):
        utils.generate_loot(items, points=5)


def test_parse_items_text_valid():
    text = "Sword|1|Sharp blade|10|weapon,melee"
    items = utils.parse_items_text(text)
    assert len(items) == 1
    item = items[0]
    assert item.name == "Sword"
    assert item.rarity == 1
    assert item.description == "Sharp blade"
    assert item.point_value == 10
    assert item.tags == ["weapon", "melee"]


def test_parse_items_text_invalid():
    text = "Bad|data"
    with pytest.raises(ValueError):
        utils.parse_items_text(text)


def test_resolve_material_placeholders_required():
    materials = [utils.Material("Steel", 1.2, "Metal")]
    name, value = utils.resolve_material_placeholders("[Metal] Sword", 10, materials)
    assert name in {"Steel Sword"}
    assert value == 12


def test_resolve_material_placeholders_optional_none():
    random.seed(1)
    materials = [utils.Material("Ruby", 1.5, "Stone")]
    name, value = utils.resolve_material_placeholders("Ring with [Stone/o]", 8, materials)
    # With seed 1 the random check drops the material
    assert name == "Ring with"
    assert value == 8


def test_resolve_material_placeholders_multiple_types():
    random.seed(0)
    materials = [
        utils.Material("Iron", 1.2, "Metal"),
        utils.Material("Oak", 1.3, "Wood"),
        utils.Material("Ruby", 1.4, "Stone"),
    ]
    name, value = utils.resolve_material_placeholders("[Wood/Metal/Stone] Ring", 10, materials)
    assert name == "Oak Ring"
    assert value == 13


def test_resolve_material_placeholders_multiple_types_optional_none():
    random.seed(1)
    materials = [
        utils.Material("Steel", 1.2, "Metal"),
        utils.Material("Birch", 1.1, "Wood"),
    ]
    name, value = utils.resolve_material_placeholders("Ring [Metal/Wood/o]", 10, materials)
    # With seed 1 optional placeholder is removed
    assert name == "Ring"
    assert value == 10


def test_generate_loot_with_materials():
    items = [utils.LootItem('[Metal] Dagger', 1, '', 10, ['weapon'])]
    materials = [utils.Material('Iron', 1.0, 'Metal')]
    random.seed(1)
    loot = utils.generate_loot(items, points=10, materials=materials)
    assert loot[0].name == 'Iron Dagger'


def test_parse_materials_text_valid():
    text = "Steel|1.2|Metal"
    mats = utils.parse_materials_text(text)
    assert len(mats) == 1
    m = mats[0]
    assert m.name == "Steel"
    assert m.modifier == 1.2
    assert m.type == "Metal"


def test_parse_materials_text_invalid():
    text = "Bad|data"
    with pytest.raises(ValueError):
        utils.parse_materials_text(text)
