"""
NHANES to Lancet - Test Suite

Run tests: python -m pytest tests/ -v
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))


def test_variables_kb():
    """Test NHANES Variable Knowledge Base."""
    from app.data.variables import NHANESVariableKB
    
    kb = NHANESVariableKB()
    
    # Test variable lookup
    var = kb.get_variable("BMXBMI")
    assert var is not None
    assert var["desc"] == "Body Mass Index (kg/m2)"
    assert var["category"] == "Body Measures"
    print("[PASS] Variable lookup: BMXBMI")
    
    # Test search
    results = kb.search("blood pressure")
    assert len(results) > 0
    print(f"[PASS] Search 'blood pressure': found {len(results)} results")
    
    # Test phenotype
    phenotypes = kb.list_phenotypes()
    assert "obesity" in phenotypes
    assert "diabetes" in phenotypes
    print(f"[PASS] Phenotypes: {len(phenotypes)} available")
    
    # Test phenotype variables
    obesity_vars = kb.get_phenotype_vars("obesity")
    assert obesity_vars is not None
    assert "exposure" in obesity_vars
    print(f"[PASS] Obesity phenotype: {len(obesity_vars['exposure'])} exposure vars")
    
    # Test categories
    categories = kb.list_categories()
    assert len(categories) > 10
    print(f"[PASS] Categories: {len(categories)} total")


def test_processor():
    """Test data processor."""
    import numpy as np
    import pandas as pd
    from app.data.processor import NHANESProcessor
    
    proc = NHANESProcessor()
    
    # Create sample data
    np.random.seed(42)
    n = 1000
    df = pd.DataFrame({
        "RIDAGEYR": np.random.normal(45, 15, n).clip(20, 80),
        "RIAGENDR": np.random.choice([1, 2], n),
        "BMXBMI": np.random.normal(28, 5, n).clip(15, 50),
        "BPXSY1": np.random.normal(125, 15, n).clip(80, 200),
        "DIQ010": np.random.choice([1, 2], n, p=[0.1, 0.9]),
        "SMQ020": np.random.choice([1, 2], n),
    })
    
    # Test BMI categories
    bmi_cats = proc.calculate_bmi_categories(df)
    assert bmi_cats.nunique() > 1
    print("[PASS] BMI categorization")
    
    # Test age groups
    age_groups = proc.calculate_age_groups(df)
    assert age_groups.nunique() > 1
    print("[PASS] Age group creation")
    
    # Test baseline summary
    summary = proc.generate_baseline_summary(
        df,
        continuous_vars=["RIDAGEYR", "BMXBMI", "BPXSY1"],
        categorical_vars=["RIAGENDR", "DIQ010"]
    )
    assert summary["total_n"] == n
    assert "continuous" in summary
    assert "categorical" in summary
    print("[PASS] Baseline summary generation")


def test_survey_analyzer():
    """Test survey-weighted analysis."""
    import numpy as np
    import pandas as pd
    from app.analysis.survey import SurveyAnalyzer
    
    analyzer = SurveyAnalyzer()
    
    # Create sample data with weights
    np.random.seed(42)
    n = 500
    df = pd.DataFrame({
        "age": np.random.normal(45, 15, n),
        "bmi": np.random.normal(28, 5, n),
        "sbp": np.random.normal(125, 15, n),
        "diabetes": np.random.choice([0, 1], n, p=[0.85, 0.15]),
        "gender": np.random.choice([1, 2], n),
        "WTMEC2YR_ADJ": np.random.exponential(5000, n),
        "SDMVPSU": np.random.choice([1, 2], n),
        "SDMVSTRA": np.random.choice(range(1, 15), n),
    })
    
    # Test weighted mean
    result = analyzer.weighted_mean(df, "bmi")
    assert "mean" in result
    assert "se" in result
    print(f"[PASS] Weighted mean: BMI = {result['mean']:.2f} (SE={result['se']:.2f})")
    
    # Test weighted frequency
    freq = analyzer.weighted_frequency(df, "diabetes")
    assert len(freq) > 0
    print(f"[PASS] Weighted frequency: diabetes categories = {len(freq)}")
    
    # Test weighted t-test
    ttest = analyzer.weighted_ttest(df, "bmi", "gender")
    assert "t_stat" in ttest
    print(f"[PASS] Weighted t-test: t={ttest['t_stat']:.2f}, p={ttest['p_value']:.4f}")
    
    # Test weighted logistic regression
    lr = analyzer.weighted_logistic_regression(
        df, "diabetes", ["age", "bmi", "sbp"]
    )
    assert "coefficients" in lr
    print(f"[PASS] Logistic regression: {len(lr['coefficients'])} coefficients")


def test_paper_writer():
    """Test paper generation."""
    from app.ai.writer import PaperWriter
    
    writer = PaperWriter()
    
    study_info = {
        "exposure": "body mass index",
        "outcome": "type 2 diabetes",
        "population": "US adults",
        "cycles": "2017-2018",
        "study_design": "cross-sectional",
    }
    
    analysis_results = {
        "n_total": 5000,
        "n_events": 500,
        "effect_size": "OR 1.05",
        "confidence_interval": "95% CI 1.03-1.07",
        "p_value": "P<0.001",
    }
    
    # Test abstract generation
    abstract = writer.generate_abstract(study_info, analysis_results)
    assert "Background" in abstract
    assert "Methods" in abstract
    assert "Findings" in abstract
    assert "Interpretation" in abstract
    print("[PASS] Abstract generation")
    
    # Test full paper generation
    paper = writer.generate_full_paper(study_info, analysis_results)
    assert "# Association between" in paper
    assert "## Introduction" in paper
    assert "## Methods" in paper
    assert "## Results" in paper
    assert "## Discussion" in paper
    assert "## References" in paper
    print(f"[PASS] Full paper generation: {len(paper)} characters")


def test_variable_mapper():
    """Test variable mapping."""
    from app.ai.mapper import VariableMapper
    
    mapper = VariableMapper()
    
    # Test mapping with topic
    proposal_vars = {
        "exposure": ["body mass index"],
        "outcome": ["diabetes"],
        "covariates": ["age", "sex"],
    }
    
    mappings = mapper.map_variables(proposal_vars, "obesity and diabetes")
    
    assert "exposure" in mappings
    assert "outcome" in mappings
    assert "covariates" in mappings
    assert "survey_design" in mappings
    
    print(f"[PASS] Variable mapping:")
    print(f"  Exposure: {len(mappings['exposure'])} mapped")
    print(f"  Outcome: {len(mappings['outcome'])} mapped")
    print(f"  Covariates: {len(mappings['covariates'])} mapped")
    
    if mappings.get("phenotype_match"):
        print(f"  Phenotype match: {mappings['phenotype_match']}")


def test_pipeline_demo_data():
    """Test pipeline demo data generation."""
    from app.pipeline.orchestrator import PipelineOrchestrator
    
    orch = PipelineOrchestrator("test")
    df = orch._generate_demo_data([], 1000)
    
    assert len(df) == 1000
    assert "RIDAGEYR" in df.columns
    assert "BMXBMI" in df.columns
    assert "BPXSY1" in df.columns
    assert "WTMEC2YR" in df.columns
    assert "CVD" in df.columns
    print(f"[PASS] Demo data: {len(df)} rows, {len(df.columns)} columns")


if __name__ == "__main__":
    print("=" * 60)
    print("NHANES to Lancet - Test Suite")
    print("=" * 60)
    print()
    
    tests = [
        ("Variable Knowledge Base", test_variables_kb),
        ("Data Processor", test_processor),
        ("Survey Analyzer", test_survey_analyzer),
        ("Paper Writer", test_paper_writer),
        ("Variable Mapper", test_variable_mapper),
        ("Pipeline Demo Data", test_pipeline_demo_data),
    ]
    
    passed = 0
    failed = 0
    
    for name, test_func in tests:
        print(f"\n--- {name} ---")
        try:
            test_func()
            passed += 1
        except Exception as e:
            print(f"[FAIL] {name}: {e}")
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 60)
