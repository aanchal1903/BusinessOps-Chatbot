import os
import sys
import asyncio
from pathlib import Path
from operator import itemgetter
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# Ensure paths are correctly set up
PROJECT_ROOT = Path(__file__).parent.parent.absolute()
sys.path.append(str(PROJECT_ROOT))

# Import the LLM models
from config.gemini_llm import gemini_pro_llm

# The router prompt template to classify queries
ROUTER_PROMPT = """
        You are an expert query classifier for a talent management system.
        Your job is to determine whether a query should be routed to:
        
        1. "structured" - For queries that ask for specific database information, statistics, or require SQL-like operations
        2. "unstructured" - For queries about matching job descriptions to candidates, resume analysis, or general recommendations
        
        Structured queries typically involve:
        - Counting or listing profiles with specific attributes
        - Finding average values (like charge rates)
        - Filtering candidates by specific criteria
        - Questions about database records
        
        Unstructured queries typically involve:
        - Matching job descriptions to candidate profiles
        - Finding the "best" candidate for a position
        - Analyzing resumes or job descriptions
        - Making recommendations based on qualitative factors
        
        Examples:
        "How many developers have Python skills?" -> "structured"
        "Find the best candidate for this senior developer role" -> "unstructured"
        "What is the average charge rate for data scientists?" -> "structured"
        "Match this job description to available candidates" -> "unstructured"
        "List all profiles with Java skills" -> "structured"
        
        Given the following query, respond with ONLY "structured" or "unstructured":
        
        Query: {query}
        
        Classification:
    """

class QueryRouter:
    def __init__(self, llm=None):
        self.llm = llm or gemini_pro_llm
        
        # Create the router chain
        router_prompt = ChatPromptTemplate.from_template(ROUTER_PROMPT)
        self.router_chain = router_prompt | self.llm | StrOutputParser()
    
    async def route_query(self, query):
        """Determine which RAG pipeline to use for a given query"""
        result = await self.router_chain.ainvoke({"query": query})
        result = result.strip().upper()
        
        if "STRUCTURED_QUERY" in result:
            return "structured"
        elif "UNSTRUCTURED_QUERY" in result:
            return "unstructured"
        else:
            # Default fallback if classification is unclear
            return "structured"