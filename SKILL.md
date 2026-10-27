---
name: plant-flow-html-builder
description: Convert factory floor-plan images, PowerPoint/PDF screenshots, scans, or annotated layout references into self-contained interactive HTML/SVG material-flow visualizations. Use when an AI coding agent must preserve plant-zone geometry, transcribe labels, reproduce colored flow paths, animate source-to-destination direction with dots, add independent speed controls, or validate generated HTML against a ground-truth plant-flow manifest.
---

# Plant Flow HTML Builder

Create a faithful, testable HTML visualization from a static plant layout. Treat geometry and flow direction as data, not decoration.

## Non-negotiable rules

1. Preserve every identified zone's relative position, size, adjacency, and orientation. Never rearrange the plant to improve aesthetics.
2. Transcribe visible labels verbatim. Do not silently correct operational names such as `STAKING AREA`.
3. Encode each route from source to destination. Moving dots must advance in the same order as the route's SVG path or waypoint list.
4. Route lines through visible aisles or around expanded zone boundaries. Do not cross a production zone unless the source image clearly does.
5. Offset different-colored routes into separate lanes. Do not stack them on one path.
6. Give every flow layer its own numeric speed input. Never share one speed value across layers.
7. Build the layout as native SVG/HTML. Do not use the reference screenshot as the interactive map background.
8. Keep all UI copy in the user's requested language. Preserve units and terminology.

Read [references/specification.md](references/specification.md) before extracting geometry, routing flows, or scoring fidelity.

## Workflow

### 1. Inspect inputs

- Inspect every supplied image at original detail.
- Inspect an existing HTML file when the user provides one; reuse its interaction logic without inheriting inaccurate geometry.
- Identify the canvas boundary, structural zones, labels, route colors, arrowheads, docks, and destination areas.
- If a route direction is not supported by an arrowhead, a start/end annotation, or explicit user text, mark it uncertain and ask one focused question before finalizing. Do not guess silently.

### 2. Create the ground-truth manifest first

- Use the schema in [references/specification.md](references/specification.md).
- Normalize coordinates to the source image's own canvas.
- Record every zone as `id`, `label`, and `[x, y, width, height]`.
- Record every route as ordered waypoints from source to destination.
- Record evidence and confidence for any inferred label or direction.
- Resolve contradictions before writing the HTML.

### 3. Build from the reusable template

- Copy [assets/interactive-flow-template.html](assets/interactive-flow-template.html) into the user's requested output location.
- Replace the sample zones, labels, routes, viewBox, colors, and copy with manifest data.
- Add `data-zone-id` to each zone shape.
- Add `data-route-id`, `data-source`, `data-destination`, and ordered `data-waypoints` to each route path.
- Keep the plant map visually dominant. Put controls in a compact side rail or bottom panel without shrinking the map unnecessarily.
- Use thin colored paths with a white casing and small moving dots.
- Use `prefers-reduced-motion` to hide or stop decorative animation.

Use `frontend-design` only for visual polish after geometry is locked. Use `frontend-app-builder` browser QA conventions when that skill is available. Neither design pass may move zones or reverse routes.

### 4. Verify direction and interaction

- Confirm each SVG path starts at the manifest source and ends at its destination.
- Observe representative dots at two times; verify progress increases along the ordered path.
- Test all layer filters, every speed input, Pause/Play, Labels, and Reset.
- Confirm Labels hides text only, not zones or routes.
- Check desktop and narrow layouts and inspect browser console errors.

### 5. Validate and report

Run:

```bash
python3 scripts/validate_flow_html.py OUTPUT.html --manifest ground-truth.json
```

Fix every error. Treat warnings as review items rather than automatic failures.

Report:

- output HTML path;
- manifest path;
- uncertain or user-confirmed interpretations;
- desktop and narrow viewport results;
- zone, label, route, direction, control, and console validation results.

## Acceptance threshold

Do not call an output complete unless:

- all required labels are present;
- all zone boxes are within the manifest tolerance;
- all route sources, destinations, colors, and ordered waypoints match;
- route layers do not overlap one another;
- independent speed inputs work;
- no critical browser-console errors remain.

