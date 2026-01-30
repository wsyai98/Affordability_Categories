# app.py
import math
import pandas as pd
import streamlit as st
from pathlib import Path
import base64

# ==========================================================
# Rental Affordability Checker (UI Focus)
# ----------------------------------------------------------
# - 2 tabs only: Checker | By Negeri
# - 3 states only: Selangor, Putrajaya, Kuala Lumpur
# - No calculation table, no CSV download, no "Rules used"
# - Results labels are general (no formulas shown)
# - Checker tab uses Greater Klang Valley coefficients (MAINTAIN)
# - By Negeri uses state-specific coefficients (UPDATED from your table)
# - UX:
#   (1) Full width page (remove max-width constraint)
#   (2) Dark mode dropdown list uses WHITE bg + BLACK font (readable)
#   (3) Bilingual labels: English (big) + Malay (small)
#   (4) Each variable has a "?" help indicator (EN + BM)
#   (5) ✅ Hide the internal widget variable names (ethnicityS, depositS, etc.)
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
# ✅ OPTIONS (internal values stay as your original)
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

# --- Display (bilingual) for dropdown options (English first) ---
DISPLAY = {
    "Gender": {
        "Lelaki": "Male (Lelaki)",
        "Perempuan": "Female (Perempuan)",
    },
    "Nationality": {
        "Malaysian": "Malaysian (Warganegara Malaysia)",
        "Non-Malaysian": "Non-Malaysian (Bukan warganegara)",
    },
    "Ethnicity": {
        "Bumiputera": "Bumiputera (Bumiputera)",
        "Cina": "Chinese (Cina)",
        "India": "Indian (India)",
        "Lain-lain": "Other (Lain-lain)",
    },
    "Religion": {
        "Islam": "Islam (Islam)",
        "Buddha": "Buddhism (Buddha)",
        "Hindu": "Hinduism (Hindu)",
        "Lain-lain": "Other (Lain-lain)",
    },
    "Marital Status": {
        "Single": "Single (Bujang)",
        "Bercerai": "Divorced (Bercerai)",
        "Berkahwin": "Married (Berkahwin)",
    },
    "Education Level": {
        "SPM dan ke bawah": "SPM & below (SPM dan ke bawah)",
        "Undergraduate": "Undergraduate (Ijazah Sarjana Muda)",
        "Postgraduate": "Postgraduate (Pascasiswazah)",
    },
    "Occupation": {
        "Tidak bekerja": "Unemployed (Tidak bekerja)",
        "Bekerja sendiri": "Self-employed (Bekerja sendiri)",
        "Lain-lain": "Other (Lain-lain)",
        "Pekerja Kerajaan": "Government employee (Pekerja Kerajaan)",
        "Pekerja Swasta": "Private employee (Pekerja Swasta)",
        "Pesara": "Retired (Pesara)",
    },
    "Household Size": {
        "Kurang dari 2 orang": "1–2 people (Kurang dari 2 orang)",
        "3 - 4 orang": "3–4 people (3–4 orang)",
        "Lebih 5 orang": "5+ people (Lebih 5 orang)",
    },
    "Number of Dependents": {
        "Kurang dari 2 orang": "Less than 2 (Kurang dari 2)",
        "3 - 4 orang": "3–4 (3–4 orang)",
        "Lebih 5 orang": "More than 5 (Lebih 5)",
    },
    "Jenis Penyewaan": {
        "Rumah": "Whole house (Rumah)",
        "Bilik": "Room (Bilik)",
    },
    "Jenis Rumah Sewa": {
        "Flat": "Flat (Flat)",
        "Condominium": "Condominium (Kondominium)",
        "Pangsapuri": "Apartment (Pangsapuri)",
        "Rumah Teres": "Terrace house (Rumah Teres)",
        "Rumah 1 unit": "Detached / single unit (Rumah 1 unit)",
        "Lain-lain": "Other (Lain-lain)",
        "Rumah": "House (Rumah)",
    },
    "Furnished Type": {
        "Tiada perabot": "Unfurnished (Tiada perabot)",
        "Perabot penuh": "Fully furnished (Perabot penuh)",
        "Perabot separa": "Partly furnished (Perabot separa)",
    },
    "Deposit": {
        "Tiada deposit": "No deposit (Tiada deposit)",
        "1 + 1": "1+1 deposit (1+1)",
        "2 + 1": "2+1 deposit (2+1)",
        "3 + 1": "3+1 deposit (3+1)",
    },
    "Tempoh Menyewa": {
        "Kurang dari 2 tahun": "Less than 2 years (Kurang dari 2 tahun)",
        "3 - 5 tahun": "3–5 years (3–5 tahun)",
        "Lebih 6 tahun": "More than 6 years (Lebih 6 tahun)",
    },
    "Skim": {
        "Ya": "Yes (Ya)",
        "Tidak": "No (Tidak)",
    },
}


# ==========================================================
# ✅ COEFFICIENTS
# ==========================================================
# --- (A) Checker tab: GREATER KLANG VALLEY (MAINTAIN your current set) ---
COEF_GKV = {
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

# --- (B) By Negeri tab: UPDATED from your table (exact labels as given) ---
COEF_SELANGOR_STATE = {
    "@3.Umur": 0.018,
    "woman(1)": 0.196,
    "foreigner(1)": -19.896,
    "cina(1)": -0.155,
    "india(1)": 20.278,
    "bangsa_lain(1)": 20.391,
    "budhha(1)": -0.531,
    "hindu(1)": -20.168,
    "agama_lain(1)": -0.523,
    "kahwin(1)": -0.148,
    "bercerai(1)": -0.986,
    "undergraduate(1)": 0.473,
    "postgraduate(1)": -0.41,
    "kerja_sendiri(1)": -0.385,
    "kerja_lain(1)": -1.063,
    "kerja_kerajaan(1)": 0.841,
    "kerja_swasta(1)": 0.797,
    "isi_rumah_3_4(1)": -0.23,
    "isi_rumah_lebih_5(1)": 0.309,
    "tanggungan_kurang_2(1)": -0.379,
    "tanggungan_lebih_5(1)": -0.495,
    "sewa_bilik(1)": 0.818,
    "condo(1)": 0.035,
    "rumah_lain(1)": 0.047,
    "apartment(1)": 0.029,
    "rumah_1_unit(1)": -0.327,
    "rumah_teres(1)": -0.199,
    "perabot_penuh(1)": -0.45,
    "perabot_separa(1)": -0.596,
    "deposit_1_1(1)": -0.275,
    "deposit_2_1(1)": -0.433,
    "deposit_3_1(1)": -0.53,
    "sewa_tahun_3_5(1)": 0.503,
    "sewa_lebih_6(1)": 0.408,
    "skim_tidak(1)": 0.515,
    "Constant": -0.032,
}

COEF_PUTRAJAYA_STATE = {
    "@3.Umur": -0.098,
    "woman(1)": -1.296,
    "foreigner(1)": 14.4,
    "cina(1)": -21.515,
    "india(1)": -0.309,
    "bangsa_lain(1)": -17.168,
    "budhha(1)": 21.369,
    "hindu(1)": -1.237,
    "agama_lain(1)": 20.119,
    "kahwin(1)": 0.722,
    "bercerai(1)": 2.741,
    "undergraduate(1)": 0.668,
    "postgraduate(1)": -2.917,
    "kerja_sendiri(1)": 0.091,
    "kerja_kerajaan(1)": 2.668,
    "kerja_swasta(1)": 2.875,
    "pesara(1)": 2.367,
    "isi_rumah_3_4(1)": 1.519,
    "isi_rumah_lebih_5(1)": 0.139,
    "tanggungan_3_4(1)": -1.174,
    "tanggungan_kurang_2(1)": -1.641,
    "sewa_bilik(1)": 3.542,
    "condo(1)": -3.775,
    "rumah_lain(1)": -2.408,
    "apartment(1)": -2.596,
    "rumah_1_unit(1)": 19.119,
    "rumah_teres(1)": 0.854,
    "perabot_penuh(1)": -1.537,
    "perabot_separa(1)": -0.494,
    "deposit_1_1(1)": -3.171,
    "deposit_2_1(1)": -2.843,
    "deposit_3_1(1)": -7.405,
    "sewa_tahun_3_5(1)": -0.279,
    "sewa_lebih_6(1)": 0.613,
    "skim_tidak(1)": -0.378,
    "Constant": 8.023,
}

COEF_KUALALUMPUR_STATE = {
    "@3.Umur": -0.002,
    "woman(1)": -0.188,
    "foreigner(1)": -0.874,
    "cina(1)": 0.354,
    "india(1)": 0.194,
    "bangsa_lain(1)": 1.206,
    "budhha(1)": -0.4,
    "hindu(1)": -0.129,
    "agama_lain(1)": -0.811,
    "kahwin(1)": -0.072,
    "bercerai(1)": -0.788,
    "undergraduate(1)": 0.507,
    "postgraduate(1)": -0.913,
    "kerja_sendiri(1)": 0.884,
    "kerja_lain(1)": -1.77,
    "kerja_kerajaan(1)": 1.018,
    "kerja_swasta(1)": 0.82,
    "pesara(1)": -0.991,
    "isi_rumah_3_4(1)": 0.263,
    "isi_rumah_lebih_5(1)": 0.486,
    "tanggungan_3_4(1)": -1.008,
    "tanggungan_kurang_2(1)": -0.397,
    "sewa_bilik(1)": 1.257,
    "condo(1)": -1.707,
    "rumah_lain(1)": -0.271,
    "apartment(1)": -1.043,
    "rumah_1_unit(1)": -1.006,
    "rumah_teres(1)": -0.783,
    "perabot_penuh(1)": 0.535,
    "perabot_separa(1)": -0.254,
    "deposit_1_1(1)": 0.015,
    "deposit_2_1(1)": -0.397,
    "deposit_3_1(1)": -0.483,
    "sewa_tahun_3_5(1)": 0.495,
    "sewa_lebih_6(1)": 0.885,
    "skim_tidak(1)": -0.201,
    "Constant": 1.146,
}

COEF_BY_STATE = {
    "Selangor": COEF_SELANGOR_STATE,
    "Putrajaya": COEF_PUTRAJAYA_STATE,
    "Kuala Lumpur": COEF_KUALALUMPUR_STATE,
}

COEF_DEFAULT = COEF_GKV  # Checker tab default (Greater Klang Valley)


# ==========================================================
# ✅ MAP CENTER POINTS (STATE HIGHLIGHT via point)
# ==========================================================
STATE_CENTER = {
    "Selangor": (3.0738, 101.5183),  # Shah Alam area
    "Putrajaya": (2.9264, 101.6964),
    "Kuala Lumpur": (3.1390, 101.6869),
}


# ==========================================================
# BILINGUAL LABEL + HELP (user guide indicator "?")
# ==========================================================
def label_html(en: str, ms: str) -> str:
    return f"""
<div class="lbl">
  <div class="en">{en}</div>
  <div class="ms">{ms}</div>
</div>
""".strip()


def help_text(en: str, ms: str) -> str:
    return f"EN: {en}\nBM: {ms}"


def fmt(field: str):
    m = DISPLAY.get(field, {})
    return lambda x: m.get(x, str(x))


# ==========================================================
# INPUT MAPPING -> MODEL DUMMIES (supports BOTH key styles)
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
    if "Constant" in inp:
        inp["Constant"] = 1.0

    # Age
    if "Umur" in inp:
        inp["Umur"] = float(age)
    if "@3.Umur" in inp:
        inp["@3.Umur"] = float(age)

    # Gender: female
    is_female = 1.0 if gender == "Perempuan" else 0.0
    if "Jantina ketua keluarga(1)" in inp:
        inp["Jantina ketua keluarga(1)"] = is_female
    if "woman(1)" in inp:
        inp["woman(1)"] = is_female

    # Nationality: foreigner / non-malaysian
    is_foreigner = 1.0 if nationality == "Non-Malaysian" else 0.0
    if "Warganegara(1)" in inp:
        inp["Warganegara(1)"] = is_foreigner
    if "foreigner(1)" in inp:
        inp["foreigner(1)"] = is_foreigner

    # Ethnicity base = Bumiputera
    is_cina = 1.0 if ethnicity == "Cina" else 0.0
    is_india = 1.0 if ethnicity == "India" else 0.0
    is_other_eth = 1.0 if ethnicity == "Lain-lain" else 0.0
    if "Bangsa=Cina(1)" in inp:
        inp["Bangsa=Cina(1)"] = is_cina
    if "Bangsa=India(1)" in inp:
        inp["Bangsa=India(1)"] = is_india
    if "Bangsa=Lain-lain(1)" in inp:
        inp["Bangsa=Lain-lain(1)"] = is_other_eth
    if "cina(1)" in inp:
        inp["cina(1)"] = is_cina
    if "india(1)" in inp:
        inp["india(1)"] = is_india
    if "bangsa_lain(1)" in inp:
        inp["bangsa_lain(1)"] = is_other_eth

    # Religion base = Islam
    is_buddha = 1.0 if religion == "Buddha" else 0.0
    is_hindu = 1.0 if religion == "Hindu" else 0.0
    is_other_rel = 1.0 if religion == "Lain-lain" else 0.0
    if "Agama=Buddha(1)" in inp:
        inp["Agama=Buddha(1)"] = is_buddha
    if "Agama=Hindu(1)" in inp:
        inp["Agama=Hindu(1)"] = is_hindu
    if "Agama=Lain-lain(1)" in inp:
        inp["Agama=Lain-lain(1)"] = is_other_rel
    if "budhha(1)" in inp:
        inp["budhha(1)"] = is_buddha
    if "hindu(1)" in inp:
        inp["hindu(1)"] = is_hindu
    if "agama_lain(1)" in inp:
        inp["agama_lain(1)"] = is_other_rel

    # Marital base = Single
    is_married = 1.0 if marital == "Berkahwin" else 0.0
    is_divorced = 1.0 if marital == "Bercerai" else 0.0
    if "Status Perkahwinan=Berkahwin(1)" in inp:
        inp["Status Perkahwinan=Berkahwin(1)"] = is_married
    if "Status Perkahwinan=Cerai/BaluDuda/Pisah(1)" in inp:
        inp["Status Perkahwinan=Cerai/BaluDuda/Pisah(1)"] = is_divorced
    if "kahwin(1)" in inp:
        inp["kahwin(1)"] = is_married
    if "bercerai(1)" in inp:
        inp["bercerai(1)"] = is_divorced

    # Education base = SPM dan ke bawah
    is_ug = 1.0 if edu == "Undergraduate" else 0.0
    is_pg = 1.0 if edu == "Postgraduate" else 0.0
    if "Tahap Pendidikan=Undergraduate(1)" in inp:
        inp["Tahap Pendidikan=Undergraduate(1)"] = is_ug
    if "Tahap Pendidikan=Postgraduate(1)" in inp:
        inp["Tahap Pendidikan=Postgraduate(1)"] = is_pg
    if "undergraduate(1)" in inp:
        inp["undergraduate(1)"] = is_ug
    if "postgraduate(1)" in inp:
        inp["postgraduate(1)"] = is_pg

    # Occupation base = Tidak bekerja
    is_self = 1.0 if job == "Bekerja sendiri" else 0.0
    is_other_job = 1.0 if job == "Lain-lain" else 0.0
    is_gov = 1.0 if job == "Pekerja Kerajaan" else 0.0
    is_priv = 1.0 if job == "Pekerja Swasta" else 0.0
    is_ret = 1.0 if job == "Pesara" else 0.0

    if "Pekerjaan=Bekerja sendiri(1)" in inp:
        inp["Pekerjaan=Bekerja sendiri(1)"] = is_self
    if "Pekerjaan=Lain-lain(1)" in inp:
        inp["Pekerjaan=Lain-lain(1)"] = is_other_job
    if "Pekerjaan=Pekerja Kerajaan(1)" in inp:
        inp["Pekerjaan=Pekerja Kerajaan(1)"] = is_gov
    if "Pekerjaan=Pekerja Swasta(1)" in inp:
        inp["Pekerjaan=Pekerja Swasta(1)"] = is_priv
    if "Pekerjaan=Pesara(1)" in inp:
        inp["Pekerjaan=Pesara(1)"] = is_ret

    if "kerja_sendiri(1)" in inp:
        inp["kerja_sendiri(1)"] = is_self
    if "kerja_lain(1)" in inp:
        inp["kerja_lain(1)"] = is_other_job
    if "kerja_kerajaan(1)" in inp:
        inp["kerja_kerajaan(1)"] = is_gov
    if "kerja_swasta(1)" in inp:
        inp["kerja_swasta(1)"] = is_priv
    if "pesara(1)" in inp:
        inp["pesara(1)"] = is_ret

    # Household base = Kurang dari 2 orang
    is_hh_3_4 = 1.0 if household == "3 - 4 orang" else 0.0
    is_hh_5p = 1.0 if household == "Lebih 5 orang" else 0.0
    if "Bilangan isi rumah=3-4 orang(1)" in inp:
        inp["Bilangan isi rumah=3-4 orang(1)"] = is_hh_3_4
    if "Bilangan isi rumah=5+ orang(1)" in inp:
        inp["Bilangan isi rumah=5+ orang(1)"] = is_hh_5p
    if "isi_rumah_3_4(1)" in inp:
        inp["isi_rumah_3_4(1)"] = is_hh_3_4
    if "isi_rumah_lebih_5(1)" in inp:
        inp["isi_rumah_lebih_5(1)"] = is_hh_5p

    # Dependents (varies by state tables)
    is_dep_less2 = 1.0 if dependents == "Kurang dari 2 orang" else 0.0
    is_dep_3_4 = 1.0 if dependents == "3 - 4 orang" else 0.0
    is_dep_5p = 1.0 if dependents == "Lebih 5 orang" else 0.0

    # GKV style
    if "Bilangan tanggungan=3-4 orang(1)" in inp:
        inp["Bilangan tanggungan=3-4 orang(1)"] = is_dep_3_4
    if "Bilangan tanggungan=5+ orang(1)" in inp:
        inp["Bilangan tanggungan=5+ orang(1)"] = is_dep_5p

    # State-table style
    if "tanggungan_kurang_2(1)" in inp:
        inp["tanggungan_kurang_2(1)"] = is_dep_less2
    if "tanggungan_3_4(1)" in inp:
        inp["tanggungan_3_4(1)"] = is_dep_3_4
    if "tanggungan_lebih_5(1)" in inp:
        inp["tanggungan_lebih_5(1)"] = is_dep_5p

    # Jenis Penyewaan base = Rumah
    is_room = 1.0 if jenis_penyewaan == "Bilik" else 0.0
    if "Jenis Penyewaan=Bilik(1)" in inp:
        inp["Jenis Penyewaan=Bilik(1)"] = is_room
    if "sewa_bilik(1)" in inp:
        inp["sewa_bilik(1)"] = is_room

    # Jenis Rumah Sewa base = Rumah/Flat (depends on model, keep dummies only)
    is_condo = 1.0 if jenis_rumah == "Condominium" else 0.0
    is_apartment = 1.0 if jenis_rumah == "Pangsapuri" else 0.0
    is_teres = 1.0 if jenis_rumah == "Rumah Teres" else 0.0
    is_1unit = 1.0 if jenis_rumah == "Rumah 1 unit" else 0.0
    is_other_house = 1.0 if jenis_rumah == "Lain-lain" else 0.0

    if "Jenis rumah sewa=Kondominium(1)" in inp:
        inp["Jenis rumah sewa=Kondominium(1)"] = is_condo
    if "Jenis rumah sewa=Pangsapuri(1)" in inp:
        inp["Jenis rumah sewa=Pangsapuri(1)"] = is_apartment
    if "Jenis rumah sewa=Rumah Teres(1)" in inp:
        inp["Jenis rumah sewa=Rumah Teres(1)"] = is_teres
    if "Jenis rumah sewa=Rumah 1 unit(1)" in inp:
        inp["Jenis rumah sewa=Rumah 1 unit(1)"] = is_1unit
    if "Jenis rumah sewa=Lain-lain(1)" in inp:
        inp["Jenis rumah sewa=Lain-lain(1)"] = is_other_house

    if "condo(1)" in inp:
        inp["condo(1)"] = is_condo
    if "apartment(1)" in inp:
        inp["apartment(1)"] = is_apartment
    if "rumah_teres(1)" in inp:
        inp["rumah_teres(1)"] = is_teres
    if "rumah_1_unit(1)" in inp:
        inp["rumah_1_unit(1)"] = is_1unit
    if "rumah_lain(1)" in inp:
        inp["rumah_lain(1)"] = is_other_house

    # Furnished base = Tiada perabot
    is_full = 1.0 if furnished == "Perabot penuh" else 0.0
    is_partial = 1.0 if furnished == "Perabot separa" else 0.0
    if "Jenis kelengkapan perabot=Berperabot penuh(1)" in inp:
        inp["Jenis kelengkapan perabot=Berperabot penuh(1)"] = is_full
    if "Jenis kelengkapan perabot=Berperabot separa(1)" in inp:
        inp["Jenis kelengkapan perabot=Berperabot separa(1)"] = is_partial
    if "perabot_penuh(1)" in inp:
        inp["perabot_penuh(1)"] = is_full
    if "perabot_separa(1)" in inp:
        inp["perabot_separa(1)"] = is_partial

    # Deposit base = Tiada deposit
    if "deposit_1_1(1)" in inp:
        inp["deposit_1_1(1)"] = 1.0 if deposit == "1 + 1" else 0.0
    if "deposit_2_1(1)" in inp:
        inp["deposit_2_1(1)"] = 1.0 if deposit == "2 + 1" else 0.0
    if "deposit_3_1(1)" in inp:
        inp["deposit_3_1(1)"] = 1.0 if deposit == "3 + 1" else 0.0

    # Tempoh Menyewa base = Kurang dari 2 tahun
    is_3_5 = 1.0 if tempoh == "3 - 5 tahun" else 0.0
    is_6p = 1.0 if tempoh == "Lebih 6 tahun" else 0.0
    if "Berapa lama anda telah menyewa rumah=3-5 tahun(1)" in inp:
        inp["Berapa lama anda telah menyewa rumah=3-5 tahun(1)"] = is_3_5
    if "Berapa lama anda telah menyewa rumah=6+ tahun(1)" in inp:
        inp["Berapa lama anda telah menyewa rumah=6+ tahun(1)"] = is_6p
    if "sewa_tahun_3_5(1)" in inp:
        inp["sewa_tahun_3_5(1)"] = is_3_5
    if "sewa_lebih_6(1)" in inp:
        inp["sewa_lebih_6(1)"] = is_6p

    # Skim (note: state tables use skim_tidak(1) = 1 if "Tidak")
    if "Adakah anda mengetahui terdapat skim mampu sewa di Malaysia? (contoh: SMART sewa)(1)" in inp:
        inp["Adakah anda mengetahui terdapat skim mampu sewa di Malaysia? (contoh: SMART sewa)(1)"] = (
            1.0 if skim == "Ya" else 0.0
        )
    if "skim_tidak(1)" in inp:
        inp["skim_tidak(1)"] = 1.0 if skim == "Tidak" else 0.0

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

  /* ✅ FULL WIDTH FIX */
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

  /* Bilingual label */
  .lbl {{
    margin: 0 0 .25rem 0;
    line-height: 1.1;
  }}
  .lbl .en {{
    font-weight: 800;
    font-size: 14px;
    color: {TXT};
  }}
  .lbl .ms {{
    font-size: 12px;
    opacity: .80;
    color: {TXT};
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

  /* ✅ Dropdown list (options) - ALWAYS readable */
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

  /* Metrics size */
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
# TAB 1: CHECKER (GKV COEF - MAINTAIN)
# ==========================================================
with tab_checker:
    left, right = st.columns([1, 1.35], gap="large")

    with left:
        st.markdown('<div class="purple-card">', unsafe_allow_html=True)
        st.subheader("User Inputs")

        colA, colB = st.columns(2)
        with colA:
            st.markdown(label_html("Age (years)", "Umur (tahun)"), unsafe_allow_html=True)
            age = st.number_input(
                "age_hidden",
                min_value=15,
                max_value=100,
                value=38,
                step=1,
                label_visibility="collapsed",
                help=help_text("Enter the respondent's age in years.", "Masukkan umur responden dalam tahun."),
            )

            st.markdown(label_html("Gender", "Jantina"), unsafe_allow_html=True)
            gender = st.selectbox(
                "gender_hidden",
                OPTIONS["Gender"],
                index=0,
                format_func=fmt("Gender"),
                label_visibility="collapsed",
                help=help_text("Select the gender of household head.", "Pilih jantina ketua isi rumah."),
            )

            st.markdown(label_html("Nationality", "Warganegara"), unsafe_allow_html=True)
            nationality = st.selectbox(
                "nat_hidden",
                OPTIONS["Nationality"],
                index=0,
                format_func=fmt("Nationality"),
                label_visibility="collapsed",
                help=help_text(
                    "Select whether the respondent is Malaysian or non-Malaysian.",
                    "Pilih sama ada responden warganegara atau bukan warganegara.",
                ),
            )

            st.markdown(label_html("Ethnicity", "Bangsa"), unsafe_allow_html=True)
            ethnicity = st.selectbox(
                "eth_hidden",
                OPTIONS["Ethnicity"],
                index=0,
                format_func=fmt("Ethnicity"),
                label_visibility="collapsed",
                help=help_text("Choose the respondent's ethnicity category.", "Pilih kategori bangsa responden."),
            )

            st.markdown(label_html("Religion", "Agama"), unsafe_allow_html=True)
            religion = st.selectbox(
                "rel_hidden",
                OPTIONS["Religion"],
                index=0,
                format_func=fmt("Religion"),
                label_visibility="collapsed",
                help=help_text("Choose the respondent's religion category.", "Pilih kategori agama responden."),
            )

            st.markdown(label_html("Marital status", "Status perkahwinan"), unsafe_allow_html=True)
            marital = st.selectbox(
                "mar_hidden",
                OPTIONS["Marital Status"],
                index=0,
                format_func=fmt("Marital Status"),
                label_visibility="collapsed",
                help=help_text("Select the respondent's marital status.", "Pilih status perkahwinan responden."),
            )

            st.markdown(label_html("Education level", "Tahap pendidikan"), unsafe_allow_html=True)
            edu = st.selectbox(
                "edu_hidden",
                OPTIONS["Education Level"],
                index=0,
                format_func=fmt("Education Level"),
                label_visibility="collapsed",
                help=help_text("Select the highest education level.", "Pilih tahap pendidikan tertinggi."),
            )

        with colB:
            st.markdown(label_html("Occupation", "Pekerjaan"), unsafe_allow_html=True)
            job = st.selectbox(
                "job_hidden",
                OPTIONS["Occupation"],
                index=0,
                format_func=fmt("Occupation"),
                label_visibility="collapsed",
                help=help_text("Select the respondent's occupation category.", "Pilih kategori pekerjaan responden."),
            )

            st.markdown(label_html("Household size", "Bilangan isi rumah"), unsafe_allow_html=True)
            household = st.selectbox(
                "hh_hidden",
                OPTIONS["Household Size"],
                index=0,
                format_func=fmt("Household Size"),
                label_visibility="collapsed",
                help=help_text("Total number of people living in the household.", "Jumlah orang yang tinggal dalam isi rumah."),
            )

            st.markdown(label_html("Number of dependents", "Bilangan tanggungan"), unsafe_allow_html=True)
            dependents = st.selectbox(
                "dep_hidden",
                OPTIONS["Number of Dependents"],
                index=0,
                format_func=fmt("Number of Dependents"),
                label_visibility="collapsed",
                help=help_text(
                    "Number of dependents financially supported by the respondent.",
                    "Bilangan tanggungan yang ditanggung dari segi kewangan.",
                ),
            )

            st.markdown(label_html("Rental type", "Jenis penyewaan"), unsafe_allow_html=True)
            jenis_penyewaan = st.selectbox(
                "renttype_hidden",
                OPTIONS["Jenis Penyewaan"],
                index=0,
                format_func=fmt("Jenis Penyewaan"),
                label_visibility="collapsed",
                help=help_text("Choose whether renting a whole unit/house or just a room.", "Pilih sama ada menyewa rumah/unit atau bilik sahaja."),
            )

            st.markdown(label_html("Type of rental housing", "Jenis rumah sewa"), unsafe_allow_html=True)
            jenis_rumah = st.selectbox(
                "house_hidden",
                OPTIONS["Jenis Rumah Sewa"],
                index=0,
                format_func=fmt("Jenis Rumah Sewa"),
                label_visibility="collapsed",
                help=help_text("Select the rental housing type (e.g., flat/condo/terrace).", "Pilih jenis rumah sewa (cth: flat/kondo/teres)."),
            )

            st.markdown(label_html("Furnished type", "Jenis kelengkapan perabot"), unsafe_allow_html=True)
            furnished = st.selectbox(
                "furn_hidden",
                OPTIONS["Furnished Type"],
                index=0,
                format_func=fmt("Furnished Type"),
                label_visibility="collapsed",
                help=help_text("Indicate the furnishing level of the rental unit.", "Nyatakan tahap perabot bagi rumah sewa."),
            )

            st.markdown(label_html("Deposit", "Deposit"), unsafe_allow_html=True)
            deposit = st.selectbox(
                "depst_hidden",
                OPTIONS["Deposit"],
                index=0,
                format_func=fmt("Deposit"),
                label_visibility="collapsed",
                help=help_text(
                    "Choose the deposit arrangement (e.g., 2+1 means 2 months deposit + 1 month utility).",
                    "Pilih jenis deposit (cth: 2+1 = 2 bulan deposit + 1 bulan utiliti).",
                ),
            )

            st.markdown(label_html("Total years renting", "Tempoh menyewa"), unsafe_allow_html=True)
            tempoh = st.selectbox(
                "temp_hidden",
                OPTIONS["Tempoh Menyewa"],
                index=0,
                format_func=fmt("Tempoh Menyewa"),
                label_visibility="collapsed",
                help=help_text("How long the respondent has been renting.", "Tempoh responden telah menyewa."),
            )

            st.markdown(label_html("Know SMART SEWA scheme?", "Tahu skim SMART SEWA?"), unsafe_allow_html=True)
            skim = st.selectbox(
                "skim_hidden",
                OPTIONS["Skim"],
                index=1,
                format_func=fmt("Skim"),
                label_visibility="collapsed",
                help=help_text(
                    "Whether the respondent is aware of affordable rental schemes (e.g., SMART SEWA).",
                    "Sama ada responden tahu skim mampu sewa (cth: SMART SEWA).",
                ),
            )

        st.divider()
        st.subheader("Income & Rent Inputs")

        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown(label_html("Monthly income (RM)", "Pendapatan bulanan (RM)"), unsafe_allow_html=True)
            income = st.number_input(
                "income_hidden",
                min_value=0.0,
                value=6000.0,
                step=100.0,
                label_visibility="collapsed",
                help=help_text("Enter total monthly household income in RM.", "Masukkan jumlah pendapatan isi rumah bulanan (RM)."),
            )
        with c2:
            st.markdown(label_html("Monthly rent (RM)", "Sewa bulanan (RM)"), unsafe_allow_html=True)
            rent = st.number_input(
                "rent_hidden",
                min_value=0.0,
                value=2000.0,
                step=50.0,
                label_visibility="collapsed",
                help=help_text("Enter monthly rent amount in RM.", "Masukkan jumlah sewa bulanan (RM)."),
            )
        with c3:
            st.markdown(label_html("Rent ratio threshold", "Had nisbah sewa"), unsafe_allow_html=True)
            ratio = st.number_input(
                "ratio_hidden",
                min_value=0.0,
                max_value=1.0,
                value=0.38,
                step=0.01,
                label_visibility="collapsed",
                help=help_text("Max recommended rent share of income (example: 0.38 = 38%).", "Had maksimum sewa berbanding pendapatan (cth: 0.38 = 38%)."),
            )

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

    st.markdown(label_html("Select state", "Pilih negeri"), unsafe_allow_html=True)
    negeri = st.selectbox(
        "negeri_hidden",
        ["Selangor", "Putrajaya", "Kuala Lumpur"],
        index=0,
        label_visibility="collapsed",
        help=help_text(
            "Choose a state to use the state-specific coefficients.",
            "Pilih negeri untuk guna pekali (coefficients) khusus negeri.",
        ),
    )

    lat, lon = STATE_CENTER[negeri]
    st.caption(f"Location preview: {negeri}")
    st.map(pd.DataFrame([{"lat": lat, "lon": lon}]), zoom=9)

    st.divider()

    leftS, rightS = st.columns([1, 1.35], gap="large")

    with leftS:
        st.subheader("User Inputs")

        colA, colB = st.columns(2)
        with colA:
            st.markdown(label_html("Age (years)", "Umur (tahun)"), unsafe_allow_html=True)
            ageS = st.number_input(
                "",
                min_value=15,
                max_value=100,
                value=38,
                step=1,
                key="ageS",
                label_visibility="collapsed",
                help=help_text("Enter age in years.", "Masukkan umur dalam tahun."),
            )

            st.markdown(label_html("Gender", "Jantina"), unsafe_allow_html=True)
            genderS = st.selectbox(
                "",
                OPTIONS["Gender"],
                index=0,
                format_func=fmt("Gender"),
                key="genderS",
                label_visibility="collapsed",
                help=help_text("Select gender.", "Pilih jantina."),
            )

            st.markdown(label_html("Nationality", "Warganegara"), unsafe_allow_html=True)
            nationalityS = st.selectbox(
                "",
                OPTIONS["Nationality"],
                index=0,
                format_func=fmt("Nationality"),
                key="nationalityS",
                label_visibility="collapsed",
                help=help_text("Select nationality.", "Pilih warganegara."),
            )

            st.markdown(label_html("Ethnicity", "Bangsa"), unsafe_allow_html=True)
            ethnicityS = st.selectbox(
                "",
                OPTIONS["Ethnicity"],
                index=0,
                format_func=fmt("Ethnicity"),
                key="ethnicityS",
                label_visibility="collapsed",
                help=help_text("Select ethnicity.", "Pilih bangsa."),
            )

            st.markdown(label_html("Religion", "Agama"), unsafe_allow_html=True)
            religionS = st.selectbox(
                "",
                OPTIONS["Religion"],
                index=0,
                format_func=fmt("Religion"),
                key="religionS",
                label_visibility="collapsed",
                help=help_text("Select religion.", "Pilih agama."),
            )

            st.markdown(label_html("Marital status", "Status perkahwinan"), unsafe_allow_html=True)
            maritalS = st.selectbox(
                "",
                OPTIONS["Marital Status"],
                index=0,
                format_func=fmt("Marital Status"),
                key="maritalS",
                label_visibility="collapsed",
                help=help_text("Select marital status.", "Pilih status perkahwinan."),
            )

            st.markdown(label_html("Education level", "Tahap pendidikan"), unsafe_allow_html=True)
            eduS = st.selectbox(
                "",
                OPTIONS["Education Level"],
                index=0,
                format_func=fmt("Education Level"),
                key="eduS",
                label_visibility="collapsed",
                help=help_text("Select education level.", "Pilih tahap pendidikan."),
            )

        with colB:
            st.markdown(label_html("Occupation", "Pekerjaan"), unsafe_allow_html=True)
            jobS = st.selectbox(
                "",
                OPTIONS["Occupation"],
                index=0,
                format_func=fmt("Occupation"),
                key="jobS",
                label_visibility="collapsed",
                help=help_text("Select occupation.", "Pilih pekerjaan."),
            )

            st.markdown(label_html("Household size", "Bilangan isi rumah"), unsafe_allow_html=True)
            householdS = st.selectbox(
                "",
                OPTIONS["Household Size"],
                index=0,
                format_func=fmt("Household Size"),
                key="householdS",
                label_visibility="collapsed",
                help=help_text("Select household size.", "Pilih bilangan isi rumah."),
            )

            st.markdown(label_html("Number of dependents", "Bilangan tanggungan"), unsafe_allow_html=True)
            dependentsS = st.selectbox(
                "",
                OPTIONS["Number of Dependents"],
                index=0,
                format_func=fmt("Number of Dependents"),
                key="dependentsS",
                label_visibility="collapsed",
                help=help_text("Select number of dependents.", "Pilih bilangan tanggungan."),
            )

            st.markdown(label_html("Rental type", "Jenis penyewaan"), unsafe_allow_html=True)
            jenis_penyewaanS = st.selectbox(
                "",
                OPTIONS["Jenis Penyewaan"],
                index=0,
                format_func=fmt("Jenis Penyewaan"),
                key="jenis_penyewaanS",
                label_visibility="collapsed",
                help=help_text("Whole house or room.", "Rumah/unit atau bilik."),
            )

            st.markdown(label_html("Type of rental housing", "Jenis rumah sewa"), unsafe_allow_html=True)
            jenis_rumahS = st.selectbox(
                "",
                OPTIONS["Jenis Rumah Sewa"],
                index=0,
                format_func=fmt("Jenis Rumah Sewa"),
                key="jenis_rumahS",
                label_visibility="collapsed",
                help=help_text("Select rental housing type.", "Pilih jenis rumah sewa."),
            )

            st.markdown(label_html("Furnished type", "Jenis kelengkapan perabot"), unsafe_allow_html=True)
            furnishedS = st.selectbox(
                "",
                OPTIONS["Furnished Type"],
                index=0,
                format_func=fmt("Furnished Type"),
                key="furnishedS",
                label_visibility="collapsed",
                help=help_text("Select furnishing level.", "Pilih tahap perabot."),
            )

            st.markdown(label_html("Deposit", "Deposit"), unsafe_allow_html=True)
            depositS = st.selectbox(
                "",
                OPTIONS["Deposit"],
                index=0,
                format_func=fmt("Deposit"),
                key="depositS",
                label_visibility="collapsed",
                help=help_text("Select deposit arrangement.", "Pilih jenis deposit."),
            )

            st.markdown(label_html("Total years renting", "Tempoh menyewa"), unsafe_allow_html=True)
            tempohS = st.selectbox(
                "",
                OPTIONS["Tempoh Menyewa"],
                index=0,
                format_func=fmt("Tempoh Menyewa"),
                key="tempohS",
                label_visibility="collapsed",
                help=help_text("Select renting duration.", "Pilih tempoh menyewa."),
            )

            st.markdown(label_html("Know SMART SEWA scheme?", "Tahu skim SMART SEWA?"), unsafe_allow_html=True)
            skimS = st.selectbox(
                "",
                OPTIONS["Skim"],
                index=1,
                format_func=fmt("Skim"),
                key="skimS",
                label_visibility="collapsed",
                help=help_text("Awareness of affordable rental schemes.", "Tahap pengetahuan skim mampu sewa."),
            )

        st.divider()
        st.subheader("Income & Rent Inputs")

        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown(label_html("Monthly income (RM)", "Pendapatan bulanan (RM)"), unsafe_allow_html=True)
            incomeS = st.number_input(
                "",
                min_value=0.0,
                value=6000.0,
                step=100.0,
                key="incomeS",
                label_visibility="collapsed",
                help=help_text("Enter monthly income.", "Masukkan pendapatan bulanan."),
            )
        with c2:
            st.markdown(label_html("Monthly rent (RM)", "Sewa bulanan (RM)"), unsafe_allow_html=True)
            rentS = st.number_input(
                "",
                min_value=0.0,
                value=2000.0,
                step=50.0,
                key="rentS",
                label_visibility="collapsed",
                help=help_text("Enter monthly rent.", "Masukkan sewa bulanan."),
            )
        with c3:
            st.markdown(label_html("Rent ratio threshold", "Had nisbah sewa"), unsafe_allow_html=True)
            ratioS = st.number_input(
                "",
                min_value=0.0,
                max_value=1.0,
                value=0.38,
                step=0.01,
                key="ratioS",
                label_visibility="collapsed",
                help=help_text("Max rent share of income.", "Had maksimum sewa berbanding pendapatan."),
            )

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
