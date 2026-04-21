# NHANES到柳叶刀

NHANES数据分析平台

## 项目简介

NHANES数据分析和柳叶刀期刊投稿平台

## 功能特性

- 📊 数据采集与处理
- 🔬 统计分析与可视化
- 📝 论文写作与润色
- 🌍 多语言支持
- 🔒 数据安全与隐私保护

## 技术栈

- **后端**: Python, FastAPI
- **前端**: React, TypeScript
- **数据分析**: Pandas, NumPy, SciPy
- **可视化**: Matplotlib, Plotly, Seaborn
- **AI模型**: OpenAI, LangChain
- **部署**: Docker, Kubernetes

## 快速开始

### 环境要求

- Python 3.10+
- Node.js 18+
- Docker & Docker Compose

### 安装步骤

1. 克隆仓库
```bash
git clone https://github.com/MoKangMedical/nhanes-to-lancet.git
cd nhanes-to-lancet
```

2. 安装依赖
```bash
pip install -r requirements.txt
```

3. 配置环境变量
```bash
cp .env.example .env
# 编辑.env文件
```

4. 启动服务
```bash
docker-compose up -d
```

## 项目结构

```
nhanes-to-lancet/
├── data/              # 数据存储
├── analysis/          # 分析脚本
├── visualization/     # 可视化工具
├── writing/           # 论文写作工具
├── docs/              # 项目文档
├── tests/             # 测试用例
├── docker-compose.yml # Docker编排文件
└── README.md          # 项目说明
```

## 使用示例

### 数据下载与处理
```python
from analysis.data_loader import DataLoader

loader = DataLoader()
data = loader.load_nhanes_data()
processed_data = loader.preprocess(data)
```

### 统计分析
```python
from analysis.statistical_analysis import StatisticalAnalyzer

analyzer = StatisticalAnalyzer()
results = analyzer.run_analysis(processed_data)
analyzer.generate_report(results)
```

### 论文写作辅助
```python
from writing.paper_assistant import PaperAssistant

assistant = PaperAssistant()
draft = assistant.generate_draft(results)
revised_draft = assistant.revise_draft(draft)
```

## API文档

启动服务后，访问以下地址查看API文档：

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 贡献指南

我们欢迎任何形式的贡献！请遵循以下步骤：

1. Fork本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建Pull Request

## 许可证

本项目采用 [MIT License](LICENSE) 许可证。

## 联系方式

- 项目维护者: MoKangMedical
- 邮箱: contact@mokangmedical.com
- 项目主页: https://github.com/MoKangMedical/nhanes-to-lancet

## 致谢

感谢所有为这个项目做出贡献的开发者和医疗领域专家！
