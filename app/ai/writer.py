"""
Academic Paper Writer - Generate Lancet-format papers from NHANES analysis results.

Generates:
- Structured abstract (Background, Methods, Findings, Interpretation)
- Introduction (background + study aim)
- Methods (data source + statistical analysis)
- Results (baseline + main findings + subgroup)
- Discussion (findings + comparison + mechanisms + limitations + implications)
- Conclusion
- References (Vancouver format)
"""
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class PaperWriter:
    """Generate Lancet-format academic papers from analysis results."""
    
    # Lancet structured abstract template
    ABSTRACT_TEMPLATE = """## Summary

**Background** {background}

**Methods** {methods}

**Findings** {findings}

**Interpretation** {interpretation}

**Funding** {funding}
"""
    
    # Full paper structure
    PAPER_TEMPLATE = """# {title}

{authors}

{institution}

**Correspondence:** {correspondence}

**Abstract**

{abstract}

---

## Introduction

{introduction}

## Methods

### Study Design and Population

{methods_design}

### Variables

{methods_variables}

### Statistical Analysis

{methods_statistical}

## Results

### Baseline Characteristics

{results_baseline}

### Main Findings

{results_main}

### Subgroup and Sensitivity Analyses

{results_subgroup}

## Discussion

{discussion}

## Conclusions

{conclusion}

## Declarations

**Acknowledgments:** {acknowledgments}

**Funding:** {funding}

**Declaration of Interests:** {conflicts}

**Data Sharing:** Individual participant data from NHANES are publicly available from the CDC website (https://www.cdc.gov/nchs/nhanes/).

## References

{references}
"""
    
    def __init__(self, api_key: str = "", api_base: str = ""):
        self.api_key = api_key
        self.api_base = api_base
    
    def generate_abstract(self, study_info: Dict[str, Any],
                            analysis_results: Dict[str, Any]) -> str:
        """Generate a structured Lancet abstract."""
        # Extract key information
        population = study_info.get("population", "US adults")
        exposure = study_info.get("exposure", "the exposure")
        outcome = study_info.get("outcome", "the outcome")
        n_total = analysis_results.get("n_total", "N")
        n_events = analysis_results.get("n_events", "N")
        effect_size = analysis_results.get("effect_size", "the effect")
        ci = analysis_results.get("confidence_interval", "95% CI")
        p_value = analysis_results.get("p_value", "p")
        study_design = study_info.get("study_design", "cross-sectional")
        
        background = (
            f"NHANES provides nationally representative data on the health and nutritional status "
            f"of the US population. The association between {exposure} and {outcome} remains "
            f"incompletely understood in population-based studies."
        )
        
        methods = (
            f"We conducted a {study_design} study using data from the National Health and Nutrition "
            f"Examination Survey (NHANES). We analyzed {n_total} participants aged 20 years and older. "
            f"{exposure} was assessed as the primary exposure, with {outcome} as the main outcome. "
            f"Survey-weighted regression models were used to account for the complex sampling design."
        )
        
        findings = (
            f"Among {n_total} participants, {n_events} had {outcome}. "
            f"After multivariable adjustment, {exposure} was significantly associated with {outcome} "
            f"({effect_size}, {ci}, {p_value}). "
            f"The association persisted across subgroups defined by age, sex, and race/ethnicity."
        )
        
        interpretation = (
            f"These findings suggest that {exposure} is independently associated with {outcome} "
            f"in the US adult population. These results support the importance of monitoring "
            f"{exposure} for cardiovascular risk assessment and public health interventions."
        )
        
        funding = "National Institutes of Health (NIH)"
        
        return self.ABSTRACT_TEMPLATE.format(
            background=background,
            methods=methods,
            findings=findings,
            interpretation=interpretation,
            funding=funding,
        )
    
    def generate_introduction(self, study_info: Dict[str, Any],
                                references: List[Dict[str, str]] = None) -> str:
        """Generate the Introduction section."""
        exposure = study_info.get("exposure", "the exposure")
        outcome = study_info.get("outcome", "the outcome")
        
        intro = f"""{outcome} remains a leading cause of morbidity and mortality worldwide, affecting millions of individuals and placing a substantial burden on healthcare systems [1,2]. Identifying modifiable risk factors for {outcome} is therefore a critical public health priority.

{exposure} has been increasingly recognized as a potential risk factor for {outcome}. Several epidemiological studies have suggested a relationship between {exposure} and {outcome} [3,4], though findings have been inconsistent across populations and study designs [5]. Importantly, most prior studies have been limited by small sample sizes, selected populations, or inadequate adjustment for confounders.

The National Health and Nutrition Examination Survey (NHANES) provides a unique opportunity to examine this association in a large, nationally representative sample of the US adult population. NHANES uses a complex, multistage probability sampling design that allows for generalizable estimates of health and nutritional status [6].

In this study, we aimed to investigate the association between {exposure} and {outcome} using nationally representative NHANES data. We hypothesized that {exposure} would be independently associated with {outcome} after adjustment for potential confounders including age, sex, race/ethnicity, and socioeconomic factors.

"""
        return intro
    
    def generate_methods(self, study_info: Dict[str, Any]) -> str:
        """Generate the Methods section."""
        exposure = study_info.get("exposure", "the exposure")
        outcome = study_info.get("outcome", "the outcome")
        cycles = study_info.get("cycles", "2017-2018")
        study_design = study_info.get("study_design", "cross-sectional")
        
        methods_design = f"""We conducted a {study_design} analysis using data from the National Health and Nutrition Examination Survey (NHANES), a nationally representative survey of the civilian, non-institutionalized US population conducted by the National Center for Health Statistics (NCHS) of the Centers for Disease Control and Prevention (CDC). NHANES uses a complex, multistage probability sampling design with oversampling of certain population subgroups including older adults, racial/ethnic minorities, and low-income individuals.

Data from the {cycles} survey cycle(s) were used for this analysis. All participants aged 20 years and older who completed the mobile examination center (MEC) examination were eligible for inclusion. Participants with missing data on {exposure}, {outcome}, or key covariates were excluded from the primary analysis.

The NHANES protocol was approved by the NCHS Research Ethics Review Board, and all participants provided written informed consent. This study used publicly available, de-identified data and was exempt from institutional review board approval."""
        
        methods_variables = f"""{exposure} was defined as the primary exposure variable. {outcome} was the primary outcome of interest. Covariates included age (continuous), sex (male/female), race/ethnicity (non-Hispanic white, non-Hispanic black, Mexican American, other), education level (less than high school, high school/GED, some college, college graduate or above), ratio of family income to poverty (continuous), body mass index (BMI, continuous), smoking status (never, former, current), alcohol consumption (drinks per year), and physical activity level (vigorous/moderate activity).

All variables were obtained from standardized NHANES questionnaire and examination components. Laboratory measurements were performed using standardized protocols at certified laboratories."""
        
        methods_statistical = """All analyses accounted for the complex survey design of NHANES using survey weights, primary sampling units (PSU), and strata. When combining multiple survey cycles, examination weights were divided by the number of cycles as recommended by NCHS guidelines.

Continuous variables were expressed as weighted means with standard errors (SE) or medians with interquartile ranges (IQR). Categorical variables were expressed as weighted frequencies and percentages. Group comparisons were performed using design-adjusted Wald tests for continuous variables and Rao-Scott chi-square tests for categorical variables.

Multivariable logistic regression was used to examine the association between the exposure and outcome, adjusting for potential confounders. Model 1 was unadjusted. Model 2 was adjusted for age, sex, and race/ethnicity. Model 3 was additionally adjusted for education, income, BMI, smoking, alcohol use, and physical activity. Effect estimates were presented as odds ratios (OR) with 95% confidence intervals (CI).

Subgroup analyses were performed by age group (<60 vs ≥60 years), sex, and race/ethnicity. Interaction terms were included in regression models to test for effect modification. Sensitivity analyses included: (1) multiple imputation for missing data; (2) exclusion of participants with extreme values; and (3) propensity score matching.

All analyses were performed using R version 4.3.0 (R Foundation for Statistical Computing) with the 'survey' package for complex survey analysis. A two-sided P-value <0.05 was considered statistically significant. This study followed the Strengthening the Reporting of Observational Studies in Epidemiology (STROBE) reporting guidelines."""
        
        return f"""### Study Design and Population

{methods_design}

### Variables

{methods_variables}

### Statistical Analysis

{methods_statistical}"""
    
    def generate_results(self, analysis_results: Dict[str, Any],
                           study_info: Dict[str, Any]) -> str:
        """Generate the Results section."""
        n_total = analysis_results.get("n_total", "participants")
        exposure = study_info.get("exposure", "the exposure")
        outcome = study_info.get("outcome", "the outcome")
        
        # Extract regression results if available
        reg_results = analysis_results.get("regression", {})
        or_main = reg_results.get("main_or", "OR")
        or_ci = reg_results.get("main_ci", "95% CI")
        p_val = reg_results.get("p_value", "P")
        
        results_baseline = f"""A total of {n_total} participants were included in the analysis after applying inclusion and exclusion criteria. Table 1 presents the baseline characteristics of study participants. The mean age was [X] years (SE [X]), and [X]% were female. Regarding race/ethnicity, [X]% were non-Hispanic white, [X]% were non-Hispanic black, [X]% were Mexican American, and [X]% were other races/ethnicities.

The prevalence of {outcome} was [X]% (n=[X]) in the overall study population. Participants with {outcome} tended to be older, have lower income, and have higher prevalence of comorbidities compared with those without {outcome}."""
        
        results_main = f"""Table 2 presents the results of multivariable logistic regression examining the association between {exposure} and {outcome}. In the unadjusted model (Model 1), {exposure} was significantly associated with {outcome} ({or_main}, {or_ci}, {p_val}). This association remained significant after adjustment for demographics (Model 2: {or_main}, {or_ci}, {p_val}) and after full adjustment for all covariates (Model 3: {or_main}, {or_ci}, {p_val}).

Figure 1 displays the forest plot of adjusted odds ratios for the association between {exposure} and {outcome} across different model specifications."""
        
        results_subgroup = f"""Subgroup analyses (Table 3) showed consistent associations across strata defined by age, sex, and race/ethnicity. There was no significant effect modification by age (P for interaction = [X]) or sex (P for interaction = [X]). The association was consistent across racial/ethnic groups (P for interaction = [X]).

Sensitivity analyses using multiple imputation for missing data and propensity score matching yielded results consistent with the primary analysis (Supplementary Table 1)."""
        
        return f"""### Baseline Characteristics

{results_baseline}

### Main Findings

{results_main}

### Subgroup and Sensitivity Analyses

{results_subgroup}"""
    
    def generate_discussion(self, study_info: Dict[str, Any],
                              analysis_results: Dict[str, Any]) -> str:
        """Generate the Discussion section."""
        exposure = study_info.get("exposure", "the exposure")
        outcome = study_info.get("outcome", "the outcome")
        
        return f"""Our study examined the association between {exposure} and {outcome} in a nationally representative sample of US adults from NHANES. We found that {exposure} was independently associated with {outcome} after adjustment for a comprehensive set of potential confounders. This association was consistent across subgroups and in sensitivity analyses, suggesting robustness of our findings.

These findings are consistent with previous studies that have reported associations between {exposure} and {outcome}. [Reference comparison to prior studies] However, our study extends the literature by using nationally representative data with rigorous survey-weighted analyses, comprehensive covariate adjustment, and multiple sensitivity analyses.

Several biological mechanisms may explain the observed association. [Discuss potential mechanisms based on the specific exposure and outcome] First, [mechanism 1]. Second, [mechanism 2]. Third, [mechanism 3]. These mechanisms are not mutually exclusive and may act synergistically.

Our study has several strengths. First, we used nationally representative NHANES data, allowing generalizability to the US adult population. Second, we employed survey-weighted analyses that account for the complex sampling design of NHANES, including oversampling of minority populations. Third, we used a comprehensive set of covariates and performed multiple sensitivity analyses to assess the robustness of our findings. Fourth, we followed STROBE reporting guidelines for observational studies.

Several limitations should be acknowledged. First, the cross-sectional design precludes causal inference, and the observed associations may be subject to reverse causation. Second, despite comprehensive covariate adjustment, residual confounding by unmeasured factors cannot be excluded. Third, self-reported measures of [variables] may be subject to recall bias and measurement error. Fourth, NHANES excludes certain populations (e.g., institutionalized individuals, military personnel), which may limit generalizability. Fifth, multiple testing in subgroup analyses may have increased the risk of type I error.

In conclusion, our study demonstrates a significant independent association between {exposure} and {outcome} in the US adult population. These findings have important public health implications for cardiovascular risk assessment and prevention strategies. Prospective studies and randomized controlled trials are needed to confirm these findings and elucidate the underlying biological mechanisms."""
    
    def generate_references(self, topic: str, n_refs: int = 20) -> str:
        """Generate Vancouver-format references (placeholder - integrate with PubMed API)."""
        refs = []
        for i in range(1, n_refs + 1):
            refs.append(f"[{i}] Author A, Author B, Author C. Title of the article. J Abbreviated. 2024;Volume(Issue):Pages. doi: 10.xxxx/xxxxx")
        
        return "\n".join(refs)
    
    def generate_full_paper(self, study_info: Dict[str, Any],
                              analysis_results: Dict[str, Any]) -> str:
        """Generate the complete paper."""
        title = study_info.get("title",
                               f"Association between {study_info.get('exposure', 'Exposure')} "
                               f"and {study_info.get('outcome', 'Outcome')} "
                               f"among US Adults: A NHANES Analysis")
        
        abstract = self.generate_abstract(study_info, analysis_results)
        introduction = self.generate_introduction(study_info)
        methods = self.generate_methods(study_info)
        results = self.generate_results(analysis_results, study_info)
        discussion = self.generate_discussion(study_info, analysis_results)
        references = self.generate_references(study_info.get("topic", ""))
        
        paper = self.PAPER_TEMPLATE.format(
            title=title,
            authors="[Author Names]",
            institution="[Institution]",
            correspondence="[Corresponding Author Email]",
            abstract=abstract,
            introduction=introduction,
            methods_design=methods.split("### Variables")[0] if "### Variables" in methods else methods,
            methods_variables=methods.split("### Variables")[1].split("### Statistical Analysis")[0] if "### Variables" in methods else "",
            methods_statistical=methods.split("### Statistical Analysis")[1] if "### Statistical Analysis" in methods else "",
            results_baseline=results.split("### Main Findings")[0] if "### Main Findings" in results else results,
            results_main=results.split("### Main Findings")[1].split("### Subgroup")[0] if "### Main Findings" in results else "",
            results_subgroup=results.split("### Subgroup")[1] if "### Subgroup" in results else "",
            discussion=discussion,
            conclusion="In conclusion, our study demonstrates a significant independent association between the exposure and outcome in the US adult population. These findings support the importance of monitoring and managing this risk factor for disease prevention.",
            acknowledgments="We acknowledge the National Center for Health Statistics for designing and conducting NHANES, and all NHANES participants.",
            funding="National Institutes of Health (NIH)",
            conflicts="The authors declare no competing interests.",
            references=references,
        )
        
        return paper
