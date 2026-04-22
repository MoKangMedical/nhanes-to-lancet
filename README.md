# NHANES数据到柳叶刀

AI驱动的NHANES数据分析 — 从健康调查数据到顶级期刊

## 项目目标

将美国NHANES（国家健康与营养调查）数据转化为柳叶刀级别发表的临床研究论文。

## 核心能力

- NHANES数据自动下载与清洗
- 加权统计分析（考虑复杂抽样设计）
- 多变量回归+亚组分析
- 论文/图表自动生成

## 快速开始

    git clone https://github.com/MoKangMedical/nhanes-to-lancet.git
    cd nhanes-to-lancet
    pip install -r requirements.txt
    python src/main.py --topic "obesity and diabetes"

MIT License
