"""
Research Proposal Parser - Extract PICO/PECO elements from Word documents.

Uses:
- python-docx for Word document parsing
- LLM (DeepSeek/ChatGPT) for intelligent information extraction
"""
import logging
import re
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)


class ResearchProposalParser:
    """Parse research proposals from Word documents and extract PICO/PECO elements."""
    
    PICO_PROMPT = """Analyze the following research proposal text and extract structured information.

Return a JSON object with these fields:
{{
  "study_design": "cross-sectional|cohort|case-control|clinical trial",
  "research_question": "Main research question in one sentence",
  "pico": {{
    "population": "Target population description",
    "intervention_or_exposure": "Intervention or exposure variable",
    "comparison": "Comparison group",
    "outcome": "Primary outcome measure"
  }},
  "variables": {{
    "exposure": ["list of exposure variable names"],
    "outcome": ["list of outcome variable names"],
    "covariates": ["list of covariate names"]
  }},
  "statistical_methods": ["list of planned statistical methods"],
  "keywords": ["list of keywords"]
}}

Research Proposal Text:
{text}
"""
    
    def __init__(self, api_key: str = "", api_base: str = ""):
        self.api_key = api_key
        self.api_base = api_base
    
    def parse_docx(self, file_path: str) -> str:
        """Extract text from Word document."""
        try:
            from docx import Document
            doc = Document(file_path)
            paragraphs = []
            for para in doc.paragraphs:
                if para.text.strip():
                    paragraphs.append(para.text.strip())
            return "\n".join(paragraphs)
        except ImportError:
            logger.warning("python-docx not installed, trying docx2txt")
            try:
                import docx2txt
                return docx2txt.process(file_path)
            except ImportError:
                return ""
    
    def parse_text(self, text: str) -> Dict[str, Any]:
        """Parse text directly and extract PICO elements using pattern matching."""
        result = {
            "study_design": self._extract_study_design(text),
            "research_question": self._extract_research_question(text),
            "pico": {
                "population": self._extract_section(text, ["population", "participants", "study population"]),
                "intervention_or_exposure": self._extract_section(text, ["intervention", "exposure", "treatment"]),
                "comparison": self._extract_section(text, ["comparison", "control", "comparator"]),
                "outcome": self._extract_section(text, ["outcome", "endpoints", "primary outcome"]),
            },
            "variables": {
                "exposure": self._extract_variable_names(text, "exposure"),
                "outcome": self._extract_variable_names(text, "outcome"),
                "covariates": self._extract_variable_names(text, "covariate"),
            },
            "statistical_methods": self._extract_statistical_methods(text),
            "keywords": self._extract_keywords(text),
        }
        return result
    
    def _extract_study_design(self, text: str) -> str:
        """Extract study design from text."""
        text_lower = text.lower()
        designs = {
            "cross-sectional": ["cross-sectional", "cross sectional", "横断面"],
            "cohort": ["cohort", "longitudinal", "prospective", "retrospective", "队列"],
            "case-control": ["case-control", "case control", "病例对照"],
            "clinical trial": ["randomized", "clinical trial", "rct", "randomized controlled", "临床试验"],
            "meta-analysis": ["meta-analysis", "systematic review", "荟萃分析"],
        }
        
        for design, keywords in designs.items():
            for kw in keywords:
                if kw in text_lower:
                    return design
        return "cross-sectional"
    
    def _extract_research_question(self, text: str) -> str:
        """Extract the main research question."""
        patterns = [
            r"(?:research question|study question|aim|objective)[:\s]+(.+?)(?:\.|$)",
            r"(?:we (?:aimed|aim|sought) to)\s+(.+?)(?:\.|$)",
            r"(?:the (?:aim|goal|purpose) (?:of this study|was))[:\s]+(.+?)(?:\.|$)",
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        return ""
    
    def _extract_section(self, text: str, keywords: List[str]) -> str:
        """Extract text section related to specific keywords."""
        for kw in keywords:
            # Look for section headers
            patterns = [
                rf"(?:^|\n)\s*(?:{kw})[:\s]+(.+?)(?:\n\n|\n(?=[A-Z]))",
                rf"{kw}[:\s]+(.+?)(?:\.|$)",
            ]
            for pattern in patterns:
                match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
                if match:
                    return match.group(1).strip()[:500]
        return ""
    
    def _extract_variable_names(self, text: str, var_type: str) -> List[str]:
        """Extract variable names from text."""
        # Common NHANES-related variable patterns
        nhanes_patterns = {
            "exposure": [
                r"(?:exposure|intervention|independent variable|predictor)[:\s]+(.+?)(?:\.|$)",
                r"(?:we (?:examined|assessed|measured))[:\s]+(.+?)(?:\.|$)",
            ],
            "outcome": [
                r"(?:outcome|dependent variable|endpoint|primary endpoint)[:\s]+(.+?)(?:\.|$)",
                r"(?:we (?:evaluated|assessed))[:\s]+(.+?)(?:as (?:the )?(?:outcome|endpoint))",
            ],
            "covariate": [
                r"(?:covariate|confounder|adjusted for|adjustment)[:\s]+(.+?)(?:\.|$)",
                r"(?:we adjusted for)[:\s]+(.+?)(?:\.|$)",
            ],
        }
        
        variables = []
        patterns = nhanes_patterns.get(var_type, [])
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                # Split by commas and clean
                var_text = match.group(1)
                vars_list = [v.strip() for v in re.split(r'[,;]', var_text)]
                variables.extend(vars_list[:10])
        
        return variables[:10]
    
    def _extract_statistical_methods(self, text: str) -> List[str]:
        """Extract statistical methods mentioned in text."""
        methods = []
        method_keywords = [
            "logistic regression", "linear regression", "cox regression",
            "kaplan-meier", "survival analysis", "chi-square", "t-test",
            "anova", "log-rank", "fine-gray", "competing risk",
            "propensity score", "multiple imputation", "sensitivity analysis",
            "subgroup analysis", "survey-weighted", "svydesign",
        ]
        
        text_lower = text.lower()
        for method in method_keywords:
            if method in text_lower:
                methods.append(method.title())
        
        return methods
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract keywords from text."""
        # Look for explicit keywords section
        match = re.search(r"(?:keyword|key word)[:\s]+(.+?)(?:\n\n|\n(?=[A-Z]))", text, re.IGNORECASE)
        if match:
            keywords = [k.strip() for k in re.split(r'[,;]', match.group(1))]
            return keywords[:10]
        
        return []
