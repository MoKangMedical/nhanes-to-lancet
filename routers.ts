import { TRPCError } from "@trpc/server";
import { z } from "zod";
import { COOKIE_NAME } from "@shared/const";
import { getSessionCookieOptions } from "./_core/cookies";
import { systemRouter } from "./_core/systemRouter";
import { publicProcedure, protectedProcedure, router } from "./_core/trpc";
import { storagePut } from "./storage";
import { 
  createProject, getProjectById, getProjectsByUserId, updateProject,
  createVariableMapping, getVariableMappingsByProjectId, updateVariableMapping,
  createAnalysisTask, getAnalysisTasksByProjectId, updateAnalysisTask,
  createFile, getFilesByProjectId,
  createPaper, getPaperByProjectId, updatePaper
} from "./db";
import { parseWordDocument, extractResearchElements, mapToNHANESVariables } from "./wordParser";
import { searchPubMed, generateLiteratureQueries } from "./pubmedSearch";
import { generateLancetPaper, assemblePaper } from "./paperGenerator";
import { nanoid } from "nanoid";

export const appRouter = router({
  system: systemRouter,
  auth: router({
    me: publicProcedure.query(opts => opts.ctx.user),
    logout: publicProcedure.mutation(({ ctx }) => {
      const cookieOptions = getSessionCookieOptions(ctx.req);
      ctx.res.clearCookie(COOKIE_NAME, { ...cookieOptions, maxAge: -1 });
      return {
        success: true,
      } as const;
    }),
  }),

  // Project management
  projects: router({
    list: protectedProcedure.query(async ({ ctx }) => {
      return getProjectsByUserId(ctx.user.id);
    }),

    get: protectedProcedure
      .input(z.object({ id: z.number() }))
      .query(async ({ input, ctx }) => {
        const project = await getProjectById(input.id);
        if (!project) {
          throw new TRPCError({ code: "NOT_FOUND", message: "Project not found" });
        }
        if (project.userId !== ctx.user.id) {
          throw new TRPCError({ code: "FORBIDDEN", message: "Access denied" });
        }
        return project;
      }),

    create: protectedProcedure
      .input(z.object({
        title: z.string(),
        description: z.string().optional(),
      }))
      .mutation(async ({ input, ctx }) => {
        const project = await createProject({
          userId: ctx.user.id,
          title: input.title,
          description: input.description,
          status: "draft"
        });
        return project;
      }),

    uploadProposal: protectedProcedure
      .input(z.object({
        projectId: z.number(),
        fileName: z.string(),
        fileData: z.string(), // base64 encoded
      }))
      .mutation(async ({ input, ctx }) => {
        const project = await getProjectById(input.projectId);
        if (!project || project.userId !== ctx.user.id) {
          throw new TRPCError({ code: "FORBIDDEN" });
        }

        // Decode base64 and upload to S3
        const buffer = Buffer.from(input.fileData, "base64");
        const fileKey = `projects/${input.projectId}/proposal-${nanoid()}.docx`;
        const { url } = await storagePut(fileKey, buffer, "application/vnd.openxmlformats-officedocument.wordprocessingml.document");

        // Save file record
        await createFile({
          projectId: input.projectId,
          userId: ctx.user.id,
          fileType: "proposal",
          fileName: input.fileName,
          fileKey,
          fileUrl: url,
          mimeType: "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
          fileSize: buffer.length
        });

        // Update project
        await updateProject(input.projectId, {
          proposalFileKey: fileKey,
          proposalFileUrl: url,
          status: "parsing"
        });

        // Parse document in background (simplified - should use job queue)
        parseProposalBackground(input.projectId, buffer, ctx.user.id).catch(console.error);

        return { success: true, fileUrl: url };
      }),

    getVariables: protectedProcedure
      .input(z.object({ projectId: z.number() }))
      .query(async ({ input, ctx }) => {
        const project = await getProjectById(input.projectId);
        if (!project || project.userId !== ctx.user.id) {
          throw new TRPCError({ code: "FORBIDDEN" });
        }
        return getVariableMappingsByProjectId(input.projectId);
      }),

    confirmVariable: protectedProcedure
      .input(z.object({
        mappingId: z.number(),
        confirmed: z.boolean(),
      }))
      .mutation(async ({ input }) => {
        await updateVariableMapping(input.mappingId, { confirmed: input.confirmed });
        return { success: true };
      }),

    getAnalysisTasks: protectedProcedure
      .input(z.object({ projectId: z.number() }))
      .query(async ({ input, ctx }) => {
        const project = await getProjectById(input.projectId);
        if (!project || project.userId !== ctx.user.id) {
          throw new TRPCError({ code: "FORBIDDEN" });
        }
        return getAnalysisTasksByProjectId(input.projectId);
      }),

    getFiles: protectedProcedure
      .input(z.object({ projectId: z.number() }))
      .query(async ({ input, ctx }) => {
        const project = await getProjectById(input.projectId);
        if (!project || project.userId !== ctx.user.id) {
          throw new TRPCError({ code: "FORBIDDEN" });
        }
        return getFilesByProjectId(input.projectId);
      }),

    getPaper: protectedProcedure
      .input(z.object({ projectId: z.number() }))
      .query(async ({ input, ctx }) => {
        const project = await getProjectById(input.projectId);
        if (!project || project.userId !== ctx.user.id) {
          throw new TRPCError({ code: "FORBIDDEN" });
        }
        return getPaperByProjectId(input.projectId);
      }),

    generatePaper: protectedProcedure
      .input(z.object({ projectId: z.number() }))
      .mutation(async ({ input, ctx }) => {
        const project = await getProjectById(input.projectId);
        if (!project || project.userId !== ctx.user.id) {
          throw new TRPCError({ code: "FORBIDDEN" });
        }

        // Search literature
        const queries = generateLiteratureQueries(project.picoData || {});
        const references = await searchPubMed(queries[0] || "NHANES survival analysis", 15);

        // Generate paper sections
        const sections = await generateLancetPaper({
          projectTitle: project.title,
          pico: project.picoData || {},
          methods: ["Kaplan-Meier", "Cox regression"],
          analysisResults: {
            baselineTable: "See Table 1",
            survivalAnalysis: "See Figure 1",
            coxRegression: "See Table 2"
          },
          references
        });

        const fullContent = assemblePaper(sections);

        // Save paper to database
        const existingPaper = await getPaperByProjectId(input.projectId);
        if (existingPaper) {
          await updatePaper(existingPaper.id, {
            ...sections,
            fullContent,
            references: references as any
          });
        } else {
          await createPaper({
            projectId: input.projectId,
            userId: ctx.user.id,
            ...sections,
            fullContent,
            references: references as any
          });
        }

        return { success: true, content: fullContent };
      }),
  }),
});

export type AppRouter = typeof appRouter;

// Background parsing function
async function parseProposalBackground(projectId: number, buffer: Buffer, userId: number) {
  try {
    // Parse Word document
    const text = await parseWordDocument(buffer);
    
    // Extract research elements
    const parsed = await extractResearchElements(text);

    // Update project with PICO data
    await updateProject(projectId, {
      picoData: parsed.pico as any,
      status: "parsed"
    });

    // Map variables to NHANES
    const mappings = await mapToNHANESVariables(
      parsed.variables,
      parsed.nhanesCompatibility.suggestedCycles
    );

    // Save variable mappings
    for (const mapping of mappings) {
      await createVariableMapping({
        projectId,
        category: mapping.category,
        proposalVariable: mapping.proposalVariable,
        nhanesVariable: mapping.nhanesVariable,
        nhanesDataset: mapping.nhanesDataset,
        nhanesCycle: mapping.nhanesCycle,
        confirmed: false
      });
    }

    // Update status
    await updateProject(projectId, { status: "mapping" });
  } catch (error) {
    console.error("[ParseProposal] Background parsing failed:", error);
    await updateProject(projectId, { status: "failed" });
  }
}
