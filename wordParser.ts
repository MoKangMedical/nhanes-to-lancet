import mammoth from "mammoth";
import { invokeLLM } from "./_core/llm";

export interface ParsedProposal {
  rawText: string;
  pico: {
    population?: string;
    intervention?: string;
    comparison?: string;
    outcome?: string;
    exposure?: string;
  };
  variables: Array<{
    category: string;
    name: string;
    description?: string;
  }>;
  statisticalMethods: string[];
  nhanesCompatibility: {
    compatible: boolean;
    reason: string;
    suggestedCycles?: string[];
  };
}

/**
 * Parse Word document and extract text content
 */
export async function parseWordDocument(buffer: Buffer): Promise<string> {
  try {
    const result = await mammoth.extractRawText({ buffer });
    return result.value;
  } catch (error) {
    console.error("[WordParser] Failed to parse document:", error);
    throw new Error("Failed to parse Word document");
  }
}

/**
 * Use LLM to extract PICO/PECO elements and variables from research proposal
 */
export async function extractResearchElements(proposalText: string): Promise<ParsedProposal> {
  try {
    const response = await invokeLLM({
      messages: [
        {
          role: "system",
          content: `You are an expert epidemiologist and biostatistician. Analyze research proposals and extract PICO/PECO elements, variables, and assess NHANES data compatibility.

NHANES (National Health and Nutrition Examination Survey) is a US population health survey with:
- Demographics (age, sex, race, education, income)
- Physical measurements (height, weight, blood pressure)
- Laboratory tests (cholesterol, glucose, kidney function)
- Questionnaires (diet, physical activity, smoking, medical history)
- Available cycles: 1999-2000, 2001-2002, ..., 2017-2018 (biennial)

Extract information in JSON format.`
        },
        {
          role: "user",
          content: `Analyze this research proposal and extract:

1. PICO/PECO elements:
   - Population: target population
   - Intervention/Exposure: what is being studied
   - Comparison: control or comparison group (if applicable)
   - Outcome: primary outcome of interest

2. Variables needed:
   - Categorize as: exposure, outcome, covariate, confounder
   - List variable names and descriptions

3. Statistical methods mentioned

4. NHANES compatibility:
   - Is this study feasible with NHANES data?
   - Which NHANES cycles would be most appropriate?
   - Any limitations or concerns?

Research Proposal:
${proposalText}

Respond in JSON format only.`
        }
      ],
      response_format: {
        type: "json_schema",
        json_schema: {
          name: "research_proposal_analysis",
          strict: true,
          schema: {
            type: "object",
            properties: {
              pico: {
                type: "object",
                properties: {
                  population: { type: "string" },
                  intervention: { type: "string" },
                  comparison: { type: "string" },
                  outcome: { type: "string" },
                  exposure: { type: "string" }
                },
                required: [],
                additionalProperties: false
              },
              variables: {
                type: "array",
                items: {
                  type: "object",
                  properties: {
                    category: { type: "string" },
                    name: { type: "string" },
                    description: { type: "string" }
                  },
                  required: ["category", "name"],
                  additionalProperties: false
                }
              },
              statisticalMethods: {
                type: "array",
                items: { type: "string" }
              },
              nhanesCompatibility: {
                type: "object",
                properties: {
                  compatible: { type: "boolean" },
                  reason: { type: "string" },
                  suggestedCycles: {
                    type: "array",
                    items: { type: "string" }
                  }
                },
                required: ["compatible", "reason"],
                additionalProperties: false
              }
            },
            required: ["pico", "variables", "statisticalMethods", "nhanesCompatibility"],
            additionalProperties: false
          }
        }
      }
    });

    const content = response.choices[0]?.message?.content;
    if (!content || typeof content !== 'string') {
      throw new Error("No response from LLM");
    }

    const parsed = JSON.parse(content);
    
    return {
      rawText: proposalText,
      pico: parsed.pico || {},
      variables: parsed.variables || [],
      statisticalMethods: parsed.statisticalMethods || [],
      nhanesCompatibility: parsed.nhanesCompatibility || {
        compatible: false,
        reason: "Unable to assess compatibility"
      }
    };
  } catch (error) {
    console.error("[WordParser] Failed to extract research elements:", error);
    throw new Error("Failed to analyze research proposal");
  }
}

/**
 * Map research variables to NHANES variable codes
 */
export async function mapToNHANESVariables(
  variables: Array<{ category: string; name: string; description?: string }>,
  suggestedCycles?: string[]
): Promise<Array<{
  category: string;
  proposalVariable: string;
  nhanesVariable: string;
  nhanesDataset: string;
  nhanesCycle: string;
  confidence: string;
}>> {
  try {
    const response = await invokeLLM({
      messages: [
        {
          role: "system",
          content: `You are an NHANES data expert. Map research variables to specific NHANES variable codes and datasets.

Common NHANES datasets:
- DEMO: Demographics
- BMX: Body Measurements
- BPX: Blood Pressure
- TCHOL: Total Cholesterol
- GLU: Glucose
- ALB_CR: Albumin & Creatinine
- SMQ: Smoking
- ALQ: Alcohol Use
- PAQ: Physical Activity
- DIQ: Diabetes
- MCQ: Medical Conditions

Provide specific variable codes (e.g., RIAGENDR for gender, RIDAGEYR for age).`
        },
        {
          role: "user",
          content: `Map these research variables to NHANES variables:

Variables: ${JSON.stringify(variables, null, 2)}

Suggested NHANES cycles: ${suggestedCycles?.join(", ") || "Any recent cycle"}

For each variable, provide:
- NHANES variable code
- Dataset name
- Recommended cycle
- Confidence level (high/medium/low)

Respond in JSON format.`
        }
      ],
      response_format: {
        type: "json_schema",
        json_schema: {
          name: "nhanes_variable_mapping",
          strict: true,
          schema: {
            type: "object",
            properties: {
              mappings: {
                type: "array",
                items: {
                  type: "object",
                  properties: {
                    category: { type: "string" },
                    proposalVariable: { type: "string" },
                    nhanesVariable: { type: "string" },
                    nhanesDataset: { type: "string" },
                    nhanesCycle: { type: "string" },
                    confidence: { type: "string" }
                  },
                  required: ["category", "proposalVariable", "nhanesVariable", "nhanesDataset", "nhanesCycle", "confidence"],
                  additionalProperties: false
                }
              }
            },
            required: ["mappings"],
            additionalProperties: false
          }
        }
      }
    });

    const content = response.choices[0]?.message?.content;
    if (!content || typeof content !== 'string') {
      throw new Error("No response from LLM");
    }

    const parsed = JSON.parse(content);
    return parsed.mappings || [];
  } catch (error) {
    console.error("[WordParser] Failed to map NHANES variables:", error);
    throw new Error("Failed to map variables to NHANES");
  }
}
