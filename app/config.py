"""NHANES to Lancet - Configuration"""
import os
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
NHANES_CACHE = DATA_DIR / "nhanes_cache"
RESULTS_DIR = BASE_DIR / "results"
TEMP_DIR = BASE_DIR / "temp"

# Create directories
for d in [DATA_DIR, NHANES_CACHE, RESULTS_DIR, TEMP_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# NHANES CDC data source
NHANES_BASE_URL = "https://wwwn.cdc.gov/Nchs/Nhanes"
NHANES_CYCLES = [
    "1999-2000", "2001-2002", "2003-2004", "2005-2006",
    "2007-2008", "2009-2010", "2011-2012", "2013-2014",
    "2015-2016", "2017-2018", "2017-2020"
]

# NHANES data file categories
NHANES_DATA_CATEGORIES = {
    "DEMO": "Demographics",
    "BMX": "Body Measures",
    "BPX": "Blood Pressure",
    "BPQ": "Blood Pressure Questionnaire",
    "TCHOL": "Total Cholesterol",
    "HDL": "HDL Cholesterol",
    "TRIGLY": "Triglycerides",
    "GLU": "Glucose",
    "INS": "Insulin",
    "HBA1C": "Glycohemoglobin",
    "DIQ": "Diabetes",
    "MCQ": "Medical Conditions",
    "CDQ": "Cardiovascular Disease",
    "SMQ": "Smoking",
    "ALQ": "Alcohol Use",
    "PAQ": "Physical Activity",
    "DBQ": "Diet Behavior",
    "DR1TOT": "Dietary Intake Day 1",
    "DR2TOT": "Dietary Intake Day 2",
    "RXQ_RX": "Prescription Medications",
    "HUQ": "Health Care Utilization",
    "KIQ_U": "Kidney Conditions",
    "HEQ": "Hepatitis",
    "AUQ": "Audiometry",
    "OHQ": "Oral Health",
    "SLQ": "Sleep",
    "DPQ": "Depression",
    "CBQ": "Consumer Behavior",
    "WHQ": "Weight History",
    "PUQMEC": "Consumer Behavior Phone",
}

# Survey design parameters
SURVEY_PARAMS = {
    "weights": {
        "mec": "WTMEC2YR",       # MEC exam weight
        "interview": "WTINT2YR",  # Interview weight
        "dietary": "WTDRD1",      # Dietary day 1 weight
    },
    "psu": "SDMVPSU",    # Pseudo-PSU
    "strata": "SDMVSTRA", # Strata
}

# Lancet journal formatting
LANCET_CONFIG = {
    "abstract_max_words": 300,
    "article_max_words": 3000,
    "max_references": 30,
    "max_tables": 4,
    "max_figures": 3,
    "structured_sections": [
        "Background", "Methods", "Findings", "Interpretation"
    ],
    "color_scheme": {
        "primary": "#A51C30",
        "secondary": "#6B7280",
        "accent": "#1E40AF",
    }
}

# AI Configuration
AI_CONFIG = {
    "model": os.getenv("AI_MODEL", "deepseek-chat"),
    "api_key": os.getenv("DEEPSEEK_API_KEY", ""),
    "api_base": os.getenv("AI_API_BASE", "https://api.deepseek.com"),
    "temperature": 0.3,
    "max_tokens": 4096,
}

# Server
SERVER_HOST = os.getenv("HOST", "0.0.0.0")
SERVER_PORT = int(os.getenv("PORT", "8501"))
DEBUG = os.getenv("DEBUG", "false").lower() == "true"
