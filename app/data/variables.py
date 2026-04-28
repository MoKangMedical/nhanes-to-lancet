"""
NHANES Variable Knowledge Base - Comprehensive dictionary of NHANES variables.

Provides:
- Variable code -> description mapping
- Data type and value range information
- Category grouping (demographics, lab, questionnaire)
- Semantic search via keyword matching
"""
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from ..config import DATA_DIR

logger = logging.getLogger(__name__)


# Comprehensive NHANES variable dictionary
NHANES_VARIABLES = {
    # === DEMOGRAPHICS ===
    "SEQN": {"desc": "Respondent sequence number", "type": "id", "category": "Demographics", "file": "DEMO"},
    "RIDAGEYR": {"desc": "Age in years at screening", "type": "continuous", "range": [0, 80], "unit": "years", "category": "Demographics", "file": "DEMO"},
    "RIDAGEMN": {"desc": "Age in months at screening", "type": "continuous", "range": [0, 960], "unit": "months", "category": "Demographics", "file": "DEMO"},
    "RIAGENDR": {"desc": "Gender", "type": "categorical", "values": {1: "Male", 2: "Female"}, "category": "Demographics", "file": "DEMO"},
    "RIDRETH1": {"desc": "Race/Hispanic origin", "type": "categorical", "values": {1: "Mexican American", 2: "Other Hispanic", 3: "Non-Hispanic White", 4: "Non-Hispanic Black", 5: "Other Race/Multi-Racial"}, "category": "Demographics", "file": "DEMO"},
    "RIDRETH3": {"desc": "Race/Hispanic origin with NH Asian", "type": "categorical", "values": {1: "Mexican American", 2: "Other Hispanic", 3: "Non-Hispanic White", 4: "Non-Hispanic Black", 6: "Non-Hispanic Asian", 7: "Other Race/Multi-Racial"}, "category": "Demographics", "file": "DEMO"},
    "DMDEDUC2": {"desc": "Education level (adults 20+)", "type": "categorical", "values": {1: "<9th grade", 2: "9-11th grade", 3: "HS/GED", 4: "Some college", 5: "College+"}, "category": "Demographics", "file": "DEMO"},
    "DMDEDUC3": {"desc": "Education level (children 6-19)", "type": "categorical", "category": "Demographics", "file": "DEMO"},
    "DMDMARTL": {"desc": "Marital status", "type": "categorical", "values": {1: "Married", 2: "Widowed", 3: "Divorced", 4: "Separated", 5: "Never married", 6: "Living with partner"}, "category": "Demographics", "file": "DEMO"},
    "INDFMPIR": {"desc": "Ratio of family income to poverty", "type": "continuous", "range": [0, 5], "category": "Demographics", "file": "DEMO"},
    "DMDBORN4": {"desc": "Country of birth", "type": "categorical", "values": {1: "Born in US", 2: "Born elsewhere"}, "category": "Demographics", "file": "DEMO"},
    "RIDEXPRG": {"desc": "Pregnancy status", "type": "categorical", "values": {1: "Yes", 2: "No", 3: "Could not determine"}, "category": "Demographics", "file": "DEMO"},
    "WTMEC2YR": {"desc": "Full sample 2 year MEC exam weight", "type": "weight", "category": "Demographics", "file": "DEMO"},
    "WTINT2YR": {"desc": "Full sample 2 year interview weight", "type": "weight", "category": "Demographics", "file": "DEMO"},
    "SDMVPSU": {"desc": "Masked variance pseudo-PSU", "type": "survey", "category": "Demographics", "file": "DEMO"},
    "SDMVSTRA": {"desc": "Masked variance pseudo-stratum", "type": "survey", "category": "Demographics", "file": "DEMO"},
    
    # === BODY MEASURES ===
    "BMXBMI": {"desc": "Body Mass Index (kg/m2)", "type": "continuous", "range": [10, 80], "unit": "kg/m2", "category": "Body Measures", "file": "BMX"},
    "BMXWT": {"desc": "Weight (kg)", "type": "continuous", "range": [2, 300], "unit": "kg", "category": "Body Measures", "file": "BMX"},
    "BMXHT": {"desc": "Standing Height (cm)", "type": "continuous", "range": [80, 210], "unit": "cm", "category": "Body Measures", "file": "BMX"},
    "BMXWAIST": {"desc": "Waist Circumference (cm)", "type": "continuous", "range": [40, 200], "unit": "cm", "category": "Body Measures", "file": "BMX"},
    "BMXHEAD": {"desc": "Head Circumference (cm)", "type": "continuous", "range": [20, 70], "unit": "cm", "category": "Body Measures", "file": "BMX"},
    "BMXARML": {"desc": "Upper Arm Length (cm)", "type": "continuous", "range": [15, 55], "unit": "cm", "category": "Body Measures", "file": "BMX"},
    "BMXLEG": {"desc": "Upper Leg Length (cm)", "type": "continuous", "range": [20, 60], "unit": "cm", "category": "Body Measures", "file": "BMX"},
    "BMXARMC": {"desc": "Arm Circumference (cm)", "type": "continuous", "range": [15, 60], "unit": "cm", "category": "Body Measures", "file": "BMX"},
    "BMXTRI": {"desc": "Triceps Skinfold (mm)", "type": "continuous", "range": [2, 80], "unit": "mm", "category": "Body Measures", "file": "BMX"},
    "BMXSUB": {"desc": "Subscapular Skinfold (mm)", "type": "continuous", "range": [2, 80], "unit": "mm", "category": "Body Measures", "file": "BMX"},
    
    # === BLOOD PRESSURE ===
    "BPXSY1": {"desc": "Systolic BP - 1st reading", "type": "continuous", "range": [60, 280], "unit": "mmHg", "category": "Blood Pressure", "file": "BPX"},
    "BPXSY2": {"desc": "Systolic BP - 2nd reading", "type": "continuous", "range": [60, 280], "unit": "mmHg", "category": "Blood Pressure", "file": "BPX"},
    "BPXSY3": {"desc": "Systolic BP - 3rd reading", "type": "continuous", "range": [60, 280], "unit": "mmHg", "category": "Blood Pressure", "file": "BPX"},
    "BPXDI1": {"desc": "Diastolic BP - 1st reading", "type": "continuous", "range": [20, 150], "unit": "mmHg", "category": "Blood Pressure", "file": "BPX"},
    "BPXDI2": {"desc": "Diastolic BP - 2nd reading", "type": "continuous", "range": [20, 150], "unit": "mmHg", "category": "Blood Pressure", "file": "BPX"},
    "BPXDI3": {"desc": "Diastolic BP - 3rd reading", "type": "continuous", "range": [20, 150], "unit": "mmHg", "category": "Blood Pressure", "file": "BPX"},
    "BPQ020": {"desc": "Ever told you had high blood pressure", "type": "categorical", "values": {1: "Yes", 2: "No"}, "category": "BP Questionnaire", "file": "BPQ"},
    "BPQ030": {"desc": "Told had high blood pressure - 2+ times", "type": "categorical", "values": {1: "Yes", 2: "No"}, "category": "BP Questionnaire", "file": "BPQ"},
    "BPQ040A": {"desc": "Taking prescribed medicine for HBP", "type": "categorical", "values": {1: "Yes", 2: "No"}, "category": "BP Questionnaire", "file": "BPQ"},
    "BPQ050A": {"desc": "Now taking prescribed medicine for HBP", "type": "categorical", "values": {1: "Yes", 2: "No"}, "category": "BP Questionnaire", "file": "BPQ"},
    
    # === LABORATORY - CHOLESTEROL ===
    "LBXTC": {"desc": "Total cholesterol (mg/dL)", "type": "continuous", "range": [50, 400], "unit": "mg/dL", "category": "Cholesterol", "file": "TCHOL"},
    "LBDTCSI": {"desc": "Total cholesterol (mmol/L)", "type": "continuous", "range": [1, 10], "unit": "mmol/L", "category": "Cholesterol", "file": "TCHOL"},
    "LBXHDD": {"desc": "Direct HDL-cholesterol (mg/dL)", "type": "continuous", "range": [10, 150], "unit": "mg/dL", "category": "HDL", "file": "HDL"},
    "LBDHDD": {"desc": "Direct HDL-cholesterol (mg/dL) - derived", "type": "continuous", "range": [10, 150], "unit": "mg/dL", "category": "HDL", "file": "HDL"},
    "LBXTR": {"desc": "Triglycerides (mg/dL)", "type": "continuous", "range": [20, 2000], "unit": "mg/dL", "category": "Triglycerides", "file": "TRIGLY"},
    "LBDTRSI": {"desc": "Triglycerides (mmol/L)", "type": "continuous", "range": [0.2, 22], "unit": "mmol/L", "category": "Triglycerides", "file": "TRIGLY"},
    "LBDLDL": {"desc": "LDL-cholesterol (mg/dL) - Friedewald", "type": "continuous", "range": [10, 300], "unit": "mg/dL", "category": "Triglycerides", "file": "TRIGLY"},
    
    # === LABORATORY - GLUCOSE / DIABETES ===
    "LBXGLU": {"desc": "Fasting glucose (mg/dL)", "type": "continuous", "range": [30, 500], "unit": "mg/dL", "category": "Glucose", "file": "GLU"},
    "LBDGLUSI": {"desc": "Fasting glucose (mmol/L)", "type": "continuous", "range": [1.5, 28], "unit": "mmol/L", "category": "Glucose", "file": "GLU"},
    "LBXIN": {"desc": "Insulin (uU/mL)", "type": "continuous", "range": [1, 500], "unit": "uU/mL", "category": "Insulin", "file": "INS"},
    "LBDINSI": {"desc": "Insulin (pmol/L)", "type": "continuous", "range": [5, 3000], "unit": "pmol/L", "category": "Insulin", "file": "INS"},
    "LBXGH": {"desc": "Glycohemoglobin (%)", "type": "continuous", "range": [2, 18], "unit": "%", "category": "HbA1c", "file": "HBA1C"},
    "DIQ010": {"desc": "Doctor told you have diabetes", "type": "categorical", "values": {1: "Yes", 2: "No", 3: "Borderline"}, "category": "Diabetes", "file": "DIQ"},
    "DIQ050": {"desc": "Taking insulin now", "type": "categorical", "values": {1: "Yes", 2: "No"}, "category": "Diabetes", "file": "DIQ"},
    
    # === MEDICAL CONDITIONS ===
    "MCQ160A": {"desc": "Ever told had arthritis", "type": "categorical", "values": {1: "Yes", 2: "No"}, "category": "Medical Conditions", "file": "MCQ"},
    "MCQ160C": {"desc": "Ever told had congestive heart failure", "type": "categorical", "values": {1: "Yes", 2: "No"}, "category": "Medical Conditions", "file": "MCQ"},
    "MCQ160D": {"desc": "Ever told had coronary heart disease", "type": "categorical", "values": {1: "Yes", 2: "No"}, "category": "Medical Conditions", "file": "MCQ"},
    "MCQ160E": {"desc": "Ever told had heart attack", "type": "categorical", "values": {1: "Yes", 2: "No"}, "category": "Medical Conditions", "file": "MCQ"},
    "MCQ160F": {"desc": "Ever told had stroke", "type": "categorical", "values": {1: "Yes", 2: "No"}, "category": "Medical Conditions", "file": "MCQ"},
    "MCQ220": {"desc": "Ever told had cancer or malignancy", "type": "categorical", "values": {1: "Yes", 2: "No"}, "category": "Medical Conditions", "file": "MCQ"},
    "MCQ300A": {"desc": "Close relative had heart attack", "type": "categorical", "values": {1: "Yes", 2: "No"}, "category": "Medical Conditions", "file": "MCQ"},
    "MCQ300B": {"desc": "Close relative had stroke", "type": "categorical", "values": {1: "Yes", 2: "No"}, "category": "Medical Conditions", "file": "MCQ"},
    
    # === SMOKING ===
    "SMQ020": {"desc": "Smoked at least 100 cigarettes in life", "type": "categorical", "values": {1: "Yes", 2: "No"}, "category": "Smoking", "file": "SMQ"},
    "SMQ040": {"desc": "Do you now smoke cigarettes", "type": "categorical", "values": {1: "Every day", 2: "Some days", 3: "Not at all"}, "category": "Smoking", "file": "SMQ"},
    "SMD050": {"desc": "Age started smoking", "type": "continuous", "range": [5, 80], "unit": "years", "category": "Smoking", "file": "SMQ"},
    "SMD057": {"desc": "# cigarettes smoked per day now", "type": "continuous", "range": [0, 100], "category": "Smoking", "file": "SMQ"},
    "SMD059": {"desc": "During past 30 days # cigarettes/day", "type": "continuous", "range": [0, 100], "category": "Smoking", "file": "SMQ"},
    
    # === ALCOHOL ===
    "ALQ101": {"desc": "Had at least 12 drinks in a year", "type": "categorical", "values": {1: "Yes", 2: "No"}, "category": "Alcohol", "file": "ALQ"},
    "ALQ111": {"desc": "Had at least 12 drinks in lifetime", "type": "categorical", "values": {1: "Yes", 2: "No"}, "category": "Alcohol", "file": "ALQ"},
    "ALQ120Q": {"desc": "How often drink per year", "type": "continuous", "range": [0, 365], "unit": "times/year", "category": "Alcohol", "file": "ALQ"},
    "ALQ130": {"desc": "Average # drinks on drinking day", "type": "continuous", "range": [0, 30], "category": "Alcohol", "file": "ALQ"},
    "ALQ141Q": {"desc": "# days had 4-5 drinks past 30 days", "type": "continuous", "range": [0, 30], "category": "Alcohol", "file": "ALQ"},
    
    # === PHYSICAL ACTIVITY ===
    "PAQ605": {"desc": "Vigorous work activity", "type": "categorical", "values": {1: "Yes", 2: "No"}, "category": "Physical Activity", "file": "PAQ"},
    "PAQ610": {"desc": "Days vigorous work per week", "type": "continuous", "range": [0, 7], "unit": "days", "category": "Physical Activity", "file": "PAQ"},
    "PAQ620": {"desc": "Moderate work activity", "type": "categorical", "values": {1: "Yes", 2: "No"}, "category": "Physical Activity", "file": "PAQ"},
    "PAQ635": {"desc": "Vigorous recreational activities", "type": "categorical", "values": {1: "Yes", 2: "No"}, "category": "Physical Activity", "file": "PAQ"},
    "PAQ650": {"desc": "Moderate recreational activities", "type": "categorical", "values": {1: "Yes", 2: "No"}, "category": "Physical Activity", "file": "PAQ"},
    "PAQ665": {"desc": "Days moderate recreational per week", "type": "continuous", "range": [0, 7], "unit": "days", "category": "Physical Activity", "file": "PAQ"},
    "PAD615": {"desc": "Minutes vigorous-intensity work", "type": "continuous", "range": [0, 600], "unit": "min", "category": "Physical Activity", "file": "PAQ"},
    "PAD660": {"desc": "Minutes moderate recreational", "type": "continuous", "range": [0, 600], "unit": "min", "category": "Physical Activity", "file": "PAQ"},
    "PAD680": {"desc": "Minutes sedentary activity", "type": "continuous", "range": [0, 1440], "unit": "min", "category": "Physical Activity", "file": "PAQ"},
    
    # === DIET ===
    "DBQ700": {"desc": "How healthy is your diet", "type": "categorical", "values": {1: "Excellent", 2: "Very good", 3: "Good", 4: "Fair", 5: "Poor"}, "category": "Diet", "file": "DBQ"},
    "DBQ197": {"desc": "Past 30 day milk products consumed", "type": "categorical", "values": {1: "Yes", 2: "No"}, "category": "Diet", "file": "DBQ"},
    "DR1TKCAL": {"desc": "Energy (kcal) - Day 1", "type": "continuous", "range": [0, 10000], "unit": "kcal", "category": "Dietary Intake", "file": "DR1TOT"},
    "DR1TPROT": {"desc": "Protein (g) - Day 1", "type": "continuous", "range": [0, 500], "unit": "g", "category": "Dietary Intake", "file": "DR1TOT"},
    "DR1TTFAT": {"desc": "Total fat (g) - Day 1", "type": "continuous", "range": [0, 500], "unit": "g", "category": "Dietary Intake", "file": "DR1TOT"},
    "DR1TCARB": {"desc": "Carbohydrate (g) - Day 1", "type": "continuous", "range": [0, 1000], "unit": "g", "category": "Dietary Intake", "file": "DR1TOT"},
    "DR1TFIBE": {"desc": "Dietary fiber (g) - Day 1", "type": "continuous", "range": [0, 200], "unit": "g", "category": "Dietary Intake", "file": "DR1TOT"},
    "DR1TSUGR": {"desc": "Total sugars (g) - Day 1", "type": "continuous", "range": [0, 500], "unit": "g", "category": "Dietary Intake", "file": "DR1TOT"},
    "DR1TSODI": {"desc": "Sodium (mg) - Day 1", "type": "continuous", "range": [0, 20000], "unit": "mg", "category": "Dietary Intake", "file": "DR1TOT"},
    "DR1TPOTA": {"desc": "Potassium (mg) - Day 1", "type": "continuous", "range": [0, 20000], "unit": "mg", "category": "Dietary Intake", "file": "DR1TOT"},
    "DR1TIRON": {"desc": "Iron (mg) - Day 1", "type": "continuous", "range": [0, 100], "unit": "mg", "category": "Dietary Intake", "file": "DR1TOT"},
    "DR1TCAFF": {"desc": "Caffeine (mg) - Day 1", "type": "continuous", "range": [0, 5000], "unit": "mg", "category": "Dietary Intake", "file": "DR1TOT"},
    "DR1TALCO": {"desc": "Alcohol (g) - Day 1", "type": "continuous", "range": [0, 500], "unit": "g", "category": "Dietary Intake", "file": "DR1TOT"},
    "WTDRD1": {"desc": "Dietary day 1 sample weight", "type": "weight", "category": "Dietary Intake", "file": "DR1TOT"},
    
    # === KIDNEY ===
    "KIQ022": {"desc": "Ever told had weak/failing kidneys", "type": "categorical", "values": {1: "Yes", 2: "No"}, "category": "Kidney", "file": "KIQ_U"},
    "KIQ025": {"desc": "Received dialysis in past 12 months", "type": "categorical", "values": {1: "Yes", 2: "No"}, "category": "Kidney", "file": "KIQ_U"},
    "URXUMA": {"desc": "Albumin, urine (ug/mL)", "type": "continuous", "range": [0, 500], "unit": "ug/mL", "category": "Kidney Labs", "file": "ALB"},
    "URXUCR": {"desc": "Creatinine, urine (mg/dL)", "type": "continuous", "range": [0, 500], "unit": "mg/dL", "category": "Kidney Labs", "file": "ALB"},
    "LBXSCR": {"desc": "Creatinine, serum (mg/dL)", "type": "continuous", "range": [0, 20], "unit": "mg/dL", "category": "Kidney Labs", "file": "SCR"},
    "LBXBPB": {"desc": "Blood lead (ug/dL)", "type": "continuous", "range": [0, 100], "unit": "ug/dL", "category": "Environmental", "file": "PBP"},
    
    # === SLEEP ===
    "SLQ050": {"desc": "Ever told had sleep disorder", "type": "categorical", "values": {1: "Yes", 2: "No"}, "category": "Sleep", "file": "SLQ"},
    "SLQ060": {"desc": "Hours of sleep on weekdays", "type": "continuous", "range": [0, 24], "unit": "hours", "category": "Sleep", "file": "SLQ"},
    "SLQ080": {"desc": "Hours of sleep on weekends", "type": "continuous", "range": [0, 24], "unit": "hours", "category": "Sleep", "file": "SLQ"},
    "SLQ100": {"desc": "Trouble sleeping in past month", "type": "categorical", "values": {1: "Almost always", 2: "Sometimes", 3: "Rarely", 4: "Never"}, "category": "Sleep", "file": "SLQ"},
    
    # === DEPRESSION ===
    "DPQ010": {"desc": "Have little interest in things", "type": "ordinal", "values": {0: "Not at all", 1: "Several days", 2: "More than half", 3: "Nearly every day"}, "category": "Depression (PHQ-9)", "file": "DPQ"},
    "DPQ020": {"desc": "Feeling down/depressed/hopeless", "type": "ordinal", "values": {0: "Not at all", 1: "Several days", 2: "More than half", 3: "Nearly every day"}, "category": "Depression (PHQ-9)", "file": "DPQ"},
    "DPQ030": {"desc": "Trouble sleeping", "type": "ordinal", "values": {0: "Not at all", 1: "Several days", 2: "More than half", 3: "Nearly every day"}, "category": "Depression (PHQ-9)", "file": "DPQ"},
    "DPQ040": {"desc": "Feeling tired/low energy", "type": "ordinal", "values": {0: "Not at all", 1: "Several days", 2: "More than half", 3: "Nearly every day"}, "category": "Depression (PHQ-9)", "file": "DPQ"},
    "DPQ050": {"desc": "Poor appetite or overeating", "type": "ordinal", "values": {0: "Not at all", 1: "Several days", 2: "More than half", 3: "Nearly every day"}, "category": "Depression (PHQ-9)", "file": "DPQ"},
    "DPQ060": {"desc": "Feeling bad about yourself", "type": "ordinal", "values": {0: "Not at all", 1: "Several days", 2: "More than half", 3: "Nearly every day"}, "category": "Depression (PHQ-9)", "file": "DPQ"},
    "DPQ070": {"desc": "Trouble concentrating", "type": "ordinal", "values": {0: "Not at all", 1: "Several days", 2: "More than half", 3: "Nearly every day"}, "category": "Depression (PHQ-9)", "file": "DPQ"},
    "DPQ080": {"desc": "Moving/speaking slowly or fidgety", "type": "ordinal", "values": {0: "Not at all", 1: "Several days", 2: "More than half", 3: "Nearly every day"}, "category": "Depression (PHQ-9)", "file": "DPQ"},
    "DPQ090": {"desc": "Thoughts of self-harm", "type": "ordinal", "values": {0: "Not at all", 1: "Several days", 2: "More than half", 3: "Nearly every day"}, "category": "Depression (PHQ-9)", "file": "DPQ"},
    
    # === CARDIOVASCULAR ===
    "CDQ001": {"desc": "Chest pain when walking uphill/hurry", "type": "categorical", "values": {1: "Yes", 2: "No"}, "category": "Cardiovascular", "file": "CDQ"},
    "CDQ002": {"desc": "Chest pain when walking at normal pace", "type": "categorical", "values": {1: "Yes", 2: "No"}, "category": "Cardiovascular", "file": "CDQ"},
    "CDQ003": {"desc": "Chest pain at rest", "type": "categorical", "values": {1: "Yes", 2: "No"}, "category": "Cardiovascular", "file": "CDQ"},
    "CDQ004": {"desc": "Chest pain relieved by standing/rest", "type": "categorical", "values": {1: "Yes", 2: "No"}, "category": "Cardiovascular", "file": "CDQ"},
    
    # === HEALTH CARE UTILIZATION ===
    "HUQ010": {"desc": "General health condition", "type": "categorical", "values": {1: "Excellent", 2: "Very good", 3: "Good", 4: "Fair", 5: "Poor"}, "category": "Health Care", "file": "HUQ"},
    "HUQ030": {"desc": "Routine place to go for health care", "type": "categorical", "values": {1: "Yes", 2: "No"}, "category": "Health Care", "file": "HUQ"},
    "HUQ050": {"desc": "# times in hospital past 12 months", "type": "continuous", "range": [0, 30], "category": "Health Care", "file": "HUQ"},
    
    # === WEIGHT HISTORY ===
    "WHD010": {"desc": "Current self-reported height", "type": "continuous", "range": [50, 220], "unit": "cm", "category": "Weight History", "file": "WHQ"},
    "WHD020": {"desc": "Current self-reported weight", "type": "continuous", "range": [20, 300], "unit": "kg", "category": "Weight History", "file": "WHQ"},
    "WHD050": {"desc": "Weight 1 year ago", "type": "continuous", "range": [20, 300], "unit": "kg", "category": "Weight History", "file": "WHQ"},
    "WHD110": {"desc": "Weight 10 years ago", "type": "continuous", "range": [20, 300], "unit": "kg", "category": "Weight History", "file": "WHQ"},
    "WHD120": {"desc": "Greatest weight", "type": "continuous", "range": [20, 300], "unit": "kg", "category": "Weight History", "file": "WHQ"},
    "WHD140": {"desc": "Age when heaviest", "type": "continuous", "range": [5, 100], "unit": "years", "category": "Weight History", "file": "WHQ"},
    "WHD150": {"desc": "Trying to lose weight in past year", "type": "categorical", "values": {1: "Yes", 2: "No"}, "category": "Weight History", "file": "WHQ"},
    
    # === ORAL HEALTH ===
    "OHQ030": {"desc": "Last dental visit", "type": "categorical", "values": {1: "<6 months", 2: "6-12 months", 3: "1-2 years", 4: "2-5 years", 5: ">5 years", 6: "Never"}, "category": "Oral Health", "file": "OHQ"},
    
    # === MORTALITY (linked data) ===
    "UCOD_LEADING": {"desc": "Underlying cause of death - recode", "type": "categorical", "category": "Mortality", "file": "MORT"},
    "MORTSTAT": {"desc": "Final mortality status", "type": "categorical", "values": {0: "Assumed alive", 1: "Assumed deceased"}, "category": "Mortality", "file": "MORT"},
    "PERMTH_INT": {"desc": "Months of follow-up from interview", "type": "continuous", "range": [0, 300], "unit": "months", "category": "Mortality", "file": "MORT"},
    "PERMTH_EXM": {"desc": "Months of follow-up from MEC exam", "type": "continuous", "range": [0, 300], "unit": "months", "category": "Mortality", "file": "MORT"},
}

# Disease-phenotype -> recommended variable sets
PHENOTYPE_VARIABLES = {
    "obesity": {
        "exposure": ["BMXBMI", "BMXWT", "BMXHT", "BMXWAIST"],
        "outcome": ["DIQ010", "MCQ160C", "MCQ160D", "MCQ160E", "BPQ020"],
        "covariates": ["RIDAGEYR", "RIAGENDR", "RIDRETH1", "DMDEDUC2", "INDFMPIR", "SMQ020", "SMQ040", "PAQ605", "ALQ120Q"],
    },
    "diabetes": {
        "exposure": ["LBXGLU", "LBXGH", "LBXIN", "DIQ010"],
        "outcome": ["MCQ160C", "MCQ160D", "MCQ160E", "MCQ160F", "MORTSTAT"],
        "covariates": ["RIDAGEYR", "RIAGENDR", "RIDRETH1", "BMXBMI", "BPXSY1", "BPXDI1", "LBXTC", "LBXHDD", "SMQ020", "PAQ605"],
    },
    "hypertension": {
        "exposure": ["BPXSY1", "BPXSY2", "BPXSY3", "BPXDI1", "BPXDI2", "BPXDI3", "BPQ020"],
        "outcome": ["MCQ160C", "MCQ160D", "MCQ160E", "MCQ160F", "MORTSTAT"],
        "covariates": ["RIDAGEYR", "RIAGENDR", "RIDRETH1", "BMXBMI", "DIQ010", "LBXTC", "SMQ020", "DR1TSODI", "ALQ120Q"],
    },
    "dyslipidemia": {
        "exposure": ["LBXTC", "LBXHDD", "LBXTR", "LBDLDL"],
        "outcome": ["MCQ160D", "MCQ160E", "MCQ160C", "MORTSTAT"],
        "covariates": ["RIDAGEYR", "RIAGENDR", "RIDRETH1", "BMXBMI", "DIQ010", "BPQ020", "SMQ020", "PAQ605"],
    },
    "cardiovascular_disease": {
        "exposure": ["MCQ160D", "MCQ160E", "MCQ160C", "CDQ001", "CDQ002", "CDQ003"],
        "outcome": ["MORTSTAT", "UCOD_LEADING", "PERMTH_INT"],
        "covariates": ["RIDAGEYR", "RIAGENDR", "RIDRETH1", "BMXBMI", "BPXSY1", "LBXTC", "LBXHDD", "DIQ010", "SMQ020", "PAQ605"],
    },
    "smoking": {
        "exposure": ["SMQ020", "SMQ040", "SMD050", "SMD057", "SMD059"],
        "outcome": ["MCQ160C", "MCQ160D", "MCQ160E", "MCQ160F", "MCQ220", "MORTSTAT"],
        "covariates": ["RIDAGEYR", "RIAGENDR", "RIDRETH1", "BMXBMI", "DMDEDUC2", "INDFMPIR", "ALQ120Q", "PAQ605"],
    },
    "depression": {
        "exposure": ["DPQ010", "DPQ020", "DPQ030", "DPQ040", "DPQ050", "DPQ060", "DPQ070", "DPQ080", "DPQ090"],
        "outcome": ["MORTSTAT", "PERMTH_INT", "HUQ010"],
        "covariates": ["RIDAGEYR", "RIAGENDR", "RIDRETH1", "DMDEDUC2", "INDFMPIR", "BMXBMI", "SLQ060", "SMQ020", "ALQ120Q"],
    },
    "chronic_kidney_disease": {
        "exposure": ["LBXSCR", "URXUMA", "URXUCR", "KIQ022"],
        "outcome": ["MORTSTAT", "MCQ160C", "MCQ160D"],
        "covariates": ["RIDAGEYR", "RIAGENDR", "RIDRETH1", "BMXBMI", "BPXSY1", "DIQ010", "LBXTC", "SMQ020"],
    },
    "diet_quality": {
        "exposure": ["DR1TKCAL", "DR1TPROT", "DR1TTFAT", "DR1TCARB", "DR1TFIBE", "DR1TSUGR", "DR1TSODI", "DR1TPOTA"],
        "outcome": ["BMXBMI", "DIQ010", "BPQ020", "MCQ160D", "MORTSTAT"],
        "covariates": ["RIDAGEYR", "RIAGENDR", "RIDRETH1", "DMDEDUC2", "INDFMPIR", "SMQ020", "PAQ605", "WTDRD1"],
    },
    "sleep": {
        "exposure": ["SLQ060", "SLQ080", "SLQ050", "SLQ100"],
        "outcome": ["BMXBMI", "DIQ010", "BPQ020", "DPQ010", "MORTSTAT"],
        "covariates": ["RIDAGEYR", "RIAGENDR", "RIDRETH1", "DMDEDUC2", "INDFMPIR", "SMQ020", "PAQ605"],
    },
}


class NHANESVariableKB:
    """NHANES Variable Knowledge Base with semantic search."""
    
    def __init__(self):
        self.variables = NHANES_VARIABLES
        self.phenotypes = PHENOTYPE_VARIABLES
    
    def get_variable(self, code: str) -> Optional[dict]:
        return self.variables.get(code.upper())
    
    def search(self, query: str, top_k: int = 10) -> List[Tuple[str, dict, float]]:
        """Search variables by keyword matching (simple TF-IDF-like scoring)."""
        query_lower = query.lower()
        query_words = set(query_lower.split())
        
        results = []
        for code, info in self.variables.items():
            desc_lower = info["desc"].lower()
            cat_lower = info.get("category", "").lower()
            
            # Score based on word overlap
            desc_words = set(desc_lower.split())
            cat_words = set(cat_lower.split())
            
            # Exact match bonus
            if query_lower in desc_lower:
                score = 2.0
            elif query_lower in cat_lower:
                score = 1.5
            else:
                overlap = len(query_words & desc_words) + len(query_words & cat_words) * 0.5
                score = overlap / max(len(query_words), 1)
            
            if score > 0:
                results.append((code, info, score))
        
        results.sort(key=lambda x: x[2], reverse=True)
        return results[:top_k]
    
    def get_phenotype_vars(self, phenotype: str) -> Optional[dict]:
        return self.phenotypes.get(phenotype.lower())
    
    def list_phenotypes(self) -> List[str]:
        return list(self.phenotypes.keys())
    
    def list_categories(self) -> List[str]:
        cats = set()
        for v in self.variables.values():
            cats.add(v.get("category", "Unknown"))
        return sorted(cats)
    
    def get_variables_by_category(self, category: str) -> List[Tuple[str, dict]]:
        return [(code, info) for code, info in self.variables.items()
                if info.get("category", "").lower() == category.lower()]
    
    def to_json(self) -> str:
        return json.dumps(self.variables, indent=2)
    
    def export_for_chromadb(self) -> List[dict]:
        """Export variables in a format suitable for ChromaDB embedding."""
        docs = []
        for code, info in self.variables.items():
            docs.append({
                "id": code,
                "text": f"{code}: {info['desc']} (Category: {info.get('category', 'N/A')}, Type: {info.get('type', 'N/A')})",
                "metadata": {
                    "code": code,
                    "category": info.get("category", ""),
                    "type": info.get("type", ""),
                    "file": info.get("file", ""),
                }
            })
        return docs
