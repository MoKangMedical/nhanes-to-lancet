"""
NHANES-to-Lancet 主服务器
完整的FastAPI后端 + Jinja2模板前端

API端点:
  GET  /                         首页
  GET  /dashboard                仪表盘
  GET  /projects/new             新建项目
  GET  /projects/{id}            项目详情
  POST /api/projects             创建项目
  GET  /api/projects             项目列表
  GET  /api/projects/{id}        项目详情
  DELETE /api/projects/{id}      删除项目
  POST /api/analyze              启动分析
  GET  /api/analyze/{id}/status  分析状态
  GET  /api/variables/search     搜索NHANES变量
  GET  /api/variables/{name}     变量详情
  GET  /api/download/{id}        下载结果ZIP
  GET  /api/paper/{id}           获取论文内容
"""

import os
import sys
import json
import uuid
import math
import shutil
import logging
import asyncio
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime

from fastapi import FastAPI, HTTPException, Request, BackgroundTasks, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field

# 内部导入
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.nhanes import NHANESDownloader, NHANES_VARIABLES, NHANESDataProcessor
from src.analysis import RScriptGenerator, AnalysisConfig
from src.analysis.orchestrator import AnalysisOrchestrator, ResearchProject
from src.paper import LancetPaperGenerator

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# ============================================================
# SafeJSONResponse - handles inf/nan in JSON output
# ============================================================

def _sanitize_for_json(obj):
    """Recursively replace inf/nan with None in nested dicts/lists."""
    if isinstance(obj, float):
        if math.isinf(obj) or math.isnan(obj):
            return None
        return obj
    elif isinstance(obj, dict):
        return {k: _sanitize_for_json(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_sanitize_for_json(v) for v in obj]
    return obj


class SafeJSONResponse(JSONResponse):
    """JSONResponse that converts inf/nan to null for JSON compliance."""
    def render(self, content) -> bytes:
        sanitized = _sanitize_for_json(content)
        return json.dumps(
            sanitized,
            ensure_ascii=False,
            allow_nan=False,
            default=str,
        ).encode("utf-8")


# ============================================================
# FastAPI应用
# ============================================================

app = FastAPI(
    title="NHANES to Lancet",
    description="AI驱动的NHANES数据分析平台 — 从健康调查数据到顶级期刊",
    version="2.0.0",
    default_response_class=SafeJSONResponse,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 静态文件和模板
BASE_DIR = Path(__file__).parent
STATIC_DIR = BASE_DIR / "src" / "static"
TEMPLATE_DIR = BASE_DIR / "src" / "templates"
OUTPUT_DIR = BASE_DIR / "output"
DATA_DIR = BASE_DIR / "src" / "data"

for d in [STATIC_DIR, TEMPLATE_DIR, OUTPUT_DIR, DATA_DIR]:
    d.mkdir(parents=True, exist_ok=True)

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
templates = Jinja2Templates(directory=str(TEMPLATE_DIR))

# ============================================================
# 内存数据库 (项目状态)
# ============================================================

projects_db: Dict[str, Dict[str, Any]] = {}
analysis_tasks: Dict[str, Dict[str, Any]] = {}

# ============================================================
# 数据模型
# ============================================================

class ProjectCreateRequest(BaseModel):
    title: str
    study_design: str = "cross_sectional"
    exposure_var: str
    outcome_var: str
    covariates: List[str] = []
    cycles: List[str] = ["2017-2018"]
    subgroup_var: Optional[str] = None
    analysis_type: str = "logistic"
    age_min: int = 20
    age_max: int = 80

class VariableSearchRequest(BaseModel):
    keyword: str

class AnalysisStatusResponse(BaseModel):
    task_id: str
    status: str
    progress: int
    current_step: str
    message: str

# ============================================================
# HTML页面路由
# ============================================================

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """首页"""
    return templates.TemplateResponse("home.html", {
        "request": request,
        "total_projects": len(projects_db),
        "total_analyses": len(analysis_tasks),
    })

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    """仪表盘"""
    projects_list = list(projects_db.values())
    projects_list.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "projects": projects_list,
    })

@app.get("/projects/new", response_class=HTMLResponse)
async def new_project_page(request: Request):
    """新建项目页面"""
    # 提供常用变量列表供选择
    common_vars = []
    for name, info in NHANES_VARIABLES.items():
        common_vars.append({
            "name": name,
            "desc": info["desc"],
            "table": info["table"],
            "type": info["type"],
        })
    common_vars.sort(key=lambda x: x["name"])

    return templates.TemplateResponse("new_project.html", {
        "request": request,
        "common_vars": common_vars,
        "cycles": ["1999-2000", "2001-2002", "2003-2004", "2005-2006",
                   "2007-2008", "2009-2010", "2011-2012", "2013-2014",
                   "2015-2016", "2017-2018"],
    })

@app.get("/projects/{project_id}", response_class=HTMLResponse)
async def project_detail_page(request: Request, project_id: str):
    """项目详情页面"""
    project = projects_db.get(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="项目未找到")

    task = analysis_tasks.get(project_id, {})
    return templates.TemplateResponse("project_detail.html", {
        "request": request,
        "project": project,
        "task": task,
    })

# ============================================================
# API路由
# ============================================================

@app.get("/api/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy", "version": "2.0.0", "projects": len(projects_db)}

@app.post("/api/projects")
async def create_project(req: ProjectCreateRequest):
    """创建新项目"""
    project_id = str(uuid.uuid4())[:8]

    project = {
        "id": project_id,
        "title": req.title,
        "study_design": req.study_design,
        "exposure_var": req.exposure_var,
        "outcome_var": req.outcome_var,
        "covariates": req.covariates,
        "cycles": req.cycles,
        "subgroup_var": req.subgroup_var,
        "analysis_type": req.analysis_type,
        "age_min": req.age_min,
        "age_max": req.age_max,
        "status": "created",
        "created_at": datetime.now().isoformat(),
        "output_dir": str(OUTPUT_DIR / project_id),
    }

    projects_db[project_id] = project
    logger.info(f"项目已创建: {project_id} - {req.title}")

    return {"id": project_id, "status": "created", "project": project}

@app.get("/api/projects")
async def list_projects():
    """列出所有项目"""
    projects_list = list(projects_db.values())
    projects_list.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    return {"projects": projects_list, "total": len(projects_list)}

@app.get("/api/projects/{project_id}")
async def get_project(project_id: str):
    """获取项目详情"""
    project = projects_db.get(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="项目未找到")

    task = analysis_tasks.get(project_id, {})
    return {"project": project, "analysis": task}

@app.delete("/api/projects/{project_id}")
async def delete_project(project_id: str):
    """删除项目"""
    if project_id not in projects_db:
        raise HTTPException(status_code=404, detail="项目未找到")

    # 删除输出目录
    output_path = Path(projects_db[project_id].get("output_dir", ""))
    if output_path.exists():
        shutil.rmtree(output_path, ignore_errors=True)

    del projects_db[project_id]
    if project_id in analysis_tasks:
        del analysis_tasks[project_id]

    return {"status": "deleted"}

# ============================================================
# 分析API
# ============================================================

@app.post("/api/analyze/{project_id}")
async def start_analysis(project_id: str, background_tasks: BackgroundTasks):
    """启动分析 (后台执行)"""
    project_data = projects_db.get(project_id)
    if not project_data:
        raise HTTPException(status_code=404, detail="项目未找到")

    if project_data["status"] == "analyzing":
        raise HTTPException(status_code=400, detail="分析已在进行中")

    # 更新状态
    project_data["status"] = "analyzing"
    analysis_tasks[project_id] = {
        "status": "analyzing",
        "progress": 0,
        "current_step": "初始化",
        "started_at": datetime.now().isoformat(),
        "message": "正在准备分析..."
    }

    # 后台执行分析
    background_tasks.add_task(_run_analysis_background, project_id, project_data)

    return {"status": "started", "project_id": project_id}

async def _run_analysis_background(project_id: str, project_data: Dict[str, Any]):
    """后台执行分析"""
    try:
        project = ResearchProject(
            project_id=project_id,
            title=project_data["title"],
            study_design=project_data["study_design"],
            exposure_var=project_data["exposure_var"],
            outcome_var=project_data["outcome_var"],
            covariates=project_data.get("covariates", []),
            cycles=project_data.get("cycles", ["2017-2018"]),
            subgroup_var=project_data.get("subgroup_var"),
            analysis_type=project_data.get("analysis_type", "logistic"),
            age_min=project_data.get("age_min", 20),
            age_max=project_data.get("age_max", 80),
            output_dir=project_data.get("output_dir", str(OUTPUT_DIR)),
        )

        orchestrator = AnalysisOrchestrator(project)

        # 逐步执行并更新状态
        analysis_tasks[project_id]["current_step"] = "解析变量"
        analysis_tasks[project_id]["progress"] = 10
        var_info = orchestrator.step1_resolve_variables()

        analysis_tasks[project_id]["current_step"] = "下载数据"
        analysis_tasks[project_id]["progress"] = 25
        raw_df = orchestrator.step2_download_data()

        analysis_tasks[project_id]["current_step"] = "清洗数据"
        analysis_tasks[project_id]["progress"] = 35
        clean_df = orchestrator.step3_clean_data(raw_df)

        analysis_tasks[project_id]["current_step"] = "生成R脚本"
        analysis_tasks[project_id]["progress"] = 45
        scripts = orchestrator.step4_generate_r_scripts()

        analysis_tasks[project_id]["current_step"] = "执行统计分析"
        analysis_tasks[project_id]["progress"] = 55
        r_results = orchestrator.step5_execute_r_scripts(scripts)

        analysis_tasks[project_id]["current_step"] = "提取结果"
        analysis_tasks[project_id]["progress"] = 70
        analysis_results = orchestrator.step6_extract_results()

        analysis_tasks[project_id]["current_step"] = "生成论文"
        analysis_tasks[project_id]["progress"] = 85
        paper_sections = orchestrator.step7_generate_paper(analysis_results)

        analysis_tasks[project_id]["current_step"] = "打包结果"
        analysis_tasks[project_id]["progress"] = 95
        zip_path = orchestrator.step8_package_output()

        # 完成
        analysis_tasks[project_id].update({
            "status": "completed",
            "progress": 100,
            "current_step": "完成",
            "completed_at": datetime.now().isoformat(),
            "message": "分析完成!",
            "zip_path": zip_path,
            "sample_size": len(clean_df),
            "tables_count": len(analysis_results.get("tables", [])),
            "figures_count": len(analysis_results.get("figures", [])),
        })

        project_data["status"] = "completed"
        logger.info(f"分析完成: {project_id}")

    except Exception as e:
        logger.error(f"分析失败: {project_id} - {e}")
        analysis_tasks[project_id].update({
            "status": "failed",
            "message": str(e),
            "current_step": "失败"
        })
        project_data["status"] = "failed"

@app.get("/api/analyze/{project_id}/status")
async def get_analysis_status(project_id: str):
    """获取分析状态"""
    task = analysis_tasks.get(project_id)
    if not task:
        raise HTTPException(status_code=404, detail="未找到分析任务")
    return task

# ============================================================
# 变量API
# ============================================================

@app.get("/api/variables/search")
async def search_variables(q: str = ""):
    """搜索NHANES变量"""
    if not q:
        # 返回常用变量
        common = []
        for name, info in list(NHANES_VARIABLES.items())[:50]:
            common.append({"name": name, **info})
        return {"variables": common, "total": len(common)}

    results = []
    q_lower = q.lower()
    for name, info in NHANES_VARIABLES.items():
        if q_lower in name.lower() or q_lower in info["desc"].lower():
            results.append({"name": name, **info})

    return {"variables": results[:100], "total": len(results)}

@app.get("/api/variables/{var_name}")
async def get_variable_info(var_name: str):
    """获取变量详情"""
    info = NHANES_VARIABLES.get(var_name.upper())
    if not info:
        raise HTTPException(status_code=404, detail="变量未找到")
    return {"name": var_name.upper(), **info}

# ============================================================
# 下载API
# ============================================================

@app.get("/api/download/{project_id}")
async def download_results(project_id: str):
    """下载分析结果ZIP"""
    project = projects_db.get(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="项目未找到")

    task = analysis_tasks.get(project_id, {})
    zip_path = task.get("zip_path")

    if not zip_path or not Path(zip_path).exists():
        # 尝试重新打包
        output_dir = Path(project.get("output_dir", ""))
        if not output_dir.exists():
            raise HTTPException(status_code=404, detail="分析结果不存在")

        zip_path = str(output_dir.parent / f"{project_id}_results.zip")
        shutil.make_archive(zip_path.replace(".zip", ""), 'zip', output_dir)

    return FileResponse(
        zip_path,
        media_type="application/zip",
        filename=f"nhanes_analysis_{project_id}.zip"
    )

@app.get("/api/paper/{project_id}")
async def get_paper(project_id: str, section: str = "full_text"):
    """获取论文内容"""
    project = projects_db.get(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="项目未找到")

    paper_path = Path(project.get("output_dir", "")) / "paper" / f"{section}.md"
    if not paper_path.exists():
        raise HTTPException(status_code=404, detail="论文未生成")

    content = paper_path.read_text(encoding="utf-8")
    return {"section": section, "content": content, "project_id": project_id}

# ============================================================
# 启动
# ============================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
