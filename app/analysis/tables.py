"""
Lancet-Standard Table Generator for NHANES Data.

Generates publication-ready tables:
- Table 1: Baseline characteristics
- Table 2: Regression results (OR/HR)
- Table 3: Subgroup analysis results
- STROBE checklist
"""
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class TableGenerator:
    """Generate Lancet-standard publication tables."""
    
    def __init__(self):
        pass
    
    def table1_baseline(self, df: pd.DataFrame,
                         group_var: Optional[str] = None,
                         continuous_vars: Optional[List[str]] = None,
                         categorical_vars: Optional[List[str]] = None,
                         weight_col: Optional[str] = None,
                         var_labels: Optional[Dict[str, str]] = None) -> str:
        """
        Generate Table 1: Baseline characteristics.
        Returns Markdown-formatted table.
        """
        lines = []
        var_labels = var_labels or {}
        
        # Header
        if group_var and group_var in df.columns:
            groups = sorted(df[group_var].dropna().unique())
            header = f"| Characteristic | Overall (n={len(df)}) |"
            separator = "|---|---|"
            for g in groups:
                n_g = len(df[df[group_var] == g])
                header += f" {g} (n={n_g}) |"
                separator += "---|"
            lines.append(header)
            lines.append(separator)
        else:
            lines.append(f"| Characteristic | N | Value |")
            lines.append("|---|---|---|")
        
        # Continuous variables
        if continuous_vars:
            for var in continuous_vars:
                if var not in df.columns:
                    continue
                label = var_labels.get(var, var)
                
                # Overall
                mean_all = df[var].mean()
                sd_all = df[var].std()
                n_all = df[var].notna().sum()
                
                if group_var:
                    row = f"| {label} | {mean_all:.1f} ({sd_all:.1f}) |"
                    for g in groups:
                        sub = df[df[group_var] == g][var]
                        if len(sub.dropna()) > 0:
                            row += f" {sub.mean():.1f} ({sub.std():.1f}) |"
                        else:
                            row += " — |"
                    lines.append(row)
                else:
                    lines.append(f"| {label} | {n_all} | {mean_all:.1f} ({sd_all:.1f}) |")
        
        # Categorical variables
        if categorical_vars:
            for var in categorical_vars:
                if var not in df.columns:
                    continue
                label = var_labels.get(var, var)
                lines.append(f"| **{label}** | | |")
                
                categories = sorted(df[var].dropna().unique())
                for cat in categories:
                    count = (df[var] == cat).sum()
                    pct = count / len(df) * 100
                    
                    if group_var:
                        row = f"|   {cat} | {count} ({pct:.1f}%) |"
                        for g in groups:
                            sub = df[df[group_var] == g]
                            n_g = (sub[var] == cat).sum()
                            pct_g = n_g / len(sub) * 100 if len(sub) > 0 else 0
                            row += f" {n_g} ({pct_g:.1f}%) |"
                        lines.append(row)
                    else:
                        lines.append(f"|   {cat} | {count} | {pct:.1f}% |")
        
        # P-value (if grouped)
        if group_var:
            lines.append("")
            lines.append("*P-values from chi-square test (categorical) or t-test (continuous)*")
        
        return "\n".join(lines)
    
    def table2_regression(self, results: Dict[str, Any],
                           model_type: str = "logistic",
                           title: str = "Regression Results") -> str:
        """
        Generate Table 2: Regression results.
        model_type: "logistic" (OR) or "cox" (HR)
        """
        lines = []
        measure = "OR" if model_type == "logistic" else "HR"
        
        lines.append(f"### {title}")
        lines.append("")
        lines.append(f"| Variable | {measure} (95% CI) | P-value |")
        lines.append("|---|---|---|")
        
        if "coefficients" in results:
            for coef in results["coefficients"]:
                var_name = coef.get("variable", "")
                if var_name == "Intercept":
                    continue
                
                if model_type == "logistic":
                    est = coef.get("odds_ratio", coef.get("OR", ""))
                    ci_low = coef.get("or_ci_lower", coef.get("OR_lower", ""))
                    ci_high = coef.get("or_ci_upper", coef.get("OR_upper", ""))
                else:
                    est = coef.get("hazard_ratio", coef.get("HR", ""))
                    ci_low = coef.get("hr_ci_lower", coef.get("HR_lower", ""))
                    ci_high = coef.get("hr_ci_upper", coef.get("HR_upper", ""))
                
                p_val = coef.get("p_value", "")
                
                if isinstance(p_val, float):
                    p_str = "<0.001" if p_val < 0.001 else f"{p_val:.3f}"
                else:
                    p_str = str(p_val)
                
                if isinstance(est, float) and isinstance(ci_low, float):
                    lines.append(f"| {var_name} | {est:.2f} ({ci_low:.2f}-{ci_high:.2f}) | {p_str} |")
                else:
                    lines.append(f"| {var_name} | {est} ({ci_low}-{ci_high}) | {p_str} |")
        
        # Model fit statistics
        lines.append("")
        if "n" in results:
            lines.append(f"*N = {results['n']}*")
        if "r_squared" in results:
            lines.append(f"*R² = {results['r_squared']:.3f}*")
        if "pseudo_r_squared" in results:
            lines.append(f"*Pseudo R² = {results['pseudo_r_squared']:.3f}*")
        if "aic" in results:
            lines.append(f"*AIC = {results['aic']:.1f}*")
        
        return "\n".join(lines)
    
    def table3_subgroup(self, subgroup_results: Dict[str, Dict],
                          title: str = "Subgroup Analysis") -> str:
        """Generate Table 3: Subgroup analysis results."""
        lines = []
        lines.append(f"### {title}")
        lines.append("")
        lines.append("| Subgroup | N | Mean (SD) | Effect (95% CI) | P-value |")
        lines.append("|---|---|---|---|---|")
        
        for group, stats in subgroup_results.items():
            n = stats.get("n", "—")
            mean = stats.get("mean", "—")
            se = stats.get("se", "—")
            ci_low = stats.get("ci_lower", "—")
            ci_high = stats.get("ci_upper", "—")
            
            if isinstance(mean, float):
                lines.append(f"| {group} | {n} | {mean:.2f} (SE={se:.2f}) | ({ci_low:.2f}, {ci_high:.2f}) | — |")
            else:
                lines.append(f"| {group} | {n} | — | — | — |")
        
        return "\n".join(lines)
    
    def generate_strobe_checklist(self, study_type: str = "cohort") -> str:
        """Generate STROBE checklist for observational studies."""
        checklist = """
### STROBE Checklist (Observational Studies)

| Item | Description | Reported |
|------|-------------|----------|
| **Title and Abstract** | | |
| 1 | Indicate study design in title/abstract | [ ] |
| 2 | Structured abstract (Background, Methods, Results, Conclusion) | [ ] |
| **Introduction** | | |
| 3 | Scientific background and rationale | [ ] |
| 4 | Objectives and hypotheses | [ ] |
| **Methods** | | |
| 5 | Study design | [ ] |
| 6 | Setting (location, dates, follow-up) | [ ] |
| 7 | Participants (eligibility criteria, selection) | [ ] |
| 8 | Variables (outcomes, exposures, confounders) | [ ] |
| 9 | Data sources/measurement | [ ] |
| 10 | Bias considerations | [ ] |
| 11 | Study size | [ ] |
| 12 | Quantitative variables handling | [ ] |
| 13 | Statistical methods (handling of weights, missing data) | [ ] |
| **Results** | | |
| 14 | Participants (flow diagram, reasons for exclusion) | [ ] |
| 15 | Descriptive data (baseline characteristics) | [ ] |
| 16 | Outcome data (numbers, events, summary measures) | [ ] |
| 17 | Main results (effect sizes, confidence intervals) | [ ] |
| 18 | Subgroup/sensitivity analyses | [ ] |
| **Discussion** | | |
| 19 | Key results interpretation | [ ] |
| 20 | Limitations (bias, imprecision, generalizability) | [ ] |
| 21 | Generalizability | [ ] |
| 22 | Funding and role of funders | [ ] |
"""
        return checklist
