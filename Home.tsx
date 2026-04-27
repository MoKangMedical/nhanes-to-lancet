import { useAuth } from "@/_core/hooks/useAuth";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { getLoginUrl } from "@/const";
import { 
  FileText, BarChart3, FileSpreadsheet, BookOpen, ArrowRight, 
  Users, Database, Calendar, TrendingUp, ExternalLink 
} from "lucide-react";
import { Link } from "wouter";

export default function Home() {
  const { isAuthenticated, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-background to-secondary/20">
      {/* Header */}
      <header className="border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 sticky top-0 z-50">
        <div className="container flex h-16 items-center justify-between">
          <div className="flex items-center gap-2">
            <BarChart3 className="h-6 w-6 text-primary" />
            <span className="text-xl font-bold">NHANES to Lancet</span>
          </div>
          <div className="flex items-center gap-4">
            {isAuthenticated ? (
              <Link href="/dashboard">
                <Button>进入工作台</Button>
              </Link>
            ) : (
              <Button asChild>
                <a href={getLoginUrl()}>登录</a>
              </Button>
            )}
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="container py-24 space-y-8">
        <div className="max-w-3xl mx-auto text-center space-y-6">
          <h1 className="text-5xl font-bold tracking-tight">
            <span className="text-primary">NHANES to Lancet</span>
            <br />
            智能分析与论文生成平台
          </h1>
          <p className="text-xl text-muted-foreground">
            从研究方案上传到Lancet标准论文生成，全流程自动化。支持生存分析、Cox回归、竞争风险模型，生成符合Lancet杂志要求的表格和图形。
          </p>
          <div className="flex gap-4 justify-center pt-4">
            {isAuthenticated ? (
              <Link href="/projects/new">
                <Button size="lg" className="gap-2">
                  创建新项目 <ArrowRight className="h-4 w-4" />
                </Button>
              </Link>
            ) : (
              <Button size="lg" asChild>
                <a href={getLoginUrl()}>开始使用</a>
              </Button>
            )}
          </div>
        </div>
      </section>

      {/* NHANES Introduction */}
      <section className="container py-16 space-y-8">
        <div className="text-center space-y-4">
          <h2 className="text-3xl font-bold">关于NHANES数据库</h2>
          <p className="text-muted-foreground max-w-2xl mx-auto">
            National Health and Nutrition Examination Survey（美国国家健康与营养调查）是评估美国成人和儿童健康与营养状况的权威数据来源
          </p>
        </div>

        {/* NHANES Stats */}
        <div className="grid md:grid-cols-4 gap-6">
          <StatsCard
            icon={<Users className="h-8 w-8 text-primary" />}
            value="80,000+"
            label="年度参与者"
            description="每两年调查约5,000名参与者"
          />
          <StatsCard
            icon={<Database className="h-8 w-8 text-primary" />}
            value="1,000+"
            label="数据变量"
            description="涵盖人口学、体格检查、实验室检查等"
          />
          <StatsCard
            icon={<Calendar className="h-8 w-8 text-primary" />}
            value="50+"
            label="调查年限"
            description="自1971年持续至今"
          />
          <StatsCard
            icon={<TrendingUp className="h-8 w-8 text-primary" />}
            value="20,000+"
            label="年度发文量"
            description="2024年发表超过20,000篇研究论文"
          />
        </div>

        {/* NHANES Data Coverage */}
        <Card>
          <CardHeader>
            <CardTitle>NHANES数据覆盖范围</CardTitle>
            <CardDescription>全面的健康与营养数据采集</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid md:grid-cols-2 gap-6">
              <div className="space-y-3">
                <h4 className="font-semibold flex items-center gap-2">
                  <div className="w-2 h-2 rounded-full bg-primary"></div>
                  人口学数据
                </h4>
                <ul className="text-sm text-muted-foreground space-y-1 ml-4">
                  <li>• 年龄、性别、种族/民族</li>
                  <li>• 教育程度、家庭收入</li>
                  <li>• 婚姻状况、就业情况</li>
                </ul>
              </div>
              <div className="space-y-3">
                <h4 className="font-semibold flex items-center gap-2">
                  <div className="w-2 h-2 rounded-full bg-primary"></div>
                  体格测量
                </h4>
                <ul className="text-sm text-muted-foreground space-y-1 ml-4">
                  <li>• 身高、体重、BMI</li>
                  <li>• 血压、腰围</li>
                  <li>• 骨密度测量</li>
                </ul>
              </div>
              <div className="space-y-3">
                <h4 className="font-semibold flex items-center gap-2">
                  <div className="w-2 h-2 rounded-full bg-primary"></div>
                  实验室检查
                </h4>
                <ul className="text-sm text-muted-foreground space-y-1 ml-4">
                  <li>• 血脂、血糖、糖化血红蛋白</li>
                  <li>• 肾功能、肝功能</li>
                  <li>• 维生素、矿物质水平</li>
                  <li>• 炎症标志物、激素水平</li>
                </ul>
              </div>
              <div className="space-y-3">
                <h4 className="font-semibold flex items-center gap-2">
                  <div className="w-2 h-2 rounded-full bg-primary"></div>
                  问卷调查
                </h4>
                <ul className="text-sm text-muted-foreground space-y-1 ml-4">
                  <li>• 饮食摄入（24小时膳食回顾）</li>
                  <li>• 体力活动水平</li>
                  <li>• 吸烟、饮酒行为</li>
                  <li>• 慢性疾病史、用药情况</li>
                </ul>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Survey Cycles */}
        <Card>
          <CardHeader>
            <CardTitle>可用调查周期</CardTitle>
            <CardDescription>NHANES采用双年调查设计，持续更新</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-2">
              {[
                "1999-2000", "2001-2002", "2003-2004", "2005-2006", 
                "2007-2008", "2009-2010", "2011-2012", "2013-2014",
                "2015-2016", "2017-2018", "2017-2020", "2021-2023"
              ].map((cycle) => (
                <Badge key={cycle} variant="secondary" className="text-sm">
                  {cycle}
                </Badge>
              ))}
            </div>
            <p className="text-sm text-muted-foreground mt-4">
              注：2017-2020周期因COVID-19疫情调整为3年周期
            </p>
          </CardContent>
        </Card>
      </section>

      {/* Lancet Research Gallery */}
      <section className="container py-16 space-y-8">
        <div className="text-center space-y-4">
          <h2 className="text-3xl font-bold">
            <span className="text-primary">Lancet</span>杂志发表的NHANES研究
          </h2>
          <p className="text-muted-foreground max-w-2xl mx-auto">
            顶级医学期刊The Lancet及其子刊发表的高质量NHANES数据分析研究
          </p>
        </div>

        {/* Research Images Gallery */}
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          <Card className="overflow-hidden hover:shadow-xl transition-shadow">
            <div className="aspect-video bg-muted relative overflow-hidden">
              <img 
                src="/research-images/VoTdpbnLyedW.png" 
                alt="NHANES新指标发文Lancet子刊"
                className="object-cover w-full h-full hover:scale-105 transition-transform duration-300"
              />
            </div>
            <CardHeader>
              <Badge variant="destructive" className="w-fit mb-2">Lancet子刊</Badge>
              <CardTitle className="text-base">社会决定因素与健康结局</CardTitle>
              <CardDescription>
                使用NHANES数据探讨社会决定因素对健康结局的影响，发表于The Lancet Public Health
              </CardDescription>
            </CardHeader>
          </Card>

          <Card className="overflow-hidden hover:shadow-xl transition-shadow">
            <div className="aspect-video bg-muted relative overflow-hidden">
              <img 
                src="/research-images/sHqZ34CPVdok.png" 
                alt="生存曲线分析"
                className="object-cover w-full h-full hover:scale-105 transition-transform duration-300"
              />
            </div>
            <CardHeader>
              <Badge variant="destructive" className="w-fit mb-2">Lancet系列</Badge>
              <CardTitle className="text-base">生存分析与风险预测</CardTitle>
              <CardDescription>
                Kaplan-Meier生存曲线和Cox回归分析，展示NHANES数据在生存分析中的应用
              </CardDescription>
            </CardHeader>
          </Card>

          <Card className="overflow-hidden hover:shadow-xl transition-shadow">
            <div className="aspect-video bg-muted relative overflow-hidden">
              <img 
                src="/research-images/cHfn0YyOv7Lp.png" 
                alt="趋势分析图表"
                className="object-cover w-full h-full hover:scale-105 transition-transform duration-300"
              />
            </div>
            <CardHeader>
              <Badge variant="destructive" className="w-fit mb-2">Lancet子刊</Badge>
              <CardTitle className="text-base">健康指标趋势分析</CardTitle>
              <CardDescription>
                基于NHANES多周期数据的健康指标变化趋势分析，发表于Lancet系列期刊
              </CardDescription>
            </CardHeader>
          </Card>

          <Card className="overflow-hidden hover:shadow-xl transition-shadow">
            <div className="aspect-video bg-muted relative overflow-hidden">
              <img 
                src="/research-images/9ozwCPvA4494.png" 
                alt="膳食指标分析"
                className="object-cover w-full h-full hover:scale-105 transition-transform duration-300"
              />
            </div>
            <CardHeader>
              <Badge variant="destructive" className="w-fit mb-2">一区Top</Badge>
              <CardTitle className="text-base">膳食健康指数研究</CardTitle>
              <CardDescription>
                使用NHANES膳食数据开发新型健康指数，结合Meta分析验证其与健康结局的关联
              </CardDescription>
            </CardHeader>
          </Card>

          <Card className="overflow-hidden hover:shadow-xl transition-shadow">
            <div className="aspect-video bg-muted relative overflow-hidden">
              <img 
                src="/research-images/cCY1OQZdhVN4.png" 
                alt="暴露组学研究"
                className="object-cover w-full h-full hover:scale-105 transition-transform duration-300"
              />
            </div>
            <CardHeader>
              <Badge variant="destructive" className="w-fit mb-2">Nature系列</Badge>
              <CardTitle className="text-base">暴露组学与BMI关联</CardTitle>
              <CardDescription>
                全暴露组关联研究（EWAS），分析多种环境暴露因素与体重指数的关系
              </CardDescription>
            </CardHeader>
          </Card>

          <Card className="overflow-hidden hover:shadow-xl transition-shadow">
            <div className="aspect-video bg-muted relative overflow-hidden">
              <img 
                src="/research-images/aYzFhwDP92e6.png" 
                alt="可穿戴设备数据分析"
                className="object-cover w-full h-full hover:scale-105 transition-transform duration-300"
              />
            </div>
            <CardHeader>
              <Badge variant="destructive" className="w-fit mb-2">Nature系列</Badge>
              <CardTitle className="text-base">可穿戴设备活动数据</CardTitle>
              <CardDescription>
                基于NHANES可穿戴设备加速度计数据的体力活动模式分析，发表于Nature子刊
              </CardDescription>
            </CardHeader>
          </Card>
        </div>
      </section>

      {/* Features */}
      <section className="container py-16">
        <div className="text-center space-y-4 mb-12">
          <h2 className="text-3xl font-bold">平台核心功能</h2>
          <p className="text-muted-foreground max-w-2xl mx-auto">
            从研究设计到Lancet标准论文发表的全流程自动化解决方案
          </p>
        </div>
        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8">
          <FeatureCard
            icon={<FileText className="h-8 w-8 text-primary" />}
            title="智能方案解析"
            description="上传Word研究方案，自动提取PICO/PECO要素，识别研究变量和NHANES数据适配性"
          />
          <FeatureCard
            icon={<BarChart3 className="h-8 w-8 text-primary" />}
            title="R语言统计分析"
            description="Kaplan-Meier生存曲线、Cox回归、Fine-Gray竞争风险模型，专业统计分析工具"
          />
          <FeatureCard
            icon={<FileSpreadsheet className="h-8 w-8 text-primary" />}
            title="Lancet标准输出"
            description="自动生成符合Lancet杂志要求的基线特征表、回归结果表、生存曲线和森林图"
          />
          <FeatureCard
            icon={<BookOpen className="h-8 w-8 text-primary" />}
            title="学术论文撰写"
            description="集成PubMed文献搜索，使用AI生成完整的学术论文，包括摘要、引言、方法、结果、讨论和结论"
          />
        </div>
      </section>

      {/* Recent Publications */}
      <section className="container py-16 space-y-8">
        <div className="text-center space-y-4">
          <h2 className="text-3xl font-bold">NHANES研究文献精选</h2>
          <p className="text-muted-foreground max-w-2xl mx-auto">
            <span className="text-primary font-semibold">Lancet</span>及其他顶级医学期刊发表的NHANES研究成果
          </p>
        </div>

        <div className="space-y-6">
          {/* Lancet Publications */}
          <div className="space-y-4">
            <h3 className="text-xl font-semibold flex items-center gap-2">
              <Badge variant="destructive">Lancet系列</Badge>
              顶级期刊发表
            </h3>
            <div className="grid md:grid-cols-2 gap-4">
              <PublicationCard
                title="Characterising the relationships between physiological indicators and all-cause mortality"
                journal="The Lancet Healthy Longevity"
                year="2021"
                authors="Chen et al."
                description="使用NHANES 1999-2014数据，分析27个生理指标与全因死亡率的线性和非线性关系，为临床风险评估提供依据。"
                url="https://www.thelancet.com/journals/lanhl/article/PIIS2666-7568(21)00212-9/fulltext"
              />
              <PublicationCard
                title="Social determinants of health and premature death among adults in the USA"
                journal="The Lancet Public Health"
                year="2023"
                authors="Bassett et al."
                description="研究社会决定因素对美国成人过早死亡的贡献，揭示种族和民族差异的深层原因。"
                url="https://www.thelancet.com/journals/lanpub/article/PIIS2468-2667(23)00081-6/fulltext"
              />
              <PublicationCard
                title="Representative oral microbiome data for the US population"
                journal="The Lancet Microbe"
                year="2023"
                authors="Deo et al."
                description="首次提供美国人群代表性口腔微生物组数据，为口腔健康研究奠定基础。"
                url="https://www.thelancet.com/journals/lanmic/article/PIIS2666-5247(22)00333-0/fulltext"
              />
              <PublicationCard
                title="Dietary sodium intake and mortality: NHANES I"
                journal="The Lancet"
                year="1997"
                authors="Alderman et al."
                description="经典研究，评估膳食钠摄入量与全因死亡率和心血管疾病死亡率的关系。"
                url="https://www.thelancet.com/journals/lancet/article/PIIS0140-6736(97)09092-2/fulltext"
              />
            </div>
          </div>

          {/* Other High-Impact Journals */}
          <div className="space-y-4">
            <h3 className="text-xl font-semibold flex items-center gap-2">
              <Badge>其他顶级期刊</Badge>
              最新研究成果
            </h3>
            <div className="grid md:grid-cols-2 gap-4">
              <PublicationCard
                title="Metabolic health and cardiovascular disease across BMI categories"
                journal="BMC Public Health"
                year="2025"
                authors="Tu et al."
                description="使用NHANES 2017-2023数据，探讨不同BMI类别中代谢健康与心血管疾病的关系。"
                url="https://pmc.ncbi.nlm.nih.gov/articles/PMC12317518/"
              />
              <PublicationCard
                title="Balancing Efficiency and Equity in Population-Wide CKD Screening"
                journal="JAMA Network Open"
                year="2025"
                authors="Cusick et al."
                description="基于NHANES数据的成本效益分析，评估人群慢性肾病筛查策略的效率与公平性。"
                url="https://jamanetwork.com/journals/jamanetworkopen/fullarticle/2832754"
              />
              <PublicationCard
                title="Interpretable machine learning for cardiovascular risk prediction"
                journal="PLOS ONE"
                year="2025"
                authors="Ahiduzzaman et al."
                description="使用NHANES 2017-2023数据开发可解释的机器学习模型，预测心血管疾病风险。"
                url="https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0335915"
              />
              <PublicationCard
                title="Trends in body mass index, overweight and obesity among adults in the USA"
                journal="BMJ Open"
                year="2022"
                authors="Li et al."
                description="分析NHANES 2003-2018数据，揭示美国成人BMI、超重和肥胖的趋势变化。"
                url="https://bmjopen.bmj.com/content/12/12/e065425.abstract"
              />
            </div>
          </div>
        </div>

        <div className="text-center pt-8">
          <p className="text-sm text-muted-foreground">
            数据来源：PubMed、CDC NHANES官网 | 更新时间：2026年1月
          </p>
        </div>
      </section>

      {/* Workflow */}
      <section className="container py-16">
        <div className="max-w-4xl mx-auto space-y-8">
          <h2 className="text-3xl font-bold text-center">工作流程</h2>
          <div className="grid gap-6">
            <WorkflowStep
              number={1}
              title="上传研究方案"
              description="上传Word格式的研究方案文档"
            />
            <WorkflowStep
              number={2}
              title="自动解析与变量映射"
              description="AI自动提取PICO要素，映射NHANES变量，用户确认后进入下一步"
            />
            <WorkflowStep
              number={3}
              title="数据获取与分析"
              description="自动下载NHANES数据，执行R语言统计分析"
            />
            <WorkflowStep
              number={4}
              title="生成Lancet标准论文与报告"
              description="生成Lancet风格的表格、图形和完整学术论文，一键下载"
            />
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t py-8 mt-16">
        <div className="container text-center text-sm text-muted-foreground space-y-2">
          <p className="font-semibold text-primary">NHANES to Lancet 智能分析与论文生成平台 © 2026</p>
          <p>数据来源：CDC National Center for Health Statistics</p>
          <p className="text-xs">本平台生成的分析结果和论文遵循The Lancet杂志格式标准</p>
        </div>
      </footer>
    </div>
  );
}

function StatsCard({ icon, value, label, description }: { 
  icon: React.ReactNode; 
  value: string; 
  label: string;
  description: string;
}) {
  return (
    <Card>
      <CardContent className="pt-6 space-y-3">
        <div className="flex items-center justify-center w-12 h-12 rounded-lg bg-primary/10 mx-auto">
          {icon}
        </div>
        <div className="text-center space-y-1">
          <div className="text-3xl font-bold text-primary">{value}</div>
          <div className="font-semibold">{label}</div>
          <div className="text-xs text-muted-foreground">{description}</div>
        </div>
      </CardContent>
    </Card>
  );
}

function FeatureCard({ icon, title, description }: { 
  icon: React.ReactNode; 
  title: string; 
  description: string;
}) {
  return (
    <div className="bg-card border rounded-lg p-6 space-y-3 hover:shadow-lg transition-shadow">
      <div className="flex items-center justify-center w-12 h-12 rounded-lg bg-primary/10">
        {icon}
      </div>
      <h3 className="text-lg font-semibold">{title}</h3>
      <p className="text-sm text-muted-foreground">{description}</p>
    </div>
  );
}

function PublicationCard({ title, journal, year, authors, description, url }: {
  title: string;
  journal: string;
  year: string;
  authors: string;
  description: string;
  url: string;
}) {
  return (
    <Card className="hover:shadow-lg transition-shadow">
      <CardHeader>
        <div className="space-y-2">
          <CardTitle className="text-base leading-tight">{title}</CardTitle>
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <Badge variant="outline" className="text-xs">{journal}</Badge>
            <span>•</span>
            <span>{year}</span>
            <span>•</span>
            <span>{authors}</span>
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-3">
        <CardDescription className="text-sm">{description}</CardDescription>
        <Button variant="outline" size="sm" asChild>
          <a href={url} target="_blank" rel="noopener noreferrer" className="gap-2">
            查看原文 <ExternalLink className="h-3 w-3" />
          </a>
        </Button>
      </CardContent>
    </Card>
  );
}

function WorkflowStep({ number, title, description }: { 
  number: number; 
  title: string; 
  description: string;
}) {
  return (
    <div className="flex gap-4 items-start">
      <div className="flex-shrink-0 w-10 h-10 rounded-full bg-primary text-primary-foreground flex items-center justify-center font-bold">
        {number}
      </div>
      <div className="space-y-1 pt-1">
        <h3 className="text-lg font-semibold">{title}</h3>
        <p className="text-muted-foreground">{description}</p>
      </div>
    </div>
  );
}
