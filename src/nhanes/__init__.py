"""
NHANES数据自动下载引擎
从CDC官网下载XPT文件，转换为pandas DataFrame，处理调查权重

支持:
- 多周期数据下载 (1999-2020)
- XPT → DataFrame转换
- 调查权重处理 (WTMEC2YR, WTINT2YR, SDMVPSU, SDMVSTRA)
- 多周期数据合并
"""

import os
import io
import json
import logging
import hashlib
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass, field
from datetime import datetime

import pandas as pd
import httpx

logger = logging.getLogger(__name__)

# ============================================================
# NHANES变量字典 (核心知识库)
# ============================================================

NHANES_CYCLES = [
    "1999-2000", "2001-2002", "2003-2004", "2005-2006",
    "2007-2008", "2009-2010", "2011-2012", "2013-2014",
    "2015-2016", "2017-2018", "2017-2020",
]

DATA_FILE_TYPES = {
    "DEMO": "Demographics", "BMX": "Body Measures", "BPX": "Blood Pressure",
    "BPQ": "Blood Pressure Questionnaire", "GLU": "Plasma Fasting Glucose",
    "TCHOL": "Total Cholesterol", "HDL": "HDL Cholesterol",
    "TRIGLY": "Triglycerides", "GLYCO": "Glycohemoglobin", "INS": "Insulin",
    "MCQ": "Medical Conditions Questionnaire", "DIQ": "Diabetes",
    "SMQ": "Smoking Questionnaire", "ALQ": "Alcohol Use",
    "PAQ": "Physical Activity", "DBQ": "Diet Behavior",
    "HUQ": "Health Utilization", "SLQ": "Sleep Disorders",
    "DPQ": "Depression Screener", "BIOPRO": "Biochemistry",
    "CBC": "Complete Blood Count",
}

# 常用NHANES变量完整字典
NHANES_VARIABLES: Dict[str, Dict[str, Any]] = {
    # 人口学
    "RIAGENDR": {"desc": "Gender", "table": "DEMO", "type": "categorical", "values": {1: "Male", 2: "Female"}},
    "RIDAGEYR": {"desc": "Age in years at screening", "table": "DEMO", "type": "continuous", "range": [0, 80]},
    "RIDRETH1": {"desc": "Race/Hispanic origin", "table": "DEMO", "type": "categorical",
                 "values": {1: "Mexican American", 2: "Other Hispanic", 3: "Non-Hispanic White",
                           4: "Non-Hispanic Black", 5: "Other Race/Multi-Racial"}},
    "RIDRETH3": {"desc": "Race/Hispanic origin w/ NH Asian", "table": "DEMO", "type": "categorical"},
    "DMDEDUC2": {"desc": "Education level (adults 20+)", "table": "DEMO", "type": "categorical",
                 "values": {1: "<9th grade", 2: "9-11th grade", 3: "HS/GED", 4: "Some college/AA", 5: "College graduate+"}},
    "INDFMPIR": {"desc": "Family income to poverty ratio", "table": "DEMO", "type": "continuous", "range": [0, 5]},
    "DMDMARTL": {"desc": "Marital status", "table": "DEMO", "type": "categorical"},
    "WTMEC2YR": {"desc": "Full sample 2 year MEC exam weight", "table": "DEMO", "type": "weight"},
    "WTINT2YR": {"desc": "Full sample 2 year interview weight", "table": "DEMO", "type": "weight"},
    "SDMVPSU": {"desc": "Masked variance pseudo-PSU", "table": "DEMO", "type": "psu"},
    "SDMVSTRA": {"desc": "Masked variance pseudo-stratum", "table": "DEMO", "type": "stratum"},
    # 体格测量
    "BMXBMI": {"desc": "Body Mass Index (kg/m2)", "table": "BMX", "type": "continuous", "range": [10, 80]},
    "BMXWT": {"desc": "Weight (kg)", "table": "BMX", "type": "continuous"},
    "BMXHT": {"desc": "Standing Height (cm)", "table": "BMX", "type": "continuous"},
    "BMXWAIST": {"desc": "Waist Circumference (cm)", "table": "BMX", "type": "continuous"},
    # 血压
    "BPXSY1": {"desc": "Systolic BP reading 1 (mmHg)", "table": "BPX", "type": "continuous"},
    "BPXDI1": {"desc": "Diastolic BP reading 1 (mmHg)", "table": "BPX", "type": "continuous"},
    "BPXSY2": {"desc": "Systolic BP reading 2 (mmHg)", "table": "BPX", "type": "continuous"},
    "BPXDI2": {"desc": "Diastolic BP reading 2 (mmHg)", "table": "BPX", "type": "continuous"},
    "BPQ020": {"desc": "Ever told you had high blood pressure", "table": "BPQ", "type": "categorical",
               "values": {1: "Yes", 2: "No", 7: "Refused", 9: "Don't know"}},
    # 实验室
    "LBXTC": {"desc": "Total cholesterol (mg/dL)", "table": "TCHOL", "type": "continuous", "range": [50, 400]},
    "LBXHDD": {"desc": "Direct HDL-cholesterol (mg/dL)", "table": "HDL", "type": "continuous", "range": [10, 150]},
    "LBXTR": {"desc": "Triglycerides (mg/dL)", "table": "TRIGLY", "type": "continuous"},
    "LBXGLU": {"desc": "Plasma glucose - fasting (mg/dL)", "table": "GLU", "type": "continuous", "range": [30, 500]},
    "LBXGH": {"desc": "Glycohemoglobin (%)", "table": "GLYCO", "type": "continuous", "range": [3, 18]},
    "LBXIN": {"desc": "Insulin (uU/mL)", "table": "INS", "type": "continuous"},
    "LBXSCR": {"desc": "Serum creatinine (mg/dL)", "table": "BIOPRO", "type": "continuous"},
    # 问卷
    "DIQ010": {"desc": "Doctor told you have diabetes", "table": "DIQ", "type": "categorical",
               "values": {1: "Yes", 2: "No", 3: "Borderline", 7: "Refused", 9: "Don't know"}},
    "SMQ020": {"desc": "Smoked at least 100 cigarettes in life", "table": "SMQ", "type": "categorical",
               "values": {1: "Yes", 2: "No"}},
    "SMQ040": {"desc": "Do you now smoke cigarettes", "table": "SMQ", "type": "categorical",
               "values": {1: "Every day", 2: "Some days", 3: "Not at all"}},
    "ALQ101": {"desc": "Had at least 12 drinks in a year", "table": "ALQ", "type": "categorical"},
    "ALQ120Q": {"desc": "How often drink per year", "table": "ALQ", "type": "continuous"},
    "ALQ130": {"desc": "Avg # drinks on drinking day", "table": "ALQ", "type": "continuous"},
    "PAQ605": {"desc": "Vigorous work activity", "table": "PAQ", "type": "categorical"},
    "PAQ650": {"desc": "Vigorous recreational activities", "table": "PAQ", "type": "categorical"},
    "MCQ160C": {"desc": "Ever told had heart attack", "table": "MCQ", "type": "categorical"},
    "MCQ160F": {"desc": "Ever told had a stroke", "table": "MCQ", "type": "categorical"},
    "MCQ220": {"desc": "Ever told you had cancer", "table": "MCQ", "type": "categorical"},
    "HUQ010": {"desc": "General health condition", "table": "HUQ", "type": "categorical",
               "values": {1: "Excellent", 2: "Very good", 3: "Good", 4: "Fair", 5: "Poor"}},
    "SLQ060": {"desc": "Hours of sleep on workdays", "table": "SLQ", "type": "continuous", "range": [1, 18]},
    "DPQ020": {"desc": "Feeling down/depressed/hopeless", "table": "DPQ", "type": "categorical"},
}


def _cycle_to_code(cycle: str) -> str:
    cycle_map = {
        "1999-2000": "", "2001-2002": "_B", "2003-2004": "_C",
        "2005-2006": "_D", "2007-2008": "_E", "2009-2010": "_F",
        "2011-2012": "_G", "2013-2014": "_H", "2015-2016": "_I",
        "2017-2018": "_J", "2017-2020": "_P",
    }
    return cycle_map.get(cycle, "")


def _build_xpt_url(cycle: str, table_code: str) -> str:
    suffix = _cycle_to_code(cycle)
    cycle_dir = cycle.replace("-", "")
    table_name = f"{table_code}{suffix}"
    return f"https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/{cycle_dir}/DataFiles/{table_name}.XPT"


class NHANESDownloader:
    def __init__(self, cache_dir: str = "./src/data/nhanes_cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._http_client = httpx.Client(
            timeout=120.0, follow_redirects=True,
            headers={"User-Agent": "NHANES-Research-Platform/1.0"}
        )

    def _get_cache_path(self, cycle: str, table_code: str) -> Path:
        return self.cache_dir / f"{table_code}_{cycle.replace('-', '_')}.parquet"

    def _load_from_cache(self, cycle: str, table_code: str) -> Optional[pd.DataFrame]:
        cache_path = self._get_cache_path(cycle, table_code)
        if cache_path.exists():
            logger.info(f"从缓存加载: {cache_path}")
            return pd.read_parquet(cache_path)
        return None

    def _save_to_cache(self, df: pd.DataFrame, cycle: str, table_code: str):
        cache_path = self._get_cache_path(cycle, table_code)
        df.to_parquet(cache_path, index=False)

    def download_xpt(self, cycle: str, table_code: str) -> pd.DataFrame:
        cached = self._load_from_cache(cycle, table_code)
        if cached is not None:
            return cached
        url = _build_xpt_url(cycle, table_code)
        logger.info(f"下载: {url}")
        try:
            response = self._http_client.get(url)
            response.raise_for_status()
        except httpx.HTTPError as e:
            raise ValueError(f"无法下载 {table_code} ({cycle}): HTTP {e}")
        try:
            df = pd.read_sas(io.BytesIO(response.content), format="xport")
        except Exception as e:
            raise ValueError(f"XPT文件解析失败: {e}")
        df["_cycle"] = cycle
        df["_table"] = table_code
        self._save_to_cache(df, cycle, table_code)
        logger.info(f"下载完成: {table_code} ({cycle}) - {len(df)} 行")
        return df

    def download_variables(self, variables: List[str], cycles: Optional[List[str]] = None) -> Dict[str, pd.DataFrame]:
        if cycles is None:
            cycles = ["2017-2018"]
        tables_needed: Dict[str, set] = {}
        for var in variables:
            if var in NHANES_VARIABLES:
                table_code = NHANES_VARIABLES[var]["table"]
                if table_code not in tables_needed:
                    tables_needed[table_code] = set()
                tables_needed[table_code].add(var)
        results: Dict[str, pd.DataFrame] = {}
        for table_code in tables_needed:
            for cycle in cycles:
                try:
                    df = self.download_xpt(cycle, table_code)
                    key = f"{table_code}_{cycle.replace('-', '_')}"
                    results[key] = df
                except ValueError as e:
                    logger.warning(f"跳过 {table_code} ({cycle}): {e}")
        return results

    def merge_tables(self, tables: Dict[str, pd.DataFrame], merge_on: str = "SEQN") -> pd.DataFrame:
        dfs = list(tables.values())
        if not dfs:
            raise ValueError("没有数据表可合并")
        merged = dfs[0]
        for df in dfs[1:]:
            common_cols = set(merged.columns) & set(df.columns)
            cols_to_merge = [merge_on] + [c for c in df.columns if c not in common_cols or c == merge_on]
            merged = pd.merge(merged, df[cols_to_merge], on=merge_on, how="outer")
        return merged

    def search_variables(self, keyword: str) -> List[Dict[str, Any]]:
        results = []
        kw = keyword.lower()
        for var_name, info in NHANES_VARIABLES.items():
            if kw in info["desc"].lower() or kw in var_name.lower():
                results.append({"name": var_name, **info})
        return results


class NHANESDataProcessor:
    @staticmethod
    def clean_demographics(df: pd.DataFrame) -> pd.DataFrame:
        if "RIDAGEYR" in df.columns:
            df = df[df["RIDAGEYR"] >= 20].copy()
        if "RIAGENDR" in df.columns:
            df["gender"] = df["RIAGENDR"].map({1: "Male", 2: "Female"})
        if "RIDRETH1" in df.columns:
            df["race"] = df["RIDRETH1"].map({1: "Mexican American", 2: "Other Hispanic",
                                              3: "Non-Hispanic White", 4: "Non-Hispanic Black", 5: "Other Race"})
        return df

    @staticmethod
    def create_bmi_categories(df: pd.DataFrame) -> pd.DataFrame:
        if "BMXBMI" in df.columns:
            df["bmi_category"] = pd.cut(df["BMXBMI"], bins=[0, 18.5, 25, 30, 100],
                                        labels=["Underweight", "Normal", "Overweight", "Obese"])
        return df

    @staticmethod
    def create_hypertension_flag(df: pd.DataFrame) -> pd.DataFrame:
        if "BPXSY1" in df.columns and "BPXDI1" in df.columns:
            df["hypertension"] = ((df["BPXSY1"] >= 140) | (df["BPXDI1"] >= 90)).astype(int)
        if "BPQ020" in df.columns:
            df.loc[df["BPQ020"] == 1, "hypertension"] = 1
        return df

    @staticmethod
    def create_diabetes_flag(df: pd.DataFrame) -> pd.DataFrame:
        if "DIQ010" in df.columns:
            df["diabetes"] = (df["DIQ010"] == 1).astype(int)
        if "LBXGLU" in df.columns:
            df.loc[df["LBXGLU"] >= 126, "diabetes"] = 1
        return df

    @staticmethod
    def handle_missing(df: pd.DataFrame, strategy: str = "listwise") -> pd.DataFrame:
        if strategy == "listwise":
            return df.dropna()
        elif strategy == "mean":
            numeric_cols = df.select_dtypes(include=["float64", "int64"]).columns
            df[numeric_cols] = df[numeric_cols].fillna(df[numeric_cols].mean())
            return df
        return df

    @staticmethod
    def apply_survey_subset(df: pd.DataFrame, age_min: int = 20, age_max: int = 80) -> pd.DataFrame:
        if "RIDAGEYR" in df.columns:
            df = df[(df["RIDAGEYR"] >= age_min) & (df["RIDAGEYR"] <= age_max)]
        return df
