# Multi‑Agent AI Research Platform

A full‑stack, cloud‑ready research tool with:

- **Frontend:** Next.js + Material UI  
- **Backend:** FastAPI (local) / AWS Lambda‑ready (pending)  
- **Vector DB:** Elasticsearch  
- **Agents:** LangGraph orchestrating Researcher → Analyst → Report Writer  
- **Tools:** Financial API, News API, Web Scraper, Internal Docs Search  

---

## MVP: Automated Market Research Analyst

**Use Case:** Generate a competitive analysis report comparing two companies using internal documents + public data.

### Workflow

1. **Receive Request**  
   User submits “Compare Company A vs. Company B” via the frontend.

2. **Plan Data Collection**  
   **Planner Agent** defines which sources to hit.

3. **Retrieve Data**  
   **Retriever Agent** pulls from:  
   - **Internal Docs:** Elasticsearch vector search over PDFs, DOCX, etc.  
   - **Financial APIs:** 
   - **News APIs:**
   - **Web Scraper:** Official websites via Beautiful Soup  

4. **Synthesize Insights**  
   Combine all fetched data into a single context.

5. **Generate Report**  
   **Executor Agent** produces a structured Markdown report.
