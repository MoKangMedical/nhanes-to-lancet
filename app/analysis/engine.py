"""
Analysis Engine - Orchestrates all statistical analyses for NHANES data.

Coordinates:
- Survey-weighted descriptive statistics
- Survival analysis (KM, Cox, Fine-Gray)
- Table generation (Lancet standard)
- Figure generation (publication quality)
"""
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any

import pandas as pd

from .survey import SurveyAnalyzer
from .survival import SurvivalAnalyzer
from .tables import TableGenerator
from .figures import FigureGenerator
from ..config import RESULTS_DIR

logger = logging.getLogger(__name__)


class AnalysisEngine:
    """Main analysis engine orchestrating all statistical analyses."""
    
    def __init__(self, project_id: str = "default"):
        self.project_id = project_id
        self.output_dir = RESULTS_DIR / project_id
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.survey = SurveyAnalyzer()
        self.survival = SurvivalAnalyzer()
        self.tables = TableGenerator()
        self.figures = FigureGenerator(self.output_dir / "figures")
    
    def run_descriptive_analysis(self, df: pd.DataFrame,
                                   continuous_vars: List[str],
                                   categorical_vars: List[str],
                                   group_var: Optional[str] = None,
                                   weight_col: Optional[str] = None) -> Dict[str, Any]:
        """Run comprehensive descriptive analysis."""
        results = {
            "n_total": len(df),
            "continuous": {},
            "categorical": {},
            "group_comparison": {},
        }
        
        # Continuous variables
        for var in continuous_vars:
            if var in df.columns:
                stats = self.survey.weighted_mean(df, var, weight_col)
                med = self.survey.weighted_median(df, var, weight_col)
                results["continuous"][var] = {**stats, **med}
                
                # Subgroup analysis if group_var specified
                if group_var and group_var in df.columns:
                    sub = self.survey.subgroup_analysis(df, var, group_var,
                                                         "weighted_mean", weight_col)
                    results["group_comparison"][var] = sub
        
        # Categorical variables
        for var in categorical_vars:
            if var in df.columns:
                freq = self.survey.weighted_frequency(df, var, weight_col)
                results["categorical"][var] = freq
                
                # Chi-square test if grouped
                if group_var and group_var in df.columns:
                    chi2 = self.survey.weighted_chi_square(df, var, group_var, weight_col)
                    results["group_comparison"][var] = chi2
        
        return results
    
    def run_regression_analysis(self, df: pd.DataFrame,
                                  outcome: str,
                                  predictors: List[str],
                                  model_type: str = "logistic",
                                  weight_col: Optional[str] = None) -> Dict[str, Any]:
        """Run regression analysis."""
        if model_type == "logistic":
            return self.survey.weighted_logistic_regression(df, outcome, predictors, weight_col)
        elif model_type == "linear":
            return self.survey.weighted_linear_regression(df, outcome, predictors, weight_col)
        else:
            return {"error": f"Unknown model type: {model_type}"}
    
    def run_survival_analysis(self, df: pd.DataFrame,
                                time_var: str,
                                event_var: str,
                                group_var: Optional[str] = None,
                                covariates: Optional[List[str]] = None,
                                analysis_types: List[str] = None) -> Dict[str, Any]:
        """Run survival analysis (KM, Cox, Fine-Gray)."""
        analysis_types = analysis_types or ["km", "cox"]
        results = {}
        
        # Prepare data path for R scripts
        data_path = str(self.output_dir / "analysis_data.csv")
        df.to_csv(data_path, index=False)
        
        if "km" in analysis_types:
            km_script = self.survival.generate_km_script(
                data_path, str(self.output_dir),
                time_var, event_var, group_var
            )
            results["km"] = self.survival.execute_r_script(km_script, "kaplan_meier.R")
        
        if "cox" in analysis_types and covariates:
            cox_script = self.survival.generate_cox_script(
                data_path, str(self.output_dir),
                time_var, event_var, covariates
            )
            results["cox"] = self.survival.execute_r_script(cox_script, "cox_regression.R")
        
        if "fine_gray" in analysis_types and covariates:
            fg_script = self.survival.generate_fine_gray_script(
                data_path, str(self.output_dir),
                time_var, event_var,
                event_of_interest=1, competing_event=2,
                covariates=covariates
            )
            results["fine_gray"] = self.survival.execute_r_script(fg_script, "fine_gray.R")
        
        return results
    
    def generate_publication_tables(self, df: pd.DataFrame,
                                      descriptive_results: Dict[str, Any],
                                      regression_results: Optional[Dict[str, Any]] = None,
                                      group_var: Optional[str] = None,
                                      continuous_vars: Optional[List[str]] = None,
                                      categorical_vars: Optional[List[str]] = None) -> Dict[str, str]:
        """Generate all publication tables."""
        tables = {}
        
        # Table 1: Baseline
        tables["table1"] = self.tables.table1_baseline(
            df, group_var, continuous_vars, categorical_vars
        )
        
        # Table 2: Regression
        if regression_results and "coefficients" in regression_results:
            tables["table2"] = self.tables.table2_regression(regression_results)
        
        # STROBE checklist
        tables["strobe"] = self.tables.generate_strobe_checklist()
        
        return tables
    
    def generate_publication_figures(self, df: pd.DataFrame,
                                       continuous_vars: List[str],
                                       categorical_vars: List[str],
                                       group_var: Optional[str] = None,
                                       weight_col: Optional[str] = None) -> Dict[str, str]:
        """Generate all publication figures."""
        figures = {}
        
        # Histograms for continuous variables
        for var in continuous_vars[:5]:  # Limit to 5
            if var in df.columns:
                path = self.figures.weighted_histogram(
                    df, var, weight_col, group_var=group_var
                )
                figures[f"hist_{var}"] = path
        
        # Bar charts for categorical variables
        for var in categorical_vars[:3]:  # Limit to 3
            if var in df.columns:
                path = self.figures.bar_chart(df, var, weight_col, horizontal=True)
                figures[f"bar_{var}"] = path
        
        # Correlation heatmap
        if len(continuous_vars) >= 3:
            path = self.figures.correlation_heatmap(df, continuous_vars[:8])
            if path:
                figures["correlation"] = path
        
        return figures
    
    def get_output_summary(self) -> Dict[str, Any]:
        """Get summary of all generated outputs."""
        summary = {
            "tables": [],
            "figures": [],
            "r_scripts": [],
            "data_files": [],
        }
        
        for f in self.output_dir.rglob("*"):
            if f.is_file():
                rel = str(f.relative_to(self.output_dir))
                if f.suffix == ".csv":
                    summary["data_files"].append(rel)
                elif f.suffix == ".png":
                    summary["figures"].append(rel)
                elif f.suffix == ".R":
                    summary["r_scripts"].append(rel)
                elif f.suffix in [".md", ".txt"]:
                    summary["tables"].append(rel)
        
        return summary
