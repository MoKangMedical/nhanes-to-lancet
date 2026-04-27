import { useAuth } from "@/_core/hooks/useAuth";
import DashboardLayout from "@/components/DashboardLayout";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { trpc } from "@/lib/trpc";
import { Plus, FileText, Clock, CheckCircle2, XCircle, Loader2 } from "lucide-react";
import { Link } from "wouter";
import { formatDistanceToNow } from "date-fns";
import { zhCN } from "date-fns/locale";

export default function Dashboard() {
  const { user } = useAuth();
  const { data: projects, isLoading } = trpc.projects.list.useQuery();

  const getStatusBadge = (status: string) => {
    const statusConfig = {
      draft: { label: "草稿", variant: "secondary" as const, icon: FileText },
      parsing: { label: "解析中", variant: "default" as const, icon: Loader2 },
      parsed: { label: "已解析", variant: "default" as const, icon: CheckCircle2 },
      mapping: { label: "变量映射", variant: "default" as const, icon: Clock },
      ready: { label: "就绪", variant: "default" as const, icon: CheckCircle2 },
      analyzing: { label: "分析中", variant: "default" as const, icon: Loader2 },
      completed: { label: "已完成", variant: "default" as const, icon: CheckCircle2 },
      failed: { label: "失败", variant: "destructive" as const, icon: XCircle },
    };

    const config = statusConfig[status as keyof typeof statusConfig] || statusConfig.draft;
    const Icon = config.icon;

    return (
      <Badge variant={config.variant} className="gap-1">
        <Icon className="h-3 w-3" />
        {config.label}
      </Badge>
    );
  };

  return (
    <DashboardLayout>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold">我的项目</h1>
            <p className="text-muted-foreground mt-1">
              管理您的NHANES数据分析项目
            </p>
          </div>
          <Link href="/projects/new">
            <Button className="gap-2">
              <Plus className="h-4 w-4" />
              新建项目
            </Button>
          </Link>
        </div>

        {isLoading ? (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
          </div>
        ) : projects && projects.length > 0 ? (
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {projects.map((project) => (
              <Link key={project.id} href={`/projects/${project.id}`}>
                <Card className="hover:shadow-lg transition-shadow cursor-pointer h-full">
                  <CardHeader>
                    <div className="flex items-start justify-between gap-2">
                      <CardTitle className="line-clamp-2">{project.title}</CardTitle>
                      {getStatusBadge(project.status)}
                    </div>
                    {project.description && (
                      <CardDescription className="line-clamp-2">
                        {project.description}
                      </CardDescription>
                    )}
                  </CardHeader>
                  <CardContent>
                    <div className="text-sm text-muted-foreground">
                      创建于 {formatDistanceToNow(new Date(project.createdAt), { 
                        addSuffix: true,
                        locale: zhCN 
                      })}
                    </div>
                  </CardContent>
                </Card>
              </Link>
            ))}
          </div>
        ) : (
          <Card className="border-dashed">
            <CardContent className="flex flex-col items-center justify-center py-12 space-y-4">
              <FileText className="h-12 w-12 text-muted-foreground" />
              <div className="text-center space-y-2">
                <h3 className="font-semibold">暂无项目</h3>
                <p className="text-sm text-muted-foreground">
                  创建您的第一个NHANES分析项目
                </p>
              </div>
              <Link href="/projects/new">
                <Button className="gap-2">
                  <Plus className="h-4 w-4" />
                  新建项目
                </Button>
              </Link>
            </CardContent>
          </Card>
        )}
      </div>
    </DashboardLayout>
  );
}
