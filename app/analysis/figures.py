"""
Publication-Quality Figure Generator for NHANES Data.

Generates Lancet-standard figures:
- Survival curves (Kaplan-Meier)
- Forest plots (Cox regression)
- Cumulative incidence plots
- Distribution plots
- Correlation heatmaps
- Survey-weighted histograms
"""
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# Lancet color palette
LANCET_COLORS = {
    "primary": "#A51C30",      # Lancet dark red
    "secondary": "#1E40AF",    # Blue
    "accent1": "#047857",      # Green
    "accent2": "#D97706",      # Amber
    "accent3": "#7C3AED",      # Purple
    "light": "#F3F4F6",
    "dark": "#1F2937",
    "gray": "#6B7280",
}


class FigureGenerator:
    """Generate publication-quality figures."""
    
    def __init__(self, output_dir: Optional[Path] = None):
        from ..config import RESULTS_DIR
        self.output_dir = output_dir or RESULTS_DIR / "figures"
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_matplotlib(self):
        """Lazy import matplotlib to avoid import errors when not installed."""
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        import matplotlib.ticker as ticker
        plt.rcParams.update({
            'font.family': 'sans-serif',
            'font.sans-serif': ['Arial', 'Helvetica', 'DejaVu Sans'],
            'font.size': 10,
            'axes.titlesize': 12,
            'axes.labelsize': 11,
            'xtick.labelsize': 9,
            'ytick.labelsize': 9,
            'legend.fontsize': 9,
            'figure.dpi': 300,
            'savefig.dpi': 300,
            'savefig.bbox': 'tight',
            'axes.spines.top': False,
            'axes.spines.right': False,
        })
        return plt
    
    def weighted_histogram(self, df: pd.DataFrame, var: str,
                            weight_col: Optional[str] = None,
                            bins: int = 30,
                            title: str = "",
                            xlabel: str = "",
                            ylabel: str = "Weighted Frequency",
                            group_var: Optional[str] = None) -> str:
        """Generate weighted histogram."""
        plt = self._get_matplotlib()
        
        fig, ax = plt.subplots(figsize=(8, 5))
        
        data = df[df[var].notna()]
        
        if group_var and group_var in data.columns:
            groups = sorted(data[group_var].dropna().unique())
            colors = [LANCET_COLORS["primary"], LANCET_COLORS["secondary"],
                     LANCET_COLORS["accent1"], LANCET_COLORS["accent2"]]
            
            for i, g in enumerate(groups):
                sub = data[data[group_var] == g]
                weights = sub[weight_col].values if weight_col and weight_col in sub.columns else None
                color = colors[i % len(colors)]
                ax.hist(sub[var].values, bins=bins, weights=weights,
                       alpha=0.6, label=str(g), color=color, edgecolor='white')
            ax.legend(frameon=False)
        else:
            weights = data[weight_col].values if weight_col and weight_col in data.columns else None
            ax.hist(data[var].values, bins=bins, weights=weights,
                   color=LANCET_COLORS["primary"], alpha=0.8, edgecolor='white')
        
        ax.set_title(title or f"Distribution of {var}", fontweight='bold')
        ax.set_xlabel(xlabel or var)
        ax.set_ylabel(ylabel)
        
        output_path = self.output_dir / f"histogram_{var}.png"
        fig.savefig(output_path)
        plt.close(fig)
        
        return str(output_path)
    
    def forest_plot(self, results: List[Dict[str, Any]],
                     title: str = "Forest Plot",
                     measure: str = "HR",
                     figsize: Tuple[int, int] = (10, 6)) -> str:
        """Generate forest plot for regression results."""
        plt = self._get_matplotlib()
        
        n_vars = len(results)
        fig_height = max(figsize[1], 1.5 + n_vars * 0.6)
        fig, ax = plt.subplots(figsize=(figsize[0], fig_height))
        
        y_positions = list(range(n_vars, 0, -1))
        
        for i, res in enumerate(results):
            y = y_positions[i]
            est = res.get("estimate", res.get("odds_ratio", res.get("hazard_ratio", 1)))
            ci_low = res.get("ci_lower", res.get("or_ci_lower", res.get("hr_ci_lower", est)))
            ci_high = res.get("ci_upper", res.get("or_ci_upper", res.get("hr_ci_upper", est)))
            label = res.get("variable", res.get("term", f"Variable {i+1}"))
            
            # Plot CI line
            ax.plot([ci_low, ci_high], [y, y], color=LANCET_COLORS["primary"],
                   linewidth=1.5, solid_capstyle='round')
            
            # Plot point estimate
            marker_size = max(4, min(12, 200 / n_vars))
            ax.plot(est, y, 'o', color=LANCET_COLORS["primary"],
                   markersize=marker_size, markeredgecolor='white', markeredgewidth=0.5)
            
            # Label
            ax.text(-0.01, y, label, ha='right', va='center', fontsize=9,
                   transform=ax.get_yaxis_transform())
            
            # Value annotation
            ci_text = f"{est:.2f} ({ci_low:.2f}-{ci_high:.2f})"
            ax.text(1.01, y, ci_text, ha='left', va='center', fontsize=8,
                   transform=ax.get_yaxis_transform())
        
        # Reference line
        ref_val = 1 if measure in ["HR", "OR"] else 0
        ax.axvline(x=ref_val, color='gray', linestyle='--', linewidth=0.8, alpha=0.5)
        
        # Formatting
        ax.set_yticks(y_positions)
        ax.set_yticklabels([])
        ax.set_xlabel(f"{measure} (95% CI)")
        ax.set_title(title, fontweight='bold', pad=15)
        
        # Add column headers
        ax.text(-0.01, n_vars + 0.5, "Variable", ha='right', va='bottom',
               fontsize=10, fontweight='bold', transform=ax.get_yaxis_transform())
        ax.text(1.01, n_vars + 0.5, f"{measure} (95% CI)", ha='left', va='bottom',
               fontsize=10, fontweight='bold', transform=ax.get_yaxis_transform())
        
        output_path = self.output_dir / "forest_plot.png"
        fig.savefig(output_path)
        plt.close(fig)
        
        return str(output_path)
    
    def subgroup_plot(self, subgroup_results: Dict[str, Dict[str, float]],
                       title: str = "Subgroup Analysis",
                       measure: str = "Mean Difference") -> str:
        """Generate subgroup analysis plot (similar to forest plot but for subgroups)."""
        plt = self._get_matplotlib()
        
        n_groups = len(subgroup_results)
        fig, ax = plt.subplots(figsize=(10, max(4, 1 + n_groups * 0.5)))
        
        y_pos = list(range(n_groups, 0, -1))
        
        for i, (group, stats) in enumerate(subgroup_results.items()):
            y = y_pos[i]
            mean = stats.get("mean", 0)
            ci_low = stats.get("ci_lower", mean)
            ci_high = stats.get("ci_upper", mean)
            
            ax.plot([ci_low, ci_high], [y, y], color=LANCET_COLORS["primary"],
                   linewidth=1.5)
            ax.plot(mean, y, 'o', color=LANCET_COLORS["primary"], markersize=8)
            
            ax.text(-0.01, y, group, ha='right', va='center', fontsize=9,
                   transform=ax.get_yaxis_transform())
            ax.text(1.01, y, f"{mean:.2f} ({ci_low:.2f}, {ci_high:.2f})",
                   ha='left', va='center', fontsize=8, transform=ax.get_yaxis_transform())
        
        ax.axvline(x=0, color='gray', linestyle='--', linewidth=0.8)
        ax.set_yticks(y_pos)
        ax.set_yticklabels([])
        ax.set_xlabel(measure)
        ax.set_title(title, fontweight='bold')
        
        output_path = self.output_dir / "subgroup_plot.png"
        fig.savefig(output_path)
        plt.close(fig)
        
        return str(output_path)
    
    def correlation_heatmap(self, df: pd.DataFrame, vars: List[str],
                             title: str = "Correlation Matrix") -> str:
        """Generate correlation heatmap."""
        plt = self._get_matplotlib()
        
        # Calculate correlation matrix
        available_vars = [v for v in vars if v in df.columns]
        if len(available_vars) < 2:
            logger.warning("Need at least 2 variables for correlation heatmap")
            return ""
        
        corr = df[available_vars].corr()
        
        fig, ax = plt.subplots(figsize=(max(8, len(available_vars) * 0.8),
                                        max(6, len(available_vars) * 0.6)))
        
        # Create heatmap
        im = ax.imshow(corr, cmap='RdBu_r', vmin=-1, vmax=1, aspect='auto')
        
        # Add colorbar
        cbar = fig.colorbar(im, ax=ax, shrink=0.8)
        cbar.set_label('Correlation')
        
        # Labels
        ax.set_xticks(range(len(available_vars)))
        ax.set_yticks(range(len(available_vars)))
        ax.set_xticklabels(available_vars, rotation=45, ha='right', fontsize=8)
        ax.set_yticklabels(available_vars, fontsize=8)
        
        # Add correlation values
        for i in range(len(available_vars)):
            for j in range(len(available_vars)):
                val = corr.iloc[i, j]
                color = 'white' if abs(val) > 0.5 else 'black'
                ax.text(j, i, f'{val:.2f}', ha='center', va='center',
                       fontsize=7, color=color)
        
        ax.set_title(title, fontweight='bold', pad=10)
        
        output_path = self.output_dir / "correlation_heatmap.png"
        fig.savefig(output_path)
        plt.close(fig)
        
        return str(output_path)
    
    def bar_chart(self, df: pd.DataFrame, var: str,
                   weight_col: Optional[str] = None,
                   title: str = "",
                   xlabel: str = "",
                   ylabel: str = "Weighted %",
                   horizontal: bool = False) -> str:
        """Generate weighted bar chart for categorical variables."""
        plt = self._get_matplotlib()
        
        data = df[df[var].notna()]
        
        if weight_col and weight_col in data.columns:
            # Weighted frequencies
            weighted_counts = data.groupby(var)[weight_col].sum()
            total = weighted_counts.sum()
            pcts = weighted_counts / total * 100
        else:
            counts = data[var].value_counts()
            pcts = counts / counts.sum() * 100
        
        colors = [LANCET_COLORS["primary"], LANCET_COLORS["secondary"],
                 LANCET_COLORS["accent1"], LANCET_COLORS["accent2"],
                 LANCET_COLORS["accent3"], LANCET_COLORS["gray"]]
        
        fig, ax = plt.subplots(figsize=(8, max(4, len(pcts) * 0.5)))
        
        if horizontal:
            bars = ax.barh(range(len(pcts)), pcts.values, color=colors[:len(pcts)],
                          edgecolor='white', height=0.6)
            ax.set_yticks(range(len(pcts)))
            ax.set_yticklabels(pcts.index, fontsize=9)
            ax.set_xlabel(ylabel)
            for bar, pct in zip(bars, pcts.values):
                ax.text(bar.get_width() + 0.5, bar.get_y() + bar.get_height()/2,
                       f'{pct:.1f}%', va='center', fontsize=8)
        else:
            bars = ax.bar(range(len(pcts)), pcts.values, color=colors[:len(pcts)],
                         edgecolor='white', width=0.6)
            ax.set_xticks(range(len(pcts)))
            ax.set_xticklabels(pcts.index, rotation=45, ha='right', fontsize=9)
            ax.set_ylabel(ylabel)
            for bar, pct in zip(bars, pcts.values):
                ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5,
                       f'{pct:.1f}%', ha='center', fontsize=8)
        
        ax.set_title(title or f"Distribution of {var}", fontweight='bold')
        
        output_path = self.output_dir / f"bar_chart_{var}.png"
        fig.savefig(output_path)
        plt.close(fig)
        
        return str(output_path)
