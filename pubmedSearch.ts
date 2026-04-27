import axios from "axios";

export interface PubMedArticle {
  pmid: string;
  title: string;
  authors: string;
  journal: string;
  year: string;
  doi?: string;
  abstract?: string;
}

/**
 * Search PubMed for relevant articles
 */
export async function searchPubMed(
  query: string,
  maxResults: number = 10
): Promise<PubMedArticle[]> {
  try {
    // Step 1: Search for PMIDs
    const searchUrl = `https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi`;
    const searchParams = {
      db: "pubmed",
      term: query,
      retmax: maxResults,
      retmode: "json"
    };

    const searchResponse = await axios.get(searchUrl, { params: searchParams });
    const pmids = searchResponse.data?.esearchresult?.idlist || [];

    if (pmids.length === 0) {
      return [];
    }

    // Step 2: Fetch article details
    const fetchUrl = `https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi`;
    const fetchParams = {
      db: "pubmed",
      id: pmids.join(","),
      retmode: "json"
    };

    const fetchResponse = await axios.get(fetchUrl, { params: fetchParams });
    const articles: PubMedArticle[] = [];

    for (const pmid of pmids) {
      const articleData = fetchResponse.data?.result?.[pmid];
      if (!articleData) continue;

      // Extract authors
      const authors = articleData.authors
        ?.slice(0, 3)
        .map((a: { name: string }) => a.name)
        .join(", ") || "Unknown";

      articles.push({
        pmid,
        title: articleData.title || "No title",
        authors: authors + (articleData.authors?.length > 3 ? ", et al." : ""),
        journal: articleData.fulljournalname || articleData.source || "Unknown",
        year: articleData.pubdate?.split(" ")[0] || "Unknown",
        doi: articleData.elocationid?.replace("doi: ", "") || undefined
      });
    }

    return articles;
  } catch (error) {
    console.error("[PubMed] Search failed:", error);
    return [];
  }
}

/**
 * Get article abstract by PMID
 */
export async function getArticleAbstract(pmid: string): Promise<string | null> {
  try {
    const url = `https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi`;
    const params = {
      db: "pubmed",
      id: pmid,
      retmode: "xml"
    };

    const response = await axios.get(url, { params });
    const xmlData = response.data;

    // Simple XML parsing to extract abstract
    const abstractMatch = xmlData.match(/<AbstractText[^>]*>([\s\S]*?)<\/AbstractText>/);
    if (abstractMatch && abstractMatch[1]) {
      // Remove XML tags
      return abstractMatch[1].replace(/<[^>]+>/g, "").trim();
    }

    return null;
  } catch (error) {
    console.error(`[PubMed] Failed to fetch abstract for PMID ${pmid}:`, error);
    return null;
  }
}

/**
 * Generate literature search queries based on PICO elements
 */
export function generateLiteratureQueries(pico: {
  population?: string;
  intervention?: string;
  exposure?: string;
  outcome?: string;
}): string[] {
  const queries: string[] = [];

  // Main query combining all elements
  const mainTerms: string[] = [];
  if (pico.population) mainTerms.push(pico.population);
  if (pico.intervention) mainTerms.push(pico.intervention);
  if (pico.exposure) mainTerms.push(pico.exposure);
  if (pico.outcome) mainTerms.push(pico.outcome);

  if (mainTerms.length > 0) {
    queries.push(mainTerms.join(" AND "));
  }

  // Add NHANES-specific query
  if (mainTerms.length > 0) {
    queries.push(`${mainTerms.join(" AND ")} AND NHANES`);
  }

  // Add survival analysis query if relevant
  if (pico.outcome) {
    queries.push(`${pico.outcome} AND survival analysis`);
  }

  return queries;
}

/**
 * Format citation in Vancouver style (commonly used in medical journals)
 */
export function formatCitation(article: PubMedArticle, index: number): string {
  const doiPart = article.doi ? ` doi: ${article.doi}` : "";
  return `${index}. ${article.authors}. ${article.title}. ${article.journal}. ${article.year};${doiPart}`;
}
