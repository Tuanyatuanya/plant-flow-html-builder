# Plant-flow extraction and evaluation specification

## Manifest schema

Create one JSON manifest per source image:

```json
{
  "case_id": "line-assembly-01",
  "title": "Line Assembly 01",
  "canvas": {"width": 1600, "height": 900},
  "zones": [
    {"id": "receiving", "label": "RECEIVING", "bbox": [90, 120, 220, 180], "color": "#dcecff"}
  ],
  "flows": [
    {
      "id": "blue",
      "label": "PRODUCT A",
      "color": "#087fce",
      "source": "receiving",
      "destinations": ["assembly"],
      "speed": 55,
      "routes": [
        {"id": "blue-main", "destination": "assembly", "waypoints": [[310, 210], [470, 210], [470, 520], [900, 520]]}
      ]
    }
  ],
  "evidence": [
    {"field": "flows.blue.direction", "basis": "arrowhead", "confidence": 1.0}
  ]
}
```

Use stable lowercase IDs. Keep visible labels verbatim.

## Geometry extraction

1. Use the image's full pixel dimensions as the coordinate space.
2. Measure the outer edge of each colored or outlined operational area.
3. Preserve gaps, alignments, nesting, and rotations.
4. Represent nonrectangular zones with polygons, but still include a bounding box for scoring.
5. Do not move a zone to create room for controls or routes.
6. Allow a default coordinate tolerance of 1.5% of canvas width/height; tighten it for clean digital references.

## Label extraction

- Preserve capitalization, punctuation, ampersands, abbreviations, and misspellings that are operational names.
- Join visually wrapped lines into one manifest label.
- Mark unreadable text as uncertain; do not replace it with plausible factory terminology.
- Keep user corrections authoritative over OCR or visual inference.

## Route extraction

- Determine direction from, in descending authority: explicit user statement, arrowhead, numbered process order, source/destination wording, then operational inference.
- Ask the user when the first four sources do not establish direction.
- Store waypoints in travel order.
- Preserve visible bends and branches; simplify only redundant collinear points.
- Use orthogonal segments when the reference is orthogonal.
- Treat zones as obstacles expanded by 6–12 source pixels.
- Route through corridors. If two layers share a corridor, allocate parallel lanes with 8–14 pixels of separation.
- Never reverse SVG path order merely to place a label or make animation easier.

## HTML metadata contract

Add metadata that makes the output machine-checkable:

```html
<rect data-zone-id="receiving" x="90" y="120" width="220" height="180"></rect>
<path
  class="flow-path"
  data-route-id="blue-main"
  data-source="receiving"
  data-destination="assembly"
  data-waypoints="310,210;470,210;470,520;900,520"
  d="M310 210H470V520H900">
</path>
<input data-speed-layer="blue" type="number" value="55">
```

Animate positive progress from path length `0` toward `getTotalLength()`. If a route must visually run backward, reverse its `d` and `data-waypoints`; never use a negative animation speed to hide incorrect metadata.

## Visual system

- Let the plant canvas occupy roughly 75–85% of a desktop viewport.
- Use a compact control rail and readable high-contrast text.
- Draw path casing at 5–7 px and the colored path at 2–3.5 px.
- Draw moving dots at 3–5 px radius with a thin white stroke.
- Use each source route color consistently in the path, dot, filter, and speed input.
- Keep unrelated flows visible but clearly separated.
- Avoid decorative metrics, fake timestamps, and invented plant information.

## Accuracy scoring

Score 100 points:

| Category | Points | Full-credit requirement |
|---|---:|---|
| Zone geometry | 30 | IDs, positions, sizes, adjacency, and orientation match |
| Labels | 15 | Exact visible wording and zone association |
| Route geometry | 20 | Correct corridors, bends, branches, and lane separation |
| Direction | 15 | Every route starts at source and terminates at destination |
| Controls | 10 | Independent speeds, filters, Pause, Labels, Reset |
| Visual clarity | 5 | Thin routes, small legible dots, dominant map |
| Responsive/technical | 5 | Narrow layout works and console is clean |

Treat any rearranged major zone or reversed primary route as a critical failure regardless of total score.

