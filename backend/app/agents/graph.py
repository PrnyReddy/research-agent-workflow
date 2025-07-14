import os
import json
import re
from typing import TypedDict, List, Dict, Any, Optional, Union
from langchain.agents import Tool
from langchain.tools import StructuredTool
from langgraph.graph import StateGraph, END
from app.tools.financial_api import get_financial_data
from app.tools.news_api import get_news_articles
from app.tools.web_scraper import scrape_website
from app.tools.enhanced_scraper import scrape_website_enhanced
from app.utils.vector_store import VectorStore
from app.llm_manager import llm_manager
from pydantic import BaseModel, ValidationError
import logging

vector_store = VectorStore()

def search_internal_documents(query: str) -> Dict[str, Any]:
    try:
        results = vector_store.search(index_name="research_docs", query=query)
        if not results:
            return {"content": "No relevant internal documents found."}
        return {"content": "\n".join([f"Content: {res['text']}\n---" for res in results])}
    except Exception as e:
        return {"error": f"Internal document search failed: {e}"}

tools = [
    Tool(name="FinancialAPITool", func=get_financial_data, description="Fetch key financial metrics for a public company."),
    StructuredTool.from_function(
        func=get_news_articles,
        name="NewsAPITool",
        description="Fetch recent news articles about a company or topic."
    ),
    Tool(name="WebScraperTool", func=scrape_website, description="Scrape text content from a website."),
    Tool(name="EnhancedWebScraperTool", func=scrape_website_enhanced, description="Enhanced web scraping with better content extraction and metadata."),
    Tool(name="InternalDocsSearchTool", func=search_internal_documents, description="Search internal documents for proprietary information."),
]
tool_dict = {tool.name: tool for tool in tools}

class GraphState(TypedDict):
    task: str
    research_data: List[Any]
    analysis: Optional[Any]
    report: Optional[Any]

class AnalystOutput(BaseModel):
    key_insights: str
    comparative_analysis: str
    narrative: str

def extract_json_from_string(s: str) -> Optional[Any]:
    import json
    import re
    logger = logging.getLogger("multiagent")

    s = s.strip()
    s = re.sub(r"^```(?:json)?|```$", "", s, flags=re.IGNORECASE | re.MULTILINE).strip()
    # Remove leading 'content=' and any leading/trailing quotes
    if s.startswith("content="):
        s = s[len("content="):].strip()
        if s.startswith("'") or s.startswith('"'):
            s = s[1:]
        s = s.strip()
    first_brace = s.find('{')
    last_brace = s.rfind('}')
    if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
        json_str = s[first_brace:last_brace+1]
        json_str = json_str.replace('\\n', '\n').replace('\\"', '"').strip()
        if (json_str.startswith("'") and json_str.endswith("'")) or (json_str.startswith('"') and json_str.endswith('"')):
            json_str = json_str[1:-1]
        try:
            data = json.loads(json_str)
            try:
                validated = AnalystOutput(**data)
                return validated.dict()
            except ValidationError as ve:
                logger.warning(f"Analyst output JSON is missing required fields or is malformed: {ve}")
                partial = {k: data.get(k, None) for k in ["key_insights", "comparative_analysis", "narrative"]}
                partial["_warning"] = f"Validation error: {ve}"
                partial["_raw_output"] = s
                return partial
        except Exception as e:
            logger.error(f"Failed to parse analysis output as JSON after cleaning: {e}\nRaw: {json_str}")
            return {"error": "Failed to parse analysis output as JSON after cleaning. Output may be incomplete or malformed.", "raw_output": json_str}
    else:
        logger.error(f"Could not find a valid JSON object in the output. Raw: {s}")
        return {"error": "Could not find a valid JSON object in the output.", "raw_output": s}

def safe_invoke_llm(prompt_str: str, preferred_provider: Optional[str] = None) -> Union[str, Dict[str, Any]]:
    try:
        result = llm_manager.invoke_with_fallback(prompt_str, preferred_provider)
        if result["success"]:
            response = result["response"]
            # If response is a dict with 'content', extract it
            if isinstance(response, dict) and "content" in response:
                return response["content"]
            return response
        else:
            return {"error": result.get("error", "LLM invocation failed")}
    except Exception as e:
        return {"error": f"LLM invocation failed: {e}"}

def agent_node_researcher(state: GraphState) -> Dict[str, Any]:
    prompt = (
        f"You are a researcher tasked with collecting insights for this topic:\n\n"
        f"{state['task']}\n\n"
        "Only return the findings in clean, well-formatted Markdown.\n"
        "Avoid repeating your task or tool commands. Do not include code blocks or planning steps.\n"
        "Organize results into headings and bullet points. Avoid verbose filler."
    )
    llm_response = safe_invoke_llm(prompt)
    return {"research_data": [llm_response]} if not ("error" in str(llm_response)) else {"research_data": [llm_response]}

def agent_node_analyst(state: GraphState) -> Dict[str, Any]:
    prompt = (
        "You are a financial analyst. Analyze the following research data and return your findings in clean, well-formatted Markdown.\n"
        "Use the following sections as Markdown headings: Key Insights, Comparative Analysis, and Narrative.\n"
        "Do not include code blocks, JSON, or extra metadata.\n"
        "Organize your analysis clearly under each heading.\n"
        f"Research Data:\n{state.get('research_data', '')}"
    )
    llm_response = safe_invoke_llm(prompt)
    def clean_llm_output(text: str) -> str:
        text = text.strip()
        if text.startswith('content="') and text.endswith('"'):
            text = text[len('content="'):-1]
        elif text.startswith('content='):
            text = text[len('content='):].strip()
        return re.split(r"(?:additional_kwargs=|response_metadata=|id=')", text)[0].strip()
    analysis = str(llm_response)
    analysis = clean_llm_output(analysis)
    analysis = re.sub(r"\n{3,}", "\n\n", analysis)
    analysis = re.sub(r"[ \t]{2,}", " ", analysis)
    analysis = re.sub(r"(\*+)[ \t]+", r"\1 ", analysis)
    analysis = analysis.strip()
    analysis = re.sub(r'^(#+ .+)(?!\n\n)(\n)([^\n#])', r'\1\n\n\3', analysis, flags=re.MULTILINE)
    return {"analysis": [analysis]}

def agent_node_report_writer(state: GraphState) -> Dict[str, Any]:
    prompt = (
        "You are a report writer. Using the following analysis and research data, generate a professional report in clean Markdown.\n"
        "Your report must include: Executive Summary, Key Findings, Comparative Analysis, and Conclusion.\n"
        "Avoid extra spacing, repeated sections, unnecessary indentation, or tool output. Return plain Markdown.\n"
        "Keep the formatting consistent and clean. No code blocks, no triple backticks.\n"
        f"Analysis:\n{state.get('analysis', '')}\n"
        f"Research Data:\n{state.get('research_data', '')}"
    )
    llm_response = safe_invoke_llm(prompt)

    if isinstance(llm_response, dict) and "error" in llm_response:
        return {"report": [llm_response]}

    def clean_llm_output(text: str) -> str:
        return re.split(r"(?:additional_kwargs=|response_metadata=|id=')", text)[0].strip()

    report = str(llm_response)
    report = clean_llm_output(report)
    report = re.sub(r"\n{3,}", "\n\n", report)     
    report = re.sub(r"[ \t]{2,}", " ", report)     
    report = re.sub(r"(\*+)[ \t]+", r"\1 ", report)
    report = report.strip()

    return {"report": [report]}

workflow = StateGraph(GraphState)
workflow.add_node("researcher", agent_node_researcher)
workflow.add_node("analyst", agent_node_analyst)
workflow.add_node("report_writer", agent_node_report_writer)

workflow.add_conditional_edges(
    "researcher",
    lambda state: "analyst" if state['research_data'] else "researcher",
    {"analyst": "analyst", "researcher": "researcher"}
)
workflow.add_conditional_edges(
    "analyst",
    lambda state: "report_writer" if state['analysis'] else "analyst",
    {"report_writer": "report_writer"}
)
workflow.add_edge("report_writer", END)
workflow.set_entry_point("researcher")

graph = workflow.compile()