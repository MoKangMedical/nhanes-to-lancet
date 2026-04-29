import { useParams, useLocation } from "wouter";
import DashboardLayout from "@/components/DashboardLayout";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Separator } from "@/components/ui/separator";
import { trpc } from "@/lib/trpc";
import { toast } from "sonner";
import { 
  ArrowLeft, Loader2, FileText, Database, BarChart3, 
  FileSpreadsheet, Download, CheckCircle2, AlertCircle 
} from "lucide-react";
import { Streamdown } from "streamdown";

export default function ProjectDetail() {
  const params = useParams();
  const [, setLocation] = useLocation();
  const projectId = Number(params.id);

  const { data: project, isLoading: projectLoading } = trpc.projects.get.useQuery({ id: projectId });
  const { data: variables, isLoading: variablesLoading } = trpc.projects.getVariables.useQuery({ projectId });
  const { data: files, isLoading: filesLoading } = trpc.projects.getFiles.useQuery({ projectId });
  const { data: paper, isLoading: paperLoading } = trpc.projects.getPaper.useQuery({ projectId });

  const generatePaperMutation = trpc.projects.generatePaper.useMutation({
    onSuccess: () => {
      toast.success("论文生成成功！");
    },
    onError: (error) => {
      toast.error(`论文生成失败：${error.message}`);
    }
  });

  if (projectLoading) {
    return (
      <DashboardLayout>
        <div className="flex items-center justify-center py-12">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        </div>
      </DashboardLayout>
    );
  }

  if (!project) {
    return (
      <DashboardLayout>
        <div className="text-center py-12 space-y-4">
          <AlertCircle className="h-12 w-12 text-muted-foreground mx-auto" />
          <div>
            <h3 className="font-semibold">项目不存在</h3>
            <p className="text-sm text-muted-foreground">该项目可能已被删除</p>
          </div>
          <Button onClick={() => setLocation("/dashboard")}>
            返回仪表盘
          </Button>
        </div>
      </DashboardLayout>
    );
  }

  const handleGeneratePaper = async () => {
    try {
      await generatePaperMutation.mutateAsync({ projectId });
    } catch (error) {
      console.error("Generate paper error:", error);
    }
  };

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-start justify-between gap-4">
          <div className="space-y-1 flex-1">
            <Button
              variant="ghost"
              size="sm"
              className="gap-2 -ml-2 mb-2"
              onClick={() => setLocation("/dashboard")}
            >
              <ArrowLeft className="h-4 w-4" />
              返回
            </Button>
            <h1 className="text-3xl font-bold">{project.title}</h1>
            {project.description && (
              <p className="text-muted-foreground">{project.description}</p>
            )}
          </div>
          <Badge variant={project.status === "completed" ? "default" : "secondary"}>
            {project.status}
          </Badge>
        </div>

        <Tabs defaultValue="overview" className="space-y-6">
          <TabsList>
            <TabsTrigger value="overview">概览</TabsTrigger>
            <TabsTrigger value="pico">PICO分析</TabsTrigger>
            <TabsTrigger value="variables">变量映射</TabsTrigger>
            <TabsTrigger value="results">分析结果</TabsTrigger>
            <TabsTrigger value="paper">论文</TabsTrigger>
          </TabsList>

          {/* Overview Tab */}
          <TabsContent value="overview" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>项目状态</CardTitle>
                <CardDescription>当前分析进度和关键信息</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <div className="text-sm text-muted-foreground">状态</div>
                    <div className="font-medium">{project.status}</div>
                  </div>
                  <div>
                    <div className="text-sm text-muted-foreground">创建时间</div>
                    <div className="font-medium">
                      {new Date(project.createdAt).toLocaleDateString("zh-CN")}
                    </div>
                  </div>
                </div>

                {project.proposalFileUrl && (
                  <div>
                    <div className="text-sm text-muted-foreground mb-2">研究方案文档</div>
                    <Button variant="outline" size="sm" asChild>
                      <a href={project.proposalFileUrl} target="_blank" rel="noopener noreferrer">
                        <FileText className="h-4 w-4 mr-2" />
                        查看文档
                      </a>
                    </Button>
                  </div>
                )}
              </CardContent>
            </Card>

            {project.status === "parsing" && (
              <Card>
                <CardContent className="flex items-center gap-3 py-6">
                  <Loader2 className="h-5 w-5 animate-spin text-primary" />
                  <div>
                    <p className="font-medium">正在解析研究方案...</p>
                    <p className="text-sm text-muted-foreground">
                      AI正在提取PICO要素和研究变量
                    </p>
                  </div>
                </CardContent>
              </Card>
            )}
          </TabsContent>

          {/* PICO Tab */}
          <TabsContent value="pico" className="space-y-4">
            {project.picoData ? (
              <Card>
                <CardHeader>
                  <CardTitle>PICO/PECO要素</CardTitle>
                  <CardDescription>从研究方案中提取的关键要素</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  {project.picoData.population && (
                    <div>
                      <div className="text-sm font-medium text-muted-foreground mb-1">
                        Population (人群)
                      </div>
                      <p>{project.picoData.population}</p>
                    </div>
                  )}
                  <Separator />
                  {(project.picoData.intervention || project.picoData.exposure) && (
                    <div>
                      <div className="text-sm font-medium text-muted-foreground mb-1">
                        {project.picoData.intervention ? "Intervention (干预)" : "Exposure (暴露)"}
                      </div>
                      <p>{project.picoData.intervention || project.picoData.exposure}</p>
                    </div>
                  )}
                  <Separator />
                  {project.picoData.comparison && (
                    <div>
                      <div className="text-sm font-medium text-muted-foreground mb-1">
                        Comparison (对照)
                      </div>
                      <p>{project.picoData.comparison}</p>
                    </div>
                  )}
                  <Separator />
                  {project.picoData.outcome && (
                    <div>
                      <div className="text-sm font-medium text-muted-foreground mb-1">
                        Outcome (结局)
                      </div>
                      <p>{project.picoData.outcome}</p>
                    </div>
                  )}
                </CardContent>
              </Card>
            ) : (
              <Card>
                <CardContent className="text-center py-12 space-y-2">
                  <AlertCircle className="h-12 w-12 text-muted-foreground mx-auto" />
                  <p className="text-muted-foreground">
                    {project.status === "parsing" ? "正在解析PICO要素..." : "暂无PICO数据"}
                  </p>
                </CardContent>
              </Card>
            )}
          </TabsContent>

          {/* Variables Tab */}
          <TabsContent value="variables" className="space-y-4">
            {variablesLoading ? (
              <div className="flex items-center justify-center py-12">
                <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
              </div>
            ) : variables && variables.length > 0 ? (
              <Card>
                <CardHeader>
                  <CardTitle>NHANES变量映射</CardTitle>
                  <CardDescription>研究变量与NHANES数据库的对应关系</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    {variables.map((variable) => (
                      <div
                        key={variable.id}
                        className="flex items-start justify-between p-3 border rounded-lg"
                      >
                        <div className="space-y-1 flex-1">
                          <div className="flex items-center gap-2">
                            <Badge variant="outline">{variable.category}</Badge>
                            <span className="font-medium">{variable.proposalVariable}</span>
                          </div>
                          <div className="text-sm text-muted-foreground">
                            NHANES: {variable.nhanesVariable} ({variable.nhanesDataset})
                          </div>
                          <div className="text-xs text-muted-foreground">
                            Cycle: {variable.nhanesCycle}
                          </div>
                        </div>
                        {variable.confirmed && (
                          <CheckCircle2 className="h-5 w-5 text-green-600" />
                        )}
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            ) : (
              <Card>
                <CardContent className="text-center py-12 space-y-2">
                  <Database className="h-12 w-12 text-muted-foreground mx-auto" />
                  <p className="text-muted-foreground">暂无变量映射数据</p>
                </CardContent>
              </Card>
            )}
          </TabsContent>

          {/* Results Tab */}
          <TabsContent value="results" className="space-y-4">
            {filesLoading ? (
              <div className="flex items-center justify-center py-12">
                <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
              </div>
            ) : files && files.length > 0 ? (
              <div className="grid gap-4 md:grid-cols-2">
                {files.map((file) => (
                  <Card key={file.id}>
                    <CardHeader>
                      <CardTitle className="text-base flex items-center gap-2">
                        <FileSpreadsheet className="h-4 w-4" />
                        {file.fileName}
                      </CardTitle>
                      <CardDescription>{file.fileType}</CardDescription>
                    </CardHeader>
                    <CardContent>
                      <Button variant="outline" size="sm" asChild>
                        <a href={file.fileUrl} target="_blank" rel="noopener noreferrer">
                          <Download className="h-4 w-4 mr-2" />
                          下载
                        </a>
                      </Button>
                    </CardContent>
                  </Card>
                ))}
              </div>
            ) : (
              <Card>
                <CardContent className="text-center py-12 space-y-2">
                  <BarChart3 className="h-12 w-12 text-muted-foreground mx-auto" />
                  <p className="text-muted-foreground">暂无分析结果</p>
                </CardContent>
              </Card>
            )}
          </TabsContent>

          {/* Paper Tab */}
          <TabsContent value="paper" className="space-y-4">
            {paperLoading ? (
              <div className="flex items-center justify-center py-12">
                <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
              </div>
            ) : paper ? (
              <Card>
                <CardHeader>
                  <div className="flex items-start justify-between">
                    <div>
                      <CardTitle>{paper.title}</CardTitle>
                      <CardDescription>生成的学术论文</CardDescription>
                    </div>
                    {paper.paperFileUrl && (
                      <Button variant="outline" size="sm" asChild>
                        <a href={paper.paperFileUrl} target="_blank" rel="noopener noreferrer">
                          <Download className="h-4 w-4 mr-2" />
                          下载
                        </a>
                      </Button>
                    )}
                  </div>
                </CardHeader>
                <CardContent className="prose prose-sm max-w-none">
                  {paper.fullContent && <Streamdown>{paper.fullContent}</Streamdown>}
                </CardContent>
              </Card>
            ) : (
              <Card>
                <CardContent className="text-center py-12 space-y-4">
                  <FileText className="h-12 w-12 text-muted-foreground mx-auto" />
                  <div className="space-y-2">
                    <p className="text-muted-foreground">尚未生成论文</p>
                    <Button
                      onClick={handleGeneratePaper}
                      disabled={generatePaperMutation.isPending}
                      className="gap-2"
                    >
                      {generatePaperMutation.isPending ? (
                        <>
                          <Loader2 className="h-4 w-4 animate-spin" />
                          生成中...
                        </>
                      ) : (
                        "生成论文"
                      )}
                    </Button>
                  </div>
                </CardContent>
              </Card>
            )}
          </TabsContent>
        </Tabs>
      </div>
    </DashboardLayout>
  );
}
