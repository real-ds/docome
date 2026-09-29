# Docome CLI

## Installation

During development:

```bash
pip install -e ".[dev]"
```

## Examples

```bash
docome pdf merge a.pdf b.pdf -o merged.pdf

docome pdf split document.pdf -p 1-5 -o output/

docome pdf compress document.pdf -l recommended -o compressed.pdf

docome convert pdf2docx document.pdf -o document.docx

docome pdf pdf2img document.pdf -o images/

docome ocr pdf2searchable scanned.pdf -o searchable.pdf

docome pdf rotate document.pdf -d 90 -o rotated.pdf
```

## Editing

Single operations take an input and an output path:

```bash
docome edit add-text input.pdf -o out.pdf -p 1 -x 72 -y 100 -t "Hello"
docome edit annotate input.pdf -o out.pdf -p 1 --x0 70 --y0 90 --x1 220 --y1 105 -a highlight
```

For several edits at once, describe them in a JSON plan and apply them in a
single session:

```json
{
  "operations": [
    { "action": "replace_text", "page": 1, "x0": 60, "y0": 85, "x1": 300, "y1": 105,
      "new_text": "Updated heading", "fontsize": 18, "fontname": "hebo" },
    { "action": "draw_shape", "page": 1, "shape_type": "RECT",
      "x0": 60, "y0": 190, "x1": 250, "y1": 215, "color": [0.2, 0.2, 0.6] },
    { "action": "add_annotation", "page": 1, "annotation": "HIGHLIGHT",
      "x0": 70, "y0": 130, "x1": 220, "y1": 146, "color": [1, 0.9, 0.2] },
    { "action": "undo" }
  ]
}
```

```bash
docome edit actions
docome edit apply input.pdf -o out.pdf --plan plan.json
docome edit apply input.pdf -o out.pdf --plan plan.json --json
docome edit undo input.pdf -o out.pdf --times 2
```

Supported actions: `add_text`, `delete_text`, `replace_text`, `add_image`,
`draw_shape`, `add_annotation`, `move`, `resize`, `undo`, `redo`.

`apply` exits non-zero when any operation fails, and reports the failing
operation index. Colors accept `[r, g, b]` or `"r,g,b"`. `add_image` takes
`image_path` or `image_base64`. Rectangles can be given inline (`x0`, `y0`,
`x1`, `y1`) or nested under `rect`.

## Conversion Fidelity

```bash
docome convert pdf2docx-hq input.pdf -o out.docx
docome convert fidelity input.pdf -o out.docx
docome convert fidelity input.pdf -o out.docx --json
```

`fidelity` scores text, fonts, tables, images, hyperlinks, and page count,
and exits non-zero when a threshold is missed.

## Automation

Machine-readable output via `--json` flag.

Machine-readable output should contain:

- success
- operation
- input
- output
- duration
- warnings
- errors
