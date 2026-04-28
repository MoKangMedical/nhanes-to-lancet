# NHANES to Lancet

**AI-Driven Epidemiological Research Platform**  
Transform NHANES data into Lancet-quality publication-ready research papers.

## Features

- **Automated Data Pipeline**: Download NHANES data directly from CDC
- **Survey-Weighted Analysis**: Proper complex survey design handling
- **Lancet-Standard Output**: Publication-ready tables, figures, and papers
- **AI-Powered**: Automatic variable mapping and paper generation
- **10 Research Topics**: Cardiovascular, obesity, diabetes, depression, and more

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run the server
python run.py

# Open http://localhost:8501
```

## Supported Analyses

| Analysis | Method | Output |
|----------|--------|--------|
| Cross-sectional | Weighted logistic/linear regression | OR/Beta with 95% CI |
| Cohort | Cox proportional hazards | Hazard ratio |
| Survival | Kaplan-Meier | Survival curves |
| Competing Risk | Fine-Gray | Sub-hazard ratio |

## NHANES Data Coverage

- 10 survey cycles (1999-2000 to 2017-2020)
- 2000+ variables across demographics, labs, questionnaires
- Automatic survey weight adjustment for multi-cycle analyses

## Output

- **Table 1**: Baseline characteristics (Lancet format)
- **Table 2**: Multivariable regression results
- **Figure 1**: Forest plot (OR/HR with 95% CI)
- **Figure 2**: Kaplan-Meier survival curves
- **Paper**: Complete Lancet-format manuscript
- **STROBE**: Reporting checklist

## Architecture

```
app/
├── data/          # NHANES data engine (download, process, variables)
├── analysis/      # Statistical analysis (survey, survival, tables, figures)
├── ai/            # AI tools (parser, mapper, writer)
├── pipeline/      # End-to-end orchestration
├── templates/     # Web UI (Jinja2 + Bootstrap 5)
└── server.py      # FastAPI server
```

## License

MIT License

## Citation

If you use this platform in your research, please cite:
> NHANES to Lancet: AI-Driven Epidemiological Research Platform. 
> https://github.com/MoKangMedical/nhanes-to-lancet
