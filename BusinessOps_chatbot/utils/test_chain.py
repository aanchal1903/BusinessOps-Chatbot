import os, json, datetime
import sys
from uuid import uuid1
from operator import itemgetter
from langchain_community.utilities import SQLDatabase
from langchain.chains import create_sql_query_chain
# from langchain_community.tools.sql_database.tool import QuerySQLDataBaseTool
from langchain_community.tools import QuerySQLDatabaseTool
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
from langchain_groq import ChatGroq
from config.gemini_llm import gemini_flash_llm, gemini_pro_llm, gemini_embeddings

# # Initialize Groq LLM
# llm = ChatGroq(
#     model="mixtral-8x7b-32768",
#     groq_api_key="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",
#     temperature=0.7,
#     max_tokens=150,
#     timeout=30,
#     max_retries=2
# )

async def get_structured_qa_chain(
    token: str,
    connection,
    table_names: list,          # list of 3 tables to allow
    query: str,                 # the standalone modified question from the user
    real_user_question: str,                 # the raw question from the user
    chat_history: list,         # previous conversation messages 
    llm,                        # LLM
    chat_id: str                # chat/session identifier
):

    standalone_question = query
    
    # formatted_chat_history = format_chat_history(chat_history, 3) if chat_history else "No previous conversation chat history"
        
    # # # Set up the MySQL connection string
    # # mysql_conn_str = (
    # #     f"mysql+mysqlconnector://{connection['user']}:{connection['password']}"
    # #     f"@{connection['host']}/{connection['database']}?charset=utf8mb4&max_allowed_packet=67108864"
    # # )
    # # # Create a database object
    # # db = SQLDatabase.from_uri(mysql_conn_str)
    
    # ###############################connect to the DB################################
    # db_uri = f"mysql+pymysql://"
    # engine_args = {
    #     "creator": getconn,
    #     "connect_args": {
    #         "max_allowed_packet": 67108864,
    #     }
    # }
    
    sqlite_db_path = r"C:\Users\aanch\Desktop\BusinessOps_chatbot\database\talent_management.db"
    # Define SQLite Database
    db_uri = f"sqlite:///{sqlite_db_path}"
    db = SQLDatabase.from_uri(db_uri, include_tables= table_names)

    PROMPT_SUFFIX = """
        Only use the following tables:
        {table_info}
        Question: {input}
    """
    
    
    _mysql_prompt = """You are a MySQL expert. Given an input question, first create a syntactically correct MySQL query to run, then look at the results of the query and return the answer to the input question.
    Unless the user specifies in the question a specific number of examples to obtain, query for at most {top_k} results using the LIMIT clause as per MySQL. You can order the results to return the most informative data in the database.
    Never query for all columns from a table. You must query only the columns that are needed to answer the question. Wrap each column name in backticks (`) to denote them as delimited identifiers.
   
    **INSTRUCTIONS**:
        Pay attention to use only the column names you can see in the tables below. Be careful to not query for columns that do not exist. Also, pay attention to which column is in which table.
        Pay attention to use CURDATE() function to get the current date, if the question involves "today". 
        Use LIKE with '%term%' for partial matches. Always use '%' wildcards on both sides for maximum matching potential.
        Use appropriate JOIN statements when data needs to be retrieved from multiple tables.
        Use aggregate functions (COUNT, SUM, AVG, MAX, MIN) appropriately for analytical questions.
        Pay special attention to CASTING when comparing numeric values that might be stored as strings.
    
    **TABLE RELATIONSHIPS**:
    - The `users` table has a foreign key `company_id` that references `company.id`
    - The `add_profile` table has a foreign key `user_id` that references `users.id`
    - The `add_profile` table has a foreign key `company_id` that references `company.id`
    
        
    Use the following format:

    Question: Question here
    SQLQuery: SQL Query to run
    SQLResult: Result of the SQLQuery
    Answer: Final answer here   
    
    you must only return a plain SQL Query to run and nothing else.
    you must not include any of `` and ``` ``` in the SQL Query. Just return the plain query.
    you have to be very sure you were returning the sql query in correct requested format 

    Just for your understanding, here are some of the few shot examples on the type of queries you should return:
    few shot examples:
        [
            {{
                "input_question": "How many active users are in company with ID 123?",
                "SQLQuery": "SELECT COUNT(*) FROM users WHERE company_id = 123 AND is_active = 1;"
            }},
            {{
                "input_question": "List all profiles with Java skills in Mumbai location",
                "SQLQuery": "SELECT profile_name, key_skill, location FROM add_profile WHERE key_skill LIKE '%Java%' AND location = 'Mumbai';"
            }},
            {{
                "input_question": "Show companies expiring their subscription in next 30 days",
                "SQLQuery": "SELECT company_name, expire_date FROM company WHERE expire_date BETWEEN CURDATE() AND DATE_ADD(CURDATE(), INTERVAL 30 DAY);"
            }},
            {{
                "input_question": "What's the average charge rate in INR for Data Scientists?",
                "SQLQuery": "SELECT AVG(charge_rate_inr) FROM add_profile WHERE job_title = 'Data Scientist';"
            }},
            {{
                "input_question": "Show me profiles and linkedin_account of users with PHP skills who are available for immediate hiring",
                "SQLQuery": "SELECT p.profile_name, p.linkedin_account_id, p.key_skill, p.availability FROM add_profile p WHERE p.key_skill LIKE '%PHP%' AND p.availability LIKE '%immediate%'"
            }},
            {{
                "input_question": "What is the average charge rate in INR for profiles that have more than 5 years of experience?",
                "SQLQuery": "SELECT AVG(charge_rate_inr) FROM add_profile WHERE CAST(experience AS UNSIGNED) > 5;"
            }},
            {{
                "input_question": "Show me the profiles that were added in the last 30 days.",
                "SQLQuery": "SELECT profile_name, job_title, created_at FROM add_profile WHERE created_at >= CURDATE() - INTERVAL 30 DAY ORDER BY created_at DESC;"
            }},
            {{
                "input_question": "Find profiles with the highest view counts and show their companies and skills",
                "SQLQuery": "SELECT p.profile_name, c.company_name, p.job_title, p.key_skill, p.view_count FROM add_profile p JOIN company c ON p.company_id = c.id ORDER BY p.view_count DESC"
            }},
            {{
                "input_question": "Which candidates match a JD requiring Python and SQL skills with 5 years of experience?",
                "SQLQuery": "SELECT profile_name, job_title, experience, key_skill FROM add_profile WHERE key_skill LIKE '%python%' AND key_skill LIKE '%SQL%' AND CAST(experience AS UNSIGNED) >= 5"
            }},
            {{
                "input_question": "Which skills are most common among profiles with high view counts?",
                "SQLQuery": "SELECT key_skill, COUNT(*) as skill_count, AVG(view_count) as avg_views FROM add_profile WHERE view_count > (SELECT AVG(view_count) FROM add_profile) GROUP BY key_skill ORDER BY skill_count DESC;"
            }},
            {{
                "input_question": "What's the ratio of male to female profiles across different job titles?",
                "SQLQuery": "SELECT job_title, SUM(CASE WHEN gender = 'Male' THEN 1 ELSE 0 END) as male_count, SUM(CASE WHEN gender = 'Female' THEN 1 ELSE 0 END) as female_count, COUNT(*) as total FROM add_profile GROUP BY job_title HAVING male_count > 0 AND female_count > 0 ORDER BY total DESC;"
            }},
        ]

    """
    
    MYSQL_PROMPT_ = PromptTemplate(input_variables=["input", "table_info", "top_k"], template=_mysql_prompt + PROMPT_SUFFIX,)

    # Create a chain to generate a SQL query from the question.
    write_query = create_sql_query_chain(llm, db, k=25, prompt=MYSQL_PROMPT_)

    # Create a tool to execute the generated SQL query.
    execute_query = QuerySQLDatabaseTool(db=db)

    # Create a prompt to transform the SQL query result into a final human-readable answer.    
    answer_prompt = PromptTemplate.from_template(
        """You are an helpful assistant.
        Given the following user question, corresponding SQL query, and SQL result, answer the user question.
        Maintain context from previous conversations to ensure coherent and relevant responses. ONLY consider Chat History into context if you think it is needed for better understanding before answering. Do not mention database table name in the final answer
        In case If you didnt get any answer from sql result give response politely in user friendly non technical way without SQL wordings such that anyone can understand like 'There is no relevant context in database that can help answer your question'
        provide the answer in markdown with well defined formatting. Use headings, subheadings, bullet points, spacing wherever needed and Use tables for presenting structured data with multiple entries.
    
        -----------------------
        **Previous Conversation History:** {chat_history}

        **Question:** {question}

        **SQL Query:** {query}

        **SQL Result:** {result}

        **Answer:**
    
    Accumulate the complete perfect answer for the asked question and then You must strictly give your final response answer in f'{language}' language.
    """
    )

    answer = answer_prompt | llm | StrOutputParser()

    # Combine the SQL query generation, execution, and answer generation into one chain.                
    structured_qa_chain = (
        RunnablePassthrough.assign(query=write_query)
        .assign(result=itemgetter("query") | execute_query)
        | {'question':itemgetter("question"), 'language':itemgetter("language"), 'chat_history':itemgetter("chat_history"), 'output':answer, 'query':itemgetter("query")})

    chain_input = {"question": standalone_question, "language": "ENGLISH", "chat_history": "No previous conversation chat history"}


    
    response = await structured_qa_chain.ainvoke(chain_input)
    
    # yield json.dumps({"type": "chatId", "content": chat_id})

    # ai_text = ""
    # output_text = response['output']
    # stream_size = 4
    # for i in range(0, len(output_text), stream_size):
    #     chunk = output_text[i: i+stream_size]
    #     ai_text += chunk
    #     yield json.dumps({"type": "text", "content": chunk})   
    # print(f"final answer: {ai_text}")
    
    # sql_query = response['query']
    # yield json.dumps({"type": "sqlquery", "content": sql_query})   

    # msg_id = str(uuid1())
    # yield json.dumps({"type": "messageId", "content": msg_id})
    
    # ############this will be in MONGODB
    # timestamp = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    
    # sql = sqlalchemy.text("INSERT INTO messages (msg_id , user_id , chat_id , message, timestamp) VALUES (:msg_id, :user_id, :chat_id, :message, :timestamp)")
    # connection.execute(sql, {"msg_id": msg_id, "user_id": token, "chat_id": f"directory_{chat_id}", "message": json.dumps([{"key": "user", "value": real_user_question}, {"key": "bot", "value": ai_text, "msg_id": msg_id, "query": sql_query}]), "timestamp": timestamp})
    # connection.commit()

    # sql2 = sqlalchemy.text("INSERT INTO reactions (msg_id , user_id , chat_id , message, timestamp) VALUES (:msg_id, :user_id, :chat_id, :message, :timestamp)")
    # connection.execute(sql2, {"msg_id": msg_id, "user_id": token, "chat_id": f"directory_{chat_id}", "message": json.dumps([{"key": "user", "value": real_user_question}, {"key": "bot", "value": ai_text, "msg_id": msg_id, "query": sql_query}]), "timestamp": timestamp})
    # connection.commit()

    # sql3 = sqlalchemy.text("UPDATE directory_chat_list_2 SET last_followup_questions = :last_followup_questions, timestamp = :timestamp WHERE s_no = :s_no AND user_id = :user_id")
    # connection.execute(sql3, {"last_followup_questions": json.dumps(followup_question), "timestamp": timestamp, "s_no" :chat_id, "user_id": token})
    # connection.commit()
    # connection.close()
    

    return response


async def test_rag_chain(user_query):

    response = await get_structured_qa_chain(
        token="test_user",
        connection="",
        table_names=["company", "users", "add_profile"],
        query=user_query,
        real_user_question=user_query,
        chat_history=[],
        llm=gemini_pro_llm,  
        # llm = gemini_flash_llm,
        chat_id="test_chat"
    )

    print("*****************************************************************************************************")
    print(f"final sql query: {response.get('query', 'No query generated')}")
    print("*****************************************************************************************************")
    print(f"final answer: {response.get('output', 'No output generated')}")




# query = "What is the phone number and email of Bob Williams ?"
query = "what is the job title of Charlie Davis?"
# query = "What is the average charge rate in INR for profiles that have more than 5 years of experience?"
# query = "give me the details of copanies whose company_turnover is greater than $10M"
# query = "Find all employees with more than 10 years of experience."
# query = "Which skills are most common among profiles with high view counts?"


# Run Test
asyncio.run(test_rag_chain(query))