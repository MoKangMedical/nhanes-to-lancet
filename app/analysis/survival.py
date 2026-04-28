"""
Survival Analysis Engine for NHANES Data.

Generates R scripts for:
- Kaplan-Meier survival analysis
- Cox proportional hazards regression
- Fine-Gray competing risk model
- Cumulative incidence functions

All scripts follow Lancet publication standards.
"""
import os
import logging
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Any

from ..config import RESULTS_DIR

logger = logging.getLogger(__name__)


class SurvivalAnalyzer:
    """Generate and execute R scripts for survival analysis."""
    
    def __init__(self, rscript_path: str = "Rscript"):
        self.rscript_path = rscript_path
        self.output_dir = RESULTS_DIR / "survival"
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def check_r_available(self) -> bool:
        """Check if R is available."""
        try:
            result = subprocess.run(
                [self.rscript_path, "--version"],
                capture_output=True, text=True, timeout=10
            )
            return result.returncode == 0 or "R version" in result.stderr
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False
    
    def generate_km_script(self, data_path: str, output_dir: str,
                            time_var: str, event_var: str,
                            group_var: Optional[str] = None,
                            weight_var: Optional[str] = None,
                            title: str = "Kaplan-Meier Survival Curve") -> str:
        """Generate R script for Kaplan-Meier survival analysis."""
        
        group_code = f"~ data${group_var}" if group_var else "~ 1"
        risk_table_group = f'fun = "risk.table", risk.table.col = "strata"' if group_var else 'fun = "risk.table"'
        palette = 'palette = "lancet"' if group_var else ""
        
        script = f'''
# Kaplan-Meier Survival Analysis
# NHANES to Lancet Platform - Auto-generated
# Date: {__import__("datetime").datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

# Load required packages
suppressPackageStartupMessages({{
  if (!require("survival")) install.packages("survival", repos="https://cloud.r-project.org/")
  if (!require("survminer")) install.packages("survminer", repos="https://cloud.r-project.org/")
  if (!require("ggplot2")) install.packages("ggplot2", repos="https://cloud.r-project.org/")
  if (!require("dplyr")) install.packages("dplyr", repos="https://cloud.r-project.org/")
}})

library(survival)
library(survminer)
library(ggplot2)
library(dplyr)

# Load data
data <- read.csv("{data_path}")

# Remove missing values
data <- data %>% filter(!is.na({time_var}), !is.na({event_var}), {time_var} > 0)

cat("Analysis dataset: ", nrow(data), " observations\\n")

# Create survival object
surv_obj <- Surv(time = data${time_var}, event = data${event_var})

# Fit Kaplan-Meier model
km_fit <- survfit(surv_obj {group_code}, data = data)

# Print summary
cat("\\n=== Kaplan-Meier Summary ===\\n")
print(summary(km_fit))

# Log-rank test
{"log_rank <- survdiff(surv_obj ~ data$" + group_var + ", data = data)" if group_var else "# No grouping variable - skipping log-rank test"}
{"p_val <- 1 - pchisq(log_rank$chisq, length(log_rank$n) - 1)" if group_var else ""}

# Generate survival curve
output_path <- file.path("{output_dir}", "km_survival_curve.png")
png(output_path, width = 800, height = 600, res = 300)

ggsurv <- ggsurvplot(
  km_fit,
  data = data,
  pval = {str(group_var is not None).upper()},
  conf.int = TRUE,
  risk.table = TRUE,
  risk.table.height = 0.25,
  risk.table.col = "strata",
  ggtheme = theme_classic(),
  {palette}
  title = "{title}",
  xlab = "Time (months)",
  ylab = "Survival Probability",
  font.title = c(14, "bold"),
  font.x = c(12),
  font.y = c(12),
  font.tickslab = c(10),
  legend.title = "",
  legend.labs = c({', '.join(f'"{g}"' for g in (["Group 1", "Group 2"] if group_var else ["Overall"]))}),
  break.time.by = 12,
  surv.median.line = "hv",
  ggtheme = theme_classic() +
    theme(
      plot.title = element_text(hjust = 0.5, face = "bold"),
      legend.position = "bottom"
    )
)

print(ggsurv)
dev.off()

cat("\\nSurvival curve saved to: ", output_path, "\\n")

# Median survival time
cat("\\n=== Median Survival Time ===\\n")
print(summary(km_fit)$table)

# Save results
results <- list(
  n = nrow(data),
  n_events = sum(data${event_var}),
  median_survival = median(summary(km_fit)$time),
  survival_1yr = summary(km_fit, times = 12)$surv,
  survival_3yr = summary(km_fit, times = 36)$surv,
  survival_5yr = summary(km_fit, times = 60)$surv,
  log_rank_p = {"p_val" if group_var else "NA"}
)

cat("\\nAnalysis completed successfully\\n")
'''
        return script
    
    def generate_cox_script(self, data_path: str, output_dir: str,
                             time_var: str, event_var: str,
                             covariates: List[str],
                             weight_var: Optional[str] = None,
                             title: str = "Cox Regression Analysis") -> str:
        """Generate R script for Cox proportional hazards regression."""
        
        cov_formula = " + ".join(covariates)
        
        # Weighted analysis code
        if weight_var:
            weight_code = f'''
# Survey-weighted Cox regression
library(survey)
design <- svydesign(id = ~1, weights = ~{weight_var}, data = data)
cox_model <- svycoxph(Surv({time_var}, {event_var}) ~ {cov_formula}, design = design)
'''
        else:
            weight_code = f"cox_model <- coxph(Surv({time_var}, {event_var}) ~ {cov_formula}, data = data)"
        
        # Generate forest plot variables
        n_covs = len(covariates)
        fig_height = max(6, 2 + n_covs * 0.5)
        
        script = f'''
# Cox Proportional Hazards Regression
# NHANES to Lancet Platform - Auto-generated
# Date: {__import__("datetime").datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

# Load required packages
suppressPackageStartupMessages({{
  if (!require("survival")) install.packages("survival", repos="https://cloud.r-project.org/")
  if (!require("survminer")) install.packages("survminer", repos="https://cloud.r-project.org/")
  if (!require("forestplot")) install.packages("forestplot", repos="https://cloud.r-project.org/")
  if (!require("broom")) install.packages("broom", repos="https://cloud.r-project.org/")
  if (!require("dplyr")) install.packages("dplyr", repos="https://cloud.r-project.org/")
  {"if (!require(\"survey\")) install.packages(\"survey\", repos=\"https://cloud.r-project.org/\")" if weight_var else ""}
}})

library(survival)
library(survminer)
library(forestplot)
library(broom)
library(dplyr)
{"library(survey)" if weight_var else ""}

# Load data
data <- read.csv("{data_path}")

# Remove missing values
vars_needed <- c("{time_var}", "{event_var}", {', '.join(f'"{c}"' for c in covariates)})
data <- data %>% filter(complete.cases(select(., all_of(vars_needed))))
data <- data %>% filter({time_var} > 0)

cat("Analysis dataset: ", nrow(data), " observations\\n")

# Fit Cox model
{weight_code}

# Model summary
cat("\\n=== Cox Regression Summary ===\\n")
cox_summary <- summary(cox_model)
print(cox_summary)

# Extract results for table
cox_results <- tidy(cox_model, exponentiate = TRUE, conf.int = TRUE)

# Save results table
table_path <- file.path("{output_dir}", "cox_results.csv")
write.csv(cox_results, table_path, row.names = FALSE)
cat("\\nResults saved to: ", table_path, "\\n")

# Generate forest plot
forest_path <- file.path("{output_dir}", "cox_forest_plot.png")
png(forest_path, width = 1000, height = {int(fig_height * 100)}, res = 300)

# Prepare data for forest plot
coef_data <- cox_results %>%
  filter(term != "(Intercept)") %>%
  mutate(
    label = term,
    HR = sprintf("%.2f (%.2f-%.2f)", estimate, conf.low, conf.high),
    p = ifelse(p.value < 0.001, "<0.001", sprintf("%.3f", p.value))
  )

# Create forest plot
forestplot(
  labeltext = matrix(c(coef_data$label, coef_data$HR, coef_data$p), ncol = 3),
  mean = coef_data$estimate,
  lower = coef_data$conf.low,
  upper = coef_data$conf.high,
  xlog = TRUE,
  xlab = "Hazard Ratio (95% CI)",
  title = "{title}",
  txt_gp = fpTxtGp(
    label = gpar(cex = 0.8),
    ticks = gpar(cex = 0.7),
    xlab = gpar(cex = 0.8),
    title = gpar(cex = 1.0)
  ),
  col = fpColors(
    box = "darkred",
    line = "darkblue",
    summary = "red"
  ),
  zero = 1,
  clip = c(0.1, 10),
  is.summary = c(FALSE),
  graphwidth = unit(6, "cm"),
  hrzl_lines = list("1" = gpar(lwd = 2))
)

dev.off()
cat("\\nForest plot saved to: ", forest_path, "\\n")

# Proportional hazards assumption test
cat("\\n=== Proportional Hazards Assumption ===\\n")
ph_test <- cox.zph(cox_model)
print(ph_test)

# Save PH test results
ph_path <- file.path("{output_dir}", "ph_assumption_test.csv")
write.csv(as.data.frame(ph_test$table), ph_path)

# Overall model fit
cat("\\n=== Model Fit Statistics ===\\n")
cat("Log-likelihood: ", logLik(cox_model), "\\n")
cat("AIC: ", AIC(cox_model), "\\n")
cat("Concordance: ", cox_summary$concordance[1], "\\n")

cat("\\nCox regression analysis completed successfully\\n")
'''
        return script
    
    def generate_fine_gray_script(self, data_path: str, output_dir: str,
                                    time_var: str, event_var: str,
                                    event_of_interest: int,
                                    competing_event: int,
                                    covariates: List[str],
                                    title: str = "Competing Risk Analysis") -> str:
        """Generate R script for Fine-Gray competing risk analysis."""
        
        cov_formula = " + ".join(covariates)
        
        script = f'''
# Fine-Gray Competing Risk Analysis
# NHANES to Lancet Platform - Auto-generated
# Date: {__import__("datetime").datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

# Load required packages
suppressPackageStartupMessages({{
  if (!require("cmprsk")) install.packages("cmprsk", repos="https://cloud.r-project.org/")
  if (!require("tidycmprsk")) install.packages("tidycmprsk", repos="https://cloud.r-project.org/")
  if (!require("survminer")) install.packages("survminer", repos="https://cloud.r-project.org/")
  if (!require("ggplot2")) install.packages("ggplot2", repos="https://cloud.r-project.org/")
  if (!require("broom")) install.packages("broom", repos="https://cloud.r-project.org/")
  if (!require("dplyr")) install.packages("dplyr", repos="https://cloud.r-project.org/")
}})

library(cmprsk)
library(tidycmprsk)
library(survminer)
library(ggplot2)
library(broom)
library(dplyr)

# Load data
data <- read.csv("{data_path}")

# Remove missing values
vars_needed <- c("{time_var}", "{event_var}", {', '.join(f'"{c}"' for c in covariates)})
data <- data %>% filter(complete.cases(select(., all_of(vars_needed))))
data <- data %>% filter({time_var} > 0)

cat("Analysis dataset: ", nrow(data), " observations\\n")

# Recode event variable: 0=censored, 1=event of interest, 2=competing event
data$status_fg <- case_when(
  data${event_var} == {event_of_interest} ~ 1,
  data${event_var} == {competing_event} ~ 2,
  TRUE ~ 0
)

# === Cumulative Incidence Function ===
cat("\\n=== Cumulative Incidence Function ===\\n")
cif <- cuminc(
  ftime = data${time_var},
  fstatus = data$status_fg,
  cencode = 0
)

print(cif)

# Generate CIF plot
cif_path <- file.path("{output_dir}", "cif_plot.png")
png(cif_path, width = 800, height = 600, res = 300)

plot(cif,
     xlab = "Time (months)",
     ylab = "Cumulative Incidence",
     main = "{title}",
     col = c("#A51C30", "#1E40AF"),
     lwd = 2,
     curvlab = c("Event of Interest", "Competing Event"),
     xlim = c(0, max(data${time_var}, na.rm = TRUE)))

legend("topleft",
       legend = c("Event of Interest", "Competing Event"),
       col = c("#A51C30", "#1E40AF"),
       lwd = 2,
       bty = "n",
       cex = 0.8)

dev.off()
cat("\\nCIF plot saved to: ", cif_path, "\\n")

# === Fine-Gray Regression ===
cat("\\n=== Fine-Gray Regression ===\\n")

# Fit Fine-Gray model
fg_model <- crr(
  ftime = data${time_var},
  fstatus = data$status_fg,
  cov1 = model.matrix(~ {cov_formula} - 1, data = data),
  failcode = 1,
  cencode = 0
)

fg_summary <- summary(fg_model)
print(fg_summary)

# Extract results
fg_results <- data.frame(
  Variable = colnames(fg_model$cov1),
  HR = exp(fg_model$coef),
  Lower = exp(fg_model$coef - 1.96 * sqrt(diag(fg_model$var))),
  Upper = exp(fg_model$coef + 1.96 * sqrt(diag(fg_model$var))),
  P_value = 1 - pchisq((fg_model$coef / sqrt(diag(fg_model$var)))^2, 1)
)

# Save results
fg_path <- file.path("{output_dir}", "fine_gray_results.csv")
write.csv(fg_results, fg_path, row.names = FALSE)
cat("\\nFine-Gray results saved to: ", fg_path, "\\n")

# Generate Fine-Gray forest plot
fg_forest_path <- file.path("{output_dir}", "fine_gray_forest_plot.png")
png(fg_forest_path, width = 1000, height = {max(600, 200 + n_covs * 50)}, res = 300)

forestplot(
  labeltext = matrix(c(
    as.character(fg_results$Variable),
    sprintf("%.2f (%.2f-%.2f)", fg_results$HR, fg_results$Lower, fg_results$Upper),
    ifelse(fg_results$P_value < 0.001, "<0.001", sprintf("%.3f", fg_results$P_value))
  ), ncol = 3),
  mean = fg_results$HR,
  lower = fg_results$Lower,
  upper = fg_results$Upper,
  xlog = TRUE,
  xlab = "Sub-Hazard Ratio (95% CI)",
  title = "Fine-Gray Competing Risk Model",
  col = fpColors(box = "#A51C30", line = "darkblue"),
  zero = 1,
  txt_gp = fpTxtGp(label = gpar(cex = 0.8))
)

dev.off()
cat("\\nFine-Gray forest plot saved to: ", fg_forest_path, "\\n")

# === 1-year, 3-year, 5-year cumulative incidence ===
cat("\\n=== Cumulative Incidence at Specific Time Points ===\\n")
time_points <- c(12, 36, 60)
for (tp in time_points) {{
  ci_1 <- approx(cif${{`1`}}$time, cif${{`1`}}$est, xout = tp, rule = 2)$y
  ci_2 <- approx(cif${{`2`}}$time, cif${{`2`}}$est, xout = tp, rule = 2)$y
  cat(sprintf("At %d months: Event=%.3f, Competing=%.3f\\n", tp, ci_1, ci_2))
}}

cat("\\nFine-Gray analysis completed successfully\\n")
'''
        return script
    
    def execute_r_script(self, script: str, script_name: str = "analysis.R") -> Dict[str, Any]:
        """Execute an R script and return results."""
        if not self.check_r_available():
            return {"success": False, "error": "R is not installed or not in PATH"}
        
        # Write script to temp file
        script_path = self.output_dir / script_name
        script_path.write_text(script)
        
        try:
            result = subprocess.run(
                [self.rscript_path, str(script_path)],
                capture_output=True,
                text=True,
                timeout=300,
                cwd=str(self.output_dir)
            )
            
            return {
                "success": result.returncode == 0,
                "output": result.stdout,
                "error": result.stderr if result.returncode != 0 else None,
                "returncode": result.returncode,
                "script_path": str(script_path),
            }
        except subprocess.TimeoutExpired:
            return {"success": False, "error": "R script execution timed out (5 min)"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_output_files(self) -> List[str]:
        """List all output files generated by survival analyses."""
        files = []
        for f in self.output_dir.iterdir():
            if f.is_file() and f.suffix in [".png", ".csv", ".pdf"]:
                files.append(str(f))
        return sorted(files)
