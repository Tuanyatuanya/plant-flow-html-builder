#!/usr/bin/env python3
"""Validate an interactive plant-flow HTML file, optionally against a manifest."""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
from html.parser import HTMLParser
from pathlib import Path


def classes(attrs: dict[str, str]) -> set[str]:
    return set(attrs.get("class", "").split())


class FlowHTMLParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.flow_stack: list[str | None] = []
        self.svg_viewbox: str | None = None
        self.zones: dict[str, dict[str, str]] = {}
        self.routes: dict[str, dict[str, str]] = {}
        self.speed_inputs: dict[str, dict[str, str]] = {}
        self.control_ids: set[str] = set()
        self.text: list[str] = []
        self.svg_images = 0

    def handle_starttag(self, tag: str, raw_attrs: list[tuple[str, str | None]]) -> None:
        attrs = {k: (v or "") for k, v in raw_attrs}
        parent_flow = self.flow_stack[-1] if self.flow_stack else None
        if tag == "g":
            self.flow_stack.append(attrs.get("data-layer") if "flow" in classes(attrs) else parent_flow)
        if tag == "svg" and self.svg_viewbox is None:
            self.svg_viewbox = attrs.get("viewbox")
        if tag in {"rect", "polygon", "path"} and attrs.get("data-zone-id"):
            self.zones[attrs["data-zone-id"]] = attrs
        if tag == "path" and "flow-path" in classes(attrs):
            route_id = attrs.get("data-route-id", f"route-{len(self.routes) + 1}")
            attrs["_layer"] = parent_flow or ""
            self.routes[route_id] = attrs
        if tag == "input" and attrs.get("data-speed-layer"):
            self.speed_inputs[attrs["data-speed-layer"]] = attrs
        if attrs.get("id") in {"play", "labels", "reset"}:
            self.control_ids.add(attrs["id"])
        if tag == "image" and self.flow_stack:
            self.svg_images += 1

    def handle_endtag(self, tag: str) -> None:
        if tag == "g" and self.flow_stack:
            self.flow_stack.pop()

    def handle_data(self, data: str) -> None:
        value = " ".join(data.split())
        if value:
            self.text.append(value)


def number(value: str | None) -> float | None:
    try:
        return float(value) if value is not None else None
    except ValueError:
        return None


def parse_waypoints(value: str) -> list[list[float]]:
    result: list[list[float]] = []
    for point in value.split(";"):
        parts = point.split(",")
        if len(parts) != 2:
            return []
        try:
            result.append([float(parts[0]), float(parts[1])])
        except ValueError:
            return []
    return result


def normalized_text(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip().upper()


def validate(html_path: Path, manifest_path: Path | None) -> dict[str, object]:
    parser = FlowHTMLParser()
    parser.feed(html_path.read_text(encoding="utf-8"))
    errors: list[str] = []
    warnings: list[str] = []

    if not parser.svg_viewbox:
        errors.append("Missing SVG viewBox.")
    if not parser.routes:
        errors.append("No .flow-path routes found.")
    if not parser.speed_inputs:
        errors.append("No independent data-speed-layer inputs found.")
    missing_controls = {"play", "labels", "reset"} - parser.control_ids
    if missing_controls:
        errors.append("Missing controls: " + ", ".join(sorted(missing_controls)))
    if parser.svg_images:
        warnings.append("SVG contains an <image>; confirm the screenshot is not replacing native map geometry.")

    manifest = None
    if manifest_path:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        canvas = manifest.get("canvas", {})
        tol_x = float(canvas.get("width", 1000)) * 0.015
        tol_y = float(canvas.get("height", 1000)) * 0.015
        page_text = normalized_text(" ".join(parser.text))

        for zone in manifest.get("zones", []):
            zone_id = zone["id"]
            if normalized_text(zone["label"]) not in page_text:
                errors.append(f"Missing label for zone {zone_id}: {zone['label']}")
            actual = parser.zones.get(zone_id)
            if not actual:
                errors.append(f"Missing data-zone-id={zone_id}")
                continue
            if zone.get("color") and actual.get("fill", "").lower() != zone["color"].lower():
                warnings.append(f"Zone {zone_id} color differs: expected {zone['color']}, got {actual.get('fill')}")
            expected = zone.get("bbox", [])
            if len(expected) == 4 and actual.get("x") is not None:
                observed = [number(actual.get(k)) for k in ("x", "y", "width", "height")]
                for name, got, want, tol in zip(("x", "y", "width", "height"), observed, expected, (tol_x, tol_y, tol_x, tol_y)):
                    if got is None or abs(got - float(want)) > tol:
                        errors.append(f"Zone {zone_id} {name} mismatch: expected {want}, got {got}")

        for flow in manifest.get("flows", []):
            flow_id = flow["id"]
            speed = parser.speed_inputs.get(flow_id)
            if not speed:
                errors.append(f"Missing speed input for flow {flow_id}")
            elif number(speed.get("value")) != float(flow.get("speed", 0)):
                warnings.append(f"Default speed differs for {flow_id}: expected {flow.get('speed')}, got {speed.get('value')}")
            for expected_route in flow.get("routes", []):
                route_id = expected_route["id"]
                actual = parser.routes.get(route_id)
                if not actual:
                    errors.append(f"Missing data-route-id={route_id}")
                    continue
                if actual.get("_layer") != flow_id:
                    errors.append(f"Route {route_id} is in layer {actual.get('_layer')!r}, expected {flow_id!r}")
                if not actual.get("d"):
                    errors.append(f"Route {route_id} has no SVG path geometry")
                if flow.get("color") and actual.get("stroke", "").lower() != flow["color"].lower():
                    errors.append(f"Route {route_id} color mismatch: expected {flow['color']}, got {actual.get('stroke')}")
                if actual.get("data-source") != flow.get("source"):
                    errors.append(f"Route {route_id} source mismatch")
                if actual.get("data-destination") != expected_route.get("destination"):
                    errors.append(f"Route {route_id} destination mismatch")
                expected_points = expected_route.get("waypoints", [])
                actual_points = parse_waypoints(actual.get("data-waypoints", ""))
                if len(actual_points) != len(expected_points):
                    errors.append(f"Route {route_id} waypoint count mismatch")
                else:
                    for index, (got, want) in enumerate(zip(actual_points, expected_points)):
                        if math.dist(got, want) > math.hypot(tol_x, tol_y):
                            errors.append(f"Route {route_id} waypoint {index} mismatch: expected {want}, got {got}")

    return {
        "file": str(html_path),
        "manifest": str(manifest_path) if manifest_path else None,
        "summary": {
            "zones": len(parser.zones),
            "routes": len(parser.routes),
            "speed_inputs": len(parser.speed_inputs),
            "errors": len(errors),
            "warnings": len(warnings),
        },
        "errors": errors,
        "warnings": warnings,
        "passed": not errors,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("html", type=Path)
    ap.add_argument("--manifest", type=Path)
    args = ap.parse_args()
    report = validate(args.html, args.manifest)
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

