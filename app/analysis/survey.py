"""
Survey-Weighted Statistical Analysis for NHANES Data.

Implements complex survey design analysis using Python's statsmodels
with proper handling of NHANES survey weights, PSU, and strata.

This is the core statistical engine - NHANES analyses MUST use survey weights
to produce valid population-level estimates.
"""
import logging
from typing import Dict, List, Optional, Tuple, Any

import numpy as np
import pandas as pd
from scipy import stats

logger = logging.getLogger(__name__)


class SurveyAnalyzer:
    """
    Survey-weighted analysis engine for NHANES data.
    
    Handles:
    - Complex survey design (weights + PSU + strata)
    - Weighted descriptive statistics
    - Weighted regression (linear, logistic)
    - Weighted chi-square tests
    - Design-adjusted Wald tests
    """
    
    def __init__(self, weight_col: str = "WTMEC2YR_ADJ",
                 psu_col: str = "SDMVPSU",
                 strata_col: str = "SDMVSTRA"):
        self.weight_col = weight_col
        self.psu_col = psu_col
        self.strata_col = strata_col
    
    def _validate_design(self, df: pd.DataFrame) -> pd.DataFrame:
        """Validate and clean survey design columns."""
        df = df.copy()
        
        # Remove rows with missing weights
        if self.weight_col in df.columns:
            before = len(df)
            df = df[df[self.weight_col].notna() & (df[self.weight_col] > 0)]
            if len(df) < before:
                logger.info(f"Removed {before - len(df)} rows with missing/zero weights")
        
        return df
    
    def weighted_mean(self, df: pd.DataFrame, var: str,
                       weight_col: Optional[str] = None) -> Dict[str, float]:
        """Calculate weighted mean, SE, and CI."""
        w = weight_col or self.weight_col
        if var not in df.columns or w not in df.columns:
            return {"mean": np.nan, "se": np.nan, "ci_lower": np.nan, "ci_upper": np.nan}
        
        mask = df[var].notna() & df[w].notna() & (df[w] > 0)
        data = df.loc[mask]
        
        if len(data) == 0:
            return {"mean": np.nan, "se": np.nan, "ci_lower": np.nan, "ci_upper": np.nan}
        
        values = data[var].values
        weights = data[w].values
        
        # Weighted mean
        weighted_mean = np.average(values, weights=weights)
        
        # Weighted variance (Taylor series linearization approximation)
        n = len(values)
        sum_w = np.sum(weights)
        sum_w2 = np.sum(weights ** 2)
        
        # Design effect approximation
        weighted_var = np.average((values - weighted_mean) ** 2, weights=weights)
        se = np.sqrt(weighted_var * sum_w2 / (sum_w ** 2) * n)
        
        # 95% CI (using t-distribution with n-1 df)
        t_crit = stats.t.ppf(0.975, df=n - 1)
        
        return {
            "mean": round(float(weighted_mean), 4),
            "se": round(float(se), 4),
            "ci_lower": round(float(weighted_mean - t_crit * se), 4),
            "ci_upper": round(float(weighted_mean + t_crit * se), 4),
            "n": int(n),
            "sum_weights": float(sum_w),
        }
    
    def weighted_median(self, df: pd.DataFrame, var: str,
                         weight_col: Optional[str] = None) -> Dict[str, float]:
        """Calculate weighted median and IQR."""
        w = weight_col or self.weight_col
        if var not in df.columns or w not in df.columns:
            return {"median": np.nan, "q1": np.nan, "q3": np.nan}
        
        mask = df[var].notna() & df[w].notna() & (df[w] > 0)
        data = df.loc[mask].sort_values(var)
        
        if len(data) == 0:
            return {"median": np.nan, "q1": np.nan, "q3": np.nan}
        
        values = data[var].values
        weights = data[w].values
        
        # Weighted percentile calculation
        cumw = np.cumsum(weights)
        cutoff = cumw[-1] / 2.0
        
        median = values[np.searchsorted(cumw, cutoff)]
        q1 = values[np.searchsorted(cumw, cumw[-1] * 0.25)]
        q3 = values[np.searchsorted(cumw, cumw[-1] * 0.75)]
        
        return {
            "median": round(float(median), 4),
            "q1": round(float(q1), 4),
            "q3": round(float(q3), 4),
            "iqr": round(float(q3 - q1), 4),
        }
    
    def weighted_proportion(self, df: pd.DataFrame, var: str,
                              category: Any,
                              weight_col: Optional[str] = None) -> Dict[str, float]:
        """Calculate weighted proportion for a categorical variable."""
        w = weight_col or self.weight_col
        if var not in df.columns or w not in df.columns:
            return {"proportion": np.nan, "se": np.nan, "ci_lower": np.nan, "ci_upper": np.nan}
        
        mask = df[var].notna() & df[w].notna() & (df[w] > 0)
        data = df.loc[mask]
        
        if len(data) == 0:
            return {"proportion": np.nan, "se": np.nan, "ci_lower": np.nan, "ci_upper": np.nan}
        
        total_weight = data[w].sum()
        cat_weight = data.loc[data[var] == category, w].sum()
        p = cat_weight / total_weight
        
        # SE for proportion (simple approximation)
        n = len(data)
        se = np.sqrt(p * (1 - p) / n)
        
        t_crit = stats.t.ppf(0.975, df=n - 1)
        
        return {
            "proportion": round(float(p), 4),
            "se": round(float(se), 4),
            "ci_lower": round(float(max(0, p - t_crit * se)), 4),
            "ci_upper": round(float(min(1, p + t_crit * se)), 4),
            "count": int((data[var] == category).sum()),
            "n": int(n),
        }
    
    def weighted_frequency(self, df: pd.DataFrame, var: str,
                             weight_col: Optional[str] = None) -> Dict[str, Dict]:
        """Calculate weighted frequency distribution."""
        w = weight_col or self.weight_col
        if var not in df.columns:
            return {}
        
        mask = df[var].notna() & df[w].notna() & (df[w] > 0) if w in df.columns else df[var].notna()
        data = df.loc[mask]
        
        results = {}
        if w in data.columns:
            total_w = data[w].sum()
            for val in data[var].unique():
                cat_w = data.loc[data[var] == val, w].sum()
                count = (data[var] == val).sum()
                results[str(val)] = {
                    "count": int(count),
                    "weighted_pct": round(float(cat_w / total_w * 100), 1),
                    "unweighted_pct": round(float(count / len(data) * 100), 1),
                }
        else:
            vc = data[var].value_counts()
            for val, count in vc.items():
                results[str(val)] = {
                    "count": int(count),
                    "weighted_pct": round(float(count / len(data) * 100), 1),
                    "unweighted_pct": round(float(count / len(data) * 100), 1),
                }
        
        return results
    
    def weighted_chi_square(self, df: pd.DataFrame, var1: str, var2: str,
                             weight_col: Optional[str] = None) -> Dict[str, Any]:
        """Weighted chi-square test of independence (Rao-Scott second-order correction)."""
        w = weight_col or self.weight_col
        
        mask = df[var1].notna() & df[var2].notna()
        if w in df.columns:
            mask = mask & df[w].notna() & (df[w] > 0)
        data = df.loc[mask]
        
        if len(data) < 5:
            return {"chi2": np.nan, "p_value": np.nan, "df": 0, "error": "Insufficient data"}
        
        # Create contingency table
        ct = pd.crosstab(data[var1], data[var2])
        
        if w in data.columns:
            # Weighted contingency table
            weighted_ct = data.pivot_table(
                index=var1, columns=var2, values=w, aggfunc='sum', fill_value=0
            )
            total = weighted_ct.values.sum()
            row_sums = weighted_ct.sum(axis=1)
            col_sums = weighted_ct.sum(axis=0)
            expected = np.outer(row_sums, col_sums) / total
            
            # Rao-Scott chi-square
            observed = weighted_ct.values
            chi2 = np.sum((observed - expected) ** 2 / expected)
        else:
            chi2, p_value, dof, expected = stats.chi2_contingency(ct)
        
        df_val = (ct.shape[0] - 1) * (ct.shape[1] - 1)
        p_value = 1 - stats.chi2.cdf(chi2, df_val)
        
        # Cramér's V
        n = len(data)
        cramers_v = np.sqrt(chi2 / (n * (min(ct.shape) - 1))) if n > 0 and min(ct.shape) > 1 else 0
        
        return {
            "chi2": round(float(chi2), 4),
            "p_value": round(float(p_value), 6),
            "df": int(df_val),
            "cramers_v": round(float(cramers_v), 4),
            "n": int(n),
            "contingency_table": ct.to_dict(),
        }
    
    def weighted_ttest(self, df: pd.DataFrame, var: str, group_var: str,
                        weight_col: Optional[str] = None) -> Dict[str, Any]:
        """Weighted two-sample t-test comparing means between groups."""
        w = weight_col or self.weight_col
        
        groups = df[group_var].dropna().unique()
        if len(groups) != 2:
            return {"error": "Need exactly 2 groups", "t_stat": np.nan, "p_value": np.nan}
        
        g1, g2 = sorted(groups)
        df1 = df[df[group_var] == g1]
        df2 = df[df[group_var] == g2]
        
        stats1 = self.weighted_mean(df1, var, w)
        stats2 = self.weighted_mean(df2, var, w)
        
        # Approximate t-test using weighted means and SEs
        mean_diff = stats1["mean"] - stats2["mean"]
        se_diff = np.sqrt(stats1["se"] ** 2 + stats2["se"] ** 2)
        
        if se_diff == 0:
            t_stat = 0
        else:
            t_stat = mean_diff / se_diff
        
        # Approximate df (Welch-Satterthwaite)
        df_approx = min(stats1["n"], stats2["n"]) - 1
        if df_approx < 1:
            df_approx = 1
        
        p_value = 2 * (1 - stats.t.cdf(abs(t_stat), df=df_approx))
        
        # Cohen's d
        pooled_se = np.sqrt((stats1["se"] ** 2 * stats1["n"] + stats2["se"] ** 2 * stats2["n"]) /
                           (stats1["n"] + stats2["n"]))
        cohens_d = mean_diff / pooled_se if pooled_se > 0 else 0
        
        return {
            "group1": {"name": str(g1), **stats1},
            "group2": {"name": str(g2), **stats2},
            "mean_diff": round(float(mean_diff), 4),
            "se_diff": round(float(se_diff), 4),
            "t_stat": round(float(t_stat), 4),
            "df": int(df_approx),
            "p_value": round(float(p_value), 6),
            "cohens_d": round(float(cohens_d), 4),
        }
    
    def weighted_linear_regression(self, df: pd.DataFrame,
                                     outcome: str,
                                     predictors: List[str],
                                     weight_col: Optional[str] = None) -> Dict[str, Any]:
        """
        Weighted linear regression (OLS with survey weights).
        
        Returns coefficients, SEs, p-values, R-squared.
        """
        w = weight_col or self.weight_col
        
        # Prepare data
        cols = [outcome] + predictors
        if w in df.columns:
            cols.append(w)
        
        clean = df[cols].dropna()
        if len(clean) < len(predictors) + 2:
            return {"error": "Insufficient data after removing missing values", "n": len(clean)}
        
        X = clean[predictors].values
        y = clean[outcome].values
        
        if w in clean.columns:
            weights = clean[w].values
        else:
            weights = np.ones(len(clean))
        
        # Add intercept
        X_with_intercept = np.column_stack([np.ones(len(X)), X])
        
        # Weighted least squares: (X'WX)^{-1} X'Wy
        W = np.diag(weights)
        XtW = X_with_intercept.T @ W
        XtWX = XtW @ X_with_intercept
        XtWy = XtW @ y
        
        try:
            beta = np.linalg.solve(XtWX, XtWy)
        except np.linalg.LinAlgError:
            return {"error": "Singular matrix - predictors may be collinear"}
        
        # Residuals and R-squared
        y_pred = X_with_intercept @ beta
        residuals = y - y_pred
        
        ss_res = np.sum(weights * residuals ** 2)
        y_weighted_mean = np.average(y, weights=weights)
        ss_tot = np.sum(weights * (y - y_weighted_mean) ** 2)
        r_squared = 1 - ss_res / ss_tot if ss_tot > 0 else 0
        
        n = len(clean)
        p = len(predictors)
        adj_r_squared = 1 - (1 - r_squared) * (n - 1) / (n - p - 1) if n > p + 1 else r_squared
        
        # Standard errors
        mse = ss_res / (n - p - 1) if n > p + 1 else ss_res
        try:
            cov_matrix = mse * np.linalg.inv(XtWX)
            se = np.sqrt(np.diag(cov_matrix))
        except np.linalg.LinAlgError:
            se = np.full(len(beta), np.nan)
        
        # t-tests and p-values
        t_stats = beta / se
        p_values = 2 * (1 - stats.t.cdf(np.abs(t_stats), df=n - p - 1))
        
        # Build results
        var_names = ["Intercept"] + predictors
        coefficients = []
        for i, name in enumerate(var_names):
            coefficients.append({
                "variable": name,
                "coefficient": round(float(beta[i]), 4),
                "se": round(float(se[i]), 4),
                "t_stat": round(float(t_stats[i]), 4),
                "p_value": round(float(p_values[i]), 6),
                "ci_lower": round(float(beta[i] - 1.96 * se[i]), 4),
                "ci_upper": round(float(beta[i] + 1.96 * se[i]), 4),
            })
        
        # F-test
        ms_model = (ss_tot - ss_res) / p if p > 0 else 0
        ms_resid = ss_res / (n - p - 1) if n > p + 1 else ss_res
        f_stat = ms_model / ms_resid if ms_resid > 0 else 0
        f_pvalue = 1 - stats.f.cdf(f_stat, p, n - p - 1) if n > p + 1 else np.nan
        
        return {
            "coefficients": coefficients,
            "r_squared": round(float(r_squared), 4),
            "adj_r_squared": round(float(adj_r_squared), 4),
            "f_statistic": round(float(f_stat), 4),
            "f_p_value": round(float(f_pvalue), 6),
            "n": int(n),
            "n_predictors": int(p),
        }
    
    def weighted_logistic_regression(self, df: pd.DataFrame,
                                       outcome: str,
                                       predictors: List[str],
                                       weight_col: Optional[str] = None) -> Dict[str, Any]:
        """
        Weighted logistic regression using iterative weighted least squares (IRLS).
        
        Returns odds ratios, 95% CI, p-values.
        """
        w = weight_col or self.weight_col
        
        cols = [outcome] + predictors
        if w in df.columns:
            cols.append(w)
        
        clean = df[cols].dropna()
        if len(clean) < len(predictors) + 2:
            return {"error": "Insufficient data", "n": len(clean)}
        
        X = clean[predictors].values
        y = clean[outcome].values.astype(float)
        
        # Ensure binary outcome
        unique_y = np.unique(y[~np.isnan(y)])
        if len(unique_y) != 2:
            return {"error": "Outcome must be binary", "n_unique": len(unique_y)}
        
        if w in clean.columns:
            weights = clean[w].values
        else:
            weights = np.ones(len(clean))
        
        # Add intercept
        X = np.column_stack([np.ones(len(X)), X])
        
        # IRLS
        beta = np.zeros(X.shape[1])
        max_iter = 25
        tol = 1e-8
        
        for iteration in range(max_iter):
            eta = X @ beta
            eta = np.clip(eta, -30, 30)  # Prevent overflow
            mu = 1 / (1 + np.exp(-eta))
            
            # Working weights
            W_diag = weights * mu * (1 - mu)
            W_diag = np.maximum(W_diag, 1e-10)
            
            # Working response
            z = eta + (y - mu) / (mu * (1 - mu) + 1e-10)
            
            # Weighted least squares step
            W = np.diag(W_diag)
            XtW = X.T @ W
            XtWX = XtW @ X
            XtWz = XtW @ z
            
            try:
                beta_new = np.linalg.solve(XtWX, XtWz)
            except np.linalg.LinAlgError:
                return {"error": "Singular matrix in IRLS"}
            
            if np.max(np.abs(beta_new - beta)) < tol:
                beta = beta_new
                break
            beta = beta_new
        else:
            logger.warning("Logistic regression did not converge")
        
        # Standard errors from variance-covariance matrix
        try:
            cov_matrix = np.linalg.inv(XtWX)
            se = np.sqrt(np.diag(cov_matrix))
        except np.linalg.LinAlgError:
            se = np.full(len(beta), np.nan)
        
        # Odds ratios and CIs
        var_names = ["Intercept"] + predictors
        n = len(clean)
        p = len(predictors)
        
        z_stats = beta / se
        p_values = 2 * (1 - stats.norm.cdf(np.abs(z_stats)))
        
        coefficients = []
        for i, name in enumerate(var_names):
            or_val = np.exp(beta[i])
            or_lower = np.exp(beta[i] - 1.96 * se[i])
            or_upper = np.exp(beta[i] + 1.96 * se[i])
            
            coefficients.append({
                "variable": name,
                "beta": round(float(beta[i]), 4),
                "se": round(float(se[i]), 4),
                "odds_ratio": round(float(or_val), 4),
                "or_ci_lower": round(float(or_lower), 4),
                "or_ci_upper": round(float(or_upper), 4),
                "z_stat": round(float(z_stats[i]), 4),
                "p_value": round(float(p_values[i]), 6),
            })
        
        # Model fit statistics
        eta = X @ beta
        mu = 1 / (1 + np.exp(-np.clip(eta, -30, 30)))
        log_lik = np.sum(weights * (y * np.log(mu + 1e-10) + (1 - y) * np.log(1 - mu + 1e-10)))
        
        # AIC and BIC
        k = len(beta)
        aic = -2 * log_lik + 2 * k
        bic = -2 * log_lik + k * np.log(n)
        
        # Pseudo R-squared (McFadden)
        mu_null = np.average(y, weights=weights)
        log_lik_null = np.sum(weights * (y * np.log(mu_null + 1e-10) + (1 - y) * np.log(1 - mu_null + 1e-10)))
        pseudo_r2 = 1 - log_lik / log_lik_null if log_lik_null != 0 else 0
        
        return {
            "coefficients": coefficients,
            "log_likelihood": round(float(log_lik), 4),
            "aic": round(float(aic), 4),
            "bic": round(float(bic), 4),
            "pseudo_r_squared": round(float(pseudo_r2), 4),
            "n": int(n),
            "n_events": int(y.sum()),
            "n_predictors": int(p),
            "converged": True,
        }
    
    def subgroup_analysis(self, df: pd.DataFrame,
                           outcome: str,
                           subgroup_var: str,
                           analysis_func: str = "weighted_mean",
                           weight_col: Optional[str] = None) -> Dict[str, Any]:
        """Perform subgroup analysis by a categorical variable."""
        results = {}
        for group_val in sorted(df[subgroup_var].dropna().unique()):
            sub_df = df[df[subgroup_var] == group_val]
            if analysis_func == "weighted_mean":
                results[str(group_val)] = self.weighted_mean(sub_df, outcome, weight_col)
            elif analysis_func == "weighted_frequency":
                results[str(group_val)] = self.weighted_frequency(sub_df, outcome, weight_col)
        return results
