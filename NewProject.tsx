import { useState } from "react";
import { useLocation } from "wouter";
import DashboardLayout from "@/components/DashboardLayout";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { trpc } from "@/lib/trpc";
import { toast } from "sonner";
import { Upload, Loader2, FileText } from "lucide-react";

export default function NewProject() {
  const [, setLocation] = useLocation();
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);

  const createProjectMutation = trpc.projects.create.useMutation();
  const uploadProposalMutation = trpc.projects.uploadProposal.useMutation();

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile) {
      if (!selectedFile.name.endsWith(".docx") && !selectedFile.name.endsWith(".doc")) {
        toast.error("请上传Word文档（.docx或.doc格式）");
        return;
      }
      setFile(selectedFile);
      // Auto-fill title from filename if empty
      if (!title) {
        const fileName = selectedFile.name.replace(/\.(docx|doc)$/, "");
        setTitle(fileName);
      }
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!title.trim()) {
      toast.error("请输入项目标题");
      return;
    }

    if (!file) {
      toast.error("请上传研究方案文档");
      return;
    }

    setUploading(true);

    try {
      // Step 1: Create project
      const project = await createProjectMutation.mutateAsync({
        title: title.trim(),
        description: description.trim() || undefined,
      });

      // Step 2: Upload Word document
      const reader = new FileReader();
      reader.onload = async (event) => {
        try {
          const base64Data = event.target?.result as string;
          // Remove data URL prefix
          const base64Content = base64Data.split(",")[1];

          await uploadProposalMutation.mutateAsync({
            projectId: project.id,
            fileName: file.name,
            fileData: base64Content,
          });

          toast.success("项目创建成功！正在解析研究方案...");
          setLocation(`/projects/${project.id}`);
        } catch (error) {
          console.error("Upload error:", error);
          toast.error("文件上传失败");
          setUploading(false);
        }
      };

      reader.onerror = () => {
        toast.error("文件读取失败");
        setUploading(false);
      };

      reader.readAsDataURL(file);
    } catch (error) {
      console.error("Project creation error:", error);
      toast.error("项目创建失败");
      setUploading(false);
    }
  };

  return (
    <DashboardLayout>
      <div className="max-w-2xl mx-auto space-y-6">
        <div>
          <h1 className="text-3xl font-bold">新建分析项目</h1>
          <p className="text-muted-foreground mt-1">
            上传您的研究方案，开始NHANES数据分析
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>项目信息</CardTitle>
              <CardDescription>
                填写项目基本信息
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="title">项目标题 *</Label>
                <Input
                  id="title"
                  placeholder="例如：吸烟与心血管疾病风险的关联研究"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  disabled={uploading}
                  required
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="description">项目描述（可选）</Label>
                <Textarea
                  id="description"
                  placeholder="简要描述研究目的和方法"
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  disabled={uploading}
                  rows={3}
                />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>上传研究方案</CardTitle>
              <CardDescription>
                支持Word文档格式（.docx或.doc），系统将自动解析PICO/PECO要素和研究变量
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="border-2 border-dashed rounded-lg p-8 text-center hover:border-primary/50 transition-colors">
                  <input
                    type="file"
                    id="file-upload"
                    className="hidden"
                    accept=".doc,.docx,application/msword,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                    onChange={handleFileChange}
                    disabled={uploading}
                  />
                  <label
                    htmlFor="file-upload"
                    className="cursor-pointer flex flex-col items-center gap-2"
                  >
                    {file ? (
                      <>
                        <FileText className="h-12 w-12 text-primary" />
                        <div className="space-y-1">
                          <p className="font-medium">{file.name}</p>
                          <p className="text-sm text-muted-foreground">
                            {(file.size / 1024).toFixed(2)} KB
                          </p>
                        </div>
                        <Button
                          type="button"
                          variant="outline"
                          size="sm"
                          onClick={(e) => {
                            e.preventDefault();
                            setFile(null);
                          }}
                          disabled={uploading}
                        >
                          更换文件
                        </Button>
                      </>
                    ) : (
                      <>
                        <Upload className="h-12 w-12 text-muted-foreground" />
                        <div className="space-y-1">
                          <p className="font-medium">点击上传Word文档</p>
                          <p className="text-sm text-muted-foreground">
                            或拖拽文件到此处
                          </p>
                        </div>
                      </>
                    )}
                  </label>
                </div>
              </div>
            </CardContent>
          </Card>

          <div className="flex gap-4">
            <Button
              type="button"
              variant="outline"
              onClick={() => setLocation("/dashboard")}
              disabled={uploading}
            >
              取消
            </Button>
            <Button type="submit" disabled={uploading || !file} className="gap-2">
              {uploading ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  创建中...
                </>
              ) : (
                "创建项目"
              )}
            </Button>
          </div>
        </form>
      </div>
    </DashboardLayout>
  );
}
