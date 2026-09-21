# Schemas, Biomes & Tags

These are the taxonomy layer — the three ways the catalog describes *what an
asset is* beyond its own fields.

## Schemas

A schema is the **field contract for a category**. It defines which keys every
manifest in that category should have, their types, and their constraints.

Each field carries:

| Property | Meaning |
| --- | --- |
| `type` | `string`, `number`, `boolean`, `object`, or `array` |
| `required` | Whether the manifest must include it |
| `min` / `max` | Numeric bounds, where applicable |

### The editor

Selecting the **🧬 Schemas** tab opens a split editor:

- **Left — the rich editor.** Fields render as cards. Objects expand
  recursively, so nested keys are editable in place at any depth. Each field has
  a small ✕ to remove it, and an add-row to introduce new fields.
- **Right — the raw JSON.** The same content, editable directly, with syntax
  highlighting and a format button.

The two panes stay in sync: editing the rich side updates the JSON, and vice
versa. **Save** writes the schema; **Revert** throws away your draft.

### Validating

Schemas exist to be checked against. Validation runs compliance checks on every
item manifest in a category and reports which ones violate the contract —
missing required fields, wrong types, out-of-range numbers. This is how you
catch a manifest that was written by hand and drifted.

## Biomes

A biome describes an environment and which assets belong in it. Each biome is a
JSON file under `assets/biomes/`.

The biome editor mirrors the schema editor's layout: a rich pane on the left, a
raw JSON pane on the right, and Save / Revert / Format in the toolbar.

**🌍 Biomes** in the sidebar lists them; the search bar filters by name or ID.

## Tags

Tags are **virtual assets** — a tag name stands in for a list of interchangeable
real items. Where a recipe might accept any of several wood types, a single tag
can represent the whole set instead of naming each one.

A tag has:

- a **name**
- a list of **members**, each of which must be a real, existing catalog item

Because membership is validated, a tag can't point at something that doesn't
exist — if you delete a member asset, it stops satisfying the tag.

### Working with tags

Selecting the **🏷️ Tags** tab lists every tag with its member count. Use
**Add Tag** to create one, and edit a tag's name or membership from its row.

When you're viewing a tag's assets, cards gain a **❌** action to remove that
asset from the registry — useful when an item was tagged by mistake.

<blockquote>

**Note:** removing an asset from a tag only changes the tag's membership. The
asset itself is untouched.

</blockquote>

## Categories and subfolders

Categories are the top-level folders under `assets/`. Built-in categories are
hardcoded; custom ones you add are stored in `kit_config.json`.

Custom categories also carry an **asset prefix**, which is used when computing
an item's ID during a move — so items moved into your custom category get
sensible IDs automatically.

**Subfolders** group a species' lifecycle stages inside a category, which is
how a corn plant's sprout/growing/mature variants appear together as one
expandable group rather than three unrelated cards.
