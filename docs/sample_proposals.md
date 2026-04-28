# Sample Research Proposals for NHANES to Lancet

## Template 1: Cross-Sectional Study - BMI and Hypertension

**Title**: Association between Body Mass Index and Hypertension among US Adults: A Cross-Sectional Study Using NHANES 2017-2018

**Background**: Obesity is a major risk factor for hypertension. Previous studies have shown a linear relationship between BMI and blood pressure, but population-based estimates using nationally representative data with proper survey weights are needed.

**Objective**: To examine the association between BMI (continuous and categorical) and hypertension prevalence among US adults aged 20 years and older.

**Study Design**: Cross-sectional analysis of NHANES 2017-2018 data.

**Population**: Adults aged 20+ who completed MEC examination (n approximately 4,500).

**Exposure**: Body Mass Index (BMXBMI), categorized as: Normal (18.5-24.9), Overweight (25-29.9), Obese (30+).

**Outcome**: Hypertension defined as: SBP >= 130 mmHg, or DBP >= 80 mmHg, or self-reported antihypertensive medication use (BPQ050A).

**Covariates**: Age (RIDAGEYR), Sex (RIAGENDR), Race/Ethnicity (RIDRETH1), Education (DMDEDUC2), Income (INDFMPIR), Smoking (SMQ020), Alcohol (ALQ120Q), Physical Activity (PAQ605).

**Statistical Methods**: Survey-weighted logistic regression with three models: Model 1 (unadjusted), Model 2 (demographics), Model 3 (fully adjusted). Subgroup analyses by sex and race/ethnicity.

---

## Template 2: Cohort Study - Diabetes and Cardiovascular Mortality

**Title**: Diabetes Mellitus and Cardiovascular Disease Mortality: A Prospective Cohort Study Using Linked NHANES-Mortality Data

**Background**: Diabetes is associated with increased cardiovascular mortality, but the magnitude of risk in the general US population using nationally representative data needs updated quantification.

**Objective**: To estimate the hazard ratio for cardiovascular disease mortality comparing adults with and without diabetes.

**Study Design**: Prospective cohort using NHANES III (1988-1994) linked to National Death Index through 2019.

**Population**: Adults aged 30+ with fasting glucose data and mortality follow-up (n approximately 15,000).

**Exposure**: Diabetes defined as: fasting glucose >= 126 mg/dL, HbA1c >= 6.5%, self-reported diagnosis (DIQ010), or diabetes medication use.

**Outcome**: Cardiovascular mortality (ICD-10: I00-I99) from National Death Index.

**Time Variable**: PERMTH_EXM (months from MEC exam to death/censoring).

**Covariates**: Age, sex, race, BMI, blood pressure, cholesterol, smoking, eGFR.

**Statistical Methods**: Kaplan-Meier survival curves, Cox proportional hazards regression, Fine-Gray competing risk model.

---

## Template 3: Cross-Sectional - Sleep and Depression

**Title**: Association between Sleep Duration and Depression Severity among US Adults: NHANES 2017-2018

**Background**: Short and long sleep duration are associated with depression, but the dose-response relationship and effect modification by sex and age are not well characterized.

**Objective**: To examine the association between self-reported sleep duration and PHQ-9 depression scores.

**Study Design**: Cross-sectional.

**Exposure**: Sleep duration (SLQ060), categorized: <6h, 6-7h, 7-8h (reference), >8h.

**Outcome**: PHQ-9 score (sum of DPQ010-DPQ090), categorized: None (0-4), Mild (5-9), Moderate (10-14), Severe (15+).

**Analysis**: Survey-weighted multinomial logistic regression.
