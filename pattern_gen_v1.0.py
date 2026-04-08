# -*- coding: utf-8 -*-
import math
import random
from datetime import datetime
import tkinter as tk
from tkinter import messagebox, filedialog
import threading

# -----------------------------------------
#  COLOR PALETTES
# -----------------------------------------
PALETTES = [
    {"name": "Forest Ember",   "colors": ["#014040", "#02735E", "#03A678", "#F27405", "#731702"]},
    {"name": "Teal Dusk",      "colors": ["#025159", "#3E848C", "#7AB8BF", "#C4EEF2", "#A67458"]},
    {"name": "Iron Rose",      "colors": ["#BD2A2E", "#3B3936", "#B2BEBF", "#889C9B", "#486966"]},
    {"name": "Ocean Spark",    "colors": ["#026E81", "#00ABBD", "#0099DD", "#FF9933", "#A1C7E0"]},
    {"name": "Deep Teal",      "colors": ["#593954", "#013440", "#026873", "#038C8C", "#038C7F"]},
    {"name": "Emerald Dark",   "colors": ["#034159", "#025951", "#02735E", "#038C3E", "#0CF25D"]},
    {"name": "Greyscale",      "colors": ["#F2F2F2", "#D9D9D9", "#8C8C8C", "#595959", "#404040"]},
    {"name": "Solar Flare",    "colors": ["#035AA6", "#F2BB16", "#F2A71B", "#F2921D", "#D94141"]},
    {"name": "Blueprint",      "colors": ["#033E8C", "#034C8C", "#03588C", "#03658C", "#F2E6D8"]},
    {"name": "Sand Dune",      "colors": ["#F2CA52", "#F2D57E", "#D9A23D", "#F2D399", "#F2EBDF"]},
    {"name": "Amber Fire",     "colors": ["#F2B705", "#F29F05", "#F28705", "#F27405", "#732C02"]},
    {"name": "Midnight",       "colors": ["#011126", "#0F1D26", "#F2F0C9", "#F2E2C4", "#BFB49F"]},
]

MONO_PALETTE = {"name": "Monochrome", "colors": ["#CCCCCC", "#999999", "#666666", "#444444", "#222222"]}

# -----------------------------------------
#  THEME CONSTANTS
# -----------------------------------------
BG        = "#0E0F11"
BG2       = "#161719"
BG3       = "#1E2023"
BORDER    = "#2A2D32"
ACCENT    = "#F27405"
ACCENT2   = "#03A678"
FG        = "#E8E9EA"
FG2       = "#8A8D92"
FG3       = "#555860"
FONT_MONO = ("Courier New", 10)
FONT_UI   = ("Courier New", 9)
FONT_LBL  = ("Courier New", 9, "bold")
FONT_HEAD = ("Courier New", 13, "bold")
FONT_SUB  = ("Courier New", 8)

# -----------------------------------------
#  SVG GENERATOR  (pure, no GUI deps)
# -----------------------------------------
def _make_shape_svg(shape, cx, cy, radius, color, stroke_width="1", opacity="1") -> str:
    """Return an SVG element string for the given shape."""
    if shape == "circle":
        return (f'<circle cx="{cx:.2f}" cy="{cy:.2f}" r="{radius:.2f}" fill="none" '
                f'stroke="{color}" stroke-width="{stroke_width}" '
                f'stroke-opacity="{opacity}"/>\n')
    elif shape == "square":
        half = radius
        x0, y0 = cx - half, cy - half
        side   = radius * 2
        return (f'<rect x="{x0:.2f}" y="{y0:.2f}" width="{side:.2f}" height="{side:.2f}" '
                f'fill="none" stroke="{color}" stroke-width="{stroke_width}" '
                f'stroke-opacity="{opacity}"/>\n')
    else:  # hexagon
        pts = []
        for n in range(6):
            angle = math.pi / 6 + n * math.pi / 3
            pts.append(f"{cx + radius * math.cos(angle):.2f},{cy + radius * math.sin(angle):.2f}")
        return (f'<polygon points="{" ".join(pts)}" fill="none" '
                f'stroke="{color}" stroke-width="{stroke_width}" '
                f'stroke-opacity="{opacity}"/>\n')


def generate_hex_svg(params, output_file: str) -> str:
    """
    Generate an SVG pattern of hexagons, circles, or squares and write it to output_file.

    Reads pattern parameters from the params dict:
      width, height, pattern ('grid'|'helix'|'random'),
      shape ('hexagon'|'circle'|'square'),
      count, hex_size, spacing, palette (list of hex color strings),
      inverse_thickness (bool).

    Writes the SVG to output_file and returns the path.
    Raises ValueError for invalid canvas dimensions.
    """
    width        = params["width"]
    height       = params["height"]
    pattern_type = params["pattern"]
    shape        = params.get("shape", "hexagon")
    count        = params["count"]
    hex_size     = params["hex_size"]
    spacing      = params["spacing"]
    palette      = params["palette"]
    inverse      = params["inverse_thickness"]

    # validate canvas dimensions
    if width <= 0 or height <= 0:
        raise ValueError(f"Canvas dimensions must be positive (got {width}x{height}).")

    elements   = []
    amplitude  = height * 0.25
    frequency  = 2 * math.pi / width * 3

    # -- GRID ------------------------------
    if pattern_type == "grid":
        radius = hex_size
        gap    = max(-radius * 0.9, spacing)

        if shape == "hexagon":
            horiz_spacing = math.sqrt(3) * radius + gap
            vert_spacing  = 1.5 * radius + gap * 0.5
            row, y = 0, radius
            while y - radius < height:
                x_offset = 0 if row % 2 == 0 else horiz_spacing / 2
                x = radius + x_offset
                while x - radius < width:
                    color = random.choice(palette)
                    elements.append(_make_shape_svg(shape, x, y, radius, color))
                    x += horiz_spacing
                y += vert_spacing
                row += 1
        else:  # circle or square — same rectilinear grid layout
            step = radius * 2 + gap
            y = radius
            while y - radius < height:
                x = radius
                while x - radius < width:
                    color = random.choice(palette)
                    elements.append(_make_shape_svg(shape, x, y, radius, color))
                    x += step
                y += step

    # -- HELIX / RANDOM --------------------
    else:
        min_r   = width * 0.005
        max_r   = width * 0.04
        r_range = max_r - min_r or 1.0

        for _ in range(count):
            radius = random.uniform(min_r, max_r)
            cx     = random.uniform(radius, width - radius)

            if pattern_type == "helix":
                strand = random.choice([0, math.pi])
                cy     = (height / 2) + math.sin(cx * frequency + strand) * amplitude
                cy     = max(radius, min(height - radius, cy))
            else:
                cy = random.uniform(radius, height - radius)

            norm         = (radius - min_r) / r_range
            stroke_width = f"{0.5 + ((1 - norm) if inverse else norm) * 4:.2f}"
            opacity      = f"{max(0.2, 0.9 - norm):.2f}"
            color        = random.choice(palette)

            elements.append(_make_shape_svg(shape, cx, cy, radius, color, stroke_width, opacity))

    svg = (f'<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg">\n'
           + "".join(elements)
           + "</svg>")

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(svg)

    return output_file


# -----------------------------------------
#  CUSTOM WIDGETS
# -----------------------------------------
class DarkEntry(tk.Entry):
    def __init__(self, parent, default="", width=12, **kw):
        super().__init__(
            parent,
            bg=BG3, fg=FG, insertbackground=ACCENT,
            relief="flat", bd=0,
            font=FONT_MONO, width=width,
            highlightthickness=1,
            highlightbackground=BORDER,
            highlightcolor=ACCENT,
            **kw
        )
        self.insert(0, default)

    def get_int(self, fallback=0):
        try:
            return int(self.get())
        except ValueError:
            return fallback

    def get_float(self, fallback=0.0):
        try:
            return float(self.get())
        except ValueError:
            return fallback


class SectionFrame(tk.Frame):
    """
    Bordered section widget.  The public .outer attribute is the border
    wrapper frame — use it (not self) for pack_forget/pack when showing
    or hiding entire sections.
    """
    def __init__(self, parent, label, **kw):
        # FIX: store outer so callers can show/hide the border wrapper correctly
        self.outer = tk.Frame(parent, bg=BORDER, padx=1, pady=1)
        self.outer.pack(fill="x", padx=16, pady=(0, 10))
        super().__init__(self.outer, bg=BG2, **kw)
        self.pack(fill="x")

        header = tk.Frame(self, bg=BG3)
        header.pack(fill="x")
        tk.Label(header, text=f"  {label}  ",
                 bg=BG3, fg=FG, font=FONT_LBL,
                 anchor="w", pady=6).pack(side="left")

        self.body = tk.Frame(self, bg=BG2)
        self.body.pack(fill="x", padx=10, pady=8)


class PaletteButton(tk.Frame):
    """Clickable palette swatch row."""
    def __init__(self, parent, palette, on_select, **kw):
        super().__init__(parent, bg=BG3, cursor="hand2", **kw)
        self.palette   = palette
        self.on_select = on_select
        self._selected = False
        self._build()
        self.bind("<Button-1>", self._click)

    def _build(self):
        name_lbl = tk.Label(self, text=self.palette["name"],
                            bg=BG3, fg=FG2, font=FONT_SUB, width=13, anchor="w")
        name_lbl.pack(side="left", padx=(8, 4))
        name_lbl.bind("<Button-1>", self._click)

        swatch_frame = tk.Frame(self, bg=BG3)
        swatch_frame.pack(side="left", padx=(0, 8), pady=4)
        swatch_frame.bind("<Button-1>", self._click)

        for color in self.palette["colors"]:
            lbl = tk.Label(swatch_frame, bg=color, width=3, height=1, relief="flat")
            lbl.pack(side="left", padx=1)
            lbl.bind("<Button-1>", self._click)

    def set_selected(self, val: bool):
        self._selected = val
        bg = "#252830" if val else BG3
        hl = ACCENT if val else BG3
        self.config(bg=bg, highlightbackground=hl,
                    highlightthickness=1 if val else 0)
        for child in self.winfo_children():
            try:
                child.config(bg=bg)
            except Exception:
                pass

    def set_enabled(self, enabled: bool):
        """Enable or disable the palette button visually and functionally."""
        self._enabled = enabled
        # Dim the label text when disabled
        fg_color = FG2 if enabled else FG3
        for child in self.winfo_children():
            try:
                child.config(fg=fg_color)
            except Exception:
                pass
        # Update cursor
        cursor = "hand2" if enabled else "arrow"
        self.config(cursor=cursor)
        for child in self.winfo_children():
            try:
                child.config(cursor=cursor)
            except Exception:
                pass

    def _click(self, _=None):
        if getattr(self, "_enabled", True):
            self.on_select(self)


# -----------------------------------------
#  MAIN APP
# -----------------------------------------
class HexApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("SVG PATTERN GENERATOR")
        self.configure(bg=BG)
        self.resizable(True, True)

        self._selected_palette_data = PALETTES[0]["colors"]
        self._color_mode            = tk.StringVar(value="color")
        self._pattern_var           = tk.StringVar(value="helix")
        self._shape_var             = tk.StringVar(value="hexagon")
        self._inverse_var           = tk.BooleanVar(value=True)
        self._palette_btns          = []

        # FIX: will be set to a direct reference in _build_ui
        self._options_section_outer = None

        self._build_ui()
        self._on_pattern_change()
        self._on_color_mode_change()

        self.update_idletasks()
        self.minsize(self.winfo_width(), self.winfo_height())
        # Trigger first preview after layout is complete
        self.after(100, self._update_preview)

    # -- UI BUILD --------------------------
    def _build_ui(self):
        # ── Header (full width) ──────────────────────────────────────────────
        hdr = tk.Frame(self, bg=BG)
        hdr.pack(fill="x", padx=16, pady=(18, 14))
        tk.Label(hdr, text="SVG PATTERN", bg=BG, fg=ACCENT,
                 font=("Courier New", 15, "bold")).pack(side="left")
        tk.Label(hdr, text="  GENERATOR", bg=BG, fg=FG2,
                 font=("Courier New", 15)).pack(side="left")
        tk.Frame(self, bg=ACCENT, height=1).pack(fill="x", padx=16, pady=(0, 14))

        # ── Two-column body ──────────────────────────────────────────────────
        body = tk.Frame(self, bg=BG)
        body.pack(fill="both", expand=True)

        # Left column — controls (fixed width, scrolls naturally)
        left = tk.Frame(body, bg=BG)
        left.pack(side="left", fill="y", anchor="nw")

        # Right column — preview + generate
        right = tk.Frame(body, bg=BG)
        right.pack(side="left", fill="both", expand=True, padx=(0, 16), pady=(0, 16))

        # thin vertical separator
        tk.Frame(body, bg=BORDER, width=1).place(relx=0, rely=0, relheight=1)

        # ── Helper: SectionFrame into a specific parent ──────────────────────
        def left_section(title):
            return SectionFrame(left, title)

        # ── PATTERN TYPE ────────────────────────────────────────────────────
        sec = left_section("PATTERN TYPE")
        f   = sec.body
        for val, lbl in [("helix", "HELIX"), ("random", "RANDOM"), ("grid", "GRID")]:
            tk.Radiobutton(
                f, text=lbl, variable=self._pattern_var, value=val,
                bg=BG2, fg=FG, selectcolor=BG3,
                activebackground=BG2, activeforeground=ACCENT,
                font=FONT_LBL, indicatoron=0,
                relief="flat", bd=0, padx=12, pady=4,
                highlightthickness=1, highlightbackground=BORDER,
                highlightcolor=ACCENT, cursor="hand2",
                command=self._on_pattern_change
            ).pack(side="left", padx=(0, 6))

        # ── SHAPE TYPE ──────────────────────────────────────────────────────
        sec = left_section("SHAPE TYPE")
        f   = sec.body
        for val, lbl in [("hexagon", "HEXAGON"), ("circle", "CIRCLE"), ("square", "SQUARE")]:
            tk.Radiobutton(
                f, text=lbl, variable=self._shape_var, value=val,
                bg=BG2, fg=FG, selectcolor=BG3,
                activebackground=BG2, activeforeground=ACCENT2,
                font=FONT_LBL, indicatoron=0,
                relief="flat", bd=0, padx=12, pady=4,
                highlightthickness=1, highlightbackground=BORDER,
                highlightcolor=ACCENT2, cursor="hand2",
                command=self._on_shape_change,
            ).pack(side="left", padx=(0, 6))

        # ── CANVAS SIZE ─────────────────────────────────────────────────────
        sec = left_section("CANVAS SIZE")
        f   = sec.body
        for col, label, attr, default in [
            (0, "WIDTH",  "width_entry",  "1920"),
            (2, "HEIGHT", "height_entry", "600"),
        ]:
            tk.Label(f, text=label, bg=BG2, fg=FG3, font=FONT_LBL).grid(
                row=0, column=col, sticky="w", padx=(0, 6))
            e = DarkEntry(f, default=default, width=8)
            e.grid(row=1, column=col, sticky="w", padx=(0, 20), ipady=4)
            setattr(self, attr, e)

        # ── ELEMENT COUNT (helix / random) ───────────────────────────────────
        sec = left_section("ELEMENT COUNT  (helix / random)")
        self._count_section = sec
        f = sec.body
        self.count_entry = DarkEntry(f, default="250", width=8)
        self.count_entry.pack(side="left", ipady=4)
        self._count_unit_label = tk.Label(f, text="hexagons", bg=BG2, fg=FG3, font=FONT_SUB)
        self._count_unit_label.pack(side="left", padx=8)

        # ── GRID SETTINGS ───────────────────────────────────────────────────
        sec = left_section("GRID SETTINGS  (grid only)")
        self._grid_section = sec
        f = sec.body
        for col, label, attr, default, unit in [
            (0, "HEX SIZE", "size_entry",   "20", "px"),
            (3, "SPACING",  "spacing_entry", "0", "px"),
        ]:
            tk.Label(f, text=label, bg=BG2, fg=FG3, font=FONT_LBL).grid(
                row=0, column=col, sticky="w")
            e = DarkEntry(f, default=default, width=6)
            e.grid(row=1, column=col, sticky="w", padx=(0, 4), ipady=4)
            tk.Label(f, text=unit, bg=BG2, fg=FG3, font=FONT_SUB).grid(
                row=1, column=col + 1, sticky="w", padx=(0, 20))
            setattr(self, attr, e)

        # ── OPTIONS ─────────────────────────────────────────────────────────
        sec = left_section("OPTIONS")
        self._options_section_outer = sec.outer
        f   = sec.body
        self._inv_btn = tk.Checkbutton(
            f, text="INVERSE STROKE  (small → thick)",
            variable=self._inverse_var,
            bg=BG2, fg=FG2, selectcolor=BG3,
            activebackground=BG2, activeforeground=FG,
            font=FONT_UI, cursor="hand2"
        )
        self._inv_btn.pack(anchor="w")

        # ── COLOR MODE ──────────────────────────────────────────────────────
        sec = left_section("COLOR MODE")
        f   = sec.body
        mode_frame = tk.Frame(f, bg=BG2)
        mode_frame.pack(anchor="w", pady=(0, 8))
        for val, lbl in [("color", "COLOR"), ("mono", "MONO")]:
            tk.Radiobutton(
                mode_frame, text=lbl, variable=self._color_mode, value=val,
                bg=BG2, fg=FG, selectcolor=BG3,
                activebackground=BG2, activeforeground=ACCENT2,
                font=FONT_LBL, indicatoron=0,
                relief="flat", bd=0, padx=12, pady=4,
                highlightthickness=1, highlightbackground=BORDER,
                highlightcolor=ACCENT2, cursor="hand2",
                command=self._on_color_mode_change
            ).pack(side="left", padx=(0, 6))

        self._palette_container = tk.Frame(f, bg=BG2)
        self._palette_container.pack(fill="x")
        cols = 3
        for i, p in enumerate(PALETTES):
            btn = PaletteButton(self._palette_container, p, self._on_palette_select)
            btn.grid(row=i // cols, column=i % cols, padx=4, pady=3, sticky="w")
            self._palette_btns.append(btn)
        self._palette_btns[0].set_selected(True)

        # ════════════════════════════════════════════════════════════════════
        # RIGHT PANEL — preview canvas + generate
        # ════════════════════════════════════════════════════════════════════

        # Section header (manual, not SectionFrame — right panel is freeform)
        preview_header = tk.Frame(right, bg=BG3)
        preview_header.pack(fill="x", padx=0, pady=(0, 0))
        tk.Label(preview_header, text="  PREVIEW  ", bg=BG3, fg=FG,
                 font=FONT_LBL, anchor="w", pady=6).pack(side="left")
        self._preview_refresh_btn = tk.Button(
            preview_header, text="↻  REFRESH",
            bg=BG3, fg=FG3,
            activebackground=BG3, activeforeground=FG2,
            font=FONT_SUB, relief="flat", bd=0,
            padx=8, pady=6, cursor="hand2",
            command=self._update_preview
        )
        self._preview_refresh_btn.pack(side="right")

        # Border wrapper around canvas
        canvas_border = tk.Frame(right, bg=BORDER, padx=1, pady=1)
        canvas_border.pack(fill="both", expand=True, pady=(0, 10))

        canvas_inner = tk.Frame(canvas_border, bg=BG2)
        canvas_inner.pack(fill="both", expand=True)

        self._preview_canvas = tk.Canvas(
            canvas_inner,
            bg="white", highlightthickness=0, bd=0
        )
        self._preview_canvas.pack(fill="both", expand=True, padx=12, pady=12)

        # Dimension label
        self._preview_dim_var = tk.StringVar(value="")
        tk.Label(right, textvariable=self._preview_dim_var,
                 bg=BG, fg=FG3, font=FONT_SUB, anchor="center").pack(fill="x", pady=(0, 10))

        # ── Divider ─────────────────────────────────────────────────────────
        tk.Frame(right, bg=BORDER, height=1).pack(fill="x", pady=(0, 10))

        # ── GENERATE button ─────────────────────────────────────────────────
        self._gen_btn = tk.Button(
            right, text="✦  GENERATE SVG",
            bg=ACCENT, fg="#000000",
            activebackground="#D96504", activeforeground="#000000",
            font=("Courier New", 10, "bold"),
            relief="flat", bd=0, padx=20, pady=12,
            cursor="hand2", command=self._run
        )
        self._gen_btn.pack(fill="x")

        # ── Status bar ───────────────────────────────────────────────────────
        self._status_var = tk.StringVar(value="READY")
        self._status_label = tk.Label(
            right, textvariable=self._status_var,
            bg=BG, fg=FG2, font=FONT_UI, anchor="w"
        )
        self._status_label.pack(fill="x", pady=(8, 0))

    # -- EVENT HANDLERS --------------------
    def _build_preview_params(self) -> tuple:
        """
        Return (params, scale, pw, ph).
        Generates SVG at full canvas dimensions; scales coords to fit the
        preview canvas widget's actual rendered size.
        """
        full_w = max(1, self.width_entry.get_int(1920))
        full_h = max(1, self.height_entry.get_int(600))

        # Use the actual rendered widget size; fall back to 300×180 before first draw
        self._preview_canvas.update_idletasks()
        avail_w = self._preview_canvas.winfo_width()  or 300
        avail_h = self._preview_canvas.winfo_height() or 180

        scale = min(avail_w / full_w, avail_h / full_h)
        pw    = max(4, round(full_w * scale))
        ph    = max(4, round(full_h * scale))

        palette = (
            self._selected_palette_data
            if self._color_mode.get() == "color"
            else MONO_PALETTE["colors"]
        )

        params = {
            "pattern":           self._pattern_var.get(),
            "shape":             self._shape_var.get(),
            "width":             full_w,
            "height":            full_h,
            "count":             max(1, min(400, self.count_entry.get_int(250))),
            "hex_size":          self.size_entry.get_float(20),
            "spacing":           self.spacing_entry.get_float(0),
            "palette":           palette,
            "inverse_thickness": self._inverse_var.get(),
        }
        return params, scale, pw, ph

    def _update_preview(self):
        """Generate SVG at full size, scale coords down, draw on white canvas."""
        try:
            import tempfile, os
            params, scale, pw, ph = self._build_preview_params()

            full_w, full_h = params["width"], params["height"]
            ratio_str = f"1:{1/scale:.1f}" if scale < 1 else f"{scale:.1f}:1"
            self._preview_dim_var.set(
                f"{full_w} × {full_h} px  ·  preview {pw} × {ph} px  ({ratio_str})"
            )

            with tempfile.NamedTemporaryFile(suffix=".svg", delete=False, mode="w",
                                             encoding="utf-8") as tmp:
                tmp_path = tmp.name
            generate_hex_svg(params, tmp_path)
            with open(tmp_path, encoding="utf-8") as f:
                svg_text = f.read()
            os.unlink(tmp_path)
            self._render_svg_on_canvas(svg_text, scale, pw, ph)
        except Exception:
            pass  # preview is best-effort; never crash the app

    def _render_svg_on_canvas(self, svg_text: str, scale: float, pw: int, ph: int):
        """Parse SVG elements, scale coords, center in the canvas, draw on white."""
        import re
        c = self._preview_canvas
        c.delete("all")
        c.config(bg="white")

        # Center offset so the scaled SVG sits in the middle of the canvas widget
        cw = c.winfo_width()  or pw
        ch = c.winfo_height() or ph
        ox = (cw - pw) / 2
        oy = (ch - ph) / 2

        # Draw white rect exactly the size of the SVG (canvas bg may be larger)
        c.create_rectangle(ox, oy, ox + pw, oy + ph, fill="white", outline=BORDER, width=1)

        def sc(v):
            return float(v) * scale

        # Draw polygon (hexagon)
        for m in re.finditer(
            r'<polygon points="([^"]+)"[^>]*stroke="([^"]+)"[^>]*stroke-width="([^"]+)"'
            r'(?:[^>]*stroke-opacity="([^"]+)")?', svg_text
        ):
            raw_pts, color, sw_str = m.group(1), m.group(2), m.group(3)
            try:
                flat  = [float(v) for pair in raw_pts.split() for v in pair.split(",")]
                pts   = [sc(flat[i]) + (ox if i % 2 == 0 else oy) for i in range(len(flat))]
                w_val = max(1, round(float(sw_str) * scale))
                c.create_polygon(pts, outline=color, fill="", width=w_val)
            except Exception:
                pass

        # Draw circle
        for m in re.finditer(
            r'<circle cx="([^"]+)" cy="([^"]+)" r="([^"]+)"[^>]*stroke="([^"]+)"'
            r'[^>]*stroke-width="([^"]+)"', svg_text
        ):
            try:
                cx   = sc(m.group(1)) + ox
                cy   = sc(m.group(2)) + oy
                r    = sc(m.group(3))
                color = m.group(4)
                w_val = max(1, round(float(m.group(5)) * scale))
                c.create_oval(cx - r, cy - r, cx + r, cy + r,
                              outline=color, fill="", width=w_val)
            except Exception:
                pass

        # Draw rect (square)
        for m in re.finditer(
            r'<rect x="([^"]+)" y="([^"]+)" width="([^"]+)" height="([^"]+)"'
            r'[^>]*stroke="([^"]+)"[^>]*stroke-width="([^"]+)"', svg_text
        ):
            try:
                x0   = sc(m.group(1)) + ox
                y0   = sc(m.group(2)) + oy
                rw   = sc(m.group(3))
                rh   = sc(m.group(4))
                color = m.group(5)
                w_val = max(1, round(float(m.group(6)) * scale))
                c.create_rectangle(x0, y0, x0 + rw, y0 + rh,
                                   outline=color, fill="", width=w_val)
            except Exception:
                pass

    def _on_shape_change(self):
        """Update the count unit label to match the selected shape."""
        shape = self._shape_var.get()
        label = {"hexagon": "hexagons", "circle": "circles", "square": "squares"}.get(shape, "elements")
        self._count_unit_label.config(text=label)
        self._update_preview()

    def _on_pattern_change(self):
        if self._options_section_outer is None:
            return  # called before UI is fully built
        is_grid = self._pattern_var.get() == "grid"
        if is_grid:
            self._count_section.outer.pack_forget()
            self._grid_section.outer.pack_forget()
            self._grid_section.outer.pack(
                fill="x", padx=16, pady=(0, 10),
                before=self._options_section_outer
            )
        else:
            self._grid_section.outer.pack_forget()
            self._count_section.outer.pack_forget()
            self._count_section.outer.pack(
                fill="x", padx=16, pady=(0, 10),
                before=self._options_section_outer
            )
        self._update_preview()

    def _on_color_mode_change(self):
        is_color = self._color_mode.get() == "color"
        for btn in self._palette_btns:
            btn.set_enabled(is_color)
        self._update_preview()

    def _on_palette_select(self, clicked_btn):
        if self._color_mode.get() != "color":
            return
        for btn in self._palette_btns:
            btn.set_selected(btn is clicked_btn)
        self._selected_palette_data = clicked_btn.palette["colors"]
        self._update_preview()

    # -- GENERATE -------------------------
    def _run(self):
        try:
            width  = self.width_entry.get_int(1920)
            height = self.height_entry.get_int(600)

            # FIX: validate dimensions before spawning thread
            if width <= 0 or height <= 0:
                messagebox.showerror(
                    "Input Error",
                    f"Width and height must be positive integers (got {width}×{height})."
                )
                return

            max_hex_size = min(width, height) / 2
            raw_hex_size = self.size_entry.get_float(20)
            hex_size     = min(raw_hex_size, max_hex_size)
            if hex_size != raw_hex_size:
                # Update the entry so the user sees the actual value used
                self.size_entry.delete(0, tk.END)
                self.size_entry.insert(0, f"{hex_size:.1f}")
                messagebox.showwarning(
                    "Hex Size Clamped",
                    f"Hex size clamped from {raw_hex_size:.1f} to {hex_size:.1f} px\n"
                    f"(max is half the shortest canvas dimension)."
                )

            raw_count = self.count_entry.get_int(250)
            count     = max(1, raw_count)
            if count != raw_count:
                self.count_entry.delete(0, tk.END)
                self.count_entry.insert(0, "1")

            params = {
                "pattern":           self._pattern_var.get(),
                "shape":             self._shape_var.get(),
                "width":             width,
                "height":            height,
                "count":             count,
                "hex_size":          hex_size,
                "spacing":           self.spacing_entry.get_float(0),
                "inverse_thickness": self._inverse_var.get(),
                "palette": (
                    self._selected_palette_data
                    if self._color_mode.get() == "color"
                    else MONO_PALETTE["colors"]
                ),
            }
        except Exception as e:
            messagebox.showerror("Input Error", str(e))
            return

        # FIX: ask the user where to save the file
        timestamp    = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_name = f"{params['shape']}_{params['pattern']}_{timestamp}.svg"
        output_file  = filedialog.asksaveasfilename(
            defaultextension=".svg",
            filetypes=[("SVG files", "*.svg"), ("All files", "*.*")],
            initialfile=default_name,
            title="Save SVG as…"
        )
        if not output_file:
            return  # user cancelled

        self._gen_btn.config(state="disabled", text="  GENERATING...")
        self._status_var.set("working...")
        # FIX: use update_idletasks instead of update to avoid re-entrant events
        self.update_idletasks()

        def worker():
            try:
                filename = generate_hex_svg(params, output_file)
                self.after(0, lambda: self._done(filename))
            except Exception as exc:
                self.after(0, lambda: self._error(exc))

        threading.Thread(target=worker, daemon=True).start()

    def _done(self, filename):
        self._gen_btn.config(state="normal", text="✦  GENERATE SVG")
        self._status_var.set(f"✓  saved → {filename}")
        self._status_label.config(fg=ACCENT2)

    def _error(self, exc):
        self._gen_btn.config(state="normal", text="✦  GENERATE SVG")
        self._status_var.set(f"✗  error: {exc}")
        self._status_label.config(fg="#D94141")
        messagebox.showerror("Generation Error", str(exc))


# -----------------------------------------
if __name__ == "__main__":
    app = HexApp()
    app.mainloop()