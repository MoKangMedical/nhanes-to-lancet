"""
Variable Mapper - Map research variables to NHANES database variables.

Uses semantic matching and the NHANES Variable Knowledge Base
to find the best NHANES variables for a given research proposal.
"""
import logging
from typing import Dict, List, Optional, Tuple, Any

from ..data.variables import NHANESVariableKB

logger = logging.getLogger(__name__)


class VariableMapper:
    """Map research proposal variables to NHANES database variables."""
    
    def __init__(self):
        self.kb = NHANESVariableKB()
    
    def map_variables(self, proposal_variables: Dict[str, List[str]],
                       research_topic: str = "") -> Dict[str, Any]:
        """
        Map proposal variables to NHANES variables.
        
        Args:
            proposal_variables: Dict with 'exposure', 'outcome', 'covariates' lists
            research_topic: Overall research topic for context
            
        Returns:
            Mapping results with confidence scores
        """
        mappings = {
            "exposure": [],
            "outcome": [],
            "covariates": [],
            "suggested_cycles": ["2017-2018"],
            "phenotype_match": None,
        }
        
        # Try phenotype-based mapping first
        if research_topic:
            phenotype = self._match_phenotype(research_topic)
            if phenotype:
                mappings["phenotype_match"] = phenotype
                phenotype_vars = self.kb.get_phenotype_vars(phenotype)
                if phenotype_vars:
                    for var_type in ["exposure", "outcome", "covariates"]:
                        for var_code in phenotype_vars.get(var_type, []):
                            var_info = self.kb.get_variable(var_code)
                            if var_info:
                                mappings[var_type].append({
                                    "nhanes_code": var_code,
                                    "description": var_info["desc"],
                                    "category": var_info.get("category", ""),
                                    "file": var_info.get("file", ""),
                                    "confidence": 0.9,
                                    "mapping_method": "phenotype",
                                })
        
        # Semantic search for each variable type
        for var_type in ["exposure", "outcome", "covariates"]:
            proposed_vars = proposal_variables.get(var_type, [])
            for var_text in proposed_vars:
                matches = self._search_variable(var_text)
                for code, info, score in matches:
                    # Avoid duplicates
                    existing_codes = [m["nhanes_code"] for m in mappings[var_type]]
                    if code not in existing_codes:
                        mappings[var_type].append({
                            "nhanes_code": code,
                            "description": info["desc"],
                            "category": info.get("category", ""),
                            "file": info.get("file", ""),
                            "confidence": round(score, 2),
                            "mapping_method": "semantic_search",
                            "original_text": var_text,
                        })
        
        # Add standard covariates if not already present
        standard_covariates = ["RIDAGEYR", "RIAGENDR", "RIDRETH1", "DMDEDUC2", "INDFMPIR"]
        existing_covs = [m["nhanes_code"] for m in mappings["covariates"]]
        for code in standard_covariates:
            if code not in existing_covs:
                var_info = self.kb.get_variable(code)
                if var_info:
                    mappings["covariates"].append({
                        "nhanes_code": code,
                        "description": var_info["desc"],
                        "category": var_info.get("category", ""),
                        "file": var_info.get("file", ""),
                        "confidence": 1.0,
                        "mapping_method": "standard_covariate",
                    })
        
        # Add survey design variables
        mappings["survey_design"] = {
            "weight": "WTMEC2YR",
            "psu": "SDMVPSU",
            "strata": "SDMVSTRA",
        }
        
        return mappings
    
    def _match_phenotype(self, topic: str) -> Optional[str]:
        """Match research topic to known phenotype."""
        topic_lower = topic.lower()
        
        phenotype_keywords = {
            "obesity": ["obesity", "obese", "bmi", "overweight", "weight", "adiposity", "肥胖"],
            "diabetes": ["diabetes", "diabetic", "glucose", "insulin", "hba1c", "glycemic", "糖尿病"],
            "hypertension": ["hypertension", "blood pressure", "systolic", "diastolic", "bp", "高血压"],
            "dyslipidemia": ["cholesterol", "lipid", "hdl", "ldl", "triglyceride", "血脂"],
            "cardiovascular_disease": ["cardiovascular", "heart disease", "coronary", "stroke", "mi", "心血管"],
            "smoking": ["smoking", "smoker", "cigarette", "tobacco", "nicotine", "吸烟"],
            "depression": ["depression", "depressive", "mental health", "phq", "mood", "抑郁"],
            "chronic_kidney_disease": ["kidney", "renal", "creatinine", "egfr", "albuminuria", "肾脏"],
            "diet_quality": ["diet", "dietary", "nutrition", "nutrient", "food intake", "膳食"],
            "sleep": ["sleep", "insomnia", "sleep duration", "sleep quality", "睡眠"],
        }
        
        best_match = None
        best_score = 0
        
        for phenotype, keywords in phenotype_keywords.items():
            score = sum(1 for kw in keywords if kw in topic_lower)
            if score > best_score:
                best_score = score
                best_match = phenotype
        
        return best_match if best_score > 0 else None
    
    def _search_variable(self, query: str, top_k: int = 5) -> List[Tuple[str, dict, float]]:
        """Search for NHANES variables matching a query."""
        return self.kb.search(query, top_k)
    
    def get_required_data_files(self, mappings: Dict[str, Any]) -> List[str]:
        """Get list of NHANES data file prefixes needed for a study."""
        files = set()
        
        for var_type in ["exposure", "outcome", "covariates"]:
            for mapping in mappings.get(var_type, []):
                file_prefix = mapping.get("file", "")
                if file_prefix:
                    files.add(file_prefix)
        
        # Always need demographics
        files.add("DEMO")
        
        return sorted(files)
    
    def get_all_variable_codes(self, mappings: Dict[str, Any]) -> List[str]:
        """Get all NHANES variable codes needed for a study."""
        codes = []
        
        for var_type in ["exposure", "outcome", "covariates"]:
            for mapping in mappings.get(var_type, []):
                code = mapping.get("nhanes_code", "")
                if code:
                    codes.append(code)
        
        # Add survey design variables
        survey = mappings.get("survey_design", {})
        for key in ["weight", "psu", "strata"]:
            if key in survey:
                codes.append(survey[key])
        
        return sorted(set(codes))
