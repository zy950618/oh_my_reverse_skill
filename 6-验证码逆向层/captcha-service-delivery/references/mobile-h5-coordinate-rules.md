# Mobile H5 coordinate rules

Version: 0.1.0

Mobile H5 CAPTCHA action replay fails when image pixels, CSS pixels, viewport
coordinates, and transformed element coordinates are mixed. Every action
manifest must carry enough geometry to reconstruct the intended tap or drag.

## Coordinate spaces

| space | origin | unit | use |
|---|---|---|---|
| `viewport_css_px` | top-left viewport | CSS px | Playwright or browser pointer actions |
| `element_css_px` | target element bounding box | CSS px | widget-relative labels |
| `image_px` | image bitmap | image px | model predictions from raw image |
| `normalized` | top-left sample | ratio 0..1 | portable labels |

## Transform requirements

```json
{
  "mobile_h5_transform": {
    "input_space": "image_px",
    "output_space": "viewport_css_px",
    "device_pixel_ratio": 3.0,
    "image_size_px": {"width": 732, "height": 480},
    "element_bbox_css_px": {"x": 12, "y": 220, "width": 366, "height": 240},
    "scroll_offset_css_px": {"x": 0, "y": 0},
    "safe_area_css_px": {"top": 0, "right": 0, "bottom": 0, "left": 0}
  }
}
```

## Rules

- Convert image-pixel predictions to CSS pixels before browser replay.
- Record viewport size, device pixel ratio, element bounding box, scroll offset,
  and safe-area offsets.
- Clamp final coordinates to the visible target element unless the challenge
  explicitly requires an off-element release.
- Do not infer DPR from screenshots when the browser can report it.
