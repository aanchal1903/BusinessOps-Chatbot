import os
import sys
import asyncio
from pathlib import Path
import json

# Ensure paths are correctly set up
PROJECT_ROOT = Path(__file__).parent.absolute()
sys.path.append(str(PROJECT_ROOT))

# Import the router
from routers.query_router import QueryRouter
    
# Import the structured RAG chain
from utils.test_chain import test_rag_chain

# Import the unstructured RAG chain
from utils.doc_upload import create_candidate_matcher

class RAGSystem:
    def __init__(self):
        """Initialize the RAG system with both chains and the router"""
        self.router = QueryRouter()
        
        # Initialize the unstructured RAG chain (candidate matcher)
        self.candidate_matcher = create_candidate_matcher()
        
        print("RAG System initialized successfully!")
    
    async def process_query(self, query, job_description_path=None):
        """Process a user query and route it to the appropriate chain"""
        # Determine which chain to use
        chain_type = await self.router.route_query(query)
        print(f"Router decision: {chain_type}")
        
        if chain_type == "structured":
            # Use the structured RAG chain
            print("Using structured RAG chain...")
            response = await test_rag_chain(query)
            return {
                "chain_type": "structured",
                "query": query,
                "sql_query": response.get("query", "No SQL query generated"),
                "answer": response.get("output", "No answer generated")
            }
        else:
            # Use the unstructured RAG chain (candidate matcher)
            print("Using unstructured RAG chain...")
            if job_description_path:
                result = self.candidate_matcher(document_path=job_description_path)
            else:
                result = self.candidate_matcher(input_data=query)
            return {
                "chain_type": "unstructured",
                "query": query,
                "answer": result
            }

async def main():
    """Main entry point for the application"""
    # Initialize the RAG system
    rag_system = RAGSystem()
    
    while True:
        # Get user input
        print("\n" + "="*80)
        print("Enter your query (or 'exit' to quit, 'jd' to provide a job description path):")
        user_input = input("> ")
        
        # Check if user wants to exit
        if user_input.lower() == "exit":
            print("Exiting application...")
            break
        
        # Check if user wants to provide a job description path
        job_description_path = None
        if user_input.lower() == "jd":
            print("Enter the path to the job description PDF:")
            job_description_path = input("> ")
            if not os.path.exists(job_description_path):
                print(f"Error: File not found at {job_description_path}")
                continue
            
            print("Enter your query to match with this job description:")
            user_input = input("> ")
        
        # Process the query
        try:
            result = await rag_system.process_query(user_input, job_description_path)
            
            # Display the result
            print("\nResult:")
            print(f"Chain used: {result['chain_type']}")
            print("-" * 40)
            
            if result['chain_type'] == 'structured':
                print(f"SQL Query: {result['sql_query']}")
                print("-" * 40)
            
            print("Answer:")
            print(result['answer'])
            
        except Exception as e:
            print(f"Error processing query: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())