# Import necessary libraries
import pandas as pd
import os
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.vectorstores import Chroma
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain.embeddings import HuggingFaceEmbeddings
from langchain_groq import ChatGroq
import json
import re
import PyPDF2  # For PDF text extraction

# Set your Grok API key
os.environ["GROQ_API_KEY"] = "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"

# Function to extract text from a PDF file
def extract_text_from_pdf(file_path):
    try:
        with open(file_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            text = ""
            for page in reader.pages:
                text += page.extract_text() or ""
            return text.strip()
    except Exception as e:
        raise Exception(f"Error reading PDF file: {str(e)}")

# Step 1: Load and preprocess the data (unchanged)
def load_and_preprocess_data(file_path):
    df = pd.read_csv(file_path)
    
    profiles = []
    
    for _, row in df.iterrows():
        skills = row['key_skill'].split(',') if pd.notna(row['key_skill']) else []
        skills = [skill.strip() for skill in skills]
        
        projects = []
        if pd.notna(row['projects']):
            try:
                project_str = row['projects']
                matches = re.findall(r'projects_title : (.?) \| projects:(.?)"', project_str)
                for match in matches:
                    projects.append({
                        "title": match[0].strip(),
                        "description": match[1].strip()
                    })
            except:
                projects = [{"title": "Project", "description": str(row['projects'])}]
        
        profile_text = f"""
        CANDIDATE ID: {row['id']}
        NAME: {row['profile_name']}
        JOB TITLE: {row['job_title']}
        EXPERIENCE: {row['experience']}
        DEPARTMENT: {row['department']}
        PROFESSIONAL SUMMARY: {row['professional_summary']}
        SKILLS: {', '.join(skills)}
        EDUCATION: {row['education']}
        CERTIFICATION: {row['certificate'] if pd.notna(row['certificate']) else 'None'}
        CHARGE RATE: {row['charge_rate'] if pd.notna(row['charge_rate']) else 'Not specified'}
        AVAILABILITY: {row['availability'] if pd.notna(row['availability']) else 'Not specified'}
        LOCATION: {row['location'] if pd.notna(row['location']) else 'Not specified'}
        """
        
        if projects:
            profile_text += "\nPROJECTS:\n"
            for project in projects:
                profile_text += f"- {project['title']}: {project['description']}\n"
        
        profiles.append({
            "id": row['id'],
            "name": row['profile_name'],
            "content": profile_text,
            "metadata": {
                "job_title": row['job_title'],
                "experience": row['experience'],
                "skills": skills,
                "charge_rate": row['charge_rate'] if pd.notna(row['charge_rate']) else 'Not specified',
            }
        })
    
    return profiles

# Step 2: Create vector embeddings and store in ChromaDB (unchanged)
def create_vector_store(profiles, persist_directory="candidate_db"):
    documents = [profile["content"] for profile in profiles]
    metadatas = [{"id": profile["id"], "name": profile["name"]} for profile in profiles]
    
    embedding_function = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    
    vector_store = Chroma.from_texts(
        documents,
        embedding_function,
        metadatas=metadatas,
        persist_directory=persist_directory
    )
    
    return vector_store

# Step 3: Define the retriever (unchanged)
def get_retriever(vector_store):
    return vector_store.as_retriever(
        search_type="similarity",
        search_kwargs={"k": 3}
    )

# Step 4: Create the RAG prompt (unchanged)
def create_rag_chain():
    template = """
    You are an expert HR consultant who specializes in matching candidates to job descriptions.
    I need you to analyze the job description or resume and find the best candidate match from the retrieved profiles.
    
    INPUT:
    {job_description}
    
    RETRIEVED CANDIDATE PROFILES:
    {context}
    
    Based on the input (job description or resume) and candidate profiles:
    1. Analyze each candidate's skills, experience, and background
    2. Evaluate how well they match the requirements
    3. Consider factors like availability, charge rate, and location
    4. Select the BEST candidate that meets the requirements
    
    First provide a summary of the top candidate and why they're a good match.
    Then provide a comparison with the other candidates (if any).
    
    Your response should be structured as follows:
    
    TOP CANDIDATE RECOMMENDATION:
    [Name of the best candidate, with their key qualifications and why they're the best match]
    
    DETAILED ANALYSIS:
    [Provide a detailed analysis of how the candidate matches the requirements]
    
    ALTERNATIVE CANDIDATES:
    [Brief overview of other candidates and why they weren't selected as the top choice]
    
    NEXT STEPS:
    [Suggested action items for proceeding with the recommended candidate]
    """
    
    prompt = ChatPromptTemplate.from_template(template)
    model = ChatGroq(model="llama3-70b-8192", temperature=0)
    
    chain = (
        {"context": lambda x: x["retriever_results"], "job_description": lambda x: x["job_description"]}
        | prompt
        | model
        | StrOutputParser()
    )
    
    return chain

# Step 5: Create the main function with document upload option
def create_candidate_matcher(file_path=r"C:\Users\Priyansh Tyagi\Desktop\Businessopschatbot\data\my_company_data_with_headers.csv"):
    profiles = load_and_preprocess_data(file_path)
    vector_store = create_vector_store(profiles)
    retriever = get_retriever(vector_store)
    chain = create_rag_chain()
    
    def match_candidate(input_data=None, document_path=None):
        # Determine the input source
        if document_path:
            if not os.path.exists(document_path):
                raise FileNotFoundError(f"Document not found at {document_path}")
            job_description = extract_text_from_pdf(document_path)
        elif input_data:
            job_description = input_data
        else:
            raise ValueError("Please provide either a job description or a document path.")
        
        # Retrieve relevant candidates
        retriever_results = retriever.invoke(job_description)
        retriever_docs = [doc.page_content for doc in retriever_results]
        
        # Format the documents for the prompt
        formatted_docs = "\n\n".join(retriever_docs)
        
        # Invoke the chain
        response = chain.invoke({
            "retriever_results": formatted_docs,
            "job_description": job_description
        })
        
        return response
    
    return match_candidate

# Example usage
if __name__ == "__main__":
    # Create the candidate matcher
    candidate_matcher = create_candidate_matcher()
    
    # Option 1: Use a typed job description
    sample_job_description = """
    We are looking for an experienced Data Engineer with strong Python skills and experience with AWS cloud services. 
    The ideal candidate should have 10+ years of experience in building data pipelines and working with big data technologies.
    Experience with Machine Learning frameworks is a plus. The candidate should be available within 30 days.
    """
    print("Matching based on typed job description:")
    recommendation = candidate_matcher(input_data=sample_job_description)
    print(recommendation)
    
    # Option 2: Use a document upload (e.g., a PDF job description or resume)
    sample_pdf_path = r"C:\Users\Priyansh Tyagi\Desktop\Businessopschatbot\sample-job-description.pdf"  # Replace with actual PDF path
    try:
        print("\nMatching based on uploaded document:")
        recommendation = candidate_matcher(document_path=sample_pdf_path)
        print(recommendation)
    except Exception as e:
        print(f"Error: {str(e)}")
