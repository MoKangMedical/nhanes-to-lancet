"""
NHANES Data Processor - Clean, merge, and prepare NHANES data for analysis.

Key features:
- Survey weight calculation (multi-cycle adjustment)
- Variable recoding (age groups, BMI categories, etc.)
- Missing data handling
- Merging demographics + lab + questionnaire data
"""
import logging
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from ..config import SURVEY_PARAMS

logger = logging.getLogger(__name__)


class NHANESProcessor:
    """Process and clean NHANES data for statistical analysis."""
    
    # Standard NHANES recoding rules
    RECODE_RULES = {
        # Gender: 1=Male, 2=Female
        "RIAGENDR": {1: "Male", 2: "Female"},
        # Race/Ethnicity (RIDRETH1)
        "RIDRETH1": {
            1: "Mexican American",
            2: "Other Hispanic",
            3: "Non-Hispanic White",
            4: "Non-Hispanic Black",
            5: "Other Race/Multi-Racial",
        },
        # Race/Ethnicity (RIDRETH3) - newer version
        "RIDRETH3": {
            1: "Mexican American",
            2: "Other Hispanic",
            3: "Non-Hispanic White",
            4: "Non-Hispanic Black",
            6: "Non-Hispanic Asian",
            7: "Other Race/Multi-Racial",
        },
        # Education level (adults 20+)
        "DMDEDUC2": {
            1: "Less than 9th grade",
            2: "9-11th grade",
            3: "High school/GED",
            4: "Some college/AA degree",
            5: "College graduate or above",
            7: "Refused",
            9: "Don't know",
        },
        # Marital status
        "DMDMARTL": {
            1: "Married/living with partner",
            2: "Widowed",
            3: "Divorced",
            4: "Separated",
            5: "Never married",
            6: "Living with partner",
            77: "Refused",
            99: "Don't know",
        },
        # Diabetes diagnosis
        "DIQ010": {1: "Yes", 2: "No", 3: "Borderline", 7: "Refused", 9: "Don't know"},
        # Smoking status
        "SMQ020": {1: "Yes", 2: "No", 7: "Refused", 9: "Don't know"},
        "SMQ040": {1: "Every day", 2: "Some days", 3: "Not at all", 7: "Refused", 9: "Don't know"},
        # Hypertension
        "BPQ020": {1: "Yes", 2: "No", 7: "Refused", 9: "Don't know"},
        # General health
        "HUQ010": {
            1: "Excellent", 2: "Very good", 3: "Good", 4: "Fair", 5: "Poor",
            7: "Refused", 9: "Don't know",
        },
    }
    
    # Missing data codes in NHANES
    MISSING_CODES = {7, 9, 77, 99, 777, 999, 7777, 9999}
    
    def __init__(self):
        pass
    
    def clean_missing(self, df: pd.DataFrame, columns: Optional[List[str]] = None) -> pd.DataFrame:
        """Replace NHANES missing codes with NaN."""
        df = df.copy()
        cols = columns or df.columns.tolist()
        for col in cols:
            if col in df.columns and df[col].dtype in [np.float64, np.int64, float, int]:
                df[col] = df[col].replace(self.MISSING_CODES, np.nan)
        return df
    
    def recode_variable(self, df: pd.DataFrame, var: str) -> pd.Series:
        """Apply standard NHANES recoding to a variable."""
        if var in self.RECODE_RULES:
            return df[var].map(self.RECODE_RULES[var])
        return df[var]
    
    def calculate_bmi_categories(self, df: pd.DataFrame, bmi_col: str = "BMXBMI") -> pd.Series:
        """Categorize BMI according to WHO standards."""
        conditions = [
            df[bmi_col] < 18.5,
            (df[bmi_col] >= 18.5) & (df[bmi_col] < 25),
            (df[bmi_col] >= 25) & (df[bmi_col] < 30),
            df[bmi_col] >= 30,
        ]
        choices = ["Underweight", "Normal weight", "Overweight", "Obese"]
        return pd.Series(np.select(conditions, choices, default="Missing"), index=df.index)
    
    def calculate_age_groups(self, df: pd.DataFrame, age_col: str = "RIDAGEYR") -> pd.Series:
        """Create standard age groups."""
        bins = [0, 18, 30, 45, 60, 75, 120]
        labels = ["<18", "18-29", "30-44", "45-59", "60-74", "75+"]
        return pd.cut(df[age_col], bins=bins, labels=labels, right=False)
    
    def calculate_bp_categories(self, df: pd.DataFrame,
                                 sbp_col: str = "BPXSY1", dbp_col: str = "BPXDI1",
                                 med_col: str = "BPQ050A") -> pd.Series:
        """Classify blood pressure per ACC/AHA 2017 guidelines."""
        sbp = df[sbp_col]
        dbp = df[dbp_col]
        
        conditions = [
            (sbp < 120) & (dbp < 80),
            (sbp >= 120) & (sbp < 130) & (dbp < 80),
            ((sbp >= 130) & (sbp < 140)) | ((dbp >= 80) & (dbp < 90)),
            (sbp >= 140) | (dbp >= 90),
        ]
        choices = ["Normal", "Elevated", "Stage 1 Hypertension", "Stage 2 Hypertension"]
        bp_status = pd.Series(np.select(conditions, choices, default="Missing"), index=df.index)
        
        # If on BP medication, classify as hypertension
        if med_col in df.columns:
            on_meds = df[med_col] == 1
            bp_status[on_meds] = "Hypertension (treated)"
        
        return bp_status
    
    def calculate_smoking_status(self, df: pd.DataFrame,
                                  ever_smoke: str = "SMQ020",
                                  current_smoke: str = "SMQ040") -> pd.Series:
        """Classify smoking status."""
        conditions = [
            df[ever_smoke] == 2,  # Never smoked 100 cigarettes
            (df[ever_smoke] == 1) & (df[current_smoke] == 3),  # Former smoker
            (df[ever_smoke] == 1) & (df[current_smoke].isin([1, 2])),  # Current smoker
        ]
        choices = ["Never smoker", "Former smoker", "Current smoker"]
        return pd.Series(np.select(conditions, choices, default="Missing"), index=df.index)
    
    def adjust_survey_weights(self, df: pd.DataFrame, n_cycles: int,
                                weight_col: str = "WTMEC2YR") -> pd.Series:
        """
        Adjust survey weights when combining multiple NHANES cycles.
        
        NHANES guidelines: divide weight by number of cycles when combining.
        For 2 cycles: weight / 2, etc.
        """
        if weight_col not in df.columns:
            logger.warning(f"Weight column {weight_col} not found")
            return pd.Series(np.ones(len(df)), index=df.index)
        
        weights = df[weight_col].copy()
        # Divide by number of cycles
        adjusted = weights / n_cycles
        
        # Set zero/negative weights to NaN
        adjusted[adjusted <= 0] = np.nan
        
        return adjusted
    
    def create_analysis_dataset(
        self,
        demo_df: pd.DataFrame,
        lab_data: Dict[str, pd.DataFrame],
        quest_data: Dict[str, pd.DataFrame],
        variables: List[str],
        cycles: List[str],
    ) -> pd.DataFrame:
        """
        Merge demographics + lab + questionnaire data into analysis-ready dataset.
        
        Args:
            demo_df: Demographics dataframe
            lab_data: Dict of prefix -> merged lab dataframe
            quest_data: Dict of prefix -> merged questionnaire dataframe
            variables: List of variable names needed
            cycles: Number of cycles (for weight adjustment)
        """
        # Start with demographics
        df = demo_df.copy()
        
        # Add cycle count for weight adjustment
        n_cycles = len(cycles)
        
        # Merge lab data
        for prefix, lab_df in lab_data.items():
            if "SEQN" in lab_df.columns and "SEQN" in df.columns:
                # Keep only relevant columns
                keep_cols = ["SEQN"] + [c for c in lab_df.columns if c.upper() in [v.upper() for v in variables]]
                keep_cols = [c for c in keep_cols if c in lab_df.columns]
                if len(keep_cols) > 1:
                    lab_subset = lab_df[keep_cols].drop_duplicates(subset=["SEQN"])
                    df = df.merge(lab_subset, on="SEQN", how="left", suffixes=("", f"_{prefix}"))
        
        # Merge questionnaire data
        for prefix, quest_df in quest_data.items():
            if "SEQN" in quest_df.columns and "SEQN" in df.columns:
                keep_cols = ["SEQN"] + [c for c in quest_df.columns if c.upper() in [v.upper() for v in variables]]
                keep_cols = [c for c in keep_cols if c in quest_df.columns]
                if len(keep_cols) > 1:
                    quest_subset = quest_df[keep_cols].drop_duplicates(subset=["SEQN"])
                    df = df.merge(quest_subset, on="SEQN", how="left", suffixes=("", f"_{prefix}"))
        
        # Clean missing values
        df = self.clean_missing(df)
        
        # Adjust weights
        if n_cycles > 1:
            df["WTMEC2YR_ADJ"] = self.adjust_survey_weights(df, n_cycles, "WTMEC2YR")
            df["WTINT2YR_ADJ"] = self.adjust_survey_weights(df, n_cycles, "WTINT2YR")
        
        logger.info(f"Analysis dataset: {len(df)} rows, {len(df.columns)} columns")
        return df
    
    def generate_baseline_summary(self, df: pd.DataFrame,
                                    group_var: Optional[str] = None,
                                    continuous_vars: Optional[List[str]] = None,
                                    categorical_vars: Optional[List[str]] = None) -> dict:
        """Generate baseline characteristics summary (Table 1 style)."""
        result = {"total_n": len(df)}
        
        if continuous_vars:
            stats = {}
            for var in continuous_vars:
                if var in df.columns:
                    stats[var] = {
                        "mean": round(df[var].mean(), 2),
                        "sd": round(df[var].std(), 2),
                        "median": round(df[var].median(), 2),
                        "q1": round(df[var].quantile(0.25), 2),
                        "q3": round(df[var].quantile(0.75), 2),
                        "n_valid": int(df[var].notna().sum()),
                        "n_missing": int(df[var].isna().sum()),
                    }
            result["continuous"] = stats
        
        if categorical_vars:
            freq = {}
            for var in categorical_vars:
                if var in df.columns:
                    vc = df[var].value_counts(dropna=False)
                    freq[var] = {
                        str(k): {"count": int(v), "pct": round(v / len(df) * 100, 1)}
                        for k, v in vc.items()
                    }
            result["categorical"] = freq
        
        if group_var and group_var in df.columns:
            groups = {}
            for gval in df[group_var].dropna().unique():
                sub = df[df[group_var] == gval]
                groups[str(gval)] = {
                    "n": len(sub),
                    **self.generate_baseline_summary(sub, None, continuous_vars, categorical_vars)
                }
            result["by_group"] = groups
        
        return result
