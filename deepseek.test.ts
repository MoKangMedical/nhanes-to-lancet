import { describe, expect, it } from "vitest";
import { invokeLLM } from "./_core/llm";

describe("DeepSeek API Integration", () => {
  it("should successfully call DeepSeek API with valid credentials", async () => {
    // Simple test to verify API key works
    const response = await invokeLLM({
      messages: [
        {
          role: "user",
          content: "Say 'API test successful' if you can read this message."
        }
      ]
    });

    expect(response).toBeDefined();
    expect(response.choices).toBeDefined();
    expect(response.choices.length).toBeGreaterThan(0);
    expect(response.choices[0]?.message?.content).toBeDefined();
    
    const content = response.choices[0]?.message?.content;
    expect(typeof content === 'string' || Array.isArray(content)).toBe(true);
    
    console.log("DeepSeek API test passed. Response:", content);
  }, 30000); // 30 second timeout for API call

  it("should extract structured data using JSON schema", async () => {
    const response = await invokeLLM({
      messages: [
        {
          role: "system",
          content: "You are a helpful assistant that extracts information."
        },
        {
          role: "user",
          content: "Extract the name and age from: 'John is 30 years old.'"
        }
      ],
      response_format: {
        type: "json_schema",
        json_schema: {
          name: "person_info",
          strict: true,
          schema: {
            type: "object",
            properties: {
              name: { type: "string" },
              age: { type: "number" }
            },
            required: ["name", "age"],
            additionalProperties: false
          }
        }
      }
    });

    expect(response.choices[0]?.message?.content).toBeDefined();
    const content = response.choices[0]?.message?.content;
    expect(typeof content).toBe('string');
    
    if (typeof content === 'string') {
      const parsed = JSON.parse(content);
      expect(parsed.name).toBeDefined();
      expect(parsed.age).toBeDefined();
      expect(typeof parsed.age).toBe('number');
      
      console.log("Structured extraction test passed. Parsed:", parsed);
    }
  }, 30000);
});
