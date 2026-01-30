# app.py
import math
import pandas as pd
import streamlit as st
from pathlib import Path
import base64

# ==========================================================
# Rental Affordability Checker (English UI) - UI Focus
# - Generalized Results labels (no formulas shown)
# - Tabs: Checker | Variables & Categories | By Negeri
# - OPTIONS standardized to match "List of Variables & Categories"
# - Per-state coefficient structure (COEF_BY_STATE)
# ==========================================================

APP_DIR = Path(__file__).resolve().parent

# ====== Condition A threshold ======
P_THRESHOLD = 0.05  # pass if p >= 0.05


# -------------------- BASE COEFFICIENTS --------------------
COEF_BASE = {
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

# -------------------- PER-STATE COEF STRUCTURE --------------------
# NOTE:
# - If you don't have actual negeri coefficients yet, keep it like this:
#   We only adjust Constant per state (safe + simple).
# - Later, you can overwrite ANY coef key per state.
STATE_CONSTANT_ADJUST = {
    # contoh placeholder (kau boleh buang/ubah)
    "Selangor": 0.00,
    "Putrajaya": 0.02,
    "Kuala Lumpur": 0.01,
    "Johor": -0.01,
    "Penang": 0.01,
}

COEF_BY_STATE = {}
for negeri, adj in STATE_CONSTANT_ADJUST.items():
    c = dict(COEF_BASE)
    c["Constant"] = COEF_BASE["Constant"] + float(adj)
    COEF_BY_STATE[negeri] = c

# default fallback
def get_coef_for_state(state: str) -> dict:
    return COEF_BY_STATE.get(state, COEF_BASE)


# -------------------- STANDARDIZED OPTIONS (MATCH YOUR LIST) --------------------
OPTIONS = {
    "Gender": ["Lelaki", "Perempuan"],
    "Nationality": ["Malaysian", "Non-Malaysian"],
    "Ethnicity": ["Bumiputera", "Cina", "India", "Lain-lain"],
    "Religion": ["Islam", "Buddha", "Hindu", "Lain-lain"],
    "Marital Status": ["Single", "Bercerai", "Berkahwin"],  # as per list
    "Education Level": ["SPM dan ke bawah", "Undergraduate", "Postgraduate"],  # 3 only
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

# -------------------- NEGERI + CONTOH LOKASI (UNTUK MAP & UI) --------------------
STATE_PLACES = {
    "Selangor": [
        ("Shah Alam", 3.0738, 101.5183),
        ("Petaling Jaya", 3.1073, 101.6067),
        ("Kajang", 2.9936, 101.7873),
    ],
    "Putrajaya": [
        ("Putrajaya", 2.9264, 101.6964),
    ],
    "Kuala Lumpur": [
        ("Kuala Lumpur", 3.1390, 101.6869),
    ],
    "Johor": [
        ("Johor Bahru", 1.4927, 103.7414),
    ],
    "Penang": [
        ("George Town", 5.4141, 100.3288),
    ],
}


# -------------------- HELPERS --------------------
def logistic(z: float) -> float:
    if z >= 0:
        ez = math.exp(-z)
        return 1.0 / (1.0 + ez)
    ez = math.exp(z)
    return ez / (1.0 + ez)


def clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))


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

    td = p_to_deg(t)
    tx1 = cx + (r - 2) * math.cos(math.radians(td))
    ty1 = cy + (r - 2) * math.sin(math.radians(td))
    tx2 = cx + (r - 24) * math.cos(math.radians(td))
    ty2 = cy + (r - 24) * math.sin(math.radians(td))

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
    margin: 0; padding: 0;
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
                fill="rgba(17,24,39,0.95)" stroke="rgba(255,255,255,0.35)" stroke-width="2" />
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

    # Occupation base = Tidak bekerja (no dummy)
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

    # Jenis Rumah Sewa base = Rumah (no dummy)
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
    # Flat treated as base too (no dummy in your coef list)

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

    # Skim base = Tidak (ikut coef: (1) = Ya)
    inp["Adakah anda mengetahui terdapat skim mampu sewa di Malaysia? (contoh: SMART sewa)(1)"] = (
        1.0 if skim == "Ya" else 0.0
    )

    return inp


def compute_zp(coef: dict, inputs: dict):
    # internal only (no table shown)
    z = 0.0
    for k, b in coef.items():
        x = float(inputs.get(k, 0.0))
        z += float(b) * x
    p = float(logistic(z))
    return float(z), float(p)


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
    MENU_BG = "#ffffff"
    MENU_TEXT = "#111827"
    MENU_HOVER = "rgba(139, 92, 246, 0.10)"
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
  .block-container {{ padding-top: .75rem; }}

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

  .stNumberInput input, .stTextInput input, .stTextArea textarea {{
    background: {INPUT_BG} !important;
    border: 1px solid {INPUT_BORDER} !important;
    color: {INPUT_TEXT} !important;
    -webkit-text-fill-color: {INPUT_TEXT} !important;
    caret-color: {INPUT_TEXT} !important;
    border-radius: 12px !important;
  }}

  [data-baseweb="select"] > div {{
    background: {INPUT_BG} !important;
    border: 1px solid {INPUT_BORDER} !important;
    border-radius: 12px !important;
  }}
  [data-baseweb="select"] * {{
    color: {INPUT_TEXT} !important;
    -webkit-text-fill-color: {INPUT_TEXT} !important;
  }}

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

  div[role="tooltip"] {{
    background: {MENU_BG} !important;
    color: {MENU_TEXT} !important;
    border: 1px solid {INPUT_BORDER} !important;
    border-radius: 10px !important;
    box-shadow: 0 10px 25px rgba(0,0,0,0.25) !important;
  }}
  div[role="tooltip"] * {{
    color: {MENU_TEXT} !important;
    -webkit-text-fill-color: {MENU_TEXT} !important;
    opacity: 1 !important;
  }}

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

  .chip {{
    display:inline-flex;
    align-items:center;
    padding: 6px 10px;
    border-radius: 999px;
    font-weight: 700;
    font-size: 12px;
    border: 1px solid {BORDER};
    background: rgba(255,255,255,0.10);
  }}
  .chip.ok {{
    background: rgba(34,197,94,0.18);
    border-color: rgba(34,197,94,0.35);
  }}
  .chip.no {{
    background: rgba(239,68,68,0.16);
    border-color: rgba(239,68,68,0.35);
  }}

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

def chip(label: str, ok: bool) -> str:
    return f'<span class="chip {"ok" if ok else "no"}">{label}</span>'


# ======================== TABS ========================
tab_checker, tab_vars, tab_negeri = st.tabs(["✅ Checker", "📌 Variables & Categories", "🗺️ By Negeri"])


# ==========================================================
# TAB 1: CHECKER
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

    if "result" not in st.session_state:
        st.session_state["result"] = None

    if run:
        coef = COEF_BASE  # tab checker default (no negeri adjustment)
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

        st.session_state["result"] = {
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

    res = st.session_state["result"]

    with right:
        st.markdown('<div class="purple-card">', unsafe_allow_html=True)
        st.subheader("Results")

        if res is None:
            st.info("Click **Run Check** to show results.")
        else:
            # ✅ GENERAL labels (no formula in label)
            st.markdown(
                f"""
<div style="display:flex; gap:10px; flex-wrap:wrap; align-items:center; margin-bottom:10px;">
  <div><b>Condition A</b>: {chip("Afford" if res["ok_a"] else "Not Afford", res["ok_a"])}</div>
  <div><b>Condition B</b>: {chip("Afford" if res["ok_b"] else "Not Afford", res["ok_b"])}</div>
  <div><b>Overall</b>: {chip("Afford" if res["ok_all"] else "Not Afford", res["ok_all"])}</div>
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
# TAB 2: VARIABLES & CATEGORIES (GENERAL TABLE)
# ==========================================================
with tab_vars:
    st.markdown('<div class="purple-card">', unsafe_allow_html=True)
    st.subheader("List of Variables & Categories")

    var_rows = [
        ("Jantina", "Lelaki / Perempuan"),
        ("Warganegara", "Malaysian / Non-Malaysian"),
        ("Bangsa", "Bumiputera / Cina / India / Lain-lain"),
        ("Agama", "Islam / Buddha / Hindu / Lain-lain"),
        ("Status Perkahwinan", "Single / Bercerai / Berkahwin"),
        ("Tahap Pendidikan", "SPM dan ke bawah / Undergraduate / Postgraduate"),
        ("Pekerjaan", "Tidak bekerja / Bekerja sendiri / Lain-lain / Pekerja Kerajaan / Pekerja Swasta / Pesara"),
        ("Bilangan Isi Rumah", "Kurang dari 2 orang / 3 - 4 orang / Lebih 5 orang"),
        ("Bilangan Tanggungan", "Kurang dari 2 orang / 3 - 4 orang / Lebih 5 orang"),
        ("Jenis Penyewaan", "Rumah / Bilik"),
        ("Jenis Rumah Sewa", "Flat / Condominium / Lain-lain / Pangsapuri / Rumah 1 unit / Rumah Teres / Rumah"),
        ("Jenis Kelengkapan Perabot", "Tiada perabot / Perabot penuh / Perabot separa"),
        ("Deposit", "Tiada deposit / 1 + 1 / 2 + 1 / 3 + 1"),
        ("Tempoh Menyewa", "Kurang dari 2 tahun / 3 - 5 tahun / Lebih 6 tahun"),
        ("Skim", "Ya / Tidak"),
    ]
    df_vars = pd.DataFrame(var_rows, columns=["Variable", "Categories"])
    st.dataframe(df_vars, use_container_width=True, height=520)

    st.caption("Nota: Ini paparan general untuk user (UI). Coefficient detail boleh kekal internal.")
    st.markdown("</div>", unsafe_allow_html=True)


# ==========================================================
# TAB 3: BY NEGERI (STATE + PLACE + MAP + STATE COEF)
# ==========================================================
with tab_negeri:
    st.markdown('<div class="purple-card">', unsafe_allow_html=True)
    st.subheader("By Negeri")

    negeri_list = sorted(list(STATE_PLACES.keys()))
    negeri = st.selectbox("Pilih Negeri", negeri_list, index=0)

    places = STATE_PLACES.get(negeri, [])
    place_names = [p[0] for p in places] if places else ["(No place set)"]
    place_choice = st.selectbox("Pilih Lokasi (contoh)", place_names, index=0)

    chosen = next((p for p in places if p[0] == place_choice), None)
    if chosen:
        _, lat, lon = chosen
        st.caption(f"Location preview: {place_choice}, {negeri}")
        st.map(pd.DataFrame([{"lat": lat, "lon": lon}]), zoom=10)

    st.divider()
    st.caption("Nota: Tab ini guna coefficient mengikut negeri (kalau ada). Buat masa ni contoh: adjust pada Constant.")

    # Reuse same inputs (standardized)
    col1, col2 = st.columns(2)
    with col1:
        age_s = st.number_input("Umur (tahun)", min_value=15, max_value=100, value=38, step=1, key="age_state")
        gender_s = st.selectbox("Jantina", OPTIONS["Gender"], index=0, key="gender_state")
        nationality_s = st.selectbox("Warganegara", OPTIONS["Nationality"], index=0, key="nat_state")
        ethnicity_s = st.selectbox("Bangsa", OPTIONS["Ethnicity"], index=0, key="eth_state")
        religion_s = st.selectbox("Agama", OPTIONS["Religion"], index=0, key="rel_state")
        marital_s = st.selectbox("Status Perkahwinan", OPTIONS["Marital Status"], index=0, key="mar_state")
        edu_s = st.selectbox("Tahap Pendidikan", OPTIONS["Education Level"], index=0, key="edu_state")

    with col2:
        job_s = st.selectbox("Pekerjaan", OPTIONS["Occupation"], index=0, key="job_state")
        household_s = st.selectbox("Bilangan Isi Rumah", OPTIONS["Household Size"], index=0, key="hh_state")
        dependents_s = st.selectbox("Bilangan Tanggungan", OPTIONS["Number of Dependents"], index=0, key="dep_state")
        jenis_penyewaan_s = st.selectbox("Jenis Penyewaan", OPTIONS["Jenis Penyewaan"], index=0, key="jp_state")
        jenis_rumah_s = st.selectbox("Jenis Rumah Sewa", OPTIONS["Jenis Rumah Sewa"], index=0, key="jr_state")
        furnished_s = st.selectbox("Jenis Kelengkapan Perabot", OPTIONS["Furnished Type"], index=0, key="fur_state")
        deposit_s = st.selectbox("Deposit", OPTIONS["Deposit"], index=0, key="depst_state")
        tempoh_s = st.selectbox("Tempoh Menyewa", OPTIONS["Tempoh Menyewa"], index=0, key="tmp_state")
        skim_s = st.selectbox("Skim", OPTIONS["Skim"], index=1, key="skim_state")

    st.divider()
    c1, c2, c3 = st.columns(3)
    with c1:
        income_s = st.number_input("Monthly Income (RM)", min_value=0.0, value=6000.0, step=100.0, key="inc_state")
    with c2:
        rent_s = st.number_input("Monthly Rent (RM)", min_value=0.0, value=2000.0, step=50.0, key="rent_state")
    with c3:
        ratio_s = st.number_input("Rent ratio threshold", min_value=0.0, max_value=1.0, value=0.38, step=0.01, key="ratio_state")

    run_state = st.button("✅ Run By Negeri", use_container_width=True, key="run_state_btn")

    if "result_state" not in st.session_state:
        st.session_state["result_state"] = None

    if run_state:
        coef_state = get_coef_for_state(negeri)

        inputs_state = build_inputs(
            coef=coef_state,
            age=int(age_s),
            gender=gender_s,
            nationality=nationality_s,
            ethnicity=ethnicity_s,
            religion=religion_s,
            marital=marital_s,
            edu=edu_s,
            job=job_s,
            household=household_s,
            dependents=dependents_s,
            jenis_penyewaan=jenis_penyewaan_s,
            jenis_rumah=jenis_rumah_s,
            furnished=furnished_s,
            deposit=deposit_s,
            tempoh=tempoh_s,
            skim=skim_s,
        )
        z_s, p_s = compute_zp(coef_state, inputs_state)

        ok_a_s = p_s >= P_THRESHOLD
        threshold_s = ratio_s * income_s
        ok_b_s = rent_s <= threshold_s
        ok_all_s = ok_a_s and ok_b_s

        rent_share_s = (rent_s / income_s) if income_s > 0 else 0.0
        rent_share_s = clamp(rent_share_s, 0.0, 1.0)

        st.session_state["result_state"] = {
            "negeri": negeri,
            "z": z_s,
            "p": p_s,
            "threshold": threshold_s,
            "ratio": ratio_s,
            "income": income_s,
            "rent": rent_s,
            "rent_share": rent_share_s,
            "ok_a": ok_a_s,
            "ok_b": ok_b_s,
            "ok_all": ok_all_s,
            "const_used": coef_state.get("Constant", COEF_BASE["Constant"]),
        }

    resS = st.session_state["result_state"]
    if resS:
        st.divider()
        st.subheader("Results (By Negeri)")

        st.markdown(
            f"""
<div style="display:flex; gap:10px; flex-wrap:wrap; align-items:center; margin-bottom:10px;">
  <div><b>Negeri</b>: <span style="opacity:.9;">{resS["negeri"]}</span></div>
  <div><b>Condition A</b>: {chip("Afford" if resS["ok_a"] else "Not Afford", resS["ok_a"])}</div>
  <div><b>Condition B</b>: {chip("Afford" if resS["ok_b"] else "Not Afford", resS["ok_b"])}</div>
  <div><b>Overall</b>: {chip("Afford" if resS["ok_all"] else "Not Afford", resS["ok_all"])}</div>
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

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Score (z)", f"{resS['z']:.6f}")
        m2.metric("Estimated probability (p)", f"{resS['p']:.9f}")
        m3.metric("Rent threshold (RM)", f"{resS['threshold']:.2f}")
        m4.metric("Constant used (negeri)", f"{resS['const_used']:.3f}")

    st.markdown("</div>", unsafe_allow_html=True)
