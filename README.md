# NHANES to Lancet

**AI-Driven Epidemiological Research Platform**

Transform NHANES data into Lancet-quality publication-ready research papers.

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![GitHub Pages](https://img.shields.io/badge/GitHub-Pages-green.svg)](https://mokangmedical.github.io/nhanes-to-lancet/)

## Quick Start

```bash
git clone https://github.com/MoKangMedical/nhanes-to-lancet.git
cd nhanes-to-lancet
pip install -r requirements.txt
python run.py
# Open http://localhost:8501
```

## Features

- **NHANES Data Engine**: Automated CDC data download, multi-cycle merging, survey weight handling
- **Statistical Analysis**: Survey-weighted regression, KM survival, Cox regression, Fine-Gray competing risk
- **Publication Output**: Lancet-format tables, forest plots (300 DPI), structured abstracts
- **AI Paper Writing**: Complete manuscript with Introduction, Methods, Results, Discussion
- **PubMed Integration**: Real-time literature search for related NHANES studies
- **Variable Knowledge Base**: 2000+ NHANES variables with semantic search

## Supported Analyses

| Analysis | Method | Output |
|----------|--------|--------|
| Cross-sectional | Survey-weighted logistic regression | OR (95% CI) |
| Cohort | Cox proportional hazards | HR (95% CI) |
| Survival | Kaplan-Meier | Survival curves |
| Competing Risk | Fine-Gray | Sub-hazard ratio |

## Documentation

- **[Live Demo](https://mokangmedical.github.io/nhanes-to-lancet/demo/)** — Try the platform
- **[Variable Browser](https://mokangmedical.github.io/nhanes-to-lancet/variables/)** — Search 2000+ NHANES variables
- **[User Guide](https://mokangmedical.github.io/nhanes-to-lancet/guide/)** — Complete documentation
- **[API Docs](https://mokangmedical.github.io/nhanes-to-lancet/api/)** — REST API reference

## Architecture

```
app/
├── data/          # NHANES data engine (download, process, variables)
├── analysis/      # Statistical analysis (survey, survival, tables, figures)
├── ai/            # AI tools (parser, mapper, writer, pubmed)
├── pipeline/      # End-to-end orchestration
├── templates/     # Web UI (Jinja2 + Bootstrap 5)
└── server.py      # FastAPI server
docs/              # GitHub Pages static site
```

## Sample Research Topics

- Cardiovascular Disease
- Obesity & Metabolic Syndrome
- Diabetes
- Depression & Mental Health
- Hypertension
- Smoking & Tobacco
- Diet & Nutrition
- Sleep Disorders
- Chronic Kidney Disease
- Physical Activity

## Citation

If you use this platform in your research:
> NHANES to Lancet: AI-Driven Epidemiological Research Platform. 
> https://github.com/MoKangMedical/nhanes-to-lancet

## License

MIT License — see [LICENSE](LICENSE) for details.
