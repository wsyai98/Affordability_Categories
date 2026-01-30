# app.py
import math
import pandas as pd
import streamlit as st
from pathlib import Path
import base64

# ==========================================================
# Rental Affordability Checker (UI Focus)
# - 2 tabs only: Checker | By Negeri
# - 3 states only: Selangor, Putrajaya, Kuala Lumpur
# - No calculation table, no CSV download, no "Rules used"
# - Results labels are general (no formulas shown)
# - By Negeri uses state-specific coefficients
# - FIXED:
#   (1) Full width page (remove max-width constraint)
#   (2) Dark mode dropdown list uses WHITE bg + BLACK font (readable)
# ==========================================================

APP_DIR = Path(__file__).resolve().parent

# ====== Condition A threshold ======
P_THRESHOLD = 0.05  # pass if p >= 0.05


# -------------------- LOGO HELPERS --------------------
def img_to_base64(path: Path) -> str:
    data = path.read_bytes()
    return base64.b64encode(data).decode("utf-8")


def logo_strip_html(paths, height_px=42, gap_px=10):
    imgs = []
    for p in paths:
        if not p.exists():
            continue
        b64 = img_to_base64(p)
        ext = p.suffix.lower().replace(".", "")
        mime = "png" if ext in ("png",) else "jpeg"
        imgs.append(
            f'<img class="logo-img" src="data:image/{mime};base64,{b64}" '
            f'style="height:{height_px}px; width:auto; object-fit:contain;" />'
        )
    return f"""
    <div class="logo-wrap">
      <div class="logo-strip" style="gap:{gap_px}px;">
        {''.join(imgs)}
      </div>
    </div>
    """


# -------------------- MODEL MATH --------------------
def logistic(z: float) -> float:
    if z >= 0:
        ez = math.exp(-z)
        return 1.0 / (1.0 + ez)
    ez = math.exp(z)
    return ez / (1.0 + ez)


def clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))


def _arc_path(cx, cy, r, a0_deg, a1_deg):
    a0 = math.radians(a0_deg)
    a1 = math.radians(a1_deg)
    x0, y0 = cx + r * math.cos(a0), cy + r * math.sin(a0)
    x1, y1 = cx + r * math.cos(a1), cy + r * math.sin(a1)
    large = 1 if abs(a1_deg - a0_deg) > 180 else 0
    sweep = 1
    return f"M {x0:.2f} {y0:.2f} A {r:.2f} {r:.2f} 0 {large} {sweep} {x1:.2f} {y1:.2f}"


def svg_gauge_html(
    title: str,
    value_0_1: float,
    threshold_0_1: float,
    subtitle_left: str,
    subtitle_right: str,
    text_color: str,
    border_color: str,
) -> str:
    v = clamp(value_0_1, 0.0, 1.0)
    t = clamp(threshold_0_1, 0.0, 1.0)

    W, H = 300, 190
    cx, cy = W / 2, 150
    r = 95

    def p_to_deg(p):
        return -180 + (p * 180.0)

    segs = [
        (0.00, 0.10, "rgba(239,68,68,0.85)"),
        (0.10, 0.40, "rgba(245,158,11,0.85)"),
        (0.40, 1.00, "rgba(34,197,94,0.85)"),
    ]

    # threshold tick
    td = p_to_deg(t)
    tx1 = cx + (r - 2) * math.cos(math.radians(td))
    ty1 = cy + (r - 2) * math.sin(math.radians(td))
    tx2 = cx + (r - 24) * math.cos(math.radians(td))
    ty2 = cy + (r - 24) * math.sin(math.radians(td))

    # needle
    nd = p_to_deg(v)
    nx = cx + (r - 10) * math.cos(math.radians(nd))
    ny = cy + (r - 10) * math.sin(math.radians(nd))

    paths = []
    for a0, a1, col in segs:
        paths.append(
            f'<path d="{_arc_path(cx, cy, r, p_to_deg(a0), p_to_deg(a1))}" '
            f'stroke="{col}" stroke-width="16" fill="none" stroke-linecap="round" />'
        )

    return f"""
<!doctype html>
<html>
<head>
<meta charset="utf-8" />
<style>
  html, body {{
    margin: 0;
    padding: 0;
    background: transparent;
    color: {text_color};
    font-family: system-ui, -apple-system, Segoe UI, Roboto, sans-serif;
    overflow: hidden;
  }}
  .gauge-card {{
    border: 1px solid {border_color};
    background: rgba(255,255,255,0.06);
    border-radius: 16px;
    padding: 12px 12px 14px 12px;
    box-sizing: border-box;
  }}
  .gauge-title {{
    font-weight: 800;
    margin-bottom: 6px;
    opacity: .95;
    color: {text_color};
  }}
  .gauge-value {{
    font-weight: 900;
    font-size: 20px;
    margin-top: -4px;
    color: {text_color};
  }}
  .gauge-sub {{
    display:flex;
    justify-content: space-between;
    font-size: 12px;
    opacity: .82;
    margin-top: 2px;
    color: {text_color};
  }}
</style>
</head>
<body>
  <div class="gauge-card">
    <div class="gauge-title">{title}</div>

    <div style="display:flex; justify-content:center;">
      <svg width="{W}" height="{H}" viewBox="0 0 {W} {H}">
        {''.join(paths)}
        <line x1="{tx1:.2f}" y1="{ty1:.2f}" x2="{tx2:.2f}" y2="{ty2:.2f}"
              stroke="rgba(255,255,255,0.85)" stroke-width="3" stroke-linecap="round" />
        <line x1="{cx:.2f}" y1="{cy:.2f}" x2="{nx:.2f}" y2="{ny:.2f}"
              stroke="rgba(17,24,39,0.95)" stroke-width="4" stroke-linecap="round" />
        <circle cx="{cx:.2f}" cy="{cy:.2f}" r="7"
                fill="rgba(17,24,39,0.95)" stroke="rgba(255,255,255,0.35)" stroke-width="2" stroke-linecap="round" />
      </svg>
    </div>

    <div class="gauge-value">{(v*100):.2f}%</div>
    <div class="gauge-sub">
      <span>{subtitle_left}</span>
      <span>{subtitle_right}</span>
    </div>
  </div>
</body>
</html>
"""


# ==========================================================
# ✅ OPTIONS (STANDARDIZED - ikut list variables)
# ==========================================================
OPTIONS = {
    "Gender": ["Lelaki", "Perempuan"],
    "Nationality": ["Malaysian", "Non-Malaysian"],
    "Ethnicity": ["Bumiputera", "Cina", "India", "Lain-lain"],
    "Religion": ["Islam", "Buddha", "Hindu", "Lain-lain"],
    "Marital Status": ["Single", "Bercerai", "Berkahwin"],
    "Education Level": ["SPM dan ke bawah", "Undergraduate", "Postgraduate"],
    "Occupation": [
        "Tidak bekerja",
        "Bekerja sendiri",
        "Lain-lain",
        "Pekerja Kerajaan",
        "Pekerja Swasta",
        "Pesara",
    ],
    "Household Size": ["Kurang dari 2 orang", "3 - 4 orang", "Lebih 5 orang"],
    "Number of Dependents": ["Kurang dari 2 orang", "3 - 4 orang", "Lebih 5 orang"],
    "Jenis Penyewaan": ["Rumah", "Bilik"],
    "Jenis Rumah Sewa": ["Flat", "Condominium", "Lain-lain", "Pangsapuri", "Rumah 1 unit", "Rumah Teres", "Rumah"],
    "Furnished Type": ["Tiada perabot", "Perabot penuh", "Perabot separa"],
    "Deposit": ["Tiada deposit", "1 + 1", "2 + 1", "3 + 1"],
    "Tempoh Menyewa": ["Kurang dari 2 tahun", "3 - 5 tahun", "Lebih 6 tahun"],
    "Skim": ["Ya", "Tidak"],
}


# ==========================================================
# ✅ COEFFICIENTS (STATE-SPECIFIC)
# ==========================================================
# IMPORTANT:
# - Replace Putrajaya & KL with real full sets when you have them.
COEF_SELANGOR = {
    "Umur": 0.002,
    "Jantina ketua keluarga(1)": 0.007,
    "Warganegara(1)": -0.818,
    "Bangsa=Cina(1)": -0.411,
    "Bangsa=India(1)": 0.463,
    "Bangsa=Lain-lain(1)": 0.849,
    "Agama=Buddha(1)": 0.131,
    "Agama=Hindu(1)": -0.525,
    "Agama=Lain-lain(1)": -0.158,
    "Status Perkahwinan=Berkahwin(1)": -0.007,
    "Status Perkahwinan=Cerai/BaluDuda/Pisah(1)": 0.313,
    "Tahap Pendidikan=Undergraduate(1)": -0.537,
    "Tahap Pendidikan=Postgraduate(1)": -0.808,
    "Pekerjaan=Bekerja sendiri(1)": 0.198,
    "Pekerjaan=Lain-lain(1)": -0.801,
    "Pekerjaan=Pekerja Kerajaan(1)": 0.803,
    "Pekerjaan=Pekerja Swasta(1)": 0.912,
    "Pekerjaan=Pesara(1)": 0.018,
    "Bilangan isi rumah=3-4 orang(1)": 0.096,
    "Bilangan isi rumah=5+ orang(1)": -0.403,
    "Bilangan tanggungan=3-4 orang(1)": -0.028,
    "Bilangan tanggungan=5+ orang(1)": -0.134,
    "Jenis Penyewaan=Bilik(1)": 1.121,
    "Jenis rumah sewa=Kondominium(1)": -1.007,
    "Jenis rumah sewa=Lain-lain(1)": -0.598,
    "Jenis rumah sewa=Pangsapuri(1)": -0.604,
    "Jenis rumah sewa=Rumah 1 unit(1)": -0.711,
    "Jenis rumah sewa=Rumah Teres(1)": 0.526,
    "Jenis kelengkapan perabot=Berperabot penuh(1)": -0.053,
    "Jenis kelengkapan perabot=Berperabot separa(1)": -0.370,
    "deposit_1_1(1)": 0.339,
    "deposit_2_1(1)": 0.556,
    "deposit_3_1(1)": 0.686,
    "Berapa lama anda telah menyewa rumah=3-5 tahun(1)": 0.413,
    "Berapa lama anda telah menyewa rumah=6+ tahun(1)": -0.584,
    "Adakah anda mengetahui terdapat skim mampu sewa di Malaysia? (contoh: SMART sewa)(1)": 0.200,
    "Constant": 0.310,
}

# Placeholder differences (replace with REAL values later)
COEF_PUTRAJAYA = dict(COEF_SELANGOR)
COEF_PUTRAJAYA.update({
    "Constant": 0.340,
    "Pekerjaan=Pekerja Swasta(1)": 0.880,
    "Jenis Penyewaan=Bilik(1)": 1.050,
})

COEF_KUALALUMPUR = dict(COEF_SELANGOR)
COEF_KUALALUMPUR.update({
    "Constant": 0.325,
    "Jenis rumah sewa=Kondominium(1)": -0.950,
    "Pekerjaan=Pekerja Swasta(1)": 0.940,
})

COEF_BY_STATE = {
    "Selangor": COEF_SELANGOR,
    "Putrajaya": COEF_PUTRAJAYA,
    "Kuala Lumpur": COEF_KUALALUMPUR,
}

COEF_DEFAULT = COEF_SELANGOR  # Checker tab default


# ==========================================================
# ✅ MAP CENTER POINTS (STATE HIGHLIGHT via point)
# ==========================================================
STATE_CENTER = {
    "Selangor": (3.0738, 101.5183),       # Shah Alam area
    "Putrajaya": (2.9264, 101.6964),
    "Kuala Lumpur": (3.1390, 101.6869),
}


# ==========================================================
# INPUT MAPPING -> MODEL DUMMIES
# ==========================================================
def build_inputs(
    coef: dict,
    age: int,
    gender: str,
    nationality: str,
    ethnicity: str,
    religion: str,
    marital: str,
    edu: str,
    job: str,
    household: str,
    dependents: str,
    jenis_penyewaan: str,
    jenis_rumah: str,
    furnished: str,
    deposit: str,
    tempoh: str,
    skim: str,
) -> dict:
    inp = {k: 0.0 for k in coef.keys()}
    inp["Constant"] = 1.0
    inp["Umur"] = float(age)

    # Gender (1) = Perempuan
    inp["Jantina ketua keluarga(1)"] = 1.0 if gender == "Perempuan" else 0.0

    # Nationality (1) = Non-Malaysian
    inp["Warganegara(1)"] = 1.0 if nationality == "Non-Malaysian" else 0.0

    # Ethnicity base = Bumiputera
    if ethnicity == "Cina":
        inp["Bangsa=Cina(1)"] = 1.0
    elif ethnicity == "India":
        inp["Bangsa=India(1)"] = 1.0
    elif ethnicity == "Lain-lain":
        inp["Bangsa=Lain-lain(1)"] = 1.0

    # Religion base = Islam
    if religion == "Buddha":
        inp["Agama=Buddha(1)"] = 1.0
    elif religion == "Hindu":
        inp["Agama=Hindu(1)"] = 1.0
    elif religion == "Lain-lain":
        inp["Agama=Lain-lain(1)"] = 1.0

    # Marital base = Single
    if marital == "Berkahwin":
        inp["Status Perkahwinan=Berkahwin(1)"] = 1.0
    elif marital == "Bercerai":
        inp["Status Perkahwinan=Cerai/BaluDuda/Pisah(1)"] = 1.0

    # Education base = SPM dan ke bawah
    if edu == "Undergraduate":
        inp["Tahap Pendidikan=Undergraduate(1)"] = 1.0
    elif edu == "Postgraduate":
        inp["Tahap Pendidikan=Postgraduate(1)"] = 1.0

    # Occupation base = Tidak bekerja
    if job == "Bekerja sendiri":
        inp["Pekerjaan=Bekerja sendiri(1)"] = 1.0
    elif job == "Lain-lain":
        inp["Pekerjaan=Lain-lain(1)"] = 1.0
    elif job == "Pekerja Kerajaan":
        inp["Pekerjaan=Pekerja Kerajaan(1)"] = 1.0
    elif job == "Pekerja Swasta":
        inp["Pekerjaan=Pekerja Swasta(1)"] = 1.0
    elif job == "Pesara":
        inp["Pekerjaan=Pesara(1)"] = 1.0

    # Household base = Kurang dari 2 orang
    if household == "3 - 4 orang":
        inp["Bilangan isi rumah=3-4 orang(1)"] = 1.0
    elif household == "Lebih 5 orang":
        inp["Bilangan isi rumah=5+ orang(1)"] = 1.0

    # Dependents base = Kurang dari 2 orang
    if dependents == "3 - 4 orang":
        inp["Bilangan tanggungan=3-4 orang(1)"] = 1.0
    elif dependents == "Lebih 5 orang":
        inp["Bilangan tanggungan=5+ orang(1)"] = 1.0

    # Jenis Penyewaan base = Rumah
    if jenis_penyewaan == "Bilik":
        inp["Jenis Penyewaan=Bilik(1)"] = 1.0

    # Jenis Rumah Sewa base = Rumah
    if jenis_rumah == "Condominium":
        inp["Jenis rumah sewa=Kondominium(1)"] = 1.0
    elif jenis_rumah == "Pangsapuri":
        inp["Jenis rumah sewa=Pangsapuri(1)"] = 1.0
    elif jenis_rumah == "Rumah Teres":
        inp["Jenis rumah sewa=Rumah Teres(1)"] = 1.0
    elif jenis_rumah == "Rumah 1 unit":
        inp["Jenis rumah sewa=Rumah 1 unit(1)"] = 1.0
    elif jenis_rumah == "Lain-lain":
        inp["Jenis rumah sewa=Lain-lain(1)"] = 1.0
    # Flat treated as base here

    # Furnished base = Tiada perabot
    if furnished == "Perabot penuh":
        inp["Jenis kelengkapan perabot=Berperabot penuh(1)"] = 1.0
    elif furnished == "Perabot separa":
        inp["Jenis kelengkapan perabot=Berperabot separa(1)"] = 1.0

    # Deposit base = Tiada deposit
    if deposit == "1 + 1":
        inp["deposit_1_1(1)"] = 1.0
    elif deposit == "2 + 1":
        inp["deposit_2_1(1)"] = 1.0
    elif deposit == "3 + 1":
        inp["deposit_3_1(1)"] = 1.0

    # Tempoh Menyewa base = Kurang dari 2 tahun
    if tempoh == "3 - 5 tahun":
        inp["Berapa lama anda telah menyewa rumah=3-5 tahun(1)"] = 1.0
    elif tempoh == "Lebih 6 tahun":
        inp["Berapa lama anda telah menyewa rumah=6+ tahun(1)"] = 1.0

    # Skim base = Tidak, (1)=Ya
    inp["Adakah anda mengetahui terdapat skim mampu sewa di Malaysia? (contoh: SMART sewa)(1)"] = (
        1.0 if skim == "Ya" else 0.0
    )

    return inp


def compute_zp(coef: dict, inputs: dict):
    z = 0.0
    for k, b in coef.items():
        x = float(inputs.get(k, 0.0))
        z += float(b) * x
    p = float(logistic(z))
    return float(z), float(p)


def chip(label: str, ok: bool, border_color: str) -> str:
    cls = "ok" if ok else "no"
    return f'<span class="chip {cls}" style="border:1px solid {border_color};">{label}</span>'


# ==========================================================
# STREAMLIT CONFIG
# ==========================================================
st.set_page_config(page_title="Rental Affordability Checker", layout="wide")

# ======================== TOP BAR ========================
logo_paths = [
    APP_DIR / "logo_kpkt.png",
    APP_DIR / "logo_kementerian_ekonomi.jpg",
    APP_DIR / "logo_uitm.png",
    APP_DIR / "logo_ukm.png",
]

top_l, top_r = st.columns([0.68, 0.32], vertical_alignment="center")
with top_l:
    st.markdown("## Rental Affordability Checker")
    st.caption("Two checks are applied. Overall = Afford only if both are satisfied.")
with top_r:
    st.markdown(logo_strip_html(logo_paths, height_px=40, gap_px=10), unsafe_allow_html=True)
    dark_mode = st.toggle("Dark mode", value=True)

# ======================== THEME ========================
if dark_mode:
    PAGE_BG = "linear-gradient(180deg, #0b0b14 0%, #0b0b14 45%, #1a102b 100%)"
    CARD_BG = "rgba(17, 24, 39, 0.68)"
    BORDER = "rgba(167, 139, 250, 0.22)"
    TXT = "#f8fafc"
    INPUT_BG = "rgba(17, 24, 39, 0.92)"
    INPUT_BORDER = "rgba(167, 139, 250, 0.22)"
    INPUT_TEXT = "#f8fafc"

    # ✅ IMPORTANT: Dark mode dropdown list should be WHITE background + BLACK font
    MENU_BG = "#ffffff"
    MENU_TEXT = "#111827"
    MENU_HOVER = "rgba(139, 92, 246, 0.12)"
else:
    PAGE_BG = "linear-gradient(180deg, #f7f2ff 0%, #f7f2ff 45%, #efe6ff 100%)"
    CARD_BG = "rgba(255,255,255,0.84)"
    BORDER = "rgba(139, 92, 246, 0.20)"
    TXT = "#111827"
    INPUT_BG = "rgba(255,255,255,0.98)"
    INPUT_BORDER = "rgba(139, 92, 246, 0.22)"
    INPUT_TEXT = "#111827"

    MENU_BG = "#ffffff"
    MENU_TEXT = "#111827"
    MENU_HOVER = "rgba(139, 92, 246, 0.12)"

# ======================== CSS ===========================
st.markdown(
    f"""
<style>
  header[data-testid="stHeader"] {{ display: none !important; }}
  div[data-testid="stToolbar"] {{ display: none !important; }}
  #MainMenu {{ visibility: hidden; }}
  footer {{ visibility: hidden; }}

  .stApp {{
    background: {PAGE_BG} !important;
    color: {TXT} !important;
  }}

  /* ✅ FULL WIDTH FIX (no max-width limit) */
  .block-container {{
    padding-top: .75rem;
    max-width: 100% !important;
  }}

  .purple-card {{
    background: {CARD_BG};
    border: 1px solid {BORDER};
    border-radius: 18px;
    padding: 16px 16px;
    box-shadow: 0 12px 30px rgba(76, 29, 149, 0.10);
  }}

  h1,h2,h3,h4,h5,h6, p, div, span, label, small {{
    color: {TXT} !important;
  }}

  /* Inputs */
  .stNumberInput input, .stTextInput input, .stTextArea textarea {{
    background: {INPUT_BG} !important;
    border: 1px solid {INPUT_BORDER} !important;
    color: {INPUT_TEXT} !important;
    -webkit-text-fill-color: {INPUT_TEXT} !important;
    caret-color: {INPUT_TEXT} !important;
    border-radius: 12px !important;
  }}

  /* Closed select control */
  [data-baseweb="select"] > div {{
    background: {INPUT_BG} !important;
    border: 1px solid {INPUT_BORDER} !important;
    border-radius: 12px !important;
  }}
  [data-baseweb="select"] * {{
    color: {INPUT_TEXT} !important;
    -webkit-text-fill-color: {INPUT_TEXT} !important;
  }}

  /* ==========================================================
     ✅ Dropdown list (options) - ALWAYS readable
     Dark mode: WHITE bg + BLACK font
     Light mode: already OK, still keep consistent
     ========================================================== */
  div[role="dialog"] {{
    background: {MENU_BG} !important;
  }}

  div[role="dialog"] [data-baseweb="menu"],
  div[role="dialog"] ul[role="listbox"],
  [data-baseweb="menu"],
  ul[role="listbox"],
  [data-baseweb="popover"] > div,
  div[role="listbox"],
  div[role="dialog"] div[role="listbox"] {{
    background: {MENU_BG} !important;
    border: 1px solid {INPUT_BORDER} !important;
  }}

  div[role="dialog"] [data-baseweb="menu"] *,
  div[role="dialog"] ul[role="listbox"] *,
  [data-baseweb="menu"] *,
  ul[role="listbox"] *,
  div[role="listbox"] *,
  div[role="dialog"] div[role="listbox"] * {{
    color: {MENU_TEXT} !important;
    -webkit-text-fill-color: {MENU_TEXT} !important;
    opacity: 1 !important;
  }}

  div[role="dialog"] li[role="option"],
  li[role="option"] {{
    background: transparent !important;
    color: {MENU_TEXT} !important;
    -webkit-text-fill-color: {MENU_TEXT} !important;
    opacity: 1 !important;
  }}

  div[role="dialog"] li[role="option"]:hover,
  li[role="option"]:hover {{
    background: {MENU_HOVER} !important;
  }}

  div[role="dialog"] [aria-selected="true"],
  [aria-selected="true"] {{
    background: {MENU_HOVER} !important;
  }}

  /* Buttons */
  div.stButton > button {{
    color: #ffffff !important;
    background: rgba(17, 24, 39, 0.92) !important;
    border: 1px solid {BORDER} !important;
    border-radius: 14px !important;
    padding: 12px 14px !important;
  }}
  div.stButton > button * {{
    color: #ffffff !important;
    -webkit-text-fill-color: #ffffff !important;
  }}

  /* Chips */
  .chip {{
    display:inline-flex;
    align-items:center;
    padding: 6px 10px;
    border-radius: 999px;
    font-weight: 700;
    font-size: 12px;
    background: rgba(255,255,255,0.10);
  }}
  .chip.ok {{
    background: rgba(34,197,94,0.18);
  }}
  .chip.no {{
    background: rgba(239,68,68,0.16);
  }}

  /* Metrics size (avoid "kecik") */
  [data-testid="stMetricValue"] > div {{
    font-size: 2rem !important;
    line-height: 1.15 !important;
  }}

  /* Logo strip */
  .logo-wrap {{ display:flex; justify-content:flex-end; }}
  .logo-strip {{
    display:inline-flex;
    align-items:center;
    flex-wrap: nowrap;
    padding: 2px 6px;
    border-radius: 12px;
    border: 1px solid {BORDER};
    background: rgba(255,255,255,0.55);
    line-height: 0;
    width: fit-content;
    max-width: 100%;
  }}
  .logo-img {{ display:block; }}
</style>
""",
    unsafe_allow_html=True,
)

# ==========================================================
# ✅ 2 TABS ONLY
# ==========================================================
tab_checker, tab_negeri = st.tabs(["✅ Checker", "🗺️ By Negeri"])


# ==========================================================
# TAB 1: CHECKER (DEFAULT COEF)
# ==========================================================
with tab_checker:
    left, right = st.columns([1, 1.35], gap="large")

    with left:
        st.markdown('<div class="purple-card">', unsafe_allow_html=True)
        st.subheader("User Inputs")

        colA, colB = st.columns(2)
        with colA:
            age = st.number_input("Umur (tahun)", min_value=15, max_value=100, value=38, step=1)
            gender = st.selectbox("Jantina", OPTIONS["Gender"], index=0)
            nationality = st.selectbox("Warganegara", OPTIONS["Nationality"], index=0)
            ethnicity = st.selectbox("Bangsa", OPTIONS["Ethnicity"], index=0)
            religion = st.selectbox("Agama", OPTIONS["Religion"], index=0)
            marital = st.selectbox("Status Perkahwinan", OPTIONS["Marital Status"], index=0)
            edu = st.selectbox("Tahap Pendidikan", OPTIONS["Education Level"], index=0)

        with colB:
            job = st.selectbox("Pekerjaan", OPTIONS["Occupation"], index=0)
            household = st.selectbox("Bilangan Isi Rumah", OPTIONS["Household Size"], index=0)
            dependents = st.selectbox("Bilangan Tanggungan", OPTIONS["Number of Dependents"], index=0)
            jenis_penyewaan = st.selectbox("Jenis Penyewaan", OPTIONS["Jenis Penyewaan"], index=0)
            jenis_rumah = st.selectbox("Jenis Rumah Sewa", OPTIONS["Jenis Rumah Sewa"], index=0)
            furnished = st.selectbox("Jenis Kelengkapan Perabot", OPTIONS["Furnished Type"], index=0)
            deposit = st.selectbox("Deposit", OPTIONS["Deposit"], index=0)
            tempoh = st.selectbox("Tempoh Menyewa", OPTIONS["Tempoh Menyewa"], index=0)
            skim = st.selectbox("Skim", OPTIONS["Skim"], index=1)

        st.divider()
        st.subheader("Income & Rent Inputs")
        c1, c2, c3 = st.columns(3)
        with c1:
            income = st.number_input("Monthly Income (RM)", min_value=0.0, value=6000.0, step=100.0)
        with c2:
            rent = st.number_input("Monthly Rent (RM)", min_value=0.0, value=2000.0, step=50.0)
        with c3:
            ratio = st.number_input("Rent ratio threshold", min_value=0.0, max_value=1.0, value=0.38, step=0.01)

        run = st.button("✅ Run Check", use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    if "result_checker" not in st.session_state:
        st.session_state["result_checker"] = None

    if run:
        coef = COEF_DEFAULT

        inputs = build_inputs(
            coef=coef,
            age=int(age),
            gender=gender,
            nationality=nationality,
            ethnicity=ethnicity,
            religion=religion,
            marital=marital,
            edu=edu,
            job=job,
            household=household,
            dependents=dependents,
            jenis_penyewaan=jenis_penyewaan,
            jenis_rumah=jenis_rumah,
            furnished=furnished,
            deposit=deposit,
            tempoh=tempoh,
            skim=skim,
        )

        z, p = compute_zp(coef, inputs)
        ok_a = p >= P_THRESHOLD
        threshold = ratio * income
        ok_b = rent <= threshold
        ok_all = ok_a and ok_b

        rent_share = (rent / income) if income > 0 else 0.0
        rent_share = clamp(rent_share, 0.0, 1.0)

        st.session_state["result_checker"] = {
            "z": z,
            "p": p,
            "threshold": threshold,
            "ratio": ratio,
            "income": income,
            "rent": rent,
            "rent_share": rent_share,
            "ok_a": ok_a,
            "ok_b": ok_b,
            "ok_all": ok_all,
        }

    res = st.session_state["result_checker"]

    with right:
        st.markdown('<div class="purple-card">', unsafe_allow_html=True)
        st.subheader("Results")

        if res is None:
            st.info("Click **Run Check** to show results.")
        else:
            # ✅ GENERAL labels (no formulas shown)
            st.markdown(
                f"""
<div style="display:flex; gap:10px; flex-wrap:wrap; align-items:center; margin-bottom:10px;">
  <div><b>Condition A</b>: {chip("Afford" if res["ok_a"] else "Not Afford", res["ok_a"], BORDER)}</div>
  <div><b>Condition B</b>: {chip("Afford" if res["ok_b"] else "Not Afford", res["ok_b"], BORDER)}</div>
  <div><b>Overall</b>: {chip("Afford" if res["ok_all"] else "Not Afford", res["ok_all"], BORDER)}</div>
</div>
""",
                unsafe_allow_html=True,
            )

            g1, g2 = st.columns(2)
            with g1:
                st.components.v1.html(
                    svg_gauge_html(
                        title="Condition A Meter",
                        value_0_1=float(res["p"]),
                        threshold_0_1=float(P_THRESHOLD),
                        subtitle_left="Low",
                        subtitle_right=f"Pass at {P_THRESHOLD:.2f}",
                        text_color=("#f8fafc" if dark_mode else "#111827"),
                        border_color=BORDER,
                    ),
                    height=310,
                    scrolling=False,
                )

            with g2:
                ratio_v = float(res["ratio"])
                share = float(res["rent_share"])
                closeness = clamp(share / ratio_v, 0.0, 1.0) if ratio_v > 0 else 0.0
                st.components.v1.html(
                    svg_gauge_html(
                        title="Condition B Meter",
                        value_0_1=float(closeness),
                        threshold_0_1=1.0,
                        subtitle_left=f"Rent/Income: {share:.2f}",
                        subtitle_right=f"Threshold: {ratio_v:.2f}",
                        text_color=("#f8fafc" if dark_mode else "#111827"),
                        border_color=BORDER,
                    ),
                    height=310,
                    scrolling=False,
                )

            m1, m2, m3 = st.columns(3)
            m1.metric("Score (z)", f"{res['z']:.6f}")
            m2.metric("Estimated probability (p)", f"{res['p']:.9f}")
            m3.metric("Rent threshold (RM)", f"{res['threshold']:.2f}")

        st.markdown("</div>", unsafe_allow_html=True)


# ==========================================================
# TAB 2: BY NEGERI (STATE-SPECIFIC COEF + MAP HIGHLIGHT)
# ==========================================================
with tab_negeri:
    st.markdown('<div class="purple-card">', unsafe_allow_html=True)
    st.subheader("By Negeri")

    negeri = st.selectbox("Pilih Negeri", ["Selangor", "Putrajaya", "Kuala Lumpur"], index=0)

    # ✅ map highlight (point at state center)
    lat, lon = STATE_CENTER[negeri]
    st.caption(f"Location preview: {negeri}")
    st.map(pd.DataFrame([{"lat": lat, "lon": lon}]), zoom=9)

    st.divider()

    leftS, rightS = st.columns([1, 1.35], gap="large")

    with leftS:
        st.subheader("User Inputs")

        colA, colB = st.columns(2)
        with colA:
            ageS = st.number_input("Umur (tahun)", min_value=15, max_value=100, value=38, step=1, key="ageS")
            genderS = st.selectbox("Jantina", OPTIONS["Gender"], index=0, key="genderS")
            nationalityS = st.selectbox("Warganegara", OPTIONS["Nationality"], index=0, key="nationalityS")
            ethnicityS = st.selectbox("Bangsa", OPTIONS["Ethnicity"], index=0, key="ethnicityS")
            religionS = st.selectbox("Agama", OPTIONS["Religion"], index=0, key="religionS")
            maritalS = st.selectbox("Status Perkahwinan", OPTIONS["Marital Status"], index=0, key="maritalS")
            eduS = st.selectbox("Tahap Pendidikan", OPTIONS["Education Level"], index=0, key="eduS")

        with colB:
            jobS = st.selectbox("Pekerjaan", OPTIONS["Occupation"], index=0, key="jobS")
            householdS = st.selectbox("Bilangan Isi Rumah", OPTIONS["Household Size"], index=0, key="householdS")
            dependentsS = st.selectbox("Bilangan Tanggungan", OPTIONS["Number of Dependents"], index=0, key="dependentsS")
            jenis_penyewaanS = st.selectbox("Jenis Penyewaan", OPTIONS["Jenis Penyewaan"], index=0, key="jenis_penyewaanS")
            jenis_rumahS = st.selectbox("Jenis Rumah Sewa", OPTIONS["Jenis Rumah Sewa"], index=0, key="jenis_rumahS")
            furnishedS = st.selectbox("Jenis Kelengkapan Perabot", OPTIONS["Furnished Type"], index=0, key="furnishedS")
            depositS = st.selectbox("Deposit", OPTIONS["Deposit"], index=0, key="depositS")
            tempohS = st.selectbox("Tempoh Menyewa", OPTIONS["Tempoh Menyewa"], index=0, key="tempohS")
            skimS = st.selectbox("Skim", OPTIONS["Skim"], index=1, key="skimS")

        st.divider()
        st.subheader("Income & Rent Inputs")
        c1, c2, c3 = st.columns(3)
        with c1:
            incomeS = st.number_input("Monthly Income (RM)", min_value=0.0, value=6000.0, step=100.0, key="incomeS")
        with c2:
            rentS = st.number_input("Monthly Rent (RM)", min_value=0.0, value=2000.0, step=50.0, key="rentS")
        with c3:
            ratioS = st.number_input("Rent ratio threshold", min_value=0.0, max_value=1.0, value=0.38, step=0.01, key="ratioS")

        runS = st.button("✅ Run By Negeri", use_container_width=True, key="runS")

    if "result_state" not in st.session_state:
        st.session_state["result_state"] = None

    if runS:
        coef_state = COEF_BY_STATE[negeri]

        inputsS = build_inputs(
            coef=coef_state,
            age=int(ageS),
            gender=genderS,
            nationality=nationalityS,
            ethnicity=ethnicityS,
            religion=religionS,
            marital=maritalS,
            edu=eduS,
            job=jobS,
            household=householdS,
            dependents=dependentsS,
            jenis_penyewaan=jenis_penyewaanS,
            jenis_rumah=jenis_rumahS,
            furnished=furnishedS,
            deposit=depositS,
            tempoh=tempohS,
            skim=skimS,
        )

        zS, pS = compute_zp(coef_state, inputsS)
        ok_aS = pS >= P_THRESHOLD
        thresholdS = ratioS * incomeS
        ok_bS = rentS <= thresholdS
        ok_allS = ok_aS and ok_bS

        rent_shareS = (rentS / incomeS) if incomeS > 0 else 0.0
        rent_shareS = clamp(rent_shareS, 0.0, 1.0)

        st.session_state["result_state"] = {
            "negeri": negeri,
            "z": zS,
            "p": pS,
            "threshold": thresholdS,
            "ratio": ratioS,
            "income": incomeS,
            "rent": rentS,
            "rent_share": rent_shareS,
            "ok_a": ok_aS,
            "ok_b": ok_bS,
            "ok_all": ok_allS,
        }

    resS = st.session_state["result_state"]

    with rightS:
        st.subheader("Results")

        if resS is None:
            st.info("Pick a negeri, then click **Run By Negeri**.")
        else:
            st.markdown(
                f"""
<div style="display:flex; gap:10px; flex-wrap:wrap; align-items:center; margin-bottom:10px;">
  <div><b>Negeri</b>: <span style="opacity:.9;">{resS["negeri"]}</span></div>
  <div><b>Condition A</b>: {chip("Afford" if resS["ok_a"] else "Not Afford", resS["ok_a"], BORDER)}</div>
  <div><b>Condition B</b>: {chip("Afford" if resS["ok_b"] else "Not Afford", resS["ok_b"], BORDER)}</div>
  <div><b>Overall</b>: {chip("Afford" if resS["ok_all"] else "Not Afford", resS["ok_all"], BORDER)}</div>
</div>
""",
                unsafe_allow_html=True,
            )

            g1, g2 = st.columns(2)
            with g1:
                st.components.v1.html(
                    svg_gauge_html(
                        title="Condition A Meter",
                        value_0_1=float(resS["p"]),
                        threshold_0_1=float(P_THRESHOLD),
                        subtitle_left="Low",
                        subtitle_right=f"Pass at {P_THRESHOLD:.2f}",
                        text_color=("#f8fafc" if dark_mode else "#111827"),
                        border_color=BORDER,
                    ),
                    height=310,
                    scrolling=False,
                )
            with g2:
                ratio_v = float(resS["ratio"])
                share = float(resS["rent_share"])
                closeness = clamp(share / ratio_v, 0.0, 1.0) if ratio_v > 0 else 0.0
                st.components.v1.html(
                    svg_gauge_html(
                        title="Condition B Meter",
                        value_0_1=float(closeness),
                        threshold_0_1=1.0,
                        subtitle_left=f"Rent/Income: {share:.2f}",
                        subtitle_right=f"Threshold: {ratio_v:.2f}",
                        text_color=("#f8fafc" if dark_mode else "#111827"),
                        border_color=BORDER,
                    ),
                    height=310,
                    scrolling=False,
                )

            m1, m2, m3 = st.columns(3)
            m1.metric("Score (z)", f"{resS['z']:.6f}")
            m2.metric("Estimated probability (p)", f"{resS['p']:.9f}")
            m3.metric("Rent threshold (RM)", f"{resS['threshold']:.2f}")

    st.markdown("</div>", unsafe_allow_html=True)
