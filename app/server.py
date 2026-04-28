"""
NHANES to Lancet - FastAPI Web Server

Provides:
- Web UI for the research platform
- REST API for pipeline execution
- File upload/download endpoints
- Real-time progress tracking via SSE
"""
import os
import json
import logging
import tempfile
import shutil
from pathlib import Path
from typing import Optional
from datetime import datetime

from fastapi import FastAPI, Request, UploadFile, File, Form, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from .config import (
    SERVER_HOST, SERVER_PORT, DEBUG, AI_CONFIG,
    RESULTS_DIR, TEMP_DIR, NHANES_CYCLES, NHANES_DATA_CATEGORIES,
)
from .data.variables import NHANESVariableKB
from .pipeline.orchestrator import PipelineOrchestrator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="NHANES to Lancet",
    description="AI-Driven Epidemiological Research Platform",
    version="2.0.0",
)

# Mount static files
static_dir = Path(__file__).parent / "static"
static_dir.mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# Templates
templates_dir = Path(__file__).parent / "templates"
templates_dir.mkdir(parents=True, exist_ok=True)
templates = Jinja2Templates(directory=str(templates_dir))

# Initialize knowledge base
kb = NHANESVariableKB()

# In-memory project storage (replace with database in production)
projects = {}


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Home page."""
    return templates.TemplateResponse("index.html", {
        "request": request,
        "title": "NHANES to Lancet",
        "version": "2.0.0",
    })


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Dashboard page showing all projects."""
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "projects": projects,
    })


@app.get("/new-project", response_class=HTMLResponse)
async def new_project_page(request: Request):
    """New project creation page."""
    return templates.TemplateResponse("new_project.html", {
        "request": request,
        "cycles": NHANES_CYCLES,
        "phenotypes": kb.list_phenotypes(),
        "categories": kb.list_categories(),
    })


@app.get("/project/{project_id}", response_class=HTMLResponse)
async def project_detail(request: Request, project_id: str):
    """Project detail page."""
    project = projects.get(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    return templates.TemplateResponse("project_detail.html", {
        "request": request,
        "project": project,
        "project_id": project_id,
    })


@app.get("/variables", response_class=HTMLResponse)
async def variables_browser(request: Request):
    """NHANES variable browser page."""
    return templates.TemplateResponse("variables.html", {
        "request": request,
        "categories": kb.list_categories(),
    })


# === API Endpoints ===

@app.post("/api/projects")
async def create_project(
    title: str = Form(...),
    description: str = Form(""),
    topic: str = Form(""),
    cycles: str = Form("2017-2018"),
    analysis_type: str = Form("cross_sectional"),
    outcome: str = Form(""),
    exposure: str = Form(""),
    proposal_file: Optional[UploadFile] = File(None),
):
    """Create a new analysis project."""
    project_id = f"proj_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    # Save uploaded file if provided
    file_path = None
    if proposal_file:
        file_path = TEMP_DIR / f"{project_id}_{proposal_file.filename}"
        with open(file_path, "wb") as f:
            content = await proposal_file.read()
            f.write(content)
    
    project = {
        "id": project_id,
        "title": title,
        "description": description,
        "topic": topic,
        "cycles": cycles.split(","),
        "analysis_type": analysis_type,
        "outcome": outcome,
        "exposure": exposure,
        "file_path": str(file_path) if file_path else None,
        "status": "created",
        "progress": 0,
        "created_at": datetime.now().isoformat(),
        "results": None,
    }
    
    projects[project_id] = project
    
    return {"project_id": project_id, "status": "created"}


@app.post("/api/projects/{project_id}/run")
async def run_analysis(project_id: str):
    """Run the analysis pipeline for a project."""
    project = projects.get(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    project["status"] = "running"
    project["progress"] = 0
    
    # Run pipeline in background (simplified - use Celery/Redis in production)
    try:
        orchestrator = PipelineOrchestrator(
            project_id=project_id,
            api_key=AI_CONFIG.get("api_key", ""),
        )
        
        results = orchestrator.run_full_pipeline(
            research_file=project.get("file_path", ""),
            research_topic=project.get("topic", ""),
            cycles=project.get("cycles", ["2017-2018"]),
            analysis_type=project.get("analysis_type", "cross_sectional"),
            outcome_var=project.get("outcome", ""),
            exposure_var=project.get("exposure", ""),
        )
        
        project["results"] = results
        project["status"] = results.get("status", "completed")
        project["progress"] = 100
        
    except Exception as e:
        logger.error(f"Analysis error: {e}", exc_info=True)
        project["status"] = "failed"
        project["error"] = str(e)
    
    return {"project_id": project_id, "status": project["status"]}


@app.get("/api/projects/{project_id}/status")
async def get_project_status(project_id: str):
    """Get project analysis status."""
    project = projects.get(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    return {
        "project_id": project_id,
        "status": project["status"],
        "progress": project["progress"],
    }


@app.get("/api/projects/{project_id}/results")
async def get_project_results(project_id: str):
    """Get project results."""
    project = projects.get(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    return project.get("results", {})


@app.get("/api/projects/{project_id}/paper")
async def get_project_paper(project_id: str):
    """Get generated paper."""
    project = projects.get(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    results = project.get("results", {})
    paper = results.get("paper", "Paper not yet generated")
    
    return {"paper": paper}


@app.get("/api/projects/{project_id}/download")
async def download_results(project_id: str):
    """Download all results as ZIP."""
    project = projects.get(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    results = project.get("results", {})
    zip_path = results.get("zip_path")
    
    if zip_path and Path(zip_path).exists():
        return FileResponse(
            zip_path,
            media_type="application/zip",
            filename=f"nhanes_analysis_{project_id}.zip"
        )
    
    raise HTTPException(status_code=404, detail="Results not available")


@app.get("/api/variables/search")
async def search_variables(q: str, limit: int = 10):
    """Search NHANES variables."""
    results = kb.search(q, limit)
    return [
        {
            "code": code,
            "description": info["desc"],
            "category": info.get("category", ""),
            "type": info.get("type", ""),
            "score": round(score, 2),
        }
        for code, info, score in results
    ]


@app.get("/api/variables/phenotype/{phenotype}")
async def get_phenotype_variables(phenotype: str):
    """Get recommended variables for a phenotype."""
    vars_info = kb.get_phenotype_vars(phenotype)
    if not vars_info:
        raise HTTPException(status_code=404, detail="Phenotype not found")
    
    result = {}
    for var_type, var_codes in vars_info.items():
        result[var_type] = []
        for code in var_codes:
            var = kb.get_variable(code)
            if var:
                result[var_type].append({
                    "code": code,
                    "description": var["desc"],
                    "category": var.get("category", ""),
                    "type": var.get("type", ""),
                })
    
    return result


@app.get("/api/variables/{code}")
async def get_variable_info(code: str):
    """Get detailed information about a NHANES variable."""
    var = kb.get_variable(code.upper())
    if not var:
        raise HTTPException(status_code=404, detail="Variable not found")
    
    return {"code": code.upper(), **var}


@app.get("/api/cycles")
async def list_cycles():
    """List available NHANES cycles."""
    return {"cycles": NHANES_CYCLES}


@app.get("/api/phenotypes")
async def list_phenotypes():
    """List available phenotype categories."""
    return {"phenotypes": kb.list_phenotypes()}


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "NHANES to Lancet",
        "version": "2.0.0",
        "timestamp": datetime.now().isoformat(),
    }


def run_server():
    """Run the server."""
    import uvicorn
    uvicorn.run(
        "app.server:app",
        host=SERVER_HOST,
        port=SERVER_PORT,
        reload=DEBUG,
    )


if __name__ == "__main__":
    run_server()
