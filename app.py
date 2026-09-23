import html
import importlib
import pandas as pd
import streamlit as st
import scraper

importlib.reload(scraper)
from scraper import LinkedInScraper

# Page configuration
st.set_page_config(
    page_title="يا فتّاح يا عليم يا رزّاق يا كريم... أأمر",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# UI theme styling (Dark theme)
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;500;600;700;800&display=swap');

    /* ─── Reset & Base ─────────────────────────────────────── */
    *, *::before, *::after { box-sizing: border-box; }

    html, body, .stApp {
        font-family: 'Cairo', sans-serif !important;
        direction: rtl !important;
        background-color: #0d1117 !important;
        color: #e2e8f0 !important;
    }

    /* Hide sidebar */
    [data-testid="collapsedControl"],
    section[data-testid="stSidebar"] {
        display: none !important;
    }

    /* Hide Streamlit default header */
    header[data-testid="stHeader"] {
        background: transparent !important;
        border-bottom: none !important;
    }

    /* Center and constrain main content container */
    .block-container {
        padding-top: 2rem !important;
        padding-bottom: 3rem !important;
        max-width: 860px !important;
        margin: 0 auto !important;
    }

    /* ─── Typography ────────────────────────────────────────── */
    h1, h2, h3, h4, h5, h6,
    p, label, div, span,
    .stMarkdown, .stText {
        direction: rtl !important;
        text-align: right !important;
        font-family: 'Cairo', sans-serif !important;
    }

    /* ─── Page header ───────────────────────────────────────── */
    .emad-header {
        text-align: center !important;
        margin-bottom: 2.5rem;
        padding-top: 0.5rem;
    }
    .emad-logo {
        display: inline-flex;
        align-items: center;
        gap: 10px;
        font-size: 0.8rem;
        font-weight: 700;
        color: #8b949e;
        letter-spacing: 0.12em;
        text-transform: uppercase;
        margin-bottom: 0.5rem;
    }
    .emad-logo-dot {
        width: 5px;
        height: 5px;
        border-radius: 50%;
        background: #1a7fc1;
        display: inline-block;
    }
    .emad-title {
        font-size: 2.4rem;
        font-weight: 800;
        color: #e2e8f0;
        line-height: 1.2;
        margin: 0 0 0.5rem 0;
    }
    .emad-title span { color: #1a7fc1; }
    .emad-sub {
        font-size: 0.97rem;
        color: #8b949e;
        line-height: 1.75;
        max-width: 540px;
        margin: 0 auto;
    }

    /* ─── Search cards ──────────────────────────────────────── */
    .search-card {
        background: #161b22;
        border: 1px solid #30363d;
        border-radius: 12px;
        padding: 1.6rem 1.8rem 1.4rem;
        margin-bottom: 1.2rem;
    }
    .search-card-title {
        font-size: 0.72rem;
        font-weight: 700;
        color: #8b949e;
        letter-spacing: 0.12em;
        text-transform: uppercase;
        margin-bottom: 1.1rem;
        display: flex;
        align-items: center;
        gap: 8px;
        direction: rtl;
    }
    .search-card-title::before {
        content: '';
        display: inline-block;
        width: 3px;
        height: 13px;
        background: #1a7fc1;
        border-radius: 2px;
        flex-shrink: 0;
    }

    /* ─── Text inputs ───────────────────────────────────────── */
    .stTextInput > div > div > input {
        background: #0d1117 !important;
        border: 1px solid #30363d !important;
        border-radius: 8px !important;
        color: #e2e8f0 !important;
        font-family: 'Cairo', sans-serif !important;
        font-size: 1.0rem !important;
        padding: 0.65rem 1rem !important;
        direction: rtl !important;
        text-align: right !important;
        transition: border-color 0.15s ease, box-shadow 0.15s ease !important;
    }
    .stTextInput > div > div > input:focus {
        border-color: #1a7fc1 !important;
        box-shadow: 0 0 0 3px rgba(26,127,193,0.18) !important;
        outline: none !important;
    }
    .stTextInput > div > div > input::placeholder { color: #4a5568 !important; }
    .stTextInput label {
        color: #c9d1d9 !important;
        font-weight: 600 !important;
        font-size: 0.9rem !important;
    }

    /* ─── Selectboxes ───────────────────────────────────────── */
    .stSelectbox > div > div {
        background: #0d1117 !important;
        border: 1px solid #30363d !important;
        border-radius: 8px !important;
        color: #e2e8f0 !important;
        font-family: 'Cairo', sans-serif !important;
        transition: border-color 0.15s ease !important;
    }
    .stSelectbox > div > div:focus-within {
        border-color: #1a7fc1 !important;
        box-shadow: 0 0 0 3px rgba(26,127,193,0.18) !important;
    }
    .stSelectbox label {
        color: #c9d1d9 !important;
        font-weight: 600 !important;
        font-size: 0.9rem !important;
    }
    ul[data-baseweb="menu"] {
        background: #1c2333 !important;
        border: 1px solid #30363d !important;
        border-radius: 8px !important;
    }
    li[role="option"] {
        direction: rtl !important;
        text-align: right !important;
        color: #e2e8f0 !important;
        font-family: 'Cairo', sans-serif !important;
    }
    li[role="option"]:hover,
    li[role="option"][aria-selected="true"] {
        background: rgba(26,127,193,0.15) !important;
    }

    /* ─── Active Filter Pills ──────────────────────────────── */
    .active-filters-row {
        display: flex;
        align-items: center;
        flex-wrap: wrap;
        gap: 8px;
        margin-top: 0.9rem;
        padding-top: 0.75rem;
        border-top: 1px dashed #21262d;
        direction: rtl !important;
    }
    .active-filters-title {
        color: #8b949e;
        font-size: 0.8rem;
        font-weight: 700;
        margin-left: 4px;
        display: flex;
        align-items: center;
        gap: 4px;
    }
    .filter-pill {
        display: inline-flex;
        align-items: center;
        gap: 5px;
        background: rgba(56, 139, 253, 0.12);
        border: 1px solid rgba(56, 139, 253, 0.35);
        color: #79c0ff;
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 600;
        font-family: 'Cairo', sans-serif !important;
    }
    .filter-pill-contract {
        background: rgba(240, 136, 62, 0.12);
        border-color: rgba(240, 136, 62, 0.35);
        color: #ffa657;
    }
    .filter-pill-remote {
        background: rgba(46, 160, 67, 0.12);
        border-color: rgba(46, 160, 67, 0.35);
        color: #7ee787;
    }
    .filter-pill-seniority {
        background: rgba(163, 113, 247, 0.12);
        border-color: rgba(163, 113, 247, 0.35);
        color: #d2a8ff;
    }

    /* ─── Divider ───────────────────────────────────────────── */
    hr {
        border: none !important;
        border-top: 1px solid #21262d !important;
        margin: 1.5rem 0 !important;
    }

    /* ─── Primary CTA ───────────────────────────────────────── */
    .stButton > button[kind="primary"] {
        background: #1a7fc1 !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 8px !important;
        font-family: 'Cairo', sans-serif !important;
        font-size: 1.05rem !important;
        font-weight: 700 !important;
        padding: 0.75rem 2rem !important;
        width: 100% !important;
        transition: background 0.15s ease, transform 0.1s ease, box-shadow 0.15s ease !important;
        box-shadow: 0 1px 4px rgba(0,0,0,0.5) !important;
        cursor: pointer !important;
    }
    .stButton > button[kind="primary"]:hover {
        background: #388bfd !important;
        box-shadow: 0 0 0 4px rgba(56,139,253,0.2), 0 3px 8px rgba(0,0,0,0.5) !important;
        transform: translateY(-1px) !important;
    }
    .stButton > button[kind="primary"]:active {
        transform: translateY(0) !important;
        background: #1a7fc1 !important;
    }

    /* Secondary / download */
    .stDownloadButton > button {
        background: #21262d !important;
        color: #c9d1d9 !important;
        border: 1px solid #30363d !important;
        border-radius: 8px !important;
        font-family: 'Cairo', sans-serif !important;
        font-size: 0.9rem !important;
        font-weight: 600 !important;
        padding: 0.6rem 1.2rem !important;
        transition: border-color 0.15s, color 0.15s !important;
    }
    .stDownloadButton > button:hover {
        border-color: #388bfd !important;
        color: #e2e8f0 !important;
        background: #2d333b !important;
    }

    /* ─── Metric cards ──────────────────────────────────────── */
    [data-testid="stMetric"] {
        background: #161b22 !important;
        border: 1px solid #30363d !important;
        border-radius: 10px !important;
        padding: 1rem 1.2rem !important;
        direction: rtl !important;
        text-align: right !important;
    }
    [data-testid="stMetricLabel"] {
        color: #8b949e !important;
        font-size: 0.8rem !important;
        font-weight: 600 !important;
        justify-content: flex-start !important;
    }
    [data-testid="stMetricValue"] {
        color: #e2e8f0 !important;
        font-size: 1.6rem !important;
        font-weight: 800 !important;
    }

    /* ─── Alerts ────────────────────────────────────────────── */
    .stAlert {
        border-radius: 8px !important;
        direction: rtl !important;
        text-align: right !important;
        font-family: 'Cairo', sans-serif !important;
    }
    .stAlert > div { direction: rtl !important; text-align: right !important; }

    /* ─── Progress bar ──────────────────────────────────────── */
    .stProgress > div > div { background: #1a7fc1 !important; border-radius: 4px !important; }
    .stProgress > div { background: #21262d !important; border-radius: 4px !important; }

    /* ─── Dataframe ─────────────────────────────────────────── */
    [data-testid="stDataFrame"] {
        border: 1px solid #30363d !important;
        border-radius: 10px !important;
        overflow: hidden !important;
    }

    /* ─── Welcome & tip boxes ───────────────────────────────── */
    .emad-welcome {
        background: #161b22;
        border: 1px solid #30363d;
        border-right: 3px solid #1a7fc1;
        border-radius: 10px;
        padding: 1.2rem 1.5rem;
        color: #8b949e;
        font-size: 0.95rem;
        line-height: 1.8;
        direction: rtl;
        text-align: right;
    }
    .emad-tip {
        background: #0d2818;
        border: 1px solid #21382a;
        border-right: 3px solid #2ea043;
        border-radius: 10px;
        padding: 1rem 1.4rem;
        margin-top: 1rem;
        color: #7ee787;
        font-size: 0.9rem;
        line-height: 1.7;
        direction: rtl;
        text-align: right;
    }

    /* ─── Job Cards ─────────────────────────────────────────── */
    .jobs-container {
        display: flex;
        flex-direction: column;
        gap: 0.85rem;
        margin-top: 1rem;
        direction: rtl !important;
        text-align: right !important;
    }
    .job-card {
        background: #161b22;
        border: 1px solid #30363d;
        border-radius: 12px;
        padding: 1.25rem 1.5rem;
        display: flex;
        justify-content: space-between;
        align-items: center;
        gap: 1.25rem;
        direction: rtl !important;
        text-align: right !important;
        transition: transform 0.15s ease, border-color 0.15s ease, box-shadow 0.15s ease;
    }
    .job-card:hover {
        border-color: #1a7fc1;
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.45);
        transform: translateY(-2px);
    }
    .job-card-main {
        flex: 1;
        min-width: 0;
        direction: rtl !important;
        text-align: right !important;
    }
    .job-card-header {
        margin-bottom: 0.65rem;
    }
    .job-title {
        font-size: 1.15rem;
        font-weight: 700;
        color: #58a6ff;
        margin: 0 0 0.35rem 0;
        line-height: 1.35;
        word-break: break-word;
        font-family: 'Cairo', sans-serif !important;
    }
    .job-company {
        font-size: 0.95rem;
        font-weight: 600;
        color: #c9d1d9;
        display: flex;
        align-items: center;
        gap: 6px;
        font-family: 'Cairo', sans-serif !important;
    }
    .job-badges {
        display: flex;
        flex-wrap: wrap;
        gap: 0.45rem;
        align-items: center;
        direction: rtl !important;
    }
    .job-badge {
        display: inline-flex;
        align-items: center;
        gap: 4px;
        background: #21262d;
        border: 1px solid #30363d;
        border-radius: 6px;
        padding: 0.25rem 0.65rem;
        font-size: 0.8rem;
        color: #8b949e;
        white-space: nowrap;
        font-family: 'Cairo', sans-serif !important;
    }
    .job-badge-intern {
        background: rgba(56, 139, 253, 0.12);
        border-color: rgba(56, 139, 253, 0.35);
        color: #79c0ff;
        font-weight: 600;
    }
    .job-badge-remote {
        background: rgba(46, 160, 67, 0.12);
        border-color: rgba(46, 160, 67, 0.35);
        color: #7ee787;
        font-weight: 600;
    }
    .job-badge-hybrid {
        background: rgba(210, 153, 34, 0.12);
        border-color: rgba(210, 153, 34, 0.35);
        color: #e3b341;
    }
    .job-badge-seniority {
        background: rgba(163, 113, 247, 0.12);
        border-color: rgba(163, 113, 247, 0.35);
        color: #d2a8ff;
        font-weight: 600;
    }
    .job-badge-contract {
        background: rgba(240, 136, 62, 0.12);
        border-color: rgba(240, 136, 62, 0.35);
        color: #ffa657;
        font-weight: 600;
    }
    .job-card-action {
        flex-shrink: 0;
    }
    .job-apply-btn {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        gap: 8px;
        background: #1a7fc1;
        color: #ffffff !important;
        text-decoration: none !important;
        padding: 0.65rem 1.3rem;
        border-radius: 8px;
        font-size: 0.9rem;
        font-weight: 700;
        font-family: 'Cairo', sans-serif !important;
        transition: background 0.15s ease, transform 0.1s ease, box-shadow 0.15s ease;
        box-shadow: 0 2px 6px rgba(0, 0, 0, 0.3);
        white-space: nowrap;
    }
    .job-apply-btn:hover {
        background: #388bfd;
        color: #ffffff !important;
        transform: translateY(-1px);
        box-shadow: 0 4px 14px rgba(56, 139, 253, 0.35);
    }
    .job-apply-btn:active {
        transform: translateY(0);
    }

    /* ─── Tabs ──────────────────────────────────────────────── */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: transparent !important;
        border-bottom: 1px solid #30363d !important;
        padding-bottom: 0.2rem !important;
        direction: rtl !important;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: #161b22 !important;
        border: 1px solid #30363d !important;
        border-radius: 8px 8px 0 0 !important;
        color: #8b949e !important;
        font-family: 'Cairo', sans-serif !important;
        font-weight: 600 !important;
        font-size: 0.9rem !important;
        padding: 0.5rem 1.2rem !important;
    }
    .stTabs [data-baseweb="tab"]:hover {
        color: #e2e8f0 !important;
        border-color: #484f58 !important;
    }
    .stTabs [aria-selected="true"] {
        background-color: #21262d !important;
        border-color: #1a7fc1 !important;
        border-bottom-color: #21262d !important;
        color: #58a6ff !important;
    }

    /* ─── Responsive ────────────────────────────────────────── */
    @media (max-width: 768px) {
        .block-container { padding-left: 1rem !important; padding-right: 1rem !important; }
        .emad-title { font-size: 1.8rem; }
        .search-card { padding: 1.2rem 1rem 1rem; }
        .stRadio > div { flex-direction: column !important; }
    }

    /* ─── Hide Streamlit branding ───────────────────────────── */
    #MainMenu, footer { display: none !important; }
    </style>
    """,
    unsafe_allow_html=True,
)

# Location presets and taxonomy options
COUNTRIES = {
    "مصر": {
        "مصر كلها": "Egypt",
        "القاهرة (Cairo)": "Cairo, Egypt",
        "الجيزة (Giza)": "Giza, Egypt",
        "الإسكندرية (Alexandria)": "Alexandria, Egypt",
        "المنصورة / الدقهلية (Mansoura)": "Mansoura, Egypt",
        "طنطا / الغربية (Tanta)": "Tanta, Egypt",
        "الزقازيق / الشرقية (Zagazig)": "Zagazig, Egypt",
        "الإسماعيلية (Ismailia)": "Ismailia, Egypt",
        "بورسعيد (Port Said)": "Port Said, Egypt",
        "السويس (Suez)": "Suez, Egypt",
        "القليوبية / بنها (Qalyubia)": "Qalyubia, Egypt",
        "المنوفية / شبين الكوم (Menofia)": "Menofia, Egypt",
        "دمياط (Damietta)": "Damietta, Egypt",
        "كفر الشيخ (Kafr El Sheikh)": "Kafr El Sheikh, Egypt",
        "البحيرة / دمنهور (Beheira)": "Beheira, Egypt",
        "الفيوم (Faiyum)": "Faiyum, Egypt",
        "بني سويف (Beni Suef)": "Beni Suef, Egypt",
        "المنيا (Minya)": "Minya, Egypt",
        "أسيوط (Asyut)": "Asyut, Egypt",
        "سوهاج (Sohag)": "Sohag, Egypt",
        "قنا والأقصر وأسوان (Upper Egypt)": "Aswan, Egypt",
        "الغردقة / البحر الأحمر (Hurghada)": "Hurghada, Egypt",
        "شرم الشيخ / سيناء (South Sinai)": "Sharm El Sheikh, Egypt",
        "محافظة تانية (كتابة يدوية)": "__custom__",
    },
    "السعودية": {
        "السعودية كلها": "Saudi Arabia",
        "الرياض (Riyadh)": "Riyadh, Saudi Arabia",
        "جدة (Jeddah)": "Jeddah, Saudi Arabia",
        "الدمام والخبر (Eastern Province)": "Dammam, Saudi Arabia",
        "مكة المكرمة (Mecca)": "Mecca, Saudi Arabia",
        "المدينة المنورة (Medina)": "Medina, Saudi Arabia",
        "مدينة تانية (كتابة يدوية)": "__custom__",
    },
    "الإمارات": {
        "الإمارات كلها": "United Arab Emirates",
        "دبي (Dubai)": "Dubai, United Arab Emirates",
        "أبوظبي (Abu Dhabi)": "Abu Dhabi, United Arab Emirates",
        "الشارقة (Sharjah)": "Sharjah, United Arab Emirates",
        "إمارة تانية (كتابة يدوية)": "__custom__",
    },
    "بلد تانية (كتابة يدوية)": {
        "كتابة يدوية (Custom)": "__custom__",
    },
}

JOB_TYPES = {
    "الكل (مش فارقة معايا)": "all",
    "دوام كامل (Full-time)": "full_time",
    "دوام جزئي (Part-time)": "part_time",
    "عقد عمل / عمل حر (Contract)": "contract",
}

SENIORITY_LEVELS = {
    "الكل (أي مستوى)": "all",
    "تدريب طلبة وخريجين (Internship)": "internship",
    "مبتدئ / حديث تخرج (Junior / Entry)": "entry",
    "متوسط الخبرة (Mid-Level)": "mid",
    "سينيور / خبير (Senior / Lead)": "senior",
    "إدارة وقيادة (Manager / Director)": "director",
}

WORKPLACE_TYPES = {
    "الكل (المهم نشتغل)": "all",
    "Remote - من البيت": "remote",
    "Hybrid - يومين كده ويومين كده": "hybrid",
    "On-site - من الشركة": "onsite",
}

DATE_POSTED_OPTIONS = {
    "آخر أسبوع (أحسن فرصة للتقديم)": "past_week",
    "آخر 24 ساعة (طازة طازة)": "past_24h",
    "أي وقت (المتاح كله)": "all",
}

# Page header
st.markdown(
    """
    <div class="emad-header">
        <div class="emad-logo">
            <span class="emad-logo-dot"></span>
            عماد
            <span class="emad-logo-dot"></span>
        </div>
        <div class="emad-title">يا فتّاح يا عليم، يا رزّاق يا كريم... <span>أأمر</span></div>
    </div>
    """,
    unsafe_allow_html=True,
)

# Search Card 1: Role, Seniority, and Job Type
keywords_input = st.text_input(
    "عايز تشتغل إيه بالظبط؟ (Job Title)",
    value="Data Analyst",
    placeholder="مثلاً: Python, Data Analyst, Flutter...",
    help="ممكن تكتب أكتر من مسمى وتفصل بينهم بفاصلة (,) وعماد هيدور عليهم كلهم.",
)

st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)

col_jt, col_sen, col_wp = st.columns(3)
with col_jt:
    job_type_label = st.selectbox(
        "نوع الشغلانة (التعاقد)",
        options=list(JOB_TYPES.keys()),
        index=0,
        help="دوام كامل، دوام جزئي، أو عقود عمل وفريلانس.",
    )
    selected_job_type = JOB_TYPES[job_type_label]

with col_sen:
    seniority_label = st.selectbox(
        " مستوى الخبرة (Seniority)",
        options=list(SENIORITY_LEVELS.keys()),
        index=0,
        help="مبتدئ، متوسط، سينيور، أو تدريب.. عماد هيفلترلك المسمى بدقة.",
    )
    selected_seniority = SENIORITY_LEVELS[seniority_label]

with col_wp:
    workplace_label = st.selectbox(
        "طريقة الشغل (بيئة العمل)",
        options=list(WORKPLACE_TYPES.keys()),
        index=0,
        help="عايز تشتغل من البيت وتحت التكييف، ولا مستعد تنزل مقر الشركة؟",
    )
    selected_workplace = WORKPLACE_TYPES[workplace_label]


# Search Card 2: Location and Posting Date
col_country, col_city, col_date = st.columns([1, 1.6, 1.2])
with col_country:
    selected_country = st.selectbox("الدولة", options=list(COUNTRIES.keys()), index=0)
with col_city:
    available_cities = COUNTRIES[selected_country]
    selected_city_label = st.selectbox(
        "عايزها في محافظة إيه؟", options=list(available_cities.keys()), index=0
    )
with col_date:
    date_posted_label = st.selectbox(
        "الوظيفة نازله من إمتى؟",
        options=list(DATE_POSTED_OPTIONS.keys()),
        index=0,
        help="التقديم في أول 24 ساعة أو أول أسبوع بيزود فرصتك جداً إن الـ HR يشوف الـ CV بتاعك.",
    )
    selected_date_posted = DATE_POSTED_OPTIONS[date_posted_label]

target_location_query = available_cities[selected_city_label]
if target_location_query == "__custom__":
    custom_loc = st.text_input(
        "اكتب اسم المدينة أو الدولة بالإنجليزية (زي ما مكتوبة في LinkedIn)",
        value="Mansoura, Egypt",
        help="مثال: Mansoura, Egypt أو Riyadh, Saudi Arabia",
    )
    target_location_query = custom_loc.strip()

st.markdown("</div>", unsafe_allow_html=True)

# Search Action Button
st.markdown("<div style='height:0.2rem'></div>", unsafe_allow_html=True)
search_clicked = st.button("شوفلي الشغل يا عماد", type="primary", use_container_width=True)
st.markdown("<div style='height:1.5rem'></div>", unsafe_allow_html=True)

# Search execution and results state handling
if "scraped_jobs" not in st.session_state:
    st.session_state["scraped_jobs"] = []

search_fingerprint = (
    keywords_input.strip().lower(),
    selected_job_type,
    selected_seniority,
    selected_workplace,
    target_location_query.strip().lower(),
    selected_date_posted,
)
if "last_search_fingerprint" not in st.session_state:
    st.session_state["last_search_fingerprint"] = search_fingerprint

# Reset previous results if search parameters change before running a new search
if st.session_state["last_search_fingerprint"] != search_fingerprint:
    st.session_state["scraped_jobs"] = []
    st.session_state["last_search_fingerprint"] = search_fingerprint

# Sanitize legacy workplace values in active session state
for _old_job in st.session_state["scraped_jobs"]:
    if "غير محدد" in _old_job.get("بيئة العمل", ""):
        _old_job["بيئة العمل"] = "غير محدد"

search_attempted = False

if search_clicked:
    st.session_state["last_search_fingerprint"] = search_fingerprint
    keywords = [k.strip() for k in keywords_input.split(",") if k.strip()]

    if not keywords:
        st.error("يا ريس اكتب لعماد اسم وظيفة واحدة على الأقل يعرف يدور عليها!")
    elif not target_location_query:
        st.error("عماد تايه كده.. حدد له المحافظة أو الدولة اللي هيدور فيها!")
    else:
        search_attempted = True
        effective_location = target_location_query.strip()
        scraper = LinkedInScraper()
        progress_bar = st.progress(0)
        status_box = st.empty()

        def update_progress(ratio: float, msg: str):
            try:
                progress_bar.progress(min(max(float(ratio), 0.0), 1.0))
                status_box.info(msg)
            except Exception:
                pass

        try:
            with st.spinner("عماد شمّر ونازل يفرك في LinkedIn.. ثواني وجايلك بالتفاصيل"):
                jobs = scraper.scrape(
                    keywords=keywords,
                    location=effective_location,
                    job_type=selected_job_type,
                    seniority=selected_seniority,
                    workplace_type=selected_workplace,
                    date_posted=selected_date_posted,
                    pages_per_keyword=2,
                    progress_callback=update_progress,
                )
            st.session_state["scraped_jobs"] = jobs
        except Exception as e:
            search_attempted = False
            st.session_state["scraped_jobs"] = []
            st.error(f"حصلت مشكلة وأنا بدور: {e}. استرها معايا وجرب تاني")
            try:
                with open("crash.log", "a", encoding="utf-8") as f:
                    import traceback
                    f.write(traceback.format_exc() + "\n")
            except Exception:
                pass
        finally:
            try:
                progress_bar.empty()
                status_box.empty()
            except Exception:
                pass

# Render search results
results = st.session_state["scraped_jobs"]

if results:
    df = pd.DataFrame(results)

    total_jobs = len(df)
    unique_companies = df["الشركة"].nunique()
    remote_count = len(df[df["بيئة العمل"].str.contains("عن بُعد", na=False)])

    if selected_job_type == "contract":
        col3_metric_label = "عقود وعمل حر (Contract)"
        col3_metric_val = len(df[df["نوع الوظيفة"].str.contains("عقد|Contract|حر|Freelance", na=False)])
    else:
        col3_metric_label = "تدريبات (Internships)"
        col3_metric_val = len(df[df["نوع الوظيفة"].str.contains("تدريب|Intern", na=False)])

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("إجمالي اللي لقاه عماد", total_jobs)
    col2.metric("شركات بتطلب", unique_companies)
    col3.metric(col3_metric_label, col3_metric_val)
    col4.metric("شغل من البيت (Remote)", remote_count)

    st.markdown("<div style='height:0.8rem'></div>", unsafe_allow_html=True)

    top_bar_col1, top_bar_col2 = st.columns([3, 1])
    with top_bar_col1:
        st.success(f"لقينا {total_jobs} فرصة شغل/تدريب تناسب طلبك.")
    with top_bar_col2:
        csv_bytes = df.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")
        st.download_button(
            label="نزّل اللستة دي شيت Excel",
            data=csv_bytes,
            file_name="عماد_لقالك_شغل_linkedin.csv",
            mime="text/csv",
            use_container_width=True,
        )

    cards_html = []
    for job in results:
        title = html.escape(str(job.get("المسمى الوظيفي", "وظيفة بدون عنوان")))
        company = html.escape(str(job.get("الشركة", "غير محدد")))
        loc = html.escape(str(job.get("المكان", "مصر")))
        job_type = html.escape(str(job.get("نوع الوظيفة", "غير محدد")))
        post_date = html.escape(str(job.get("تاريخ النشر", "غير محدد")))
        link = job.get("رابط التقديم", "#")

        seniority = html.escape(str(job.get("مستوى الخبرة", "غير محدد")))
        seniority_html = f'<span class="job-badge job-badge-seniority">{seniority}</span>' if seniority != "غير محدد" else ""

        if "تدريب" in job_type or "Intern" in job_type:
            type_badge_class = "job-badge-intern"
        elif "عقد" in job_type or "Contract" in job_type or "حر" in job_type or "Freelance" in job_type:
            type_badge_class = "job-badge-contract"
        else:
            type_badge_class = "job-badge-default"

        type_html = f'<span class="job-badge {type_badge_class}">{job_type}</span>' if job_type != "غير محدد" else ""

        raw_workplace = str(job.get("بيئة العمل", ""))
        if "عن بُعد" in raw_workplace or "Remote" in raw_workplace:
            workplace_html = '<span class="job-badge job-badge-remote">عن بُعد (Remote)</span>'
        elif "هجين" in raw_workplace or "Hybrid" in raw_workplace:
            workplace_html = '<span class="job-badge job-badge-hybrid">هجين (Hybrid)</span>'
        elif ("من المقر" in raw_workplace or "On-site" in raw_workplace) and ("غير محدد" not in raw_workplace):
            workplace_html = '<span class="job-badge job-badge-default">من المقر (On-site)</span>'
        else:
            workplace_html = ""

        date_html = f'<span class="job-badge job-badge-date">{post_date}</span>' if post_date != "غير محدد" else ""

        card_html = (
            f'<div class="job-card">'
            f'<div class="job-card-main">'
            f'<div class="job-card-header">'
            f'<div class="job-title">{title}</div>'
            f'<div class="job-company">{company}</div>'
            f'</div>'
            f'<div class="job-badges">'
            f'<span class="job-badge job-badge-loc">{loc}</span>'
            f'{type_html}'
            f'{seniority_html}'
            f'{workplace_html}'
            f'{date_html}'
            f'</div>'
            f'</div>'
            f'<div class="job-card-action">'
            f'<a href="{link}" target="_blank" rel="noopener noreferrer" class="job-apply-btn">'
            f'قدّم على LinkedIn ↗'
            f'</a>'
            f'</div>'
            f'</div>'
        )
        cards_html.append(card_html)

    full_cards_html = f'<div class="jobs-container">{"".join(cards_html)}</div>'
    st.markdown(full_cards_html, unsafe_allow_html=True)

elif search_attempted:
    st.warning(
        "عماد رجع بإيده فاضية المرة دي! ملقتش حاجة مطابقة بالظبط للمواصفات دي.. "
        "جرب تغير المسمى شوية (مثلاً بدل مسمى ضيق، جرب مسمى أوسع زي Software بدل Specialized Junior Tool)، "
        "أو وسع نطاق المحافظة، وعماد هيفركلك فيها تاني."
    )
else:
    st.markdown("""
    
    """,unsafe_allow_html=True)
