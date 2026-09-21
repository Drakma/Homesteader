# Keyboard & Shortcuts

A compact reference for the shortcuts and modifiers scattered through the app.

## Global

| Key            | Action                |
| -------------- | --------------------- |
| <kbd>/</kbd>   | Focus the search bar  |
| <kbd>Esc</kbd> | Close the open dialog |

<kbd>/</kbd> is ignored while you're already typing in a field, so it's safe to
press without thinking about focus.

## Mouse modifiers

| Action         | Modifier                 | Result                                        |
| -------------- | ------------------------ | --------------------------------------------- |
| Delete a card  | plain click              | Confirmation dialog                           |
| Delete a card  | <kbd>Shift</kbd> + click | Instant — no confirmation                     |
| Refresh button | plain click              | Re-read catalog and status                    |
| Refresh button | <kbd>Shift</kbd> + click | Full page reload (picks up HTML/CSS/JS edits) |

The **Don't ask again** checkbox on the delete dialog makes plain clicks behave
like <kbd>Shift</kbd>+click from then on. It's remembered between sessions, and
unchecking it restores the confirmations.

<blockquote>

**Which delete?** Deleting sends the asset to the **trash**, so even an instant
delete is recoverable. It is not permanent — permanent removal only happens from
the Trash panel.

</blockquote>

## Drag and drop

| Drag                          | Onto                 | Result                                       |
| ----------------------------- | -------------------- | -------------------------------------------- |
| **Move All** in the batch bar | a sidebar category   | Moves every checked asset into that category |
| A sidebar category tab        | another category tab | Reorders or nests the category               |
| A tag                         | a target             | Adds the tag's members to it                 |

The **Move All** button is deliberately drag-only for its primary action —
clicking it just shows a reminder of that fact. This prevents an accidental
click from relocating a large selection.

## 3D viewer

| Input      | Action |
| ---------- | ------ |
| Left drag  | Rotate |
| Right drag | Pan    |
| Scroll     | Zoom   |

## Editor panes

Both the biome and schema editors use the same layout — rich pane on the left,
raw JSON on the right — with **Save**, **Revert**, and **Format** in the
toolbar. <kbd>Esc</kbd> closes the editor dialog.

<blockquote>

**Revert is your safety net.** Both editors hold a draft separate from what's on
disk until you save, so experimenting is free — you can always revert to the
last saved state.

</blockquote>

## Confirmations

Dialogs that change data ask before acting:

| Dialog             | Asks about                           |
| ------------------ | ------------------------------------ |
| Move to Trash      | One asset, or a batch                |
| Delete field       | Removing a schema field              |
| Permanently Delete | Erasing trashed items — irreversible |
| Delete All         | Emptying the trash — irreversible    |
| Delete requests    | Clearing the request queue           |

The two irreversible ones list the affected item names so you can see exactly
what you're about to lose.
