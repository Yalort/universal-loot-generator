from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.properties import StringProperty

from .utils import load_loot_items, load_materials, generate_loot


class LootGeneratorWidget(BoxLayout):
    output_text = StringProperty("")

    def __init__(self, **kwargs):
        super().__init__(orientation="vertical", **kwargs)
        self.loot_items = load_loot_items()
        self.materials = load_materials()

        self.points_input = TextInput(hint_text="Loot Points", input_filter="int", size_hint_y=None, height="40dp")
        self.add_widget(self.points_input)

        self.include_input = TextInput(hint_text="Include Tags (comma separated)", size_hint_y=None, height="40dp")
        self.add_widget(self.include_input)

        self.exclude_input = TextInput(hint_text="Exclude Tags (comma separated)", size_hint_y=None, height="40dp")
        self.add_widget(self.exclude_input)

        self.max_rarity_input = TextInput(hint_text="Max Rarity", input_filter="int", size_hint_y=None, height="40dp")
        self.add_widget(self.max_rarity_input)

        self.min_rarity_input = TextInput(hint_text="Min Rarity", input_filter="int", size_hint_y=None, height="40dp")
        self.add_widget(self.min_rarity_input)

        btn = Button(text="Generate Loot", size_hint_y=None, height="40dp")
        btn.bind(on_press=self.generate)
        self.add_widget(btn)

        scroll = ScrollView()
        self.output_label = Label(text="", size_hint_y=None)
        self.output_label.bind(texture_size=self.output_label.setter("size"))
        scroll.add_widget(self.output_label)
        self.add_widget(scroll)

    def generate(self, *args):
        points = int(self.points_input.text) if self.points_input.text else 0
        include_tags = [t.strip() for t in self.include_input.text.split(',') if t.strip()] or None
        exclude_tags = [t.strip() for t in self.exclude_input.text.split(',') if t.strip()] or None
        max_rarity = int(self.max_rarity_input.text) if self.max_rarity_input.text else None
        min_rarity = int(self.min_rarity_input.text) if self.min_rarity_input.text else None

        loot = generate_loot(
            self.loot_items,
            points,
            include_tags=include_tags,
            exclude_tags=exclude_tags,
            min_rarity=min_rarity,
            max_rarity=max_rarity,
            materials=self.materials,
        )

        if loot:
            counts = {}
            for item in loot:
                counts[item.name] = counts.get(item.name, 0) + 1
            lines = []
            handled = set()
            for item in loot:
                if item.name in handled:
                    continue
                count = counts[item.name]
                tag_str = ", ".join(item.tags)
                if count > 1:
                    lines.append(f"{count}x {item.name} (Rarity: {item.rarity}, Tags: {tag_str}) - {item.description}")
                else:
                    lines.append(f"{item.name} (Rarity: {item.rarity}, Tags: {tag_str}) - {item.description}")
                handled.add(item.name)
            self.output_label.text = "\n".join(lines)
        else:
            self.output_label.text = "No loot items matched your criteria."


class LootGeneratorApp(App):
    def build(self):
        return LootGeneratorWidget()


if __name__ == "__main__":
    LootGeneratorApp().run()
