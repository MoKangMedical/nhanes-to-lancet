# OpenClaw快速入门指南

欢迎OpenClaw！这份文档将帮助你快速了解项目并开始开发。

---

## 第一步：理解项目

### 项目目标
构建一个自动化平台，让流行病学研究人员能够：
1. 上传Word研究方案
2. AI自动解析研究问题和变量
3. 自动下载NHANES数据
4. 执行R语言统计分析
5. 生成符合Lancet杂志标准的论文

### 当前进度
✅ **已完成**:
- 用户认证和项目管理
- Word文档解析和PICO提取
- R脚本生成（生存分析、Cox回归、竞争风险）
- PubMed文献搜索
- 学术论文生成
- Lancet品牌设计

🚧 **待完成**:
- NHANES数据自动下载
- 变量映射确认界面
- 分析进度实时显示
- 论文在线编辑
- 结果可视化预览

---

## 第二步：环境设置

### 1. 查看项目文件结构
```bash
cd /home/ubuntu/nhanes-analysis-platform
ls -la
```

### 2. 检查依赖安装
```bash
pnpm install
```

### 3. 检查数据库连接
```bash
pnpm db:push
```

### 4. 启动开发服务器
```bash
pnpm dev
```

访问: https://3000-[你的沙箱ID].manus.computer

### 5. 运行现有测试
```bash
pnpm test
```

---

## 第三步：理解代码结构

### 关键文件位置

#### 后端核心
```
server/
├── routers.ts           ← tRPC API端点定义（从这里开始）
├── db.ts                ← 数据库查询函数
├── wordParser.ts        ← Word解析和PICO提取
├── rExecutor.ts         ← R脚本生成和执行
├── pubmedSearch.ts      ← PubMed文献搜索
└── paperGenerator.ts    ← 论文生成
```

#### 前端页面
```
client/src/pages/
├── Home.tsx             ← 首页（NHANES介绍）
├── Dashboard.tsx        ← 用户仪表盘
├── NewProject.tsx       ← 创建项目（上传Word）
└── ProjectDetail.tsx    ← 项目详情（核心页面）
```

#### 数据库
```
drizzle/schema.ts        ← 数据表定义
```

### 数据流向

```
用户上传Word
    ↓
wordParser.ts (解析PICO)
    ↓
保存到projects表
    ↓
用户确认变量映射
    ↓
下载NHANES数据 (待实现)
    ↓
rExecutor.ts (执行R分析)
    ↓
保存结果到files表
    ↓
paperGenerator.ts (生成论文)
    ↓
保存到papers表
    ↓
用户下载所有文件
```

---

## 第四步：第一个任务建议

### 任务1：实现变量映射确认界面（推荐从这里开始）

**为什么选这个任务？**
- 用户体验关键功能
- 涉及前后端交互
- 难度适中
- 不依赖外部复杂系统

**实现步骤**:

#### 1. 后端：添加API端点
编辑 `server/routers.ts`，添加：

```typescript
variableMapping: router({
  // 获取项目的所有变量映射
  listByProject: protectedProcedure
    .input(z.object({ projectId: z.number() }))
    .query(async ({ input, ctx }) => {
      return await getVariableMappingsByProject(input.projectId);
    }),
  
  // 更新变量映射
  update: protectedProcedure
    .input(z.object({
      mappingId: z.number(),
      nhanesVariable: z.string(),
      nhanesTable: z.string()
    }))
    .mutation(async ({ input }) => {
      return await updateVariableMapping(input);
    }),
  
  // 确认变量映射
  confirm: protectedProcedure
    .input(z.object({ mappingId: z.number() }))
    .mutation(async ({ input }) => {
      return await confirmVariableMapping(input.mappingId);
    }),
}),
```

#### 2. 后端：实现数据库函数
编辑 `server/db.ts`，添加：

```typescript
export async function getVariableMappingsByProject(projectId: number) {
  const db = await getDb();
  if (!db) return [];
  
  return await db
    .select()
    .from(variableMappings)
    .where(eq(variableMappings.projectId, projectId));
}

export async function updateVariableMapping(data: {
  mappingId: number;
  nhanesVariable: string;
  nhanesTable: string;
}) {
  const db = await getDb();
  if (!db) throw new Error("Database not available");
  
  await db
    .update(variableMappings)
    .set({
      nhanesVariable: data.nhanesVariable,
      nhanesTable: data.nhanesTable,
    })
    .where(eq(variableMappings.id, data.mappingId));
  
  return { success: true };
}

export async function confirmVariableMapping(mappingId: number) {
  const db = await getDb();
  if (!db) throw new Error("Database not available");
  
  await db
    .update(variableMappings)
    .set({ confirmed: true })
    .where(eq(variableMappings.id, mappingId));
  
  return { success: true };
}
```

#### 3. 前端：创建变量映射组件
创建 `client/src/components/VariableMappingTable.tsx`:

```typescript
import { useState } from "react";
import { trpc } from "@/lib/trpc";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Check, Edit2, X } from "lucide-react";

export function VariableMappingTable({ projectId }: { projectId: number }) {
  const { data: mappings, refetch } = trpc.variableMapping.listByProject.useQuery({ projectId });
  const updateMutation = trpc.variableMapping.update.useMutation();
  const confirmMutation = trpc.variableMapping.confirm.useMutation();
  
  const [editingId, setEditingId] = useState<number | null>(null);
  const [editValues, setEditValues] = useState({ nhanesVariable: "", nhanesTable: "" });
  
  const handleEdit = (mapping: any) => {
    setEditingId(mapping.id);
    setEditValues({
      nhanesVariable: mapping.nhanesVariable,
      nhanesTable: mapping.nhanesTable,
    });
  };
  
  const handleSave = async (mappingId: number) => {
    await updateMutation.mutateAsync({
      mappingId,
      ...editValues,
    });
    setEditingId(null);
    refetch();
  };
  
  const handleConfirm = async (mappingId: number) => {
    await confirmMutation.mutateAsync({ mappingId });
    refetch();
  };
  
  if (!mappings) return <div>加载中...</div>;
  
  return (
    <div className="border rounded-lg overflow-hidden">
      <table className="w-full">
        <thead className="bg-muted">
          <tr>
            <th className="p-3 text-left">研究变量</th>
            <th className="p-3 text-left">NHANES变量</th>
            <th className="p-3 text-left">数据表</th>
            <th className="p-3 text-left">类型</th>
            <th className="p-3 text-left">状态</th>
            <th className="p-3 text-left">操作</th>
          </tr>
        </thead>
        <tbody>
          {mappings.map((mapping) => (
            <tr key={mapping.id} className="border-t">
              <td className="p-3">{mapping.researchVariable}</td>
              <td className="p-3">
                {editingId === mapping.id ? (
                  <Input
                    value={editValues.nhanesVariable}
                    onChange={(e) => setEditValues({ ...editValues, nhanesVariable: e.target.value })}
                    className="max-w-xs"
                  />
                ) : (
                  mapping.nhanesVariable
                )}
              </td>
              <td className="p-3">
                {editingId === mapping.id ? (
                  <Input
                    value={editValues.nhanesTable}
                    onChange={(e) => setEditValues({ ...editValues, nhanesTable: e.target.value })}
                    className="max-w-xs"
                  />
                ) : (
                  mapping.nhanesTable
                )}
              </td>
              <td className="p-3">
                <Badge variant="outline">{mapping.variableType}</Badge>
              </td>
              <td className="p-3">
                {mapping.confirmed ? (
                  <Badge variant="default" className="gap-1">
                    <Check className="h-3 w-3" /> 已确认
                  </Badge>
                ) : (
                  <Badge variant="secondary">待确认</Badge>
                )}
              </td>
              <td className="p-3">
                <div className="flex gap-2">
                  {editingId === mapping.id ? (
                    <>
                      <Button size="sm" onClick={() => handleSave(mapping.id)}>
                        <Check className="h-4 w-4" />
                      </Button>
                      <Button size="sm" variant="outline" onClick={() => setEditingId(null)}>
                        <X className="h-4 w-4" />
                      </Button>
                    </>
                  ) : (
                    <>
                      <Button size="sm" variant="outline" onClick={() => handleEdit(mapping)}>
                        <Edit2 className="h-4 w-4" />
                      </Button>
                      {!mapping.confirmed && (
                        <Button size="sm" onClick={() => handleConfirm(mapping.id)}>
                          确认
                        </Button>
                      )}
                    </>
                  )}
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
```

#### 4. 前端：在项目详情页使用组件
编辑 `client/src/pages/ProjectDetail.tsx`，添加：

```typescript
import { VariableMappingTable } from "@/components/VariableMappingTable";

// 在项目详情页的适当位置添加
<Card>
  <CardHeader>
    <CardTitle>变量映射</CardTitle>
    <CardDescription>确认AI识别的NHANES变量映射是否正确</CardDescription>
  </CardHeader>
  <CardContent>
    <VariableMappingTable projectId={projectId} />
  </CardContent>
</Card>
```

#### 5. 测试
```bash
# 运行测试
pnpm test

# 手动测试
# 1. 创建新项目
# 2. 上传Word文档
# 3. 查看变量映射表
# 4. 点击"编辑"修改变量
# 5. 点击"确认"
```

#### 6. 更新待办清单
编辑 `todo.md`，标记为已完成：
```markdown
- [x] 实现变量映射确认交互（用户可调整自动识别的变量）
```

---

## 第五步：后续任务建议

完成变量映射界面后，按以下顺序继续：

### 任务2：NHANES数据爬虫
- 难度：⭐⭐⭐⭐
- 影响：实现端到端自动化的关键
- 参考：`HANDOVER_TO_OPENCLAW.md`中的"NHANES数据爬虫模块"章节

### 任务3：分析进度实时显示
- 难度：⭐⭐⭐
- 影响：提升用户体验
- 技术：WebSocket或轮询
- 参考：`HANDOVER_TO_OPENCLAW.md`中的"分析进度实时显示"章节

### 任务4：论文在线编辑器
- 难度：⭐⭐
- 影响：增强论文生成灵活性
- 技术：`react-markdown-editor-lite`
- 参考：`HANDOVER_TO_OPENCLAW.md`中的"论文在线编辑器"章节

---

## 第六步：开发最佳实践

### 1. 代码提交前检查清单
- [ ] 运行`pnpm test`确保测试通过
- [ ] 运行`pnpm check`确保类型检查通过
- [ ] 更新`todo.md`标记已完成功能
- [ ] 手动测试新功能
- [ ] 使用`webdev_save_checkpoint`保存进度

### 2. 调试技巧
```bash
# 查看服务器日志
tail -f .manus-logs/devserver.log

# 查看浏览器控制台日志
tail -f .manus-logs/browserConsole.log

# 查看网络请求
tail -f .manus-logs/networkRequests.log
```

### 3. 常用命令
```bash
# 数据库迁移
pnpm db:push

# 重启开发服务器
# （在Manus中使用webdev_restart_server工具）

# 查看项目状态
# （在Manus中使用webdev_check_status工具）
```

### 4. 获取帮助
- 查看`HANDOVER_TO_OPENCLAW.md`了解详细技术文档
- 查看`USER_GUIDE.md`了解用户使用流程
- 查看`todo.md`了解所有待完成功能
- 查看现有代码的注释和类型定义

---

## 第七步：理解关键概念

### tRPC工作原理
```typescript
// 后端定义（server/routers.ts）
project: router({
  list: protectedProcedure.query(async ({ ctx }) => {
    return await getUserProjects(ctx.user.id);
  }),
}),

// 前端调用（client/src/pages/Dashboard.tsx）
const { data: projects } = trpc.project.list.useQuery();
// 自动类型安全，无需手动定义接口！
```

### Drizzle ORM查询
```typescript
// 查询
const projects = await db
  .select()
  .from(projects)
  .where(eq(projects.userId, userId));

// 插入
await db.insert(projects).values({
  userId: 1,
  title: "My Research",
  status: "draft",
});

// 更新
await db
  .update(projects)
  .set({ status: "completed" })
  .where(eq(projects.id, projectId));
```

### R脚本执行流程
```typescript
// 1. 生成R脚本
const script = generateKaplanMeierScript({
  dataPath: "/path/to/data.csv",
  timeVar: "time_to_event",
  eventVar: "death",
  outputDir: "/path/to/output",
});

// 2. 执行R脚本
const result = await executeRScript(script, "/path/to/output");

// 3. 检查结果
if (result.success) {
  // 读取生成的图片和表格
  const survivalCurve = `${outputDir}/survival_curve.png`;
  const resultsTable = `${outputDir}/results.csv`;
}
```

---

## 第八步：常见问题

### Q: 如何添加新的数据表？
A: 
1. 编辑`drizzle/schema.ts`添加表定义
2. 运行`pnpm db:push`执行迁移
3. 在`server/db.ts`添加查询函数
4. 在`server/routers.ts`添加API端点

### Q: 如何调试R脚本？
A:
1. 查看`rExecutor.ts`生成的脚本内容
2. 在服务器上手动运行R脚本测试
3. 检查R脚本输出和错误信息

### Q: 如何测试LLM功能？
A:
```bash
# 运行DeepSeek测试
pnpm test server/deepseek.test.ts
```

### Q: 如何添加新的前端页面？
A:
1. 在`client/src/pages/`创建新组件
2. 在`client/src/App.tsx`添加路由
3. 使用`trpc.*`调用后端API

---

## 第九步：项目愿景

### 短期目标（1-2周）
- ✅ 变量映射确认界面
- ✅ 分析进度实时显示
- ✅ 论文在线编辑器

### 中期目标（1个月）
- ✅ NHANES数据自动下载
- ✅ 结果可视化预览
- ✅ 分析配置界面

### 长期目标（3个月+）
- ✅ 支持更多统计方法（Meta分析、倾向评分匹配）
- ✅ 多用户协作功能
- ✅ 移动端适配
- ✅ 国际化（支持英文界面）

---

## 开始开发吧！

现在你已经了解了项目的全貌，可以开始开发了。建议从**变量映射确认界面**开始，这是一个难度适中且影响力大的功能。

**记住**:
- 📖 遇到问题先查看`HANDOVER_TO_OPENCLAW.md`
- ✅ 每完成一个功能更新`todo.md`
- 🧪 写测试保证代码质量
- 💾 定期保存检查点

**祝你开发顺利！有任何问题随时查看文档或提问。** 🚀
