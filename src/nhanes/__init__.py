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
    "2015-2016", "2017-2018", "2017-2020",  # 2017-2020 pre-pandemic
]

# 数据文件类型
DATA_FILE_TYPES = {
    "DEMO": "Demographics",
    "BMX": "Body Measures",
    "BPX": "Blood Pressure",
    "BPQ": "Blood Pressure Questionnaire",
    "LAB": "Laboratory",
    "GLU": "Plasma Fasting Glucose",
    "TCHOL": "Total Cholesterol",
    "HDL": "HDL Cholesterol",
    "TRIGLY": "Triglycerides",
    "GLYCO": "Glycohemoglobin",
    "INS": "Insulin",
    "MCQ": "Medical Conditions Questionnaire",
    "HIQ": "Health Insurance",
    "HUQ": "Health Utilization",
    "DIQ": "Diabetes",
    "SMQ": "Smoking Questionnaire",
    "ALQ": "Alcohol Use",
    "PAQ": "Physical Activity",
    "DBQ": "Diet Behavior",
    "OHQ": "Oral Health",
    "RXQ_RX": "Prescription Medications",
    "KIQ_U": "Kidney Conditions",
    "CDQ": "Cardiovascular Disease",
    "HSQ": "Health Status",
    "PFQ": "Physical Functioning",
    "SLQ": "Sleep Disorders",
    "DPQ": "Depression Screener",
    "OCQ": "Occupation",
    "ECQ": "Early Childhood",
    "AUQ": "Audiometry Questionnaire",
    "VIX": "Vision",
}

# 常用NHANES变量完整字典
NHANES_VARIABLES: Dict[str, Dict[str, Any]] = {
    # ============ 人口学变量 ============
    "RIAGENDR": {"desc": "Gender", "table": "DEMO", "type": "categorical", "values": {1: "Male", 2: "Female"}},
    "RIDAGEYR": {"desc": "Age in years at screening", "table": "DEMO", "type": "continuous", "range": [0, 80]},
    "RIDAGEMN": {"desc": "Age in months at screening", "table": "DEMO", "type": "continuous"},
    "RIDRETH1": {"desc": "Race/Hispanic origin", "table": "DEMO", "type": "categorical",
                 "values": {1: "Mexican American", 2: "Other Hispanic", 3: "Non-Hispanic White",
                           4: "Non-Hispanic Black", 5: "Other Race/Multi-Racial"}},
    "RIDRETH3": {"desc": "Race/Hispanic origin w/ NH Asian", "table": "DEMO", "type": "categorical"},
    "DMDEDUC2": {"desc": "Education level (adults 20+)", "table": "DEMO", "type": "categorical",
                 "values": {1: "<9th grade", 2: "9-11th grade", 3: "HS/GED", 4: "Some college/AA", 5: "College graduate+"}},
    "INDFMPIR": {"desc": "Family income to poverty ratio", "table": "DEMO", "type": "continuous", "range": [0, 5]},
    "DMDMARTL": {"desc": "Marital status", "table": "DEMO", "type": "categorical"},
    "DMDCITZN": {"desc": "Citizenship status", "table": "DEMO", "type": "categorical"},
    "WTPH2YR": {"desc": "Full sample 2 year MEC exam weight", "table": "DEMO", "type": "weight"},
    "WTMEC2YR": {"desc": "Full sample 2 year MEC exam weight", "table": "DEMO", "type": "weight"},
    "WTINT2YR": {"desc": "Full sample 2 year interview weight", "table": "DEMO", "type": "weight"},
    "SDMVPSU": {"desc": "Masked variance pseudo-PSU", "table": "DEMO", "type": "psu"},
    "SDMVSTRA": {"desc": "Masked variance pseudo-stratum", "table": "DEMO", "type": "stratum"},

    # ============ 体格测量变量 ============
    "BMXBMI": {"desc": "Body Mass Index (kg/m2)", "table": "BMX", "type": "continuous", "range": [10, 80]},
    "BMXWT": {"desc": "Weight (kg)", "table": "BMX", "type": "continuous"},
    "BMXHT": {"desc": "Standing Height (cm)", "table": "BMX", "type": "continuous"},
    "BMXWAIST": {"desc": "Waist Circumference (cm)", "table": "BMX", "type": "continuous"},
    "BMXHIP": {"desc": "Hip Circumference (cm)", "table": "BMX", "type": "continuous"},
    "BMXARML": {"desc": "Upper Arm Length (cm)", "table": "BMX", "type": "continuous"},
    "BMXARMC": {"desc": "Arm Circumference (cm)", "table": "BMX", "type": "continuous"},
    "BMXHEAD": {"desc": "Head Circumference (cm)", "table": "BMX", "type": "continuous"},
    "BMXLEG": {"desc": "Upper Leg Length (cm)", "table": "BMX", "type": "continuous"},

    # ============ 血压变量 ============
    "BPXSY1": {"desc": "Systolic BP reading 1 (mmHg)", "table": "BPX", "type": "continuous"},
    "BPXDI1": {"desc": "Diastolic BP reading 1 (mmHg)", "table": "BPX", "type": "continuous"},
    "BPXSY2": {"desc": "Systolic BP reading 2 (mmHg)", "table": "BPX", "type": "continuous"},
    "BPXDI2": {"desc": "Diastolic BP reading 2 (mmHg)", "table": "BPX", "type": "continuous"},
    "BPXSY3": {"desc": "Systolic BP reading 3 (mmHg)", "table": "BPX", "type": "continuous"},
    "BPXDI3": {"desc": "Diastolic BP reading 3 (mmHg)", "table": "BPX", "type": "continuous"},
    "BPQ020": {"desc": "Ever told you had high blood pressure", "table": "BPQ", "type": "categorical",
               "values": {1: "Yes", 2: "No", 7: "Refused", 9: "Don't know"}},
    "BPQ030": {"desc": "Told had high blood pressure - 2+ times", "table": "BPQ", "type": "categorical"},
    "BPQ040A": {"desc": "Taking prescribed medicine for HBP", "table": "BPQ", "type": "categorical"},

    # ============ 实验室变量 ============
    "LBXTC": {"desc": "Total cholesterol (mg/dL)", "table": "TCHOL", "type": "continuous", "range": [50, 400]},
    "LBDTCSI": {"desc": "Total cholesterol (mmol/L)", "table": "TCHOL", "type": "continuous"},
    "LBXHDD": {"desc": "Direct HDL-cholesterol (mg/dL)", "table": "HDL", "type": "continuous", "range": [10, 150]},
    "LBDHDDSI": {"desc": "Direct HDL-cholesterol (mmol/L)", "table": "HDL", "type": "continuous"},
    "LBXTR": {"desc": "Triglycerides (mg/dL)", "table": "TRIGLY", "type": "continuous"},
    "LBDTRSI": {"desc": "Triglycerides (mmol/L)", "table": "TRIGLY", "type": "continuous"},
    "LBXGLU": {"desc": "Plasma glucose - fasting (mg/dL)", "table": "GLU", "type": "continuous", "range": [30, 500]},
    "LBDGLUSI": {"desc": "Plasma glucose - fasting (mmol/L)", "table": "GLU", "type": "continuous"},
    "LBXGH": {"desc": "Glycohemoglobin (%)", "table": "GLYCO", "type": "continuous", "range": [3, 18]},
    "LBXIN": {"desc": "Insulin (uU/mL)", "table": "INS", "type": "continuous"},
    "LBDINSI": {"desc": "Insulin (pmol/L)", "table": "INS", "type": "continuous"},
    "LBXSCR": {"desc": "Serum creatinine (mg/dL)", "table": "BIOPRO", "type": "continuous"},
    "LBXSBU": {"desc": "Blood urea nitrogen (mg/dL)", "table": "BIOPRO", "type": "continuous"},
    "LBXSGTSI": {"desc": "GGT (U/L)", "table": "BIOPRO", "type": "continuous"},
    "LBXSATSI": {"desc": "ALT (U/L)", "table": "BIOPRO", "type": "continuous"},
    "LBXSASSI": {"desc": "AST (U/L)", "table": "BIOPRO", "type": "continuous"},
    "LBXWBCSI": {"desc": "White blood cell count (10*3/uL)", "table": "CBC", "type": "continuous"},
    "LBXHGB": {"desc": "Hemoglobin (g/dL)", "table": "CBC", "type": "continuous"},
    "LBXHCT": {"desc": "Hematocrit (%)", "table": "CBC", "type": "continuous"},
    "LBXPLTSI": {"desc": "Platelet count (10*3/uL)", "table": "CBC", "type": "continuous"},

    # ============ 问卷变量 ============
    "DIQ010": {"desc": "Doctor told you have diabetes", "table": "DIQ", "type": "categorical",
               "values": {1: "Yes", 2: "No", 3: "Borderline", 7: "Refused", 9: "Don't know"}},
    "DIQ050": {"desc": "Taking insulin now", "table": "DIQ", "type": "categorical"},
    "DIQ070": {"desc": "Take diabetic pills", "table": "DIQ", "type": "categorical"},
    "SMQ020": {"desc": "Smoked at least 100 cigarettes in life", "table": "SMQ", "type": "categorical",
               "values": {1: "Yes", 2: "No", 7: "Refused", 9: "Don't know"}},
    "SMQ040": {"desc": "Do you now smoke cigarettes", "table": "SMQ", "type": "categorical",
               "values": {1: "Every day", 2: "Some days", 3: "Not at all"}},
    "ALQ101": {"desc": "Had at least 12 drinks in a year", "table": "ALQ", "type": "categorical"},
    "ALQ111": {"desc": "Had at least 1 drink in past year", "table": "ALQ", "type": "categorical"},
    "ALQ120Q": {"desc": "How often drink per year", "table": "ALQ", "type": "continuous"},
    "ALQ130": {"desc": "Avg # drinks on drinking day", "table": "ALQ", "type": "continuous"},
    "PAQ605": {"desc": "Vigorous work activity", "table": "PAQ", "type": "categorical"},
    "PAQ610": {"desc": "Number of days vigorous work", "table": "PAQ", "type": "continuous"},
    "PAQ620": {"desc": "Moderate work activity", "table": "PAQ", "type": "categorical"},
    "PAQ650": {"desc": "Vigorous recreational activities", "table": "PAQ", "type": "categorical"},
    "PAQ660": {"desc": "Number of days vigorous recreation", "table": "PAQ", "type": "continuous"},
    "PAQ665": {"desc": "Moderate recreational activities", "table": "PAQ", "type": "categorical"},
    "MCQ160C": {"desc": "Ever told had heart attack", "table": "MCQ", "type": "categorical"},
    "MCQ160D": {"desc": "Ever told had angina/angina pectoris", "table": "MCQ", "type": "categorical"},
    "MCQ160E": {"desc": "Ever told had heart attack", "table": "MCQ", "type": "categorical"},
    "MCQ160F": {"desc": "Ever told had a stroke", "table": "MCQ", "type": "categorical"},
    "MCQ300C": {"desc": "Close relative had heart attack", "table": "MCQ", "type": "categorical"},
    "MCQ220": {"desc": "Ever told you had cancer", "table": "MCQ", "type": "categorical"},
    "HUQ010": {"desc": "General health condition", "table": "HUQ", "type": "categorical",
               "values": {1: "Excellent", 2: "Very good", 3: "Good", 4: "Fair", 5: "Poor"}},
    "HUQ030": {"desc": "Routine place to go for healthcare", "table": "HUQ", "type": "categorical"},
    "SLQ050": {"desc": "Ever told doctor had trouble sleeping", "table": "SLQ", "type": "categorical"},
    "SLQ060": {"desc": "Hours of sleep on workdays", "table": "SLQ", "type": "continuous", "range": [1, 18]},
    "DPQ020": {"desc": "Feeling down/depressed/hopeless", "table": "DPQ", "type": "categorical"},
    "DBQ700": {"desc": "How healthy is your diet", "table": "DBQ", "type": "categorical"},
}


# ============================================================
# CDC XPT文件下载
# ============================================================

@dataclass
class NHANESFileInfo:
    """NHANES数据文件元信息"""
    cycle: str              # e.g. "2017-2018"
    table_name: str         # e.g. "DEMO_J"
    file_code: str          # e.g. "DEMO"
    description: str
    url: str
    seqn_count: int = 0     # 参与者数量


def _cycle_to_code(cycle: str) -> str:
    """将调查周期转为后缀代码"""
    cycle_map = {
        "1999-2000": "", "2001-2002": "_B", "2003-2004": "_C",
        "2005-2006": "_D", "2007-2008": "_E", "2009-2010": "_F",
        "2011-2012": "_G", "2013-2014": "_H", "2015-2016": "_I",
        "2017-2018": "_J", "2017-2020": "_P",
    }
    return cycle_map.get(cycle, "")


def _build_xpt_url(cycle: str, table_code: str) -> str:
    """构建CDC XPT文件下载URL"""
    suffix = _cycle_to_code(cycle)
    cycle_dir = cycle.replace("-", "")
    table_name = f"{table_code}{suffix}"
    return f"https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/{cycle_dir}/DataFiles/{table_name}.XPT"


class NHANESDownloader:
    """
    NHANES数据下载器
    从CDC官网下载XPT文件并转换为pandas DataFrame
    """

    def __init__(self, cache_dir: str = "./src/data/nhanes_cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._http_client = httpx.Client(
            timeout=120.0,
            follow_redirects=True,
            headers={"User-Agent": "NHANES-Research-Platform/1.0"}
        )

    def _get_cache_path(self, cycle: str, table_code: str) -> Path:
        """获取缓存文件路径"""
        filename = f"{table_code}_{cycle.replace('-', '_')}.parquet"
        return self.cache_dir / filename

    def _is_cached(self, cycle: str, table_code: str) -> bool:
        """检查是否已缓存"""
        cache_path = self._get_cache_path(cycle, table_code)
        return cache_path.exists()

    def _load_from_cache(self, cycle: str, table_code: str) -> Optional[pd.DataFrame]:
        """从缓存加载数据"""
        cache_path = self._get_cache_path(cycle, table_code)
        if cache_path.exists():
            logger.info(f"从缓存加载: {cache_path}")
            return pd.read_parquet(cache_path)
        return None

    def _save_to_cache(self, df: pd.DataFrame, cycle: str, table_code: str):
        """保存数据到缓存"""
        cache_path = self._get_cache_path(cycle, table_code)
        df.to_parquet(cache_path, index=False)
        logger.info(f"已缓存: {cache_path}")

    def download_xpt(self, cycle: str, table_code: str) -> pd.DataFrame:
        """
        下载单个XPT文件并转换为DataFrame

        Args:
            cycle: 调查周期, 如 "2017-2018"
            table_code: 表代码, 如 "DEMO", "BMX"

        Returns:
            pandas DataFrame
        """
        # 检查缓存
        cached = self._load_from_cache(cycle, table_code)
        if cached is not None:
            return cached

        url = _build_xpt_url(cycle, table_code)
        logger.info(f"下载: {url}")

        try:
            response = self._http_client.get(url)
            response.raise_for_status()
        except httpx.HTTPError as e:
            logger.error(f"下载失败 {url}: {e}")
            raise ValueError(f"无法下载 {table_code} ({cycle}): HTTP {e}")

        # XPT文件转DataFrame
        try:
            df = pd.read_sas(io.BytesIO(response.content), format="xport")
        except Exception as e:
            logger.error(f"解析XPT失败 {table_code} ({cycle}): {e}")
            raise ValueError(f"XPT文件解析失败: {e}")

        # 添加元数据列
        df["_cycle"] = cycle
        df["_table"] = table_code

        logger.info(f"下载完成: {table_code} ({cycle}) - {len(df)} 行, {len(df.columns)} 列")

        # 保存到缓存
        self._save_to_cache(df, cycle, table_code)

        return df

    def download_variables(
        self,
        variables: List[str],
        cycles: Optional[List[str]] = None
    ) -> Dict[str, pd.DataFrame]:
        """
        根据变量列表下载所需的数据文件

        Args:
            variables: NHANES变量列表, 如 ["RIDAGEYR", "RIAGENDR", "BMXBMI"]
            cycles: 调查周期列表, 默认所有周期

        Returns:
            Dict[表名, DataFrame]
        """
        if cycles is None:
            cycles = ["2017-2018"]  # 默认最新完整周期

        # 确定需要下载哪些表
        tables_needed: Dict[str, set] = {}  # {table_code: {variables}}
        for var in variables:
            if var in NHANES_VARIABLES:
                table_code = NHANES_VARIABLES[var]["table"]
                if table_code not in tables_needed:
                    tables_needed[table_code] = set()
                tables_needed[table_code].add(var)
            else:
                logger.warning(f"未知变量: {var}, 尝试从DEMO表获取")

        # 下载每个表
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

    def merge_tables(
        self,
        tables: Dict[str, pd.DataFrame],
        merge_on: str = "SEQN"
    ) -> pd.DataFrame:
        """
        合并多个NHANES表

        Args:
            tables: 表字典
            merge_on: 合并键, 默认SEQN (参与者序号)

        Returns:
            合并后的DataFrame
        """
        dfs = list(tables.values())
        if not dfs:
            raise ValueError("没有数据表可合并")

        merged = dfs[0]
        for df in dfs[1:]:
            # 找到共同列（除了合并键和元数据列）
            common_cols = set(merged.columns) & set(df.columns)
            cols_to_merge = [merge_on] + [c for c in df.columns if c not in common_cols or c == merge_on]
            merged = pd.merge(merged, df[cols_to_merge], on=merge_on, how="outer")

        logger.info(f"合并完成: {len(merged)} 行, {len(merged.columns)} 列")
        return merged

    def get_variable_info(self, variable: str) -> Optional[Dict[str, Any]]:
        """获取变量信息"""
        return NHANES_VARIABLES.get(variable)

    def search_variables(self, keyword: str) -> List[Dict[str, Any]]:
        """按关键词搜索变量"""
        results = []
        keyword_lower = keyword.lower()
        for var_name, info in NHANES_VARIABLES.items():
            if keyword_lower in info["desc"].lower() or keyword_lower in var_name.lower():
                results.append({"name": var_name, **info})
        return results

    def list_available_tables(self, cycle: str) -> List[str]:
        """列出某周期可用的表"""
        return list(DATA_FILE_TYPES.keys())

    def get_cycle_info(self, cycle: str) -> Dict[str, Any]:
        """获取调查周期信息"""
        return {
            "cycle": cycle,
            "url_base": f"https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/{cycle.replace('-', '')}/",
            "available_tables": list(DATA_FILE_TYPES.keys()),
            "suffix": _cycle_to_code(cycle),
        }


# ============================================================
# 数据清洗与预处理
# ============================================================

class NHANESDataProcessor:
    """
    NHANES数据清洗与预处理
    """

    @staticmethod
    def clean_demographics(df: pd.DataFrame) -> pd.DataFrame:
        """清洗人口学数据"""
        # 年龄筛选 (通常研究成人20+)
        if "RIDAGEYR" in df.columns:
            df = df[df["RIDAGEYR"] >= 20].copy()

        # 性别编码
        if "RIAGENDR" in df.columns:
            df["gender"] = df["RIAGENDR"].map({1: "Male", 2: "Female"})

        # 种族编码
        if "RIDRETH1" in df.columns:
            race_map = {
                1: "Mexican American", 2: "Other Hispanic",
                3: "Non-Hispanic White", 4: "Non-Hispanic Black",
                5: "Other Race"
            }
            df["race"] = df["RIDRETH1"].map(race_map)

        # 教育编码
        if "DMDEDUC2" in df.columns:
            edu_map = {
                1: "<9th grade", 2: "9-11th grade",
                3: "HS/GED", 4: "Some college",
                5: "College graduate+"
            }
            df["education"] = df["DMDEDUC2"].map(edu_map)

        return df

    @staticmethod
    def create_bmi_categories(df: pd.DataFrame) -> pd.DataFrame:
        """创建BMI分类"""
        if "BMXBMI" in df.columns:
            df["bmi_category"] = pd.cut(
                df["BMXBMI"],
                bins=[0, 18.5, 25, 30, 100],
                labels=["Underweight", "Normal", "Overweight", "Obese"]
            )
        return df

    @staticmethod
    def create_hypertension_flag(df: pd.DataFrame) -> pd.DataFrame:
        """创建高血压标志"""
        if "BPXSY1" in df.columns and "BPXDI1" in df.columns:
            df["hypertension"] = (
                (df["BPXSY1"] >= 140) | (df["BPXDI1"] >= 90)
            ).astype(int)
        if "BPQ020" in df.columns:
            df.loc[df["BPQ020"] == 1, "hypertension"] = 1
        return df

    @staticmethod
    def create_diabetes_flag(df: pd.DataFrame) -> pd.DataFrame:
        """创建糖尿病标志"""
        if "DIQ010" in df.columns:
            df["diabetes"] = (df["DIQ010"] == 1).astype(int)
        if "LBXGLU" in df.columns:
            df.loc[df["LBXGLU"] >= 126, "diabetes"] = 1
        if "LBXGH" in df.columns:
            df.loc[df["LBXGH"] >= 6.5, "diabetes"] = 1
        return df

    @staticmethod
    def handle_missing(df: pd.DataFrame, strategy: str = "listwise") -> pd.DataFrame:
        """
        处理缺失数据

        Args:
            strategy: 'listwise' (删除), 'mean' (均值填充), 'median' (中位数填充)
        """
        if strategy == "listwise":
            return df.dropna()
        elif strategy == "mean":
            numeric_cols = df.select_dtypes(include=["float64", "int64"]).columns
            df[numeric_cols] = df[numeric_cols].fillna(df[numeric_cols].mean())
            return df
        elif strategy == "median":
            numeric_cols = df.select_dtypes(include=["float64", "int64"]).columns
            df[numeric_cols] = df[numeric_cols].fillna(df[numeric_cols].median())
            return df
        return df

    @staticmethod
    def apply_survey_subset(
        df: pd.DataFrame,
        age_min: int = 20,
        age_max: int = 80,
        exclude_pregnant: bool = True
    ) -> pd.DataFrame:
        """应用标准纳排条件"""
        original_n = len(df)

        if "RIDAGEYR" in df.columns:
            df = df[(df["RIDAGEYR"] >= age_min) & (df["RIDAGEYR"] <= age_max)]

        logger.info(f"纳排: {original_n} → {len(df)} 参与者")
        return df


# ============================================================
# 便捷函数
# ============================================================

def quick_download(
    variables: List[str],
    cycle: str = "2017-2018",
    output_path: Optional[str] = None
) -> pd.DataFrame:
    """
    快速下载NHANES数据

    Example:
        df = quick_download(["RIDAGEYR", "RIAGENDR", "BMXBMI", "BPXSY1"], "2017-2018")
    """
    downloader = NHANESDownloader()
    tables = downloader.download_variables(variables, [cycle])
    merged = downloader.merge_tables(tables)

    if output_path:
        merged.to_csv(output_path, index=False)
        logger.info(f"数据已保存到: {output_path}")

    return merged


def get_research_data(
    exposure_var: str,
    outcome_var: str,
    covariates: List[str],
    cycle: str = "2017-2018"
) -> pd.DataFrame:
    """
    获取研究数据

    Args:
        exposure_var: 暴露变量
        outcome_var: 结局变量
        covariates: 协变量列表
        cycle: 调查周期
    """
    all_vars = [exposure_var, outcome_var] + covariates

    # 确保包含调查权重
    weight_vars = ["WTMEC2YR", "SDMVPSU", "SDMVSTRA", "RIAGENDR", "RIDAGEYR"]
    for wv in weight_vars:
        if wv not in all_vars:
            all_vars.append(wv)

    downloader = NHANESDownloader()
    tables = downloader.download_variables(all_vars, [cycle])
    df = downloader.merge_tables(tables)

    # 数据清洗
    processor = NHANESDataProcessor()
    df = processor.clean_demographics(df)
    df = processor.handle_missing(df, strategy="listwise")

    return df


# ============================================================
# CLI入口
# ============================================================

if __name__ == "__main__":
    import sys

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    if len(sys.argv) > 1:
        topic = sys.argv[1]
        print(f"\n搜索NHANES变量: {topic}")
        downloader = NHANESDownloader()
        results = downloader.search_variables(topic)
        for r in results:
            print(f"  {r['name']:15s} | {r['table']:8s} | {r['desc']}")
    else:
        print("\nNHANES数据下载器")
        print("用法: python nhanes_downloader.py <关键词>")
        print("示例: python nhanes_downloader.py diabetes")
        print("      python nhanes_downloader.py bmi")
        print("      python nhanes_downloader.py blood pressure")
