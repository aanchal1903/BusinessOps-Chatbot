import os, json, datetime
from operator import itemgetter
import sqlite3
import asyncio
from langchain_community.utilities import SQLDatabase
from langchain.chains import create_sql_query_chain
from langchain_community.tools import QuerySQLDatabaseTool
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langchain_groq import ChatGroq

# Initialize Groq LLM
llm = ChatGroq(
    model="mixtral-8x7b-32768",
    groq_api_key="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",
    temperature=0.7,
    max_tokens=150,
    timeout=30,
    max_retries=2
)

async def get_structured_qa_chain(
    token: str,
    connection: dict,
    table_names: list,
    query: str,
    real_user_question: str,
    llm, 
    chat_id: str
):

    sqlite_db_path = "C:/Users/aanch/Desktop/BusinessOps_chatbot/database/talent_management.db"

    # Define SQLite Database
    db_uri = f"sqlite:///{sqlite_db_path}"
    db = SQLDatabase.from_uri(db_uri, include_tables=["company", "users", "add_profile"])

    # Prompt for SQL Query Generation
    _sqlite_prompt = """You are a SQLite expert. Given an input question, first create a syntactically correct SQLite query to run, then look at the results of the query and return the answer to the input question.
    Unless the user specifies in the question a specific number of examples to obtain, query for at most {top_k} results using the LIMIT clause as per SQLite. You can order the results to return the most informative data in the database.
    Never query for all columns from a table. You must query only the columns that are needed to answer the question. Wrap each column name in double quotes (") to denote them as delimited identifiers.
    Pay attention to use only the column names you can see in the tables below. Be careful to not query for columns that do not exist. Also, pay attention to which column is in which table.
    Pay attention to use date('now') function to get the current date, if the question involves "today".

    Use the following format:

    **Question:** Question here  
    **SQLQuery:** SQL Query to run  
    **SQLResult:** Result of the SQLQuery  
    **Answer:** Final answer here  

    Only use the following tables:
    {table_info}

    Question: {input}
    """

    MYSQL_PROMPT_ = PromptTemplate(input_variables=["input", "table_info", "top_k"], template=_sqlite_prompt)

    # Create Query Generation Chain
    write_query = create_sql_query_chain(llm, db, k=25, prompt=MYSQL_PROMPT_)

    # Query Execution Tool
    execute_query = QuerySQLDatabaseTool(db=db)  

    # Answer Formatting Prompt
    answer_prompt = PromptTemplate.from_template(
    """You are a helpful assistant.
    Given the following user question, corresponding SQL query, and SQL result, answer the user question.
    Maintain context from previous conversations to ensure coherent and relevant responses. ONLY consider chat history if you think it is needed for a better understanding before answering. Do not mention database table names in the final answer.
    
    If the SQL result does not return any relevant data, provide a polite, user-friendly response without using technical terms or SQL wording. Instead of stating that no data was found in the database, phrase it naturally, such as:  
    *"There is no relevant context available that can help answer your question."*

    Provide the answer in **Markdown** with well-defined formatting:
    - Use **headings** and **subheadings** where necessary.
    - Use **bullet points** and **spacing** for clarity.
    - Use **tables** when presenting structured data with multiple entries.

    -----------------------

    **Question:** {question}

    **SQL Query:** {query}

    **SQL Result:** {result}

    **Answer:**
    
    Accumulate the complete, well-structured answer for the asked question.
    """
    )

    # Generate SQL Query
    generated_query_response = await write_query.ainvoke({"question": query})

    # print("\nGenerated SQL Query Response:")
    # print(generated_query_response)

    # Extract only the raw SQL query
    if isinstance(generated_query_response, dict) and "query" in generated_query_response:
        generated_query = generated_query_response["query"]
    elif isinstance(generated_query_response, str):
        # Attempt to cleanly extract the SQL query
        generated_query = generated_query_response.split("SQLQuery:")[-1].strip()
    else:
        return {"error": "Query generation failed"}

    print("\nExtracted SQL Query:")
    print(generated_query)

    if not generated_query:
        return {"error": "Query extraction failed"}

    # Execute the SQL Query
    try:
        sql_result = execute_query.invoke(generated_query)
        print("\nSQL Query Result:")
        print(sql_result)
    except Exception as e:
        print("Error executing query:", str(e))
        return {"error": "SQL execution failed"}

    # Ensure proper handling of empty results
    if not sql_result or sql_result.strip() == "":
        sql_result = "No relevant data found."

    # Generate Final Answer
    final_answer = await llm.ainvoke(answer_prompt.format(question=query, query=generated_query, result=sql_result))

    return {
        "query": generated_query,
        "output": final_answer
    }

# Testing function
async def test_rag_chain():
    # user_query = "What is the phone number of Bob Williams ?"
    # user_query = "Find all employees with more than 10 years of experience."
    user_query = "How many tables does the database consist of ?"
    
    response = await get_structured_qa_chain(
        token="test_user",
        connection={"database": "database/talent_management.db"},
        table_names=["company", "users", "add_profile"],
        query=user_query,
        real_user_question=user_query,
        llm=llm,  
        chat_id="test_chat"
    )

    print("\nGenerated SQL Query:")
    print(response.get("query", "No query generated"))

    print("\nFinal Output:")
    print(response.get("output", "No output generated"))

# Run Test
asyncio.run(test_rag_chain())
