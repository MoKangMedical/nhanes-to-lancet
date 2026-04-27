import { spawn } from "child_process";
import { writeFile, mkdir } from "fs/promises";
import { join } from "path";
import { existsSync } from "fs";

export interface RExecutionResult {
  success: boolean;
  output: string;
  error?: string;
  outputFiles?: string[];
}

/**
 * Execute R script and return results
 */
export async function executeRScript(
  scriptContent: string,
  scriptName: string,
  workingDir: string
): Promise<RExecutionResult> {
  try {
    // Ensure working directory exists
    if (!existsSync(workingDir)) {
      await mkdir(workingDir, { recursive: true });
    }

    // Write R script to file
    const scriptPath = join(workingDir, scriptName);
    await writeFile(scriptPath, scriptContent, "utf-8");

    // Execute R script
    return new Promise((resolve) => {
      const rProcess = spawn("Rscript", [scriptPath], {
        cwd: workingDir,
        env: { ...process.env }
      });

      let stdout = "";
      let stderr = "";

      rProcess.stdout.on("data", (data) => {
        stdout += data.toString();
      });

      rProcess.stderr.on("data", (data) => {
        stderr += data.toString();
      });

      rProcess.on("close", (code) => {
        if (code === 0) {
          resolve({
            success: true,
            output: stdout,
            error: stderr || undefined
          });
        } else {
          resolve({
            success: false,
            output: stdout,
            error: stderr || `R script exited with code ${code}`
          });
        }
      });

      rProcess.on("error", (err) => {
        resolve({
          success: false,
          output: stdout,
          error: `Failed to execute R script: ${err.message}`
        });
      });
    });
  } catch (error) {
    return {
      success: false,
      output: "",
      error: error instanceof Error ? error.message : "Unknown error"
    };
  }
}

/**
 * Generate R script for Kaplan-Meier survival analysis
 */
export function generateKaplanMeierScript(params: {
  dataPath: string;
  timeVariable: string;
  eventVariable: string;
  stratifyBy?: string;
  outputPath: string;
}): string {
  return `
# Install required packages if not already installed
if (!require("survival")) install.packages("survival", repos="https://cloud.r-project.org/")
if (!require("survminer")) install.packages("survminer", repos="https://cloud.r-project.org/")
if (!require("ggplot2")) install.packages("ggplot2", repos="https://cloud.r-project.org/")

library(survival)
library(survminer)
library(ggplot2)

# Load data
data <- read.csv("${params.dataPath}")

# Create survival object
surv_obj <- Surv(time = data$${params.timeVariable}, event = data$${params.eventVariable})

# Fit Kaplan-Meier model
${params.stratifyBy 
  ? `km_fit <- survfit(surv_obj ~ data$${params.stratifyBy})`
  : `km_fit <- survfit(surv_obj ~ 1)`
}

# Generate survival curve plot
png("${params.outputPath}", width = 800, height = 600, res = 120)
ggsurvplot(
  km_fit,
  data = data,
  pval = TRUE,
  conf.int = TRUE,
  risk.table = TRUE,
  risk.table.height = 0.25,
  ggtheme = theme_minimal(),
  palette = "lancet",
  title = "Kaplan-Meier Survival Curve"
)
dev.off()

# Print summary
print(summary(km_fit))

cat("Kaplan-Meier analysis completed successfully\\n")
`;
}

/**
 * Generate R script for Cox regression analysis
 */
export function generateCoxRegressionScript(params: {
  dataPath: string;
  timeVariable: string;
  eventVariable: string;
  covariates: string[];
  outputTablePath: string;
  outputForestPlotPath: string;
}): string {
  const covariatesFormula = params.covariates.join(" + ");
  
  return `
# Install required packages
if (!require("survival")) install.packages("survival", repos="https://cloud.r-project.org/")
if (!require("forestplot")) install.packages("forestplot", repos="https://cloud.r-project.org/")
if (!require("broom")) install.packages("broom", repos="https://cloud.r-project.org/")

library(survival)
library(forestplot)
library(broom)

# Load data
data <- read.csv("${params.dataPath}")

# Fit Cox proportional hazards model
cox_model <- coxph(Surv(${params.timeVariable}, ${params.eventVariable}) ~ ${covariatesFormula}, data = data)

# Get model summary
cox_summary <- summary(cox_model)
print(cox_summary)

# Extract results for table
cox_results <- tidy(cox_model, exponentiate = TRUE, conf.int = TRUE)
write.csv(cox_results, "${params.outputTablePath}", row.names = FALSE)

# Generate forest plot
png("${params.outputForestPlotPath}", width = 1000, height = 600, res = 120)

# Prepare data for forest plot
coef_data <- data.frame(
  Variable = cox_results$term,
  HR = cox_results$estimate,
  Lower = cox_results$conf.low,
  Upper = cox_results$conf.high,
  P = cox_results$p.value
)

# Create forest plot
forestplot(
  labeltext = as.matrix(coef_data[, c("Variable", "HR", "P")]),
  mean = coef_data$HR,
  lower = coef_data$Lower,
  upper = coef_data$Upper,
  xlog = TRUE,
  xlab = "Hazard Ratio (95% CI)",
  txt_gp = fpTxtGp(label = gpar(cex = 0.9)),
  col = fpColors(box = "royalblue", line = "darkblue")
)

dev.off()

cat("Cox regression analysis completed successfully\\n")
`;
}

/**
 * Generate R script for baseline characteristics table
 */
export function generateBaselineTableScript(params: {
  dataPath: string;
  groupVariable?: string;
  variables: string[];
  outputPath: string;
}): string {
  return `
# Install required packages
if (!require("gtsummary")) install.packages("gtsummary", repos="https://cloud.r-project.org/")
if (!require("flextable")) install.packages("flextable", repos="https://cloud.r-project.org/")
if (!require("officer")) install.packages("officer", repos="https://cloud.r-project.org/")

library(gtsummary)
library(flextable)
library(officer)

# Load data
data <- read.csv("${params.dataPath}")

# Select variables for table
table_vars <- c(${params.variables.map(v => `"${v}"`).join(", ")})

# Create baseline characteristics table
${params.groupVariable
  ? `tbl <- data %>%
  select(all_of(c("${params.groupVariable}", table_vars))) %>%
  tbl_summary(by = ${params.groupVariable}) %>%
  add_p() %>%
  add_overall()`
  : `tbl <- data %>%
  select(all_of(table_vars)) %>%
  tbl_summary()`
}

# Convert to flextable and save as Word document
ft <- as_flex_table(tbl)
doc <- read_docx()
doc <- body_add_flextable(doc, ft)
print(doc, target = "${params.outputPath}")

cat("Baseline table generated successfully\\n")
`;
}

/**
 * Generate R script for Fine-Gray competing risk analysis
 */
export function generateFineGrayScript(params: {
  dataPath: string;
  timeVariable: string;
  eventVariable: string;
  competingEvent: number;
  eventOfInterest: number;
  covariates: string[];
  outputPath: string;
}): string {
  const covariatesFormula = params.covariates.join(" + ");
  
  return `
# Install required packages
if (!require("cmprsk")) install.packages("cmprsk", repos="https://cloud.r-project.org/")
if (!require("tidycmprsk")) install.packages("tidycmprsk", repos="https://cloud.r-project.org/")
if (!require("ggplot2")) install.packages("ggplot2", repos="https://cloud.r-project.org/")

library(cmprsk)
library(tidycmprsk)
library(ggplot2)

# Load data
data <- read.csv("${params.dataPath}")

# Fit Fine-Gray model
fg_model <- crr(
  ftime = data$${params.timeVariable},
  fstatus = data$${params.eventVariable},
  cov1 = as.matrix(data[, c(${params.covariates.map(v => `"${v}"`).join(", ")})]),
  failcode = ${params.eventOfInterest},
  cencode = 0
)

# Print results
print(summary(fg_model))

# Generate cumulative incidence plot
png("${params.outputPath}", width = 800, height = 600, res = 120)

cif <- cuminc(
  ftime = data$${params.timeVariable},
  fstatus = data$${params.eventVariable}
)

plot(cif, 
     xlab = "Time",
     ylab = "Cumulative Incidence",
     main = "Cumulative Incidence Function",
     col = c("blue", "red"),
     lwd = 2)

legend("topleft", 
       legend = c("Event of Interest", "Competing Event"),
       col = c("blue", "red"),
       lwd = 2)

dev.off()

cat("Fine-Gray competing risk analysis completed successfully\\n")
`;
}
