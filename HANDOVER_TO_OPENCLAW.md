# NHANES to Lancet 项目交接文档（OpenClaw）

## 项目概述

**NHANES to Lancet** 是一个自动化的流行病学研究平台，专注于NHANES数据分析和Lancet标准学术论文生成。平台支持从Word研究方案上传到完整论文生成的全流程自动化。

### 核心价值主张
- 研究方案智能解析（PICO/PECO要素提取）
- NHANES变量自动映射
- R语言统计分析（生存分析、Cox回归、竞争风险模型）
- Lancet标准表格和图形生成
- PubMed文献集成
- 完整学术论文自动撰写

### 技术栈
- **前端**: React 19 + TypeScript + Tailwind CSS 4 + Wouter + tRPC Client
- **后端**: Node.js + Express + tRPC 11 + TypeScript
- **数据库**: MySQL (TiDB) + Drizzle ORM
- **统计分析**: R语言（Kaplan-Meier、Cox回归、Fine-Gray模型）
- **AI集成**: DeepSeek API（研究方案解析、论文生成）
- **文献搜索**: PubMed E-utilities API
- **文件存储**: S3 (Manus内置)
- **认证**: Manus OAuth

---

## 项目结构

```
nhanes-analysis-platform/
├── client/                      # 前端代码
│   ├── public/                  # 静态资源
│   │   └── research-images/     # Lancet研究论文图片
│   └── src/
│       ├── pages/               # 页面组件
│       │   ├── Home.tsx         # 首页（NHANES介绍+文献展示）
│       │   ├── Dashboard.tsx    # 用户仪表盘
│       │   ├── NewProject.tsx   # 创建新项目（上传Word）
│       │   └── ProjectDetail.tsx # 项目详情（解析结果+分析+论文）
│       ├── components/          # 可复用组件
│       ├── lib/trpc.ts          # tRPC客户端配置
│       └── App.tsx              # 路由配置
│
├── server/                      # 后端代码
│   ├── _core/                   # 框架核心（OAuth、tRPC、LLM等）
│   ├── db.ts                    # 数据库查询辅助函数
│   ├── routers.ts               # tRPC路由定义
│   ├── wordParser.ts            # Word文档解析+PICO提取
│   ├── rExecutor.ts             # R脚本生成和执行
│   ├── pubmedSearch.ts          # PubMed文献搜索
│   ├── paperGenerator.ts        # 学术论文生成
│   └── storage.ts               # S3文件存储
│
├── drizzle/                     # 数据库
│   └── schema.ts                # 数据表定义
│
├── todo.md                      # 待办清单（功能开发追踪）
├── USER_GUIDE.md                # 用户使用指南
└── HANDOVER_TO_OPENCLAW.md      # 本文档
```

---

## 数据库架构

### 核心数据表

#### 1. `users` - 用户表
```typescript
{
  id: int (PK),
  openId: string (unique),  // Manus OAuth ID
  name: string,
  email: string,
  role: 'user' | 'admin',
  createdAt: timestamp,
  lastSignedIn: timestamp
}
```

#### 2. `projects` - 研究项目表
```typescript
{
  id: int (PK),
  userId: int (FK -> users.id),
  title: string,               // 研究标题
  status: 'draft' | 'analyzing' | 'completed' | 'failed',
  
  // PICO/PECO解析结果（JSON）
  picoData: {
    population: string,
    intervention: string,
    comparison: string,
    outcome: string,
    exposure: string
  },
  
  studyDesign: string,         // 研究设计类型
  researchQuestion: string,    // 研究问题
  
  createdAt: timestamp,
  updatedAt: timestamp
}
```

#### 3. `variableMappings` - 变量映射表
```typescript
{
  id: int (PK),
  projectId: int (FK -> projects.id),
  variableType: 'exposure' | 'outcome' | 'covariate',
  researchVariable: string,    // 研究方案中的变量名
  nhanesVariable: string,      // NHANES数据库变量名
  nhanesTable: string,         // NHANES数据表名
  description: string,
  confirmed: boolean           // 用户是否确认
}
```

#### 4. `analysisTasks` - 分析任务表
```typescript
{
  id: int (PK),
  projectId: int (FK -> projects.id),
  analysisType: 'kaplan_meier' | 'cox_regression' | 'fine_gray' | 'baseline_table',
  status: 'pending' | 'running' | 'completed' | 'failed',
  rScriptPath: string,         // R脚本文件路径
  outputPath: string,          // 结果输出路径
  errorMessage: string,
  startedAt: timestamp,
  completedAt: timestamp
}
```

#### 5. `files` - 文件表
```typescript
{
  id: int (PK),
  projectId: int (FK -> projects.id),
  fileType: 'proposal' | 'data' | 'table' | 'figure' | 'paper',
  fileName: string,
  fileKey: string,             // S3存储key
  fileUrl: string,             // S3公开URL
  mimeType: string,
  fileSize: int,
  uploadedAt: timestamp
}
```

#### 6. `papers` - 论文表
```typescript
{
  id: int (PK),
  projectId: int (FK -> projects.id),
  title: string,
  abstract: string,
  introduction: string,
  methods: string,
  results: string,
  discussion: string,
  conclusion: string,
  references: string,          // JSON格式的参考文献列表
  createdAt: timestamp,
  updatedAt: timestamp
}
```

---

## 核心功能模块详解

### 1. Word文档解析 (`server/wordParser.ts`)

**功能**: 解析用户上传的Word研究方案，提取PICO/PECO要素和研究变量

**技术实现**:
- 使用`mammoth`库将Word文档转换为纯文本
- 调用DeepSeek API进行结构化信息提取
- 返回JSON格式的解析结果

**关键函数**:
```typescript
export async function parseResearchProposal(wordBuffer: Buffer): Promise<{
  pico: { population, intervention, comparison, outcome, exposure },
  studyDesign: string,
  researchQuestion: string,
  variables: Array<{ name, type, description }>
}>
```

**待完善**:
- [ ] 支持更多Word格式（.doc、.docx、.odt）
- [ ] 增强PICO提取准确性（使用更大的上下文窗口）
- [ ] 支持中文研究方案解析

### 2. NHANES变量映射

**功能**: 将研究方案中的变量自动映射到NHANES数据库变量

**当前实现**: 基于LLM的语义匹配（在`wordParser.ts`中）

**待完善**:
- [ ] 构建NHANES变量知识库（所有周期的变量字典）
- [ ] 实现向量数据库检索（提高映射准确性）
- [ ] 添加用户确认和手动调整界面
- [ ] 支持跨周期变量名称变化处理

### 3. R语言统计分析 (`server/rExecutor.ts`)

**功能**: 生成并执行R脚本进行统计分析

**支持的分析类型**:
1. **Kaplan-Meier生存曲线** (`generateKaplanMeierScript`)
2. **Cox比例风险回归** (`generateCoxRegressionScript`)
3. **Fine-Gray竞争风险模型** (`generateFineGrayScript`)
4. **Lancet标准基线特征表** (`generateBaselineTableScript`)

**关键函数**:
```typescript
export async function executeRScript(
  scriptContent: string,
  outputDir: string
): Promise<{ success: boolean, output: string, error?: string }>
```

**R包依赖**:
```r
# 生存分析
survival, survminer

# 竞争风险
cmprsk, riskRegression

# 表格生成
tableone, gtsummary

# 数据处理
dplyr, tidyr, readr

# 图形生成
ggplot2, ggpubr
```

**待完善**:
- [ ] 实现R包自动安装检测
- [ ] 添加分析进度回调机制
- [ ] 支持更多统计方法（分层分析、交互效应、敏感性分析）
- [ ] 优化R脚本错误处理和日志记录

### 4. PubMed文献搜索 (`server/pubmedSearch.ts`)

**功能**: 根据研究主题搜索相关文献并格式化引用

**API**: NCBI E-utilities (https://eutils.ncbi.nlm.nih.gov/entrez/eutils/)

**关键函数**:
```typescript
export async function searchPubMed(
  query: string,
  maxResults: number = 10
): Promise<Array<{
  pmid: string,
  title: string,
  authors: string[],
  journal: string,
  year: string,
  abstract: string,
  citation: string  // Lancet格式引用
}>>
```

**待完善**:
- [ ] 添加文献相关性评分
- [ ] 支持更多引用格式（APA、Vancouver等）
- [ ] 实现文献去重和分类
- [ ] 添加文献全文链接获取

### 5. 学术论文生成 (`server/paperGenerator.ts`)

**功能**: 基于分析结果使用LLM生成完整的Lancet格式论文

**生成章节**:
1. Abstract (Summary)
2. Introduction (Background + Study Aim)
3. Methods (Data Source + Statistical Analysis)
4. Results (Baseline + Main Findings + Subgroup)
5. Discussion (Findings + Comparison + Mechanisms + Limitations + Implications)
6. Conclusion
7. References

**关键函数**:
```typescript
export async function generatePaper(params: {
  projectTitle: string,
  picoData: object,
  analysisResults: string,
  references: Array<{ title, authors, journal, year }>
}): Promise<{
  title: string,
  abstract: string,
  introduction: string,
  methods: string,
  results: string,
  discussion: string,
  conclusion: string,
  fullText: string  // Markdown格式
}>
```

**待完善**:
- [ ] 添加论文质量检查（字数、结构、引用数量）
- [ ] 支持用户自定义论文模板
- [ ] 实现论文在线编辑功能
- [ ] 添加AI辅助改写和润色功能

---

## tRPC API路由 (`server/routers.ts`)

### 已实现的API端点

#### 项目管理
```typescript
// 创建新项目（上传Word研究方案）
project.create: protectedProcedure
  .input(z.object({ 
    title: z.string(), 
    proposalFile: z.string()  // Base64编码的Word文件
  }))
  .mutation()

// 获取用户所有项目
project.list: protectedProcedure.query()

// 获取项目详情
project.getById: protectedProcedure
  .input(z.object({ id: z.number() }))
  .query()

// 删除项目
project.delete: protectedProcedure
  .input(z.object({ id: z.number() }))
  .mutation()
```

#### 分析任务
```typescript
// 启动统计分析
analysis.start: protectedProcedure
  .input(z.object({
    projectId: z.number(),
    analysisType: z.enum(['kaplan_meier', 'cox_regression', 'fine_gray', 'baseline_table'])
  }))
  .mutation()

// 获取分析任务状态
analysis.getStatus: protectedProcedure
  .input(z.object({ taskId: z.number() }))
  .query()
```

#### 论文生成
```typescript
// 生成学术论文
paper.generate: protectedProcedure
  .input(z.object({ projectId: z.number() }))
  .mutation()

// 获取论文内容
paper.get: protectedProcedure
  .input(z.object({ projectId: z.number() }))
  .query()
```

#### 文件管理
```typescript
// 上传文件到S3
file.upload: protectedProcedure
  .input(z.object({
    projectId: z.number(),
    fileType: z.enum(['proposal', 'data', 'table', 'figure', 'paper']),
    fileName: z.string(),
    fileContent: z.string()  // Base64
  }))
  .mutation()

// 获取项目所有文件
file.listByProject: protectedProcedure
  .input(z.object({ projectId: z.number() }))
  .query()

// 下载文件
file.download: protectedProcedure
  .input(z.object({ fileId: z.number() }))
  .query()
```

### 待实现的API端点

```typescript
// 变量映射确认
variableMapping.confirm: protectedProcedure
  .input(z.object({
    mappingId: z.number(),
    confirmed: z.boolean(),
    nhanesVariable: z.string().optional()  // 手动调整
  }))
  .mutation()

// NHANES数据下载
nhanes.downloadData: protectedProcedure
  .input(z.object({
    projectId: z.number(),
    cycles: z.array(z.string()),  // ['2017-2018', '2019-2020']
    variables: z.array(z.string())
  }))
  .mutation()

// 分析配置
analysis.configure: protectedProcedure
  .input(z.object({
    projectId: z.number(),
    config: z.object({
      covariates: z.array(z.string()),
      stratifyBy: z.string().optional(),
      confidenceLevel: z.number().default(0.95)
    })
  }))
  .mutation()

// 论文编辑
paper.update: protectedProcedure
  .input(z.object({
    paperId: z.number(),
    section: z.enum(['abstract', 'introduction', 'methods', 'results', 'discussion', 'conclusion']),
    content: z.string()
  }))
  .mutation()
```

---

## 前端页面说明

### 1. 首页 (`client/src/pages/Home.tsx`)

**功能**: NHANES数据库介绍 + Lancet研究文献展示

**已实现**:
- NHANES统计数据卡片（参与者、变量、年限、发文量）
- 数据覆盖范围详细说明
- 调查周期时间轴
- Lancet研究图片画廊（6张高质量研究图片）
- 精选文献列表（8篇Lancet及顶级期刊论文）
- 平台功能介绍
- 工作流程说明

**设计特点**:
- Lancet品牌配色（#A51C30深红色）
- 响应式布局
- 图片hover放大效果
- 外部链接跳转

### 2. 用户仪表盘 (`client/src/pages/Dashboard.tsx`)

**功能**: 显示用户所有研究项目和状态

**已实现**:
- 项目列表展示（标题、状态、创建时间）
- 状态徽章（draft、analyzing、completed、failed）
- 快速操作按钮（查看详情、删除）
- 创建新项目入口

**待完善**:
- [ ] 添加项目搜索和筛选
- [ ] 显示项目进度百分比
- [ ] 添加项目统计卡片（总数、进行中、已完成）
- [ ] 支持项目排序（按时间、状态）

### 3. 新建项目页面 (`client/src/pages/NewProject.tsx`)

**功能**: 上传Word研究方案并创建项目

**已实现**:
- 文件上传组件（拖拽或点击上传）
- 文件类型验证（仅.docx）
- 上传进度显示
- 自动跳转到项目详情页

**待完善**:
- [ ] 支持更多文件格式（.doc、.pdf、.txt）
- [ ] 添加研究方案模板下载
- [ ] 显示文件预览
- [ ] 支持批量上传

### 4. 项目详情页 (`client/src/pages/ProjectDetail.tsx`)

**功能**: 显示PICO解析结果、变量映射、分析任务、生成的论文

**已实现**:
- PICO/PECO要素展示
- 变量映射列表
- 分析任务状态显示
- 生成的文件列表（表格、图形、论文）
- 文件下载按钮

**待完善**:
- [ ] 变量映射确认交互（编辑、确认按钮）
- [ ] 分析配置界面（选择协变量、分层变量）
- [ ] 实时分析进度条
- [ ] 论文在线编辑器（Markdown）
- [ ] 结果可视化预览（表格、图表内嵌显示）
- [ ] 版本历史和回滚功能

---

## 环境变量配置

### 必需的环境变量

```bash
# 数据库（Manus自动注入）
DATABASE_URL=mysql://...

# Manus OAuth（Manus自动注入）
JWT_SECRET=...
OAUTH_SERVER_URL=...
VITE_OAUTH_PORTAL_URL=...

# DeepSeek API（需要用户配置）
DEEPSEEK_API_KEY=sk-...

# S3存储（Manus自动注入）
# 通过 server/_core/storage.ts 访问
```

### 配置方式

1. 在Manus Management UI中配置`DEEPSEEK_API_KEY`
2. 或使用`webdev_request_secrets`工具添加

---

## 开发工作流

### 本地开发

```bash
# 安装依赖
pnpm install

# 启动开发服务器
pnpm dev

# 数据库迁移
pnpm db:push

# 运行测试
pnpm test

# 类型检查
pnpm check
```

### 添加新功能的步骤

1. **更新`todo.md`**: 添加待办事项
2. **修改数据库** (如需要):
   - 编辑`drizzle/schema.ts`
   - 运行`pnpm db:push`
3. **实现后端逻辑**:
   - 在`server/`目录添加新模块或修改现有模块
   - 在`server/routers.ts`添加tRPC端点
4. **实现前端界面**:
   - 在`client/src/pages/`或`client/src/components/`添加组件
   - 使用`trpc.*.useQuery/useMutation`调用后端API
5. **编写测试**:
   - 在`server/*.test.ts`添加单元测试
   - 运行`pnpm test`验证
6. **更新文档**:
   - 更新`USER_GUIDE.md`（如果影响用户使用）
   - 更新本文档（如果改变架构）
7. **创建检查点**:
   - 使用`webdev_save_checkpoint`保存进度

---

## 关键待完成功能

### 高优先级

#### 1. NHANES数据爬虫模块
**目标**: 自动从CDC官网下载NHANES数据

**技术方案**:
- 使用`axios`或`node-fetch`下载XPT文件
- 使用`sas7bdat`或`haven`（R包）解析SAS数据格式
- 转换为CSV或JSON格式存储到S3

**参考资源**:
- CDC NHANES数据下载页面: https://wwwn.cdc.gov/nchs/nhanes/
- NHANES数据文件命名规则: https://wwwn.cdc.gov/nchs/nhanes/search/datapage.aspx

**实现建议**:
```typescript
// server/nhanesDownloader.ts
export async function downloadNHANESData(params: {
  cycles: string[],        // ['2017-2018', '2019-2020']
  variables: string[],     // ['SEQN', 'RIAGENDR', 'RIDAGEYR', ...]
  outputDir: string
}): Promise<{ success: boolean, files: string[] }>
```

#### 2. 变量映射确认界面
**目标**: 用户可以查看、编辑、确认AI自动识别的变量映射

**UI设计**:
- 表格形式展示（研究变量 | NHANES变量 | 数据表 | 操作）
- 每行有"编辑"和"确认"按钮
- 支持搜索NHANES变量字典
- 显示变量描述和取值范围

**API端点**:
```typescript
variableMapping.update: protectedProcedure
  .input(z.object({
    mappingId: z.number(),
    nhanesVariable: z.string(),
    nhanesTable: z.string()
  }))
  .mutation()

variableMapping.confirm: protectedProcedure
  .input(z.object({ mappingId: z.number() }))
  .mutation()
```

#### 3. 分析进度实时显示
**目标**: 用户可以看到R脚本执行的实时进度

**技术方案**:
- 方案A: WebSocket（推荐）
  - 在`server/_core/index.ts`添加Socket.IO
  - R脚本输出重定向到Node.js进程
  - 实时推送日志到前端
  
- 方案B: 轮询
  - 前端每2秒调用`analysis.getStatus`
  - 后端解析R脚本日志文件返回进度

**实现建议**:
```typescript
// 使用Socket.IO
import { Server } from 'socket.io';

const io = new Server(server, { path: '/api/socket.io' });

io.on('connection', (socket) => {
  socket.on('subscribe_analysis', (taskId) => {
    // 订阅分析任务进度
  });
});

// 在rExecutor.ts中
export async function executeRScriptWithProgress(
  scriptContent: string,
  onProgress: (message: string) => void
): Promise<...>
```

### 中优先级

#### 4. 论文在线编辑器
**目标**: 用户可以在线编辑生成的论文

**推荐组件**: 
- `react-markdown-editor-lite` (Markdown编辑器)
- `streamdown` (已集成，用于预览)

**功能需求**:
- 分章节编辑（Abstract、Introduction、Methods等）
- 实时预览
- 自动保存
- 版本历史

#### 5. 结果可视化预览
**目标**: 在项目详情页直接显示生成的表格和图表

**技术方案**:
- 表格: 解析R生成的CSV文件，使用`<table>`或`react-table`渲染
- 图表: 直接显示R生成的PNG图片（已存储在S3）

#### 6. 分析配置界面
**目标**: 用户可以自定义统计分析参数

**配置项**:
- 协变量选择（多选框）
- 分层变量（下拉框）
- 置信区间水平（滑块，默认95%）
- 是否进行敏感性分析（开关）

### 低优先级

#### 7. 用户协作功能
- 项目分享（生成分享链接）
- 团队成员管理
- 评论和批注

#### 8. 导出功能增强
- 导出为Word文档（使用`docx`库）
- 导出为LaTeX格式
- 打包下载所有文件（ZIP）

---

## 测试策略

### 单元测试

**已有测试**:
- `server/auth.logout.test.ts` - 认证登出测试
- `server/deepseek.test.ts` - DeepSeek API调用测试

**需要补充的测试**:
```typescript
// server/wordParser.test.ts
describe('parseResearchProposal', () => {
  it('should extract PICO elements from Word document', async () => {
    // 测试Word解析
  });
});

// server/rExecutor.test.ts
describe('generateKaplanMeierScript', () => {
  it('should generate valid R script for survival analysis', () => {
    // 测试R脚本生成
  });
});

// server/pubmedSearch.test.ts
describe('searchPubMed', () => {
  it('should return formatted citations', async () => {
    // 测试PubMed搜索
  });
});
```

### 集成测试

**端到端测试场景**:
1. 用户上传Word研究方案
2. 系统解析PICO要素和变量
3. 用户确认变量映射
4. 系统下载NHANES数据
5. 执行R统计分析
6. 生成Lancet标准表格和图形
7. 搜索PubMed文献
8. 生成完整学术论文
9. 用户下载所有文件

**测试工具**: Vitest + Playwright (可选)

---

## 性能优化建议

### 1. R脚本执行优化
- 使用R包缓存（避免重复安装）
- 并行执行多个分析任务（使用Node.js `child_process`的多进程）
- 限制R进程内存使用

### 2. 文件存储优化
- 大文件（>10MB）使用分片上传
- 图片压缩（使用`sharp`库）
- 实现CDN缓存策略

### 3. LLM调用优化
- 缓存常见PICO解析结果
- 使用流式响应（`stream: true`）提升用户体验
- 实现请求队列避免并发限制

### 4. 数据库优化
- 为常用查询字段添加索引（`projectId`, `userId`, `status`）
- 使用数据库连接池
- 大数据量查询使用分页

---

## 安全注意事项

### 1. 文件上传安全
- 验证文件类型（MIME type检查）
- 限制文件大小（建议<50MB）
- 扫描恶意内容（使用`clamscan`或云服务）

### 2. R脚本执行安全
- 禁止执行用户自定义R代码
- 使用沙箱环境运行R进程
- 限制R脚本执行时间（超时杀死进程）

### 3. API安全
- 所有敏感操作使用`protectedProcedure`
- 验证用户权限（只能访问自己的项目）
- 实现速率限制（防止滥用）

### 4. 数据隐私
- 用户上传的研究方案和数据仅对本人可见
- 定期清理过期文件（S3生命周期策略）
- 遵守GDPR/CCPA数据保护法规

---

## 部署和运维

### 生产环境部署

**使用Manus内置部署**:
1. 创建检查点: `webdev_save_checkpoint`
2. 在Management UI点击"Publish"按钮
3. 配置自定义域名（可选）

**环境变量检查清单**:
- [x] `DATABASE_URL` - 数据库连接
- [x] `JWT_SECRET` - Session加密
- [x] `DEEPSEEK_API_KEY` - AI功能
- [x] S3存储凭证（Manus自动注入）

### 监控和日志

**关键指标**:
- API响应时间
- R脚本执行成功率
- LLM API调用次数和成本
- 用户活跃度（DAU/MAU）

**日志位置**:
- 应用日志: `.manus-logs/devserver.log`
- 浏览器日志: `.manus-logs/browserConsole.log`
- 网络请求: `.manus-logs/networkRequests.log`

### 备份策略

- 数据库自动备份（Manus平台提供）
- S3文件定期快照
- 代码版本控制（Git）

---

## 常见问题和解决方案

### Q1: R包安装失败
**问题**: `executeRScript`报错"package 'xxx' is not available"

**解决方案**:
```bash
# 在服务器上手动安装R包
sudo R
> install.packages(c('survival', 'survminer', 'cmprsk', 'tableone'))
```

### Q2: DeepSeek API超时
**问题**: Word解析或论文生成时超时

**解决方案**:
- 增加API调用超时时间（在`server/_core/llm.ts`修改）
- 使用更快的模型（`deepseek-chat`而非`deepseek-coder`）
- 分段处理长文本

### Q3: 文件上传失败
**问题**: 大文件上传到S3失败

**解决方案**:
- 检查文件大小限制（Express默认100MB）
- 使用分片上传（`@aws-sdk/lib-storage`的`Upload`类）
- 增加超时时间

### Q4: 变量映射不准确
**问题**: AI识别的NHANES变量不正确

**解决方案**:
- 构建NHANES变量知识库（所有变量的描述和取值范围）
- 使用向量数据库（如Pinecone、Weaviate）进行语义搜索
- 提供用户手动调整界面

---

## OpenClaw开发建议

### 1. 优先完成的功能（按顺序）

1. **变量映射确认界面** - 提升用户体验的关键功能
2. **NHANES数据爬虫** - 实现真正的端到端自动化
3. **分析进度实时显示** - 让用户了解系统状态
4. **论文在线编辑器** - 增强论文生成的灵活性
5. **分析配置界面** - 支持更复杂的研究设计

### 2. 代码风格和规范

- 遵循现有的TypeScript类型定义
- 使用`tRPC`进行前后端通信（避免手动写API）
- 前端组件使用shadcn/ui（已集成）
- 数据库操作使用Drizzle ORM
- 所有异步操作添加错误处理

### 3. 文档维护

- 每次添加新功能后更新`todo.md`
- 重大架构变更更新本文档
- 用户可见功能更新`USER_GUIDE.md`

### 4. 测试要求

- 所有新的API端点必须有单元测试
- 关键业务逻辑（Word解析、R脚本生成）必须有测试覆盖
- 运行`pnpm test`确保所有测试通过

### 5. 性能考虑

- R脚本执行是CPU密集型操作，考虑使用任务队列
- LLM API调用有成本，添加缓存机制
- 大文件下载使用流式传输

### 6. 用户体验优化

- 所有耗时操作显示加载状态
- 错误信息对用户友好（避免技术术语）
- 添加操作确认对话框（删除项目等）
- 实现键盘快捷键（如Ctrl+S保存）

---

## 参考资源

### NHANES相关
- **CDC NHANES官网**: https://www.cdc.gov/nchs/nhanes/
- **NHANES数据下载**: https://wwwn.cdc.gov/nchs/nhanes/search/datapage.aspx
- **NHANES教程**: https://wwwn.cdc.gov/nchs/nhanes/tutorials/

### Lancet投稿指南
- **The Lancet作者指南**: https://www.thelancet.com/lancet/information-for-authors
- **Lancet论文格式**: https://www.thelancet.com/pb/assets/raw/Lancet/authors/tl-info-for-authors.pdf

### R语言生存分析
- **survival包文档**: https://cran.r-project.org/web/packages/survival/
- **survminer包**: https://rpkgs.datanovia.com/survminer/
- **竞争风险分析**: https://cran.r-project.org/web/packages/cmprsk/

### API文档
- **PubMed E-utilities**: https://www.ncbi.nlm.nih.gov/books/NBK25501/
- **DeepSeek API**: https://platform.deepseek.com/docs

### 技术栈文档
- **tRPC**: https://trpc.io/docs
- **Drizzle ORM**: https://orm.drizzle.team/docs/overview
- **React 19**: https://react.dev/
- **Tailwind CSS 4**: https://tailwindcss.com/docs

---

## 联系方式

如有技术问题或需要进一步说明，请通过以下方式联系：

- **项目仓库**: 查看Management UI的GitHub导出功能
- **技术文档**: 本文档和`USER_GUIDE.md`
- **待办清单**: `todo.md`

---

**祝OpenClaw开发顺利！期待看到这个平台变得更加完善和强大。** 🚀
