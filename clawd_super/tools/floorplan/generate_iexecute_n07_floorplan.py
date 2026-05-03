from __future__ import annotations

import json
import math
import re
from dataclasses import dataclass
from pathlib import Path
from xml.sax.saxutils import escape

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(r"D:\ai_brain\jiutian\clawd_super")
OUT_DIR = ROOT / "docs" / "assets" / "floorplan"
DOC_DIR = ROOT / "docs" / "floorplan"

N07_STDCELL_LEF = Path(
    r"C:\Users\yh-PC-003\Desktop\codex\tmp_n07_link\library\TSMCHOME\digital"
    r"\Back_End\lef\tcbn07_bwph240l11p57pd_base_ulvt_130a\lef"
    r"\tcbn07_bwph240l11p57pd_base_ulvt.lef"
)
N07_LOGIC_WIKI = Path(r"C:\chipwiki\wiki\synthesis\n07-logic-and-interconnect-ppa-envelope-v1.md")
N07_SRAM_WIKI = Path(r"C:\chipwiki\wiki\synthesis\n07-sram-ppa-envelope-v1.md")


@dataclass(frozen=True)
class Cell:
    name: str
    w_um: float
    h_um: float

    @property
    def area_um2(self) -> float:
        return self.w_um * self.h_um


@dataclass
class Block:
    key: str
    title: str
    count_label: str
    raw_area_um2: float
    placed_area_um2: float
    delay_ps: float
    timing_label: str
    fill: str
    stroke: str
    x_um: float = 0.0
    y_um: float = 0.0
    w_um: float = 0.0
    h_um: float = 0.0


def read_lef_cells(path: Path) -> dict[str, Cell]:
    text = path.read_text(errors="ignore")
    cells: dict[str, Cell] = {}
    for match in re.finditer(r"MACRO\s+(\S+)(.*?)(?=\nEND\s+\1\b)", text, re.S):
        name = match.group(1)
        size = re.search(r"SIZE\s+([0-9.]+)\s+BY\s+([0-9.]+)\s*;", match.group(2))
        if size:
            cells[name] = Cell(name, float(size.group(1)), float(size.group(2)))
    return cells


def pick(cells: dict[str, Cell], name: str) -> Cell:
    if name not in cells:
        raise KeyError(f"Missing N07 cell in LEF: {name}")
    return cells[name]


def cell_area(cells: dict[str, Cell], name: str) -> float:
    return pick(cells, name).area_um2


def placed(raw_um2: float, utilization: float = 0.64, channel: float = 1.22) -> float:
    return raw_um2 / utilization * channel


def delay_4ghz(logic_fo4: float, mux_ps: float, wire_ps: float, margin_ps: float, clkq_ps: float = 25.870) -> float:
    return clkq_ps + logic_fo4 * 7.252 + mux_ps + wire_ps + margin_ps


def build_blocks(cells: dict[str, Cell]) -> tuple[list[Block], dict[str, float]]:
    inv = cell_area(cells, "INVD1BWP240H11P57PDULVT")
    nd2 = cell_area(cells, "ND2D1BWP240H11P57PDULVT")
    xor2 = cell_area(cells, "XOR2D1BWP240H11P57PDULVT")
    mux2 = cell_area(cells, "MUX2D1BWP240H11P57PDULVT")
    fa1 = cell_area(cells, "FA1D1BWP240H11P57PDULVT")
    dff = cell_area(cells, "DFQD1BWP240H11P57PDULVT")
    latch = cell_area(cells, "LHQD1BWP240H11P57PDULVT")

    # Explicit structural model. Counts are zhuque v1 physical planning counts;
    # primitive dimensions come from N07 LEF above.
    operand_lane = 64 * (3 * mux2 + 3 * latch) + 64 * (4 * nd2 + 2 * inv)
    add_lane = 64 * (fa1 + xor2 + mux2) + 16 * (6 * nd2 + 2 * inv) + 96 * nd2
    cmp_lane = 64 * (xor2 + mux2) + 126 * nd2 + 32 * mux2 + 32 * inv
    shift_lane = 64 * (6 * mux2 + 2 * xor2) + 64 * mux2 + 96 * nd2
    mul_lane = (
        32 * (5 * mux2 + 4 * nd2 + 2 * inv)
        + 2200 * fa1
        + 640 * xor2
        + 384 * dff
        + 64 * (fa1 + mux2)
    )
    div_lane = (
        2 * add_lane
        + 64 * (xor2 + mux2)
        + 360 * dff
        + 480 * nd2
        + 64 * latch
    )
    special_lane = 1536 * xor2 + 1024 * mux2 + 768 * nd2 + 512 * dff
    result_slot = 64 * (3 * mux2 + latch) + 96 * dff + 192 * nd2

    blocks = [
        Block(
            "operand",
            "Operand / Bypass Slice Field",
            "30 issue targets, 64 vertical bit-slices",
            30 * operand_lane,
            placed(30 * operand_lane),
            delay_4ghz(4, 18, 15.5, 40),
            "IX_OPRD_L0, local M5",
            "#dff3ee",
            "#2e6f66",
        ),
        Block(
            "fast",
            "Fast Add / Logic Field",
            "8 lanes, 64-bit slice-based",
            8 * add_lane,
            placed(8 * add_lane),
            delay_4ghz(5, 10, 15.5, 35),
            "IX_FAST0, latch split",
            "#ffe9bf",
            "#9a6720",
        ),
        Block(
            "compare",
            "Branch / Compare Field",
            "6 lanes, local reduce trees",
            6 * cmp_lane,
            placed(6 * cmp_lane),
            delay_4ghz(7, 12, 16, 40),
            "IX_FAST0, redirect-near",
            "#ffd8d1",
            "#9a493e",
        ),
        Block(
            "shift",
            "Shift / Bitfield Field",
            "6 lanes, staged 2:1 mux fabric",
            6 * shift_lane,
            placed(6 * shift_lane),
            delay_4ghz(8, 14, 15.5, 40),
            "IX_FAST1, staged",
            "#dce8ff",
            "#4a67a1",
        ),
        Block(
            "mul",
            "Multiply / Compress Field",
            "6 lanes, encoded partial + compressor",
            6 * mul_lane,
            placed(6 * mul_lane),
            delay_4ghz(12, 18, 16, 45),
            "IX_MID, multi-stage",
            "#e4d8ff",
            "#65519a",
        ),
        Block(
            "div",
            "Divide / Iterative Field",
            "4 lanes, local state registers",
            4 * div_lane,
            placed(4 * div_lane),
            delay_4ghz(9, 16, 16, 45),
            "IX_SLOW, iterative",
            "#f5dfc9",
            "#8a5a30",
        ),
        Block(
            "special",
            "CRC / Auth / Shuffle Field",
            "4 side lanes, isolated from fast result mux",
            4 * special_lane,
            placed(4 * special_lane),
            delay_4ghz(10, 18, 16, 45),
            "IX_SLOW, side-lane",
            "#d8f0ff",
            "#32769a",
        ),
        Block(
            "result",
            "Result Merge / Writeback Field",
            "16 packet slots, staged merge",
            16 * result_slot,
            placed(16 * result_slot),
            delay_4ghz(10, 20, 16, 40),
            "IX_WB_R, M10/M12 spine",
            "#e7eadb",
            "#68733b",
        ),
    ]

    anchors = {
        "inv_d1_area_um2": inv,
        "nd2_d1_area_um2": nd2,
        "xor2_d1_area_um2": xor2,
        "mux2_d1_area_um2": mux2,
        "fa1_d1_area_um2": fa1,
        "dff_d1_area_um2": dff,
        "latch_lhqd1_area_um2": latch,
        "site_w_um": 0.057,
        "row_h_um": 0.240,
        "inv_d1_fo4_ps": 7.252,
        "dff_clkq_ps": 25.870,
        "m5_local_anchor_ps": 15.500,
        "m10_spine_anchor_ps": 4.421,
        "m12_core_anchor_ps": 0.855,
        "prf_16k_area_um2": 1417.590,
        "prf_16k_cycle_ns": 0.249,
        "target_period_ps": 250.0,
        "placement_utilization": 0.64,
        "routing_channel_factor": 1.22,
    }
    return blocks, anchors


def assign_geometry(blocks: list[Block], anchors: dict[str, float]) -> dict[str, float]:
    # One north-side PRF leaf is area-real and shape-aligned to 64 vertical bit slices.
    bit_pitch = anchors["site_w_um"] * 8
    slice_w = 64 * bit_pitch
    prf_banks = 16
    prf_area = anchors["prf_16k_area_um2"]
    prf_h = prf_area / slice_w
    prf_gap = 2.0
    x0, y0 = 18.0, 26.0

    prf_total_w = prf_banks * slice_w + (prf_banks - 1) * prf_gap

    block_by_key = {b.key: b for b in blocks}

    # All dimensions below preserve computed placed area. Widths are chosen to
    # keep bit-slices vertical and data movement short.
    operand = block_by_key["operand"]
    operand.x_um = x0
    operand.y_um = y0 + prf_h + 10.0
    operand.w_um = prf_total_w
    operand.h_um = operand.placed_area_um2 / operand.w_um

    y_main = operand.y_um + operand.h_um + 12.0
    gap = 8.0

    compare = block_by_key["compare"]
    compare.x_um = x0
    compare.y_um = y_main
    compare.w_um = 6 * slice_w
    compare.h_um = compare.placed_area_um2 / compare.w_um

    fast = block_by_key["fast"]
    fast.x_um = compare.x_um + compare.w_um + gap
    fast.y_um = y_main
    fast.w_um = 8 * slice_w
    fast.h_um = fast.placed_area_um2 / fast.w_um

    y_mid = y_main + max(compare.h_um, fast.h_um) + 12.0

    shift = block_by_key["shift"]
    shift.x_um = x0
    shift.y_um = y_mid
    shift.w_um = 6 * slice_w
    shift.h_um = shift.placed_area_um2 / shift.w_um

    mul = block_by_key["mul"]
    mul.x_um = shift.x_um + shift.w_um + gap
    mul.y_um = y_mid
    mul.w_um = 6 * slice_w
    mul.h_um = mul.placed_area_um2 / mul.w_um

    y_slow = y_mid + max(shift.h_um, mul.h_um) + 12.0

    div = block_by_key["div"]
    div.x_um = x0
    div.y_um = y_slow
    div.w_um = 4 * slice_w
    div.h_um = div.placed_area_um2 / div.w_um

    special = block_by_key["special"]
    special.x_um = div.x_um + div.w_um + gap
    special.y_um = y_slow
    special.w_um = 4 * slice_w
    special.h_um = special.placed_area_um2 / special.w_um

    result = block_by_key["result"]
    result.x_um = x0
    result.y_um = y_slow + max(div.h_um, special.h_um) + 12.0
    result.w_um = prf_total_w
    result.h_um = result.placed_area_um2 / result.w_um

    return {
        "bit_pitch_um": bit_pitch,
        "slice_w_um": slice_w,
        "prf_banks": prf_banks,
        "prf_bank_w_um": slice_w,
        "prf_bank_h_um": prf_h,
        "prf_total_w_um": prf_total_w,
        "origin_x_um": x0,
        "origin_y_um": y0,
        "canvas_w_um": prf_total_w + 2 * x0,
        "canvas_h_um": result.y_um + result.h_um + 40.0,
    }


def svg_rect(x: float, y: float, w: float, h: float, fill: str, stroke: str, sw: float = 0.35, cls: str = "") -> str:
    return (
        f'<rect class="{cls}" x="{x:.3f}" y="{y:.3f}" width="{w:.3f}" height="{h:.3f}" '
        f'fill="{fill}" stroke="{stroke}" stroke-width="{sw:.3f}" />'
    )


def svg_text(x: float, y: float, text: str, size: float = 3.0, weight: str = "500", color: str = "#1d2528") -> str:
    return (
        f'<text x="{x:.3f}" y="{y:.3f}" font-size="{size:.3f}" '
        f'font-weight="{weight}" fill="{color}">{escape(text)}</text>'
    )


def svg_slice_grid(x: float, y: float, h: float, bit_pitch: float, lanes: int, color: str) -> list[str]:
    parts: list[str] = []
    for lane in range(lanes):
        lx = x + lane * 64 * bit_pitch
        for bit in range(65):
            sx = lx + bit * bit_pitch
            if bit in {0, 32, 64}:
                sw = 0.18
                opacity = 0.82
            elif bit % 8 == 0:
                sw = 0.09
                opacity = 0.58
            else:
                sw = 0.025
                opacity = 0.30
            parts.append(
                f'<line x1="{sx:.3f}" y1="{y:.3f}" x2="{sx:.3f}" y2="{y + h:.3f}" '
                f'stroke="{color}" stroke-width="{sw:.3f}" opacity="{opacity:.2f}" />'
            )
    return parts


def block_label(block: Block) -> list[str]:
    return [
        block.title,
        block.count_label,
        f"{block.w_um:.1f} x {block.h_um:.1f} um, {block.placed_area_um2:.0f} um2",
        f"{block.delay_ps:.1f} ps, slack {250.0 - block.delay_ps:.1f} ps",
        block.timing_label,
    ]


def generate_svg(blocks: list[Block], anchors: dict[str, float], geom: dict[str, float]) -> str:
    scale = 2.0
    w = geom["canvas_w_um"]
    h = geom["canvas_h_um"]
    x0 = geom["origin_x_um"]
    y0 = geom["origin_y_um"]
    slice_w = geom["slice_w_um"]
    prf_h = geom["prf_bank_h_um"]
    prf_gap = 2.0

    parts: list[str] = []
    parts.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w * scale:.0f}" height="{h * scale:.0f}" '
        f'viewBox="0 0 {w:.3f} {h:.3f}">'
    )
    parts.append(
        "<style>"
        "text{font-family:'Segoe UI',Arial,sans-serif}.small{font-size:2.2px}.grid{stroke:#e8ecef;stroke-width:.08}"
        ".slice{stroke:#39545b;stroke-width:.035;opacity:.28}.latch{stroke:#0e5060;stroke-width:.35;stroke-dasharray:1.4 1.0}"
        ".soft{fill:#f8faf9}.legend{fill:#ffffff;stroke:#cbd5d8;stroke-width:.25}"
        "</style>"
    )
    parts.append(svg_rect(0, 0, w, h, "#f6f4ec", "#f6f4ec", 0))
    for gx in range(0, int(w) + 1, 20):
        parts.append(f'<line class="grid" x1="{gx}" y1="0" x2="{gx}" y2="{h:.3f}" />')
    for gy in range(0, int(h) + 1, 20):
        parts.append(f'<line class="grid" x1="0" y1="{gy}" x2="{w:.3f}" y2="{gy}" />')

    parts.append(svg_text(18, 13, "zhuque integer execute datapath floorplan v1", 5.8, "700"))
    parts.append(svg_text(18, 20, "N07 exact LEF cell geometry + QRT PRF area anchors; every datapath lane is drawn as 64 regular vertical slices", 2.9, "500", "#4f5b61"))

    for i in range(int(geom["prf_banks"])):
        x = x0 + i * (slice_w + prf_gap)
        parts.append(svg_rect(x, y0, slice_w, prf_h, "#eff6d7", "#7d8b44", 0.28))
        parts.append(svg_text(x + 1.6, y0 + 3.2, f"PRF{i:02d}", 2.5, "700", "#515c25"))
        parts.append(svg_text(x + 1.6, y0 + prf_h - 1.8, f"16K {anchors['prf_16k_area_um2']:.0f}um2", 2.0, "500", "#515c25"))
        parts.extend(svg_slice_grid(x, y0, prf_h, geom["bit_pitch_um"], 1, "#515c25"))
        parts.append(svg_text(x + 0.8, y0 + prf_h + 2.8, "0", 1.6, "600", "#515c25"))
        parts.append(svg_text(x + 31.0 * geom["bit_pitch_um"], y0 + prf_h + 2.8, "31|32", 1.6, "600", "#515c25"))
        parts.append(svg_text(x + 62.0 * geom["bit_pitch_um"], y0 + prf_h + 2.8, "63", 1.6, "600", "#515c25"))

    parts.append(svg_text(x0, y0 - 2.8, "North PRF boundary: area-real 1PRF leafs, width aligned to 64 vertical bit-slices", 2.5, "600", "#455047"))

    latch_y = []
    for block in blocks:
        parts.append(svg_rect(block.x_um, block.y_um, block.w_um, block.h_um, block.fill, block.stroke, 0.32))
        # Draw slice lanes every 8 bits for wide datapath fields.
        if block.key in {"operand", "fast", "compare", "shift", "mul", "div", "special"}:
            start_x = block.x_um
            lanes = max(1, int(round(block.w_um / slice_w)))
            parts.extend(svg_slice_grid(start_x, block.y_um, block.h_um, geom["bit_pitch_um"], lanes, block.stroke))
            if block.h_um > 4.8:
                parts.append(svg_text(block.x_um + 1.0, block.y_um + block.h_um - 1.5, "bit 0", 1.7, "600", block.stroke))
                parts.append(svg_text(block.x_um + 31.0 * geom["bit_pitch_um"], block.y_um + block.h_um - 1.5, "32-bit split", 1.7, "600", block.stroke))
                parts.append(svg_text(block.x_um + 62.0 * geom["bit_pitch_um"], block.y_um + block.h_um - 1.5, "63", 1.7, "600", block.stroke))
        lines = block_label(block)
        base_y = block.y_um + 4.2
        for idx, line in enumerate(lines):
            size = 2.55 if idx == 0 else 2.0
            weight = "700" if idx == 0 else "500"
            parts.append(svg_text(block.x_um + 2.0, base_y + idx * 3.0, line, size, weight))
        if block.key in {"operand", "fast", "shift", "result"}:
            latch_y.append((block.y_um, block.title.split(" / ")[0]))
            latch_y.append((block.y_um + block.h_um, block.title.split(" / ")[0]))

    for y, label in latch_y:
        parts.append(f'<line class="latch" x1="{x0:.3f}" y1="{y:.3f}" x2="{x0 + geom["prf_total_w_um"]:.3f}" y2="{y:.3f}" />')

    inset_x = x0 + 285.0
    inset_y = h - 60.0
    inset_w = 80.0
    inset_h = 20.0
    parts.append(svg_rect(inset_x, inset_y, inset_w, inset_h, "#ffffff", "#819098", 0.25))
    parts.append(svg_text(inset_x + 2.0, inset_y + 4.0, "64-bit slice ruler, one lane", 2.3, "700", "#263238"))
    ruler_x = inset_x + 4.0
    ruler_y = inset_y + 7.0
    ruler_h = 9.0
    ruler_pitch = (inset_w - 8.0) / 64.0
    for bit in range(65):
        sx = ruler_x + bit * ruler_pitch
        if bit in {0, 32, 64}:
            sw, op = 0.45, 0.90
        elif bit % 8 == 0:
            sw, op = 0.24, 0.70
        else:
            sw, op = 0.08, 0.45
        parts.append(f'<line x1="{sx:.3f}" y1="{ruler_y:.3f}" x2="{sx:.3f}" y2="{ruler_y + ruler_h:.3f}" stroke="#263238" stroke-width="{sw:.3f}" opacity="{op:.2f}" />')
    parts.append(svg_text(ruler_x, ruler_y + ruler_h + 3.0, "0", 1.8, "700"))
    parts.append(svg_text(ruler_x + 31.2 * ruler_pitch, ruler_y + ruler_h + 3.0, "31 32", 1.8, "700"))
    parts.append(svg_text(ruler_x + 61.8 * ruler_pitch, ruler_y + ruler_h + 3.0, "63", 1.8, "700"))

    # Dataflow is shown as rails, not crossing arrows.
    rail_x = x0 + geom["prf_total_w_um"] + 4.0
    y_top = y0
    y_bottom = max(b.y_um + b.h_um for b in blocks)
    for idx, (label, color) in enumerate([
        ("operand down rail", "#2e6f66"),
        ("result up/bypass rail", "#68733b"),
        ("redirect side rail", "#9a493e"),
    ]):
        rx = rail_x + idx * 3.0
        parts.append(f'<line x1="{rx:.3f}" y1="{y_top:.3f}" x2="{rx:.3f}" y2="{y_bottom:.3f}" stroke="{color}" stroke-width="1.1" opacity=".75" />')
        parts.append(svg_text(rx - 1.2, y_bottom + 5.0 + idx * 3.0, label, 2.1, "600", color))

    legend_x = x0
    legend_y = h - 28.0
    parts.append(svg_rect(legend_x, legend_y, 250.0, 20.5, "#ffffff", "#c9d2d5", 0.25, "legend"))
    parts.append(svg_text(legend_x + 3, legend_y + 4.3, "N07 anchors", 2.6, "700"))
    parts.append(svg_text(legend_x + 3, legend_y + 8.5, f"site {anchors['site_w_um']:.3f} x row {anchors['row_h_um']:.3f} um; INV {anchors['inv_d1_area_um2']:.5f} um2; NAND2 {anchors['nd2_d1_area_um2']:.5f} um2", 2.1, "500"))
    parts.append(svg_text(legend_x + 3, legend_y + 12.5, f"MUX2 {anchors['mux2_d1_area_um2']:.5f} um2; XOR2 {anchors['xor2_d1_area_um2']:.5f} um2; FA {anchors['fa1_d1_area_um2']:.5f} um2; latch {anchors['latch_lhqd1_area_um2']:.5f} um2", 2.1, "500"))
    parts.append(svg_text(legend_x + 3, legend_y + 16.5, f"FO4 {anchors['inv_d1_fo4_ps']:.3f} ps; DFF CP-Q {anchors['dff_clkq_ps']:.3f} ps; M5 {anchors['m5_local_anchor_ps']:.3f} ps; M10 {anchors['m10_spine_anchor_ps']:.3f} ps", 2.1, "500"))

    bar_x = w - 140.0
    bar_y = h - 16.0
    parts.append(f'<line x1="{bar_x:.3f}" y1="{bar_y:.3f}" x2="{bar_x + 100:.3f}" y2="{bar_y:.3f}" stroke="#1d2528" stroke-width="1.0" />')
    parts.append(svg_text(bar_x, bar_y + 5.0, "100 um scale", 2.4, "700"))

    parts.append("</svg>")
    return "\n".join(parts)


def rgb(hex_color: str) -> tuple[int, int, int]:
    value = hex_color.lstrip("#")
    return tuple(int(value[i : i + 2], 16) for i in (0, 2, 4))


def font(size: int, bold: bool = False) -> ImageFont.ImageFont:
    candidates = [
        r"C:\Windows\Fonts\msyhbd.ttc" if bold else r"C:\Windows\Fonts\msyh.ttc",
        r"C:\Windows\Fonts\simhei.ttf",
        r"C:\Windows\Fonts\segoeuib.ttf" if bold else r"C:\Windows\Fonts\segoeui.ttf",
        r"C:\Windows\Fonts\arialbd.ttf" if bold else r"C:\Windows\Fonts\arial.ttf",
    ]
    for path in candidates:
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def draw_slice_grid(draw: ImageDraw.ImageDraw, x: float, y: float, h: float, bit_pitch: float, lanes: int, color: str, scale: float) -> None:
    col = rgb(color)
    for lane in range(lanes):
        lx = x + lane * 64 * bit_pitch
        for bit in range(65):
            sx = (lx + bit * bit_pitch) * scale
            y1 = y * scale
            y2 = (y + h) * scale
            if bit in {0, 32, 64}:
                width = max(1, int(round(0.55 * scale)))
                fill = col
            elif bit % 8 == 0:
                width = max(1, int(round(0.28 * scale)))
                fill = tuple(int(c * 0.82 + 255 * 0.18) for c in col)
            else:
                width = 1
                fill = tuple(int(c * 0.55 + 255 * 0.45) for c in col)
            draw.line([(sx, y1), (sx, y2)], fill=fill, width=width)


def generate_png(blocks: list[Block], anchors: dict[str, float], geom: dict[str, float], path: Path) -> None:
    scale = 4.0
    w = int(math.ceil(geom["canvas_w_um"] * scale))
    h = int(math.ceil(geom["canvas_h_um"] * scale))
    image = Image.new("RGB", (w, h), rgb("#f6f4ec"))
    draw = ImageDraw.Draw(image)

    f_title = font(24, True)
    f_head = font(13, True)
    f_body = font(10)
    f_small = font(8)

    def xy_rect(x: float, y: float, ww: float, hh: float) -> tuple[int, int, int, int]:
        return (
            int(round(x * scale)),
            int(round(y * scale)),
            int(round((x + ww) * scale)),
            int(round((y + hh) * scale)),
        )

    for gx in range(0, int(geom["canvas_w_um"]) + 1, 20):
        draw.line([(gx * scale, 0), (gx * scale, h)], fill=rgb("#e8ecef"), width=1)
    for gy in range(0, int(geom["canvas_h_um"]) + 1, 20):
        draw.line([(0, gy * scale), (w, gy * scale)], fill=rgb("#e8ecef"), width=1)

    draw.text((18 * scale, 8 * scale), "zhuque integer execute datapath floorplan v1", fill=rgb("#1d2528"), font=f_title)
    draw.text((18 * scale, 20 * scale), "N07 LEF/QRT anchored; every datapath lane is 64 regular vertical slices", fill=rgb("#4f5b61"), font=f_body)

    x0 = geom["origin_x_um"]
    y0 = geom["origin_y_um"]
    slice_w = geom["slice_w_um"]
    prf_h = geom["prf_bank_h_um"]
    prf_gap = 2.0
    for i in range(int(geom["prf_banks"])):
        x = x0 + i * (slice_w + prf_gap)
        draw.rectangle(xy_rect(x, y0, slice_w, prf_h), fill=rgb("#eff6d7"), outline=rgb("#7d8b44"), width=1)
        draw_slice_grid(draw, x, y0, prf_h, geom["bit_pitch_um"], 1, "#515c25", scale)
        draw.text((int((x + 1.1) * scale), int((y0 + 1.2) * scale)), f"PRF{i:02d}", fill=rgb("#515c25"), font=f_small)
        draw.text((int((x + 0.8) * scale), int((y0 + prf_h - 4.0) * scale)), "0  31|32  63", fill=rgb("#515c25"), font=f_small)

    for block in blocks:
        draw.rectangle(xy_rect(block.x_um, block.y_um, block.w_um, block.h_um), fill=rgb(block.fill), outline=rgb(block.stroke), width=2)
        if block.key in {"operand", "fast", "compare", "shift", "mul", "div", "special"}:
            lanes = max(1, int(round(block.w_um / slice_w)))
            draw_slice_grid(draw, block.x_um, block.y_um, block.h_um, geom["bit_pitch_um"], lanes, block.stroke, scale)
        tx = int((block.x_um + 1.4) * scale)
        ty = int((block.y_um + 1.2) * scale)
        draw.text((tx, ty), block.title, fill=rgb("#1d2528"), font=f_head)
        draw.text((tx, ty + 15), block.count_label, fill=rgb("#1d2528"), font=f_body)
        draw.text((tx, ty + 28), f"{block.w_um:.1f} x {block.h_um:.1f} um, {block.placed_area_um2:.0f} um2", fill=rgb("#1d2528"), font=f_body)
        draw.text((tx, ty + 41), f"{block.delay_ps:.1f} ps, slack {250 - block.delay_ps:.1f} ps", fill=rgb("#1d2528"), font=f_body)
        if block.h_um * scale > 34:
            by = int((block.y_um + block.h_um - 10) * scale)
            draw.text((tx, by), "bit0 | byte groups | 32-bit split | bit63", fill=rgb(block.stroke), font=f_small)

    # Latch boundaries.
    for block in blocks:
        if block.key in {"operand", "fast", "shift", "result"}:
            for yy in [block.y_um, block.y_um + block.h_um]:
                draw.line(
                    [(x0 * scale, yy * scale), ((x0 + geom["prf_total_w_um"]) * scale, yy * scale)],
                    fill=rgb("#0e5060"),
                    width=2,
                )

    # Slice ruler inset.
    inset_x = 300.0
    inset_y = geom["canvas_h_um"] - 63.0
    draw.rectangle(xy_rect(inset_x, inset_y, 170.0, 35.0), fill=rgb("#ffffff"), outline=rgb("#819098"), width=1)
    draw.text((int((inset_x + 3) * scale), int((inset_y + 2.0) * scale)), "64-bit slice ruler, one datapath lane", fill=rgb("#263238"), font=f_head)
    rx = inset_x + 5.0
    ry = inset_y + 12.0
    rw = 160.0
    pitch = rw / 64.0
    for bit in range(65):
        sx = (rx + bit * pitch) * scale
        if bit in {0, 32, 64}:
            width = 3
            fill = rgb("#263238")
        elif bit % 8 == 0:
            width = 2
            fill = rgb("#58676d")
        else:
            width = 1
            fill = rgb("#9aa7ab")
        draw.line([(sx, ry * scale), (sx, (ry + 14.0) * scale)], fill=fill, width=width)
    draw.text((int(rx * scale), int((ry + 16.0) * scale)), "0", fill=rgb("#263238"), font=f_small)
    draw.text((int((rx + 31.0 * pitch) * scale), int((ry + 16.0) * scale)), "31 32", fill=rgb("#263238"), font=f_small)
    draw.text((int((rx + 62.0 * pitch) * scale), int((ry + 16.0) * scale)), "63", fill=rgb("#263238"), font=f_small)

    legend_y = geom["canvas_h_um"] - 28.0
    draw.rectangle(xy_rect(18, legend_y, 260, 19), fill=rgb("#ffffff"), outline=rgb("#c9d2d5"), width=1)
    draw.text((int(21 * scale), int((legend_y + 2) * scale)), "N07 anchors: site 0.057 x row 0.240 um; INV 0.04104; NAND2 0.05472; MUX2/XOR2 0.15048; FA/DFF 0.27360 um2", fill=rgb("#263238"), font=f_small)
    draw.text((int(21 * scale), int((legend_y + 8) * scale)), "Timing anchors: FO4 7.252 ps; DFF CP-Q 25.870 ps; M5 15.500 ps; M10 4.421 ps; PRF16K 1417.590 um2 / 0.249 ns", fill=rgb("#263238"), font=f_small)

    bar_x = geom["canvas_w_um"] - 140.0
    bar_y = geom["canvas_h_um"] - 16.0
    draw.line([(bar_x * scale, bar_y * scale), ((bar_x + 100.0) * scale, bar_y * scale)], fill=rgb("#1d2528"), width=4)
    draw.text((int(bar_x * scale), int((bar_y + 2) * scale)), "100 um scale", fill=rgb("#1d2528"), font=f_body)

    image.save(path)


def generate_readable_png(blocks: list[Block], anchors: dict[str, float], geom: dict[str, float], path: Path) -> None:
    main_scale = 3.35
    main_x = 72
    main_y = 142
    main_w = int(math.ceil(geom["canvas_w_um"] * main_scale))
    main_h = int(math.ceil(geom["canvas_h_um"] * main_scale))
    side_x = main_x + main_w + 46
    side_w = 650
    bottom_y = main_y + main_h + 42
    canvas_w = side_x + side_w + 72
    canvas_h = bottom_y + 410

    image = Image.new("RGB", (canvas_w, canvas_h), rgb("#f4f1e8"))
    draw = ImageDraw.Draw(image)

    f_title = font(34, True)
    f_sub = font(17)
    f_h = font(20, True)
    f_body = font(15)
    f_small = font(12)
    f_tag = font(17, True)

    def tx(x_um: float) -> int:
        return int(round(main_x + x_um * main_scale))

    def ty(y_um: float) -> int:
        return int(round(main_y + y_um * main_scale))

    def rect_px(x_um: float, y_um: float, w_um: float, h_um: float) -> tuple[int, int, int, int]:
        return (tx(x_um), ty(y_um), tx(x_um + w_um), ty(y_um + h_um))

    draw.text((72, 30), "朱雀 iexecute 数据通路 floorplan v2", fill=rgb("#20292d"), font=f_title)
    draw.text(
        (74, 76),
        "主图按 um 真实比例画分区；右侧列尺寸/面积/时延；下方单独放大 64-bit slice。",
        fill=rgb("#536068"),
        font=f_sub,
    )

    # Main physical scale frame and grid.
    draw.rectangle((main_x, main_y, main_x + main_w, main_y + main_h), fill=rgb("#faf9f2"), outline=rgb("#aab5b9"), width=2)
    for gx in range(0, int(geom["canvas_w_um"]) + 1, 50):
        x = tx(gx)
        draw.line([(x, main_y), (x, main_y + main_h)], fill=rgb("#e1e6e8"), width=1)
        draw.text((x + 3, main_y + main_h - 18), f"{gx}", fill=rgb("#8a969b"), font=f_small)
    for gy in range(0, int(geom["canvas_h_um"]) + 1, 50):
        y = ty(gy)
        draw.line([(main_x, y), (main_x + main_w, y)], fill=rgb("#e1e6e8"), width=1)
        draw.text((main_x + 4, y + 2), f"{gy}", fill=rgb("#8a969b"), font=f_small)
    draw.text((main_x, main_y - 28), "A. 真实比例分区图（单位：um）", fill=rgb("#263238"), font=f_h)

    bit_pitch = geom["bit_pitch_um"]
    slice_w = geom["slice_w_um"]
    prf_gap = 2.0
    x0 = geom["origin_x_um"]
    y0 = geom["origin_y_um"]
    prf_h = geom["prf_bank_h_um"]

    def draw_lane_guides(x_um: float, y_um: float, h_um: float, lanes: int, color: str, with_gap: bool = False) -> None:
        c = rgb(color)
        for lane in range(lanes):
            lx = x_um + lane * (slice_w + prf_gap if with_gap else slice_w)
            x_l = tx(lx)
            x_m = tx(lx + 32 * bit_pitch)
            x_r = tx(lx + 64 * bit_pitch)
            y_a = ty(y_um)
            y_b = ty(y_um + h_um)
            shade = rgb("#ffffff") if lane % 2 == 0 else tuple(int(v * 0.96 + 255 * 0.04) for v in c)
            draw.rectangle((x_l, y_a, x_r, y_b), fill=shade if lane % 2 else None)
            draw.line([(x_l, y_a), (x_l, y_b)], fill=c, width=2)
            draw.line([(x_m, y_a), (x_m, y_b)], fill=tuple(int(v * 0.75) for v in c), width=1)
            draw.line([(x_r, y_a), (x_r, y_b)], fill=c, width=2)

    # PRF north boundary.
    prf_tag = "0"
    for i in range(int(geom["prf_banks"])):
        x = x0 + i * (slice_w + prf_gap)
        box = rect_px(x, y0, slice_w, prf_h)
        draw.rectangle(box, fill=rgb("#edf6cf"), outline=rgb("#6d7c2c"), width=2)
        draw_lane_guides(x, y0, prf_h, 1, "#6d7c2c")
        if i in {0, 1, 2, 3, 8, 15}:
            draw.text((box[0] + 4, box[1] + 4), f"B{i}", fill=rgb("#4f5b21"), font=f_small)
    draw.ellipse((tx(x0) + 5, ty(y0) + 5, tx(x0) + 34, ty(y0) + 34), fill=rgb("#20292d"))
    draw.text((tx(x0) + 15, ty(y0) + 7), prf_tag, fill=rgb("#ffffff"), font=f_tag)

    tag_map = {
        "operand": "1",
        "compare": "2",
        "fast": "3",
        "shift": "4",
        "mul": "5",
        "div": "6",
        "special": "7",
        "result": "8",
    }

    for block in blocks:
        box = rect_px(block.x_um, block.y_um, block.w_um, block.h_um)
        draw.rectangle(box, fill=rgb(block.fill), outline=rgb(block.stroke), width=3)
        if block.key in {"operand", "result"}:
            draw_lane_guides(block.x_um, block.y_um, block.h_um, int(geom["prf_banks"]), block.stroke, with_gap=True)
        elif block.key in {"fast", "compare", "shift", "mul", "div", "special"}:
            lanes = max(1, int(round(block.w_um / slice_w)))
            draw_lane_guides(block.x_um, block.y_um, block.h_um, lanes, block.stroke)
        # Number tag near the block, not a full label.
        cx = max(box[0] + 10, min(box[2] - 28, box[0] + 14))
        cy = box[1] - 18 if box[3] - box[1] < 32 else box[1] + 7
        draw.ellipse((cx, cy, cx + 30, cy + 30), fill=rgb(block.stroke))
        draw.text((cx + 10, cy + 4), tag_map[block.key], fill=rgb("#ffffff"), font=f_tag)

    # Scale bar.
    sb_x = tx(geom["canvas_w_um"] - 130)
    sb_y = ty(geom["canvas_h_um"] - 18)
    draw.line([(sb_x, sb_y), (sb_x + int(100 * main_scale), sb_y)], fill=rgb("#20292d"), width=5)
    draw.text((sb_x, sb_y + 8), "100 um", fill=rgb("#20292d"), font=f_body)

    # Right-side table.
    draw.rectangle((side_x, main_y, side_x + side_w, main_y + main_h), fill=rgb("#ffffff"), outline=rgb("#c3ced2"), width=2)
    draw.text((side_x + 22, main_y + 22), "B. 分区表", fill=rgb("#263238"), font=f_h)
    draw.text((side_x + 22, main_y + 58), "编号对应左侧主图；尺寸/面积由 N07 锚点计算。", fill=rgb("#536068"), font=f_body)

    table_rows = [
        ("0", "PRF 北侧边界", f"16 x 64b bank", f"{16 * anchors['prf_16k_area_um2']:.0f} um2", f"{anchors['prf_16k_cycle_ns'] * 1000:.0f} ps"),
        ("1", "Operand / Bypass", "16 bank-aligned slice columns", f"{blocks[0].placed_area_um2:.0f} um2", f"{blocks[0].delay_ps:.0f} ps"),
    ]
    order = ["compare", "fast", "shift", "mul", "div", "special", "result"]
    block_by_key = {b.key: b for b in blocks}
    for key in order:
        b = block_by_key[key]
        lanes = "16 slots" if b.key == "result" else b.count_label.split(",")[0]
        table_rows.append((tag_map[b.key], b.title.replace(" / ", " + "), lanes, f"{b.placed_area_um2:.0f} um2", f"{b.delay_ps:.0f} ps"))

    y = main_y + 100
    for tag, name, lanes, area, delay in table_rows:
        draw.ellipse((side_x + 22, y - 2, side_x + 48, y + 24), fill=rgb("#263238"))
        draw.text((side_x + 31, y - 1), tag, fill=rgb("#ffffff"), font=f_small)
        draw.text((side_x + 62, y - 4), name, fill=rgb("#20292d"), font=f_body)
        draw.text((side_x + 62, y + 16), lanes, fill=rgb("#536068"), font=f_small)
        draw.text((side_x + 360, y - 4), area, fill=rgb("#20292d"), font=f_body)
        draw.text((side_x + 505, y - 4), delay, fill=rgb("#20292d"), font=f_body)
        y += 62

    # Slice zoom panel.
    panel_x = main_x
    panel_y = bottom_y
    panel_w = canvas_w - 2 * main_x
    panel_h = 315
    draw.rectangle((panel_x, panel_y, panel_x + panel_w, panel_y + panel_h), fill=rgb("#ffffff"), outline=rgb("#c3ced2"), width=2)
    draw.text((panel_x + 24, panel_y + 22), "C. 64-bit slice 放大图", fill=rgb("#263238"), font=f_h)
    draw.text(
        (panel_x + 24, panel_y + 56),
        f"每个 bit slice = 8 个 N07 site = {bit_pitch:.3f} um；一条 64-bit lane = {slice_w:.3f} um。粗线为 32-bit half 分界，细线为 bit slice。",
        fill=rgb("#536068"),
        font=f_body,
    )

    ruler_x = panel_x + 42
    ruler_y = panel_y + 106
    ruler_w = panel_w - 84
    ruler_h = 112
    bit_w = ruler_w / 64.0
    byte_colors = [rgb("#eaf4f0"), rgb("#f4f0df")]
    for byte in range(8):
        draw.rectangle(
            (
                int(ruler_x + byte * 8 * bit_w),
                ruler_y,
                int(ruler_x + (byte + 1) * 8 * bit_w),
                ruler_y + ruler_h,
            ),
            fill=byte_colors[byte % 2],
        )
    for bit in range(65):
        x = ruler_x + bit * bit_w
        if bit in {0, 32, 64}:
            width = 5
            color = rgb("#0f4f61")
        elif bit % 8 == 0:
            width = 3
            color = rgb("#54717a")
        else:
            width = 1
            color = rgb("#9cadb2")
        draw.line([(x, ruler_y), (x, ruler_y + ruler_h)], fill=color, width=width)
    for bit, label in [(0, "bit0"), (7, "7"), (8, "8"), (15, "15"), (16, "16"), (31, "31"), (32, "32"), (63, "bit63")]:
        x = ruler_x + bit * bit_w
        draw.text((int(x - 8), ruler_y + ruler_h + 12), label, fill=rgb("#263238"), font=f_small)
    draw.text((ruler_x + 8 * bit_w, ruler_y - 26), "byte0", fill=rgb("#536068"), font=f_small)
    draw.text((ruler_x + 32 * bit_w + 8, ruler_y - 26), "32-bit split", fill=rgb("#0f4f61"), font=f_body)
    draw.text((ruler_x + 56 * bit_w, ruler_y - 26), "byte7", fill=rgb("#536068"), font=f_small)

    # N07 anchors box.
    anchor_y = panel_y + 250
    draw.text(
        (panel_x + 24, anchor_y),
        "N07 锚点：site 0.057 x row 0.240 um；INV 0.04104、NAND2 0.05472、MUX2/XOR2 0.15048、FA/DFF 0.27360、LHQ 0.19152 um2；FO4 7.252 ps；DFF CP-Q 25.870 ps。",
        fill=rgb("#536068"),
        font=f_small,
    )

    image.save(path)


def write_doc(blocks: list[Block], anchors: dict[str, float], geom: dict[str, float]) -> str:
    rows = []
    for b in blocks:
        rows.append(
            f"| `{b.key}` | `{b.w_um:.3f} x {b.h_um:.3f}` | `{b.placed_area_um2:.3f}` | `{b.delay_ps:.3f}` | `{250.0 - b.delay_ps:.3f}` |"
        )
    return "\n".join(
        [
            "# Zhuque IExecute N07 Floorplan v1",
            "",
            "本文记录朱雀整数执行数据通路第一版物理草图的生成依据。",
            "",
            "## 输出",
            "",
            "- `docs/assets/floorplan/zhuque_iexecute_n07_floorplan_v1.svg`",
            "- `docs/assets/floorplan/zhuque_iexecute_n07_floorplan_v1.png`",
            "- `docs/assets/floorplan/zhuque_iexecute_n07_floorplan_v2.png`",
            "- `docs/assets/floorplan/zhuque_iexecute_n07_floorplan_v1.json`",
            "",
            "## 几何锚点",
            "",
            f"- 标准单元 site：`{anchors['site_w_um']:.3f} x {anchors['row_h_um']:.3f} um`",
            f"- `INV D1`：`{anchors['inv_d1_area_um2']:.5f} um2`",
            f"- `NAND2 D1`：`{anchors['nd2_d1_area_um2']:.5f} um2`",
            f"- `XOR2 D1`：`{anchors['xor2_d1_area_um2']:.5f} um2`",
            f"- `MUX2 D1`：`{anchors['mux2_d1_area_um2']:.5f} um2`",
            f"- `FA1 D1`：`{anchors['fa1_d1_area_um2']:.5f} um2`",
            f"- `LHQ D1`：`{anchors['latch_lhqd1_area_um2']:.5f} um2`",
            f"- `DFQ D1`：`{anchors['dff_d1_area_um2']:.5f} um2`",
            f"- 1PRF 16K leaf 面积：`{anchors['prf_16k_area_um2']:.3f} um2`，cycle：`{anchors['prf_16k_cycle_ns']:.3f} ns`",
            "",
            "## 时延锚点",
            "",
            f"- `INV D1 FO4`：`{anchors['inv_d1_fo4_ps']:.3f} ps`",
            f"- `DFF CP->Q`：`{anchors['dff_clkq_ps']:.3f} ps`",
            f"- `M5 local`：`{anchors['m5_local_anchor_ps']:.3f} ps`",
            f"- `M10 local spine`：`{anchors['m10_spine_anchor_ps']:.3f} ps`",
            f"- `M12 core spine`：`{anchors['m12_core_anchor_ps']:.3f} ps`",
            "",
            "## 分区尺寸",
            "",
            "| 分区 | 尺寸 um | 放置面积 um2 | 估算路径 ps | 4GHz slack ps |",
            "|---|---:|---:|---:|---:|",
            *rows,
            "",
            "## 说明",
            "",
            "图中标准单元逻辑区采用显式 cell-count 模型和 N07 LEF 单元面积计算，再加入放置利用率与局部布线通道系数。PRF 北侧边界采用 QRT 面积锚点，并按 `64` 个纵向 bit slice 对齐。每条数据 lane 均显示 bit 0、bit 31/32 分界和 bit 63，便于后续保持 slice-based 实现。该图用于 floorplan 驱动的前端数据通路设计，不替代综合、布局布线和 STA 报告。",
            "",
        ]
    )


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    DOC_DIR.mkdir(parents=True, exist_ok=True)
    cells = read_lef_cells(N07_STDCELL_LEF)
    blocks, anchors = build_blocks(cells)
    geom = assign_geometry(blocks, anchors)
    svg = generate_svg(blocks, anchors, geom)

    svg_path = OUT_DIR / "zhuque_iexecute_n07_floorplan_v1.svg"
    png_path = OUT_DIR / "zhuque_iexecute_n07_floorplan_v1.png"
    readable_png_path = OUT_DIR / "zhuque_iexecute_n07_floorplan_v2.png"
    json_path = OUT_DIR / "zhuque_iexecute_n07_floorplan_v1.json"
    md_path = DOC_DIR / "zhuque_iexecute_n07_floorplan_v1.md"

    svg_path.write_text(svg, encoding="utf-8")
    generate_png(blocks, anchors, geom, png_path)
    generate_readable_png(blocks, anchors, geom, readable_png_path)
    json_path.write_text(
        json.dumps(
            {
                "anchors": anchors,
                "geometry": geom,
                "blocks": [
                    {
                        "key": b.key,
                        "title": b.title,
                        "count_label": b.count_label,
                        "raw_area_um2": b.raw_area_um2,
                        "placed_area_um2": b.placed_area_um2,
                        "delay_ps": b.delay_ps,
                        "slack_ps": 250.0 - b.delay_ps,
                        "x_um": b.x_um,
                        "y_um": b.y_um,
                        "w_um": b.w_um,
                        "h_um": b.h_um,
                    }
                    for b in blocks
                ],
                "sources": {
                    "stdcell_lef": str(N07_STDCELL_LEF),
                    "logic_wiki": str(N07_LOGIC_WIKI),
                    "sram_wiki": str(N07_SRAM_WIKI),
                },
            },
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    md_path.write_text(write_doc(blocks, anchors, geom), encoding="utf-8")
    print(svg_path)
    print(png_path)
    print(readable_png_path)
    print(json_path)
    print(md_path)


if __name__ == "__main__":
    main()
