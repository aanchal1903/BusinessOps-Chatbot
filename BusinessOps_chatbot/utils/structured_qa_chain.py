import os, json, uuid1, datetime
from operator import itemgetter
from dependencies.database import getconn
from langchain_community.utilities import SQLDatabase
from langchain.chains import create_sql_query_chain
from langchain_community.tools.sql_database.tool import QuerySQLDataBaseTool
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langchain_groq import ChatGroq


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
    connection: dict,           # e.g. {"host": "localhost", "user": "myuser", "password": "mypass", "database": "mydb"}
    table_names: list,          # list of tables to allow
    query: str,                 # the standalone modified question from the user
    real_user_question: str,                 # the raw question from the user
    chat_history: list,         # previous conversation messages 
    llm,                        # LLM
    chat_id: str                # chat/session identifier
):

    standalone_question = query
    formatted_chat_history = format_chat_history(chat_history, 3) if chat_history else "No previous conversation chat history"
        
    # # Set up the MySQL connection string
    # mysql_conn_str = (
    #     f"mysql+mysqlconnector://{connection['user']}:{connection['password']}"
    #     f"@{connection['host']}/{connection['database']}?charset=utf8mb4&max_allowed_packet=67108864"
    # )
    # # Create a database object
    # db = SQLDatabase.from_uri(mysql_conn_str)
    
    ###############################we willsee based on the connection
    db_uri = f"mysql+pymysql://"
    engine_args = {
        "creator": getconn,
        "connect_args": {
            "max_allowed_packet": 67108864,
        }
    }
    db = SQLDatabase.from_uri(db_uri, engine_args=engine_args, include_tables= table_names, max_string_length=100000)
    
    PROMPT_SUFFIX = """
        Only use the following tables:
        {table_info}
        Question: {input}
    """
    
    
    _mysql_prompt = """You are a MySQL expert. Given an input question, first create a syntactically correct MySQL query to run, then look at the results of the query and return the answer to the input question.
    Unless the user specifies in the question a specific number of examples to obtain, query for at most {top_k} results using the LIMIT clause as per MySQL. You can order the results to return the most informative data in the database.
    Never query for all columns from a table. You must query only the columns that are needed to answer the question. Wrap each column name in backticks (`) to denote them as delimited identifiers.
    Pay attention to use only the column names you can see in the tables below. Be careful to not query for columns that do not exist. Also, pay attention to which column is in which table.
    Pay attention to use CURDATE() function to get the current date, if the question involves "today". 
    
    Use the following format:

    Question: Question here
    SQLQuery: SQL Query to run
    SQLResult: Result of the SQLQuery
    Answer: Final answer here   
    
    you must only return a plain SQL Query to run and nothing else.
    you must not include any of `` and ``` ``` in the SQL Query. Just return the plain query.
    you have to be very sure you were returning the sql query in correct requested format 

    Just for your understanding, here are some of the examples on what format you should return:

############# here will be giving few shot examples of current project #######################################
    SELECT document_name, starting_date, expiry_date FROM LLama3_statementofwork WHERE document_name = 'abc'
    SELECT document_name, company_a, company_b FROM LLama3_serviceagreement
    SELECT document_name, termination_info FROM LLama3_serviceagreement
    SELECT document_name, approval_date, commencement_date FROM LLama3_policydocument
    SELECT document_name, purpose FROM LLama3_policydocument
    SELECT document_name, key_performance_indicators FROM LLama3_businessprocessdocument
    
    """
    
    MYSQL_PROMPT_ = PromptTemplate(input_variables=["input", "table_info", "top_k"], template=_mysql_prompt + PROMPT_SUFFIX,)

    # Create a chain to generate a SQL query from the question.
    write_query = create_sql_query_chain(llm, db, k=25, prompt=MYSQL_PROMPT_)

    # Create a tool to execute the generated SQL query.
    execute_query = QuerySQLDataBaseTool(db=db)

    # Create a prompt to transform the SQL query result into a final human-readable answer.    
    answer_prompt = PromptTemplate.from_template(
        """You are an helpful assistant.
        Given the following user question, corresponding SQL query, and SQL result, answer the user question.
        Maintain context from previous conversations to ensure coherent and relevant responses. ONLY consider Chat History into context if you think it is needed for better understanding before answering. Do not mention database table name in the final answer
        In case If you didnt get any answer from sql result give response politely in user friendly non technical way without SQL wordings such that anyone can understand like 'There is no relevant context in database that can help answer your question'
        provide the answer in markdown with well defined formatting. Use headings, subheadings, bullet points, spacing wherever needed

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

    chain_input = {"question": standalone_question, "language": "ENGLISH", "chat_history": formatted_chat_history}

    
    response = await structured_qa_chain.invoke_async(chain_input)
    
    yield json.dumps({"type": "chatId", "content": chat_id})

    ai_text = ""
    output_text = response['output']
    stream_size = 4
    for i in range(0, len(output_text), stream_size):
        chunk = output_text[i: i+stream_size]
        ai_text += chunk
        yield json.dumps({"type": "text", "content": chunk})   
    print(f"final answer: {ai_text}")
    
    sql_query = response['query']
    yield json.dumps({"type": "sqlquery", "content": sql_query})   

    msg_id = str(uuid1())
    yield json.dumps({"type": "messageId", "content": msg_id})
    
    ############this will be in MONGODB
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
