import os
import json
import re
from typing import TypedDict, List, Dict, Any, Optional, Union
from langchain.agents import Tool
from langchain.tools import StructuredTool
from langgraph.graph import StateGraph, END
from dotenv import load_dotenv

from .tools.financial_api import get_financial_data
from .tools.news_api import get_news_articles
from .tools.web_scraper import scrape_website
from .tools.enhanced_scraper import scrape_website_enhanced
from .vector_store import VectorStore
from .llm_manager import llm_manager

load_dotenv()

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

def extract_json_from_string(s: str) -> Optional[Any]:
    s = re.sub(r"```(?:json)?", "", s)
    s = s.strip()
    match = re.search(r"\{.*\}", s, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except Exception as e:
            print(f"JSON extraction error: {e}")
    return None

def safe_invoke_llm(prompt_str: str, preferred_provider: Optional[str] = None) -> Union[str, Dict[str, Any]]:
    try:
        result = llm_manager.invoke_with_fallback(prompt_str, preferred_provider)
        if result["success"]:
            return result["response"]
        else:
            return {"error": result.get("error", "LLM invocation failed")}
    except Exception as e:
        print(f"LLM invocation failed: {e}")
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
        "You are a financial analyst. Analyze the following research data and return only a JSON object with these fields:\n"
        "{\n"
        '  "key_insights": "...",\n'
        '  "comparative_analysis": "...",\n'
        '  "narrative": "..."\n'
        "}\n"
        "Do NOT include Markdown, code blocks, commentary, or formatting. Return ONLY valid JSON.\n"
        f"Research Data:\n{state.get('research_data', '')}"
    )
    llm_response = safe_invoke_llm(prompt)
    if isinstance(llm_response, dict) and "error" in llm_response:
        return {"analysis": [llm_response]}
    parsed = extract_json_from_string(str(llm_response))
    return {"analysis": [parsed] if parsed else [llm_response]}

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

    report = str(llm_response)
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
print("LangGraph compiled successfully.")
