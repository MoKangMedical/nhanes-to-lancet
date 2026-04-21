import { invokeLLM } from "./_core/llm";
import { PubMedArticle } from "./pubmedSearch";

export interface PaperSections {
  title: string;
  abstract: string;
  introduction: string;
  methods: string;
  results: string;
  discussion: string;
  conclusion: string;
  references: PubMedArticle[];
}

/**
 * Generate complete academic paper in Lancet style
 */
export async function generateLancetPaper(params: {
  projectTitle: string;
  pico: {
    population?: string;
    intervention?: string;
    exposure?: string;
    outcome?: string;
  };
  methods: string[];
  analysisResults: {
    baselineTable?: string;
    survivalAnalysis?: string;
    coxRegression?: string;
    competingRisk?: string;
  };
  references: PubMedArticle[];
}): Promise<PaperSections> {
  try {
    // Generate title
    const title = await generateTitle(params.projectTitle, params.pico);

    // Generate abstract
    const abstract = await generateAbstract(params.pico, params.analysisResults);

    // Generate introduction
    const introduction = await generateIntroduction(params.pico, params.references);

    // Generate methods section
    const methods = await generateMethods(params.pico, params.methods);

    // Generate results section
    const results = await generateResults(params.analysisResults);

    // Generate discussion
    const discussion = await generateDiscussion(params.pico, params.analysisResults, params.references);

    // Generate conclusion
    const conclusion = await generateConclusion(params.pico, params.analysisResults);

    return {
      title,
      abstract,
      introduction,
      methods,
      results,
      discussion,
      conclusion,
      references: params.references
    };
  } catch (error) {
    console.error("[PaperGenerator] Failed to generate paper:", error);
    throw new Error("Failed to generate academic paper");
  }
}

async function generateTitle(projectTitle: string, pico: any): Promise<string> {
  const response = await invokeLLM({
    messages: [
      {
        role: "system",
        content: "You are an expert medical writer. Generate concise, informative titles for academic papers in Lancet style (max 150 characters)."
      },
      {
        role: "user",
        content: `Generate a title for a research paper with:
Project: ${projectTitle}
Population: ${pico.population || "Not specified"}
Exposure/Intervention: ${pico.intervention || pico.exposure || "Not specified"}
Outcome: ${pico.outcome || "Not specified"}

The title should be clear, specific, and follow Lancet journal style.`
      }
    ]
  });

  return response.choices[0]?.message?.content?.toString().trim() || projectTitle;
}

async function generateAbstract(pico: any, results: any): Promise<string> {
  const response = await invokeLLM({
    messages: [
      {
        role: "system",
        content: `You are an expert medical writer. Generate structured abstracts in Lancet style with these sections:
- Background (2-3 sentences)
- Methods (2-3 sentences)
- Findings (3-4 sentences with key statistics)
- Interpretation (2-3 sentences)

Total word count: 250-300 words.`
      },
      {
        role: "user",
        content: `Generate an abstract for a study using NHANES data:

Population: ${pico.population || "Not specified"}
Exposure: ${pico.exposure || pico.intervention || "Not specified"}
Outcome: ${pico.outcome || "Not specified"}

Analysis Results Summary:
${JSON.stringify(results, null, 2)}

Write a structured abstract following Lancet format.`
      }
    ]
  });

  return response.choices[0]?.message?.content?.toString().trim() || "";
}

async function generateIntroduction(pico: any, references: PubMedArticle[]): Promise<string> {
  const refContext = references.slice(0, 5).map(r => `${r.title} (${r.authors}, ${r.year})`).join("\n");

  const response = await invokeLLM({
    messages: [
      {
        role: "system",
        content: `You are an expert medical writer. Generate introduction sections for academic papers in Lancet style.

Structure:
1. Background and epidemiology (1-2 paragraphs)
2. Current knowledge gaps (1 paragraph)
3. Study objectives and rationale (1 paragraph)

Total: 3-4 paragraphs, approximately 400-500 words.`
      },
      {
        role: "user",
        content: `Write an introduction for a study:

Population: ${pico.population || "Not specified"}
Exposure: ${pico.exposure || pico.intervention || "Not specified"}
Outcome: ${pico.outcome || "Not specified"}

Relevant literature context:
${refContext}

Write a compelling introduction that establishes the importance of this research.`
      }
    ]
  });

  return response.choices[0]?.message?.content?.toString().trim() || "";
}

async function generateMethods(pico: any, methods: string[]): Promise<string> {
  const response = await invokeLLM({
    messages: [
      {
        role: "system",
        content: `You are an expert medical writer. Generate methods sections for academic papers using NHANES data in Lancet style.

Include:
1. Study design and data source (NHANES)
2. Study population and inclusion/exclusion criteria
3. Variable definitions
4. Statistical analysis methods
5. Ethical considerations

Be specific about NHANES cycles used and statistical methods.`
      },
      {
        role: "user",
        content: `Write a methods section for:

Population: ${pico.population || "Not specified"}
Exposure: ${pico.exposure || pico.intervention || "Not specified"}
Outcome: ${pico.outcome || "Not specified"}

Statistical Methods: ${methods.join(", ")}

Describe the methodology clearly and comprehensively.`
      }
    ]
  });

  return response.choices[0]?.message?.content?.toString().trim() || "";
}

async function generateResults(results: any): Promise<string> {
  const response = await invokeLLM({
    messages: [
      {
        role: "system",
        content: `You are an expert medical writer. Generate results sections for academic papers in Lancet style.

Structure:
1. Study population characteristics
2. Primary outcome results
3. Secondary analyses
4. Subgroup analyses (if applicable)

Present results objectively with specific statistics. Reference tables and figures.`
      },
      {
        role: "user",
        content: `Write a results section based on these analysis outputs:

${JSON.stringify(results, null, 2)}

Present the findings clearly, referencing "Table 1" for baseline characteristics, "Figure 1" for survival curves, etc.`
      }
    ]
  });

  return response.choices[0]?.message?.content?.toString().trim() || "";
}

async function generateDiscussion(pico: any, results: any, references: PubMedArticle[]): Promise<string> {
  const refContext = references.slice(0, 5).map(r => `${r.title} (${r.authors}, ${r.year})`).join("\n");

  const response = await invokeLLM({
    messages: [
      {
        role: "system",
        content: `You are an expert medical writer. Generate discussion sections for academic papers in Lancet style.

Structure:
1. Summary of key findings (1 paragraph)
2. Comparison with existing literature (2-3 paragraphs)
3. Potential mechanisms and clinical implications (1-2 paragraphs)
4. Strengths and limitations (1 paragraph)

Total: 5-7 paragraphs, approximately 600-800 words.`
      },
      {
        role: "user",
        content: `Write a discussion section for:

Study focus:
- Population: ${pico.population || "Not specified"}
- Exposure: ${pico.exposure || pico.intervention || "Not specified"}
- Outcome: ${pico.outcome || "Not specified"}

Key findings:
${JSON.stringify(results, null, 2)}

Relevant literature:
${refContext}

Discuss the findings in context of existing knowledge and their clinical implications.`
      }
    ]
  });

  return response.choices[0]?.message?.content?.toString().trim() || "";
}

async function generateConclusion(pico: any, results: any): Promise<string> {
  const response = await invokeLLM({
    messages: [
      {
        role: "system",
        content: "You are an expert medical writer. Generate concise conclusion sections (1-2 paragraphs, 100-150 words) for academic papers in Lancet style."
      },
      {
        role: "user",
        content: `Write a conclusion for a study on:

Population: ${pico.population || "Not specified"}
Exposure: ${pico.exposure || pico.intervention || "Not specified"}
Outcome: ${pico.outcome || "Not specified"}

Key findings summary:
${JSON.stringify(results, null, 2)}

Provide a clear, impactful conclusion with clinical or public health implications.`
      }
    ]
  });

  return response.choices[0]?.message?.content?.toString().trim() || "";
}

/**
 * Combine all sections into a complete Markdown paper
 */
export function assemblePaper(sections: PaperSections): string {
  let paper = `# ${sections.title}\n\n`;

  paper += `## Abstract\n\n${sections.abstract}\n\n`;
  
  paper += `## Introduction\n\n${sections.introduction}\n\n`;
  
  paper += `## Methods\n\n${sections.methods}\n\n`;
  
  paper += `## Results\n\n${sections.results}\n\n`;
  
  paper += `## Discussion\n\n${sections.discussion}\n\n`;
  
  paper += `## Conclusion\n\n${sections.conclusion}\n\n`;
  
  // Add references
  paper += `## References\n\n`;
  sections.references.forEach((ref, index) => {
    const doiPart = ref.doi ? ` doi: ${ref.doi}` : "";
    paper += `${index + 1}. ${ref.authors}. ${ref.title}. *${ref.journal}*. ${ref.year};${doiPart}\n\n`;
  });

  return paper;
}
