# NHANES Analysis Examples

## Example 1: BMI and Hypertension (Cross-Sectional)

### Research Question
Is body mass index (BMI) independently associated with hypertension prevalence among US adults?

### Variables
- **Exposure**: BMXBMI (Body Mass Index, kg/m²)
- **Outcome**: BPQ020 (Ever told had high blood pressure)
- **Covariates**: RIDAGEYR, RIAGENDR, RIDRETH1, DMDEDUC2, INDFMPIR, SMQ020, ALQ120Q, PAQ605

### Statistical Approach
```r
library(survey)
data <- read.csv("analysis_data.csv")
design <- svydesign(id=~SDMVPSU, strata=~SDMVSTRA, weights=~WTMEC2YR, data=data, nest=TRUE)

# Model 1: Unadjusted
m1 <- svyglm(BPQ020 ~ BMXBMI, design=design, family=quasibinomial)

# Model 2: Adjusted for demographics
m2 <- svyglm(BPQ020 ~ BMXBMI + RIDAGEYR + RIAGENDR + RIDRETH1, design=design, family=quasibinomial)

# Model 3: Fully adjusted
m3 <- svyglm(BPQ020 ~ BMXBMI + RIDAGEYR + RIAGENDR + RIDRETH1 + DMDEDUC2 + INDFMPIR + SMQ020, design=design, family=quasibinomial)

# Odds ratios
exp(cbind(OR=coef(m3), confint(m3)))
```

### Expected Output
| Variable | OR (95% CI) | P-value |
|----------|-------------|---------|
| BMI (per 5 kg/m²) | 1.42 (1.35-1.49) | <0.001 |
| Age (per 10 years) | 1.38 (1.31-1.45) | <0.001 |
| Male vs Female | 1.21 (1.08-1.36) | 0.001 |

---

## Example 2: Diabetes and CVD Mortality (Cohort)

### Research Question
Is diabetes associated with increased cardiovascular mortality risk?

### Variables
- **Exposure**: DIQ010 (Diabetes diagnosis)
- **Outcome**: MORTSTAT (Mortality status), UCOD_LEADING (Cause of death)
- **Time**: PERMTH_EXM (Months of follow-up)
- **Covariates**: RIDAGEYR, RIAGENDR, BMXBMI, BPXSY1, LBXTC

### Statistical Approach
```r
library(survival)
library(survminer)

# Kaplan-Meier
surv_obj <- Surv(time=data$PERMTH_EXM, event=data$MORTSTAT)
km_fit <- survfit(surv_obj ~ data$DIQ010, data=data)
ggsurvplot(km_fit, pval=TRUE, risk.table=TRUE, palette="lancet")

# Cox regression
cox_model <- coxph(Surv(PERMTH_EXM, MORTSTAT) ~ DIQ010 + RIDAGEYR + RIAGENDR + BMXBMI + BPXSY1, data=data)
summary(cox_model)
```

---

## Example 3: Sleep Duration and Depression

### Research Question
Is short sleep duration (<6 hours) associated with higher PHQ-9 depression scores?

### Variables
- **Exposure**: SLQ060 (Hours of sleep on weekdays)
- **Outcome**: PHQ-9 total score (sum of DPQ010-DPQ090)
- **Covariates**: RIDAGEYR, RIAGENDR, RIDRETH1, DMDEDUC2, BMXBMI

### Analysis
Survey-weighted linear regression with PHQ-9 score as continuous outcome.
