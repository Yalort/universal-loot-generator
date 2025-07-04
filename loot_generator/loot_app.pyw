import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, simpledialog
import tkinter.font as tkfont
import json
from utils import (
    load_loot_items,
    load_all_tags,
    load_presets,
    save_presets,
    generate_loot,
    parse_items_text,
    parse_materials_text,
    LootItem,
    load_materials,
    save_materials,
    Material,
    _resolve,
)


class LootGeneratorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Loot Generator")
        self._increase_fonts()
        self.loot_items = load_loot_items()
        self.all_tags = load_all_tags()
        self.presets = load_presets()
        self.materials = load_materials()
        self.setup_ui()
        self.update_preset_listbox()

    def setup_ui(self):
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill=tk.BOTH, expand=True)

        self.generate_tab = ttk.Frame(notebook, padding="10")
        self.items_tab = ttk.Frame(notebook, padding="10")
        self.materials_tab = ttk.Frame(notebook, padding="10")

        notebook.add(self.generate_tab, text="Generate")
        notebook.add(self.items_tab, text="Items")
        notebook.add(self.materials_tab, text="Materials")

        self.setup_generate_tab()
        self.setup_items_tab()
        self.setup_materials_tab()


    def setup_generate_tab(self):
        frame = self.generate_tab

        ttk.Label(frame, text="Loot Points:").grid(row=0, column=0, sticky=tk.W)
        self.loot_points_entry = ttk.Entry(frame)
        self.loot_points_entry.grid(row=0, column=1, sticky=tk.EW)

        ttk.Label(frame, text="Include Tags (comma-separated):").grid(row=1, column=0, sticky=tk.W)
        self.include_tags_entry = ttk.Entry(frame)
        self.include_tags_entry.grid(row=1, column=1, sticky=tk.EW)

        ttk.Label(frame, text="Exclude Tags (comma-separated):").grid(row=2, column=0, sticky=tk.W)
        self.exclude_tags_entry = ttk.Entry(frame)
        self.exclude_tags_entry.grid(row=2, column=1, sticky=tk.EW)

        ttk.Label(frame, text="Max Rarity (numeric):").grid(row=3, column=0, sticky=tk.W)
        self.max_rarity_entry = ttk.Entry(frame)
        self.max_rarity_entry.grid(row=3, column=1, sticky=tk.EW)

        ttk.Label(frame, text="Min Rarity (numeric):").grid(row=4, column=0, sticky=tk.W)
        self.min_rarity_entry = ttk.Entry(frame)
        self.min_rarity_entry.grid(row=4, column=1, sticky=tk.EW)

        ttk.Button(frame, text="Generate Loot", command=self.generate_loot).grid(row=5, column=0, columnspan=2, pady=5)

        ttk.Label(frame, text="Search Presets:").grid(row=6, column=0, sticky=tk.W)
        self.preset_search_var = tk.StringVar()
        self.preset_search_var.trace_add("write", lambda *args: self.update_preset_listbox())
        ttk.Entry(frame, textvariable=self.preset_search_var).grid(row=6, column=1, sticky=tk.EW)

        ttk.Label(frame, text="Presets:").grid(row=7, column=0, sticky=tk.W)
        self.preset_listbox = tk.Listbox(frame, height=5)
        self.preset_listbox.grid(row=7, column=1, sticky=tk.EW)

        ttk.Button(frame, text="Load Preset", command=self.load_preset).grid(row=8, column=0, columnspan=2)
        ttk.Button(frame, text="Save Preset", command=self.save_preset).grid(row=9, column=0, columnspan=2)
        ttk.Button(frame, text="Delete Preset", command=self.delete_preset).grid(row=10, column=0, columnspan=2)

        ttk.Label(frame, text="Generated Loot:").grid(row=11, column=0, sticky=tk.W)
        self.output_area = scrolledtext.ScrolledText(frame, height=8)
        self.output_area.grid(row=12, column=0, columnspan=2, sticky=tk.NSEW, pady=5)

        ttk.Button(frame, text="Show Tags", command=self.show_tags).grid(row=13, column=0, columnspan=2, pady=5)

        frame.columnconfigure(1, weight=1)
        frame.rowconfigure(12, weight=1)


    def setup_items_tab(self):
        frame = self.items_tab

        button_frame = ttk.Frame(frame)
        button_frame.grid(row=0, column=0, sticky=tk.NS, padx=(0, 5))
        ttk.Button(button_frame, text="Add Item", command=self.add_item).pack(fill=tk.X, pady=2)
        ttk.Button(button_frame, text="Edit Item", command=self.edit_item).pack(fill=tk.X, pady=2)
        ttk.Button(button_frame, text="Delete Item", command=self.delete_item).pack(fill=tk.X, pady=2)
        ttk.Button(button_frame, text="Bulk Add Items", command=self.bulk_add_items).pack(fill=tk.X, pady=2)

        columns = ("Name", "Rarity", "Description", "Value", "Tags")
        self.items_tree = ttk.Treeview(frame, columns=columns, show="headings")
        for col in columns:
            self.items_tree.heading(col, text=col, command=lambda c=col: self.sort_treeview(self.items_tree, c, False))
            self.items_tree.column(col, anchor=tk.W, minwidth=50)
        self.items_tree.grid(row=0, column=1, sticky=tk.NSEW)

        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=self.items_tree.yview)
        scrollbar.grid(row=0, column=2, sticky=tk.NS)
        self.items_tree.configure(yscrollcommand=scrollbar.set)
        self.items_tree.bind("<Double-1>", self.edit_item)

        frame.columnconfigure(1, weight=1)
        frame.rowconfigure(0, weight=1)
        self.populate_items_tree()


    def setup_materials_tab(self):
        frame = self.materials_tab

        button_frame = ttk.Frame(frame)
        button_frame.grid(row=0, column=0, sticky=tk.NS, padx=(0, 5))
        ttk.Button(button_frame, text="Add Material", command=self.add_material).pack(fill=tk.X, pady=2)
        ttk.Button(button_frame, text="Edit Material", command=self.edit_material).pack(fill=tk.X, pady=2)
        ttk.Button(button_frame, text="Delete Material", command=self.delete_material).pack(fill=tk.X, pady=2)
        ttk.Button(button_frame, text="Bulk Add Materials", command=self.bulk_add_materials).pack(fill=tk.X, pady=2)

        columns = ("Name", "Modifier", "Type")
        self.materials_tree = ttk.Treeview(frame, columns=columns, show="headings")
        for col in columns:
            self.materials_tree.heading(col, text=col, command=lambda c=col: self.sort_treeview(self.materials_tree, c, False))
            self.materials_tree.column(col, anchor=tk.W, minwidth=50)
        self.materials_tree.grid(row=0, column=1, sticky=tk.NSEW)

        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=self.materials_tree.yview)
        scrollbar.grid(row=0, column=2, sticky=tk.NS)
        self.materials_tree.configure(yscrollcommand=scrollbar.set)
        self.materials_tree.bind("<Double-1>", self.edit_material)

        frame.columnconfigure(1, weight=1)
        frame.rowconfigure(0, weight=1)
        self.populate_materials_tree()

    def generate_loot(self):
        points = int(self.loot_points_entry.get())
        include_tags = [tag.strip() for tag in self.include_tags_entry.get().split(',')] if self.include_tags_entry.get() else None
        exclude_tags = [tag.strip() for tag in self.exclude_tags_entry.get().split(',')] if self.exclude_tags_entry.get() else None
        min_rarity = int(self.min_rarity_entry.get()) if self.min_rarity_entry.get() else None
        max_rarity = int(self.max_rarity_entry.get()) if self.max_rarity_entry.get() else None

        loot = generate_loot(
            self.loot_items,
            points,
            include_tags,
            exclude_tags,
            min_rarity,
            max_rarity,
            self.materials,
        )

        self.output_area.delete('1.0', tk.END)
        if loot:
            item_counts = {}
            for item in loot:
                if item.name in item_counts:
                    item_counts[item.name]["count"] += 1
                else:
                    item_counts[item.name] = {"item": item, "count": 1}

            for data in item_counts.values():
                item = data["item"]
                count = data["count"]
                tags_str = ", ".join(item.tags)
                if count > 1:
                    self.output_area.insert(
                        tk.END,
                        f"{count}x {item.name} (Rarity: {item.rarity}, Tags: {tags_str}) - {item.description} [{item.point_value} points each]\n",
                    )
                else:
                    self.output_area.insert(
                        tk.END,
                        f"{item.name} (Rarity: {item.rarity}, Tags: {tags_str}) - {item.description} [{item.point_value} points]\n",
                    )
        else:
            self.output_area.insert(tk.END, "No loot items matched your criteria.\n")


    def load_preset(self):
        selection = self.preset_listbox.curselection()
        if not selection:
            messagebox.showerror("Error", "Preset not selected.")
            return
        preset_name = self.preset_listbox.get(selection[0])
        preset = self.presets.get(preset_name)
        if preset:
            self.loot_points_entry.delete(0, tk.END)
            self.loot_points_entry.insert(0, str(preset['loot_points']))
            include_tags = preset.get('include_tags', preset.get('tags', []))
            exclude_tags = preset.get('exclude_tags', [])
            self.include_tags_entry.delete(0, tk.END)
            self.include_tags_entry.insert(0, ', '.join(include_tags))
            self.exclude_tags_entry.delete(0, tk.END)
            self.exclude_tags_entry.insert(0, ', '.join(exclude_tags))
        else:
            messagebox.showerror("Error", "Preset not found.")

    def save_preset(self):
        preset_name = simpledialog.askstring("Save Preset", "Preset Name:")
        if preset_name:
            points = int(self.loot_points_entry.get())
            include_tags = [tag.strip() for tag in self.include_tags_entry.get().split(',') if tag.strip()]
            exclude_tags = [tag.strip() for tag in self.exclude_tags_entry.get().split(',') if tag.strip()]

            self.presets[preset_name] = {
                "loot_points": points,
                "include_tags": include_tags,
                "exclude_tags": exclude_tags,
            }
            save_presets(self.presets)
            self.update_preset_listbox()
            messagebox.showinfo("Saved", f"Preset '{preset_name}' saved successfully!")

    def delete_preset(self):
        selection = self.preset_listbox.curselection()
        if selection:
            preset_name = self.preset_listbox.get(selection[0])
        else:
            preset_name = None
        if preset_name in self.presets:
            if messagebox.askyesno("Delete", f"Are you sure you want to delete '{preset_name}'?"):
                del self.presets[preset_name]
                save_presets(self.presets)
                self.update_preset_listbox()
                messagebox.showinfo("Deleted", f"Preset '{preset_name}' deleted.")
        else:
            messagebox.showerror("Error", "Preset not found.")

    def add_item(self):
        add_window = tk.Toplevel(self.root)
        add_window.title("Add New Loot Item")

        fields = ["Name", "Rarity (numeric, higher is rarer)", "Description", "Point Value", "Tags (comma-separated)"]
        entries = {}

        for idx, field in enumerate(fields):
            ttk.Label(add_window, text=field).grid(row=idx, column=0, sticky=tk.W, pady=2)
            entry = ttk.Entry(add_window, width=40)
            entry.grid(row=idx, column=1, pady=2)
            entries[field] = entry

        def save_new_item():
            try:
                item = LootItem(
                    name=entries["Name"].get(),
                    rarity=int(entries["Rarity (numeric, higher is rarer)"].get()),
                    description=entries["Description"].get(),
                    point_value=int(entries["Point Value"].get()),
                    tags=[tag.strip() for tag in entries["Tags (comma-separated)"].get().split(',')]
                )
                self.loot_items.append(item)
                self.update_loot_file()
                self.populate_items_tree()
                messagebox.showinfo("Success", f"Item '{item.name}' added.")
                add_window.destroy()
            except Exception as e:
                messagebox.showerror("Error", f"Invalid input: {e}")

        ttk.Button(add_window, text="Add Item", command=save_new_item).grid(row=len(fields), column=0, columnspan=2, pady=5)

    def edit_item(self, event=None):
        selection = self.items_tree.selection()
        if not selection:
            messagebox.showerror("Error", "Item not selected.")
            return
        name = self.items_tree.item(selection[0], "values")[0]
        item = next((i for i in self.loot_items if i.name == name), None)
        if not item:
            messagebox.showerror("Error", "Item not found.")
            return

        edit_window = tk.Toplevel(self.root)
        edit_window.title(f"Edit Item - {name}")

        fields = [
            ("Name", item.name),
            ("Rarity (numeric, higher is rarer)", item.rarity),
            ("Description", item.description),
            ("Point Value", item.point_value),
            ("Tags (comma-separated)", ", ".join(item.tags)),
        ]
        entries = {}
        for idx, (label, value) in enumerate(fields):
            ttk.Label(edit_window, text=label).grid(row=idx, column=0, sticky=tk.W, pady=2)
            entry = ttk.Entry(edit_window, width=40)
            entry.insert(0, str(value))
            entry.grid(row=idx, column=1, pady=2)
            entries[label] = entry

        def save():
            try:
                item.name = entries["Name"].get()
                item.rarity = int(entries["Rarity (numeric, higher is rarer)"].get())
                item.description = entries["Description"].get()
                item.point_value = int(entries["Point Value"].get())
                item.tags = [t.strip() for t in entries["Tags (comma-separated)"].get().split(',') if t.strip()]
                self.update_loot_file()
                self.populate_items_tree()
                messagebox.showinfo("Updated", f"Item '{item.name}' updated.")
                edit_window.destroy()
            except Exception as exc:
                messagebox.showerror("Error", f"Invalid input: {exc}")

        ttk.Button(edit_window, text="Save", command=save).grid(row=len(fields), column=0, columnspan=2, pady=5)

    def bulk_add_items(self):
        bulk_window = tk.Toplevel(self.root)
        bulk_window.title("Bulk Add Loot Items")

        ttk.Label(
            bulk_window,
            text="Enter items one per line as name|rarity|description|point_value|tag1,tag2",
        ).pack(pady=5)
        text_area = tk.Text(bulk_window, width=60, height=10)
        text_area.pack(padx=5, pady=5)

        def save_bulk():
            try:
                items = parse_items_text(text_area.get("1.0", tk.END))
                if not items:
                    raise ValueError("No items provided")
                self.loot_items.extend(items)
                self.update_loot_file()
                self.populate_items_tree()
                messagebox.showinfo("Success", f"Added {len(items)} items.")
                bulk_window.destroy()
            except Exception as e:
                messagebox.showerror("Error", f"Invalid input: {e}")

        ttk.Button(bulk_window, text="Add Items", command=save_bulk).pack(pady=5)

    def delete_item(self):
        item_names = [item.name for item in self.loot_items]
        win = tk.Toplevel(self.root)
        win.title("Delete Loot Item")

        ttk.Label(win, text="Search:").pack(pady=2)
        search_var = tk.StringVar()
        search_entry = ttk.Entry(win, textvariable=search_var)
        search_entry.pack(pady=2, fill=tk.X, padx=5)

        listbox = tk.Listbox(win, height=10)
        listbox.pack(pady=5, fill=tk.BOTH, expand=True)

        def update_list(*args):
            term = search_var.get().lower()
            listbox.delete(0, tk.END)
            for name in item_names:
                if term in name.lower():
                    listbox.insert(tk.END, name)

        search_var.trace_add("write", update_list)
        update_list()

        def confirm_delete():
            sel = listbox.curselection()
            if not sel:
                messagebox.showerror("Error", "Item not selected.")
                return
            name = listbox.get(sel[0])
            item = next((i for i in self.loot_items if i.name == name), None)
            if item and messagebox.askyesno("Confirm Delete", f"Delete '{name}'?"):
                self.loot_items.remove(item)
                self.update_loot_file()
                self.populate_items_tree()
                messagebox.showinfo("Deleted", f"Item '{name}' deleted.")
                win.destroy()

        ttk.Button(win, text="Delete Item", command=confirm_delete).pack(pady=5)

    def add_material(self):
        add_window = tk.Toplevel(self.root)
        add_window.title("Add Material")

        fields = ["Name", "Modifier (e.g. 1.2)", "Type (Metal/Stone/Wood/Fabric)"]
        entries = {}
        for idx, field in enumerate(fields):
            ttk.Label(add_window, text=field).grid(row=idx, column=0, sticky=tk.W, pady=2)
            entry = ttk.Entry(add_window, width=30)
            entry.grid(row=idx, column=1, pady=2)
            entries[field] = entry

        def save_material():
            try:
                material = Material(
                    name=entries["Name"].get(),
                    modifier=float(entries["Modifier (e.g. 1.2)"].get()),
                    type=entries["Type (Metal/Stone/Wood/Fabric)"].get(),
                )
                self.materials.append(material)
                self.update_material_file()
                self.populate_materials_tree()
                messagebox.showinfo("Success", f"Material '{material.name}' added.")
                add_window.destroy()
            except Exception as e:
                messagebox.showerror("Error", f"Invalid input: {e}")

        ttk.Button(add_window, text="Add Material", command=save_material).grid(row=len(fields), column=0, columnspan=2, pady=5)

    def edit_material(self, event=None):
        selection = self.materials_tree.selection()
        if not selection:
            messagebox.showerror("Error", "Material not selected.")
            return
        name = self.materials_tree.item(selection[0], "values")[0]
        mat = next((m for m in self.materials if m.name == name), None)
        if not mat:
            messagebox.showerror("Error", "Material not found.")
            return

        edit_window = tk.Toplevel(self.root)
        edit_window.title(f"Edit Material - {name}")

        fields = [
            ("Name", mat.name),
            ("Modifier (e.g. 1.2)", mat.modifier),
            ("Type (Metal/Stone/Wood/Fabric)", mat.type),
        ]
        entries = {}
        for idx, (label, value) in enumerate(fields):
            ttk.Label(edit_window, text=label).grid(row=idx, column=0, sticky=tk.W, pady=2)
            entry = ttk.Entry(edit_window, width=30)
            entry.insert(0, str(value))
            entry.grid(row=idx, column=1, pady=2)
            entries[label] = entry

        def save():
            try:
                mat.name = entries["Name"].get()
                mat.modifier = float(entries["Modifier (e.g. 1.2)"].get())
                mat.type = entries["Type (Metal/Stone/Wood/Fabric)"].get()
                self.update_material_file()
                self.populate_materials_tree()
                messagebox.showinfo("Updated", f"Material '{mat.name}' updated.")
                edit_window.destroy()
            except Exception as exc:
                messagebox.showerror("Error", f"Invalid input: {exc}")

        ttk.Button(edit_window, text="Save", command=save).grid(row=len(fields), column=0, columnspan=2, pady=5)

    def delete_material(self):
        names = [m.name for m in self.materials]
        win = tk.Toplevel(self.root)
        win.title("Delete Material")

        ttk.Label(win, text="Search:").pack(pady=2)
        search_var = tk.StringVar()
        entry = ttk.Entry(win, textvariable=search_var)
        entry.pack(pady=2, fill=tk.X, padx=5)

        listbox = tk.Listbox(win, height=10)
        listbox.pack(pady=5, fill=tk.BOTH, expand=True)

        def update_list(*args):
            term = search_var.get().lower()
            listbox.delete(0, tk.END)
            for n in names:
                if term in n.lower():
                    listbox.insert(tk.END, n)

        search_var.trace_add("write", update_list)
        update_list()

        def confirm():
            sel = listbox.curselection()
            if not sel:
                messagebox.showerror("Error", "Material not selected.")
                return
            name = listbox.get(sel[0])
            mat = next((m for m in self.materials if m.name == name), None)
            if mat and messagebox.askyesno("Confirm Delete", f"Delete '{name}'?"):
                self.materials.remove(mat)
                self.update_material_file()
                self.populate_materials_tree()
                messagebox.showinfo("Deleted", f"Material '{name}' deleted.")
                win.destroy()

        ttk.Button(win, text="Delete", command=confirm).pack(pady=5)

    def bulk_add_materials(self):
        bulk_window = tk.Toplevel(self.root)
        bulk_window.title("Bulk Add Materials")

        ttk.Label(
            bulk_window,
            text="Enter materials one per line as name|modifier|type",
        ).pack(pady=5)
        text_area = tk.Text(bulk_window, width=50, height=10)
        text_area.pack(padx=5, pady=5)

        def save_bulk():
            try:
                mats = parse_materials_text(text_area.get("1.0", tk.END))
                if not mats:
                    raise ValueError("No materials provided")
                self.materials.extend(mats)
                self.update_material_file()
                self.populate_materials_tree()
                messagebox.showinfo("Success", f"Added {len(mats)} materials.")
                bulk_window.destroy()
            except Exception as e:
                messagebox.showerror("Error", f"Invalid input: {e}")

        ttk.Button(bulk_window, text="Add Materials", command=save_bulk).pack(pady=5)

    def update_preset_listbox(self):
        search = self.preset_search_var.get().lower()
        names = [name for name in self.presets.keys() if search in name.lower()]
        self.preset_listbox.delete(0, tk.END)
        for name in names:
            self.preset_listbox.insert(tk.END, name)

    def update_tag_list(self):
        self.all_tags = sorted({tag for item in self.loot_items for tag in item.tags})

    def show_tags(self):
        tags_str = ", ".join(self.all_tags) if self.all_tags else "No tags available"
        messagebox.showinfo("All Tags", tags_str)

    def update_loot_file(self):
        self.update_tag_list()
        with open(_resolve('data/loot_items.json'), 'w') as file:
            json.dump({
                "items": [item.__dict__ for item in self.loot_items],
                "tags": self.all_tags,
            }, file, indent=4)

    def update_material_file(self):
        with open(_resolve('data/materials.json'), 'w') as file:
            json.dump({"materials": [m.__dict__ for m in self.materials]}, file, indent=4)

    def populate_items_tree(self):
        if not hasattr(self, "items_tree"):
            return
        self.items_tree.delete(*self.items_tree.get_children())
        for item in self.loot_items:
            self.items_tree.insert(
                "",
                tk.END,
                values=(
                    item.name,
                    item.rarity,
                    item.description,
                    item.point_value,
                    ", ".join(item.tags),
                ),
            )

    def populate_materials_tree(self):
        if not hasattr(self, "materials_tree"):
            return
        self.materials_tree.delete(*self.materials_tree.get_children())
        for mat in self.materials:
            self.materials_tree.insert(
                "",
                tk.END,
                values=(mat.name, mat.modifier, mat.type),
            )

    def sort_treeview(self, tree, col, reverse):
        data = [(tree.set(k, col), k) for k in tree.get_children("")]

        def _convert(val):
            try:
                return float(val)
            except ValueError:
                return val.lower()

        data.sort(key=lambda t: _convert(t[0]), reverse=reverse)
        for index, (_, k) in enumerate(data):
            tree.move(k, "", index)
        tree.heading(col, command=lambda: self.sort_treeview(tree, col, not reverse))

    def _increase_fonts(self, scale: float = 1.2):
        """Increase default Tk fonts by the given scale."""
        for name in (
            "TkDefaultFont",
            "TkTextFont",
            "TkFixedFont",
            "TkMenuFont",
            "TkHeadingFont",
        ):
            try:
                f = tkfont.nametofont(name)
                size = f.cget("size")
                f.configure(size=int(round(size * scale)))
            except tk.TclError:
                pass

if __name__ == "__main__":
    root = tk.Tk()
    app = LootGeneratorApp(root)
    root.mainloop()
