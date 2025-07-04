# Loot Generator

An application designed for generating loot via a point-buy tag based system.

## Prerequisites

- Python 3.8 or newer (the GUI uses Tkinter which is included with the
  standard Python distribution)

## Installation

Clone the repository and install any dependencies (none are required beyond
Python itself):

```bash
git clone <repository-url>
cd lootgen
```

## Running the GUI

Launch the application by executing `loot_app.pyw` with Python:

```bash
python loot_generator/loot_app.pyw
```

This opens a window where you can generate loot, manage presets and maintain
the list of available items. Item and material management now live on separate
"Items" and "Materials" tabs. Generated loot includes each item's tags so you
can easily see why an item was selected.

## Using Presets

Presets store common tag and point configurations. Select a preset from the
"Preset" drop-down in the GUI and click **Load Preset** to populate the input
fields. After adjusting the values, click **Save Preset** to create or update
a preset, or **Delete Preset** to remove it.

## Adding Items

Use the **Items** tab to manage loot items. Click **Add Item** for a single
entry or **Bulk Add Items** to paste many at once. Existing entries can be
modified with **Edit Item** or removed with **Delete Item**. In bulk mode, enter
one item per line as `name|rarity|description|point_value|tag1,tag2`. All added
items are saved to `loot_items.json` and become available for future loot
generation.

## Managing Materials

Some item names may include placeholders such as `[Metal]` or `[Stone/o]` which
are replaced with a random material when loot is generated. Multiple material
types can be combined with slashes, e.g. `[Wood/Metal/Stone]`, in which case a
material of any listed type may be chosen. Materials are stored in
`materials.json` and each has a name, point modifier and type (`Metal`, `Stone`,
`Wood` or `Fabric`). The **Materials** tab provides **Add Material**, **Edit
Material**, **Bulk Add Materials** and **Delete Material** actions. Optional
placeholders denoted with `/o` may resolve to an empty string, allowing items
like `[Metal] [Stone/o] Earring` or `[Wood/Metal/o] Shield` to generate with or
without the material name.
