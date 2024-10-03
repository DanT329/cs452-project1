from openai import OpenAI
import mysql.connector
import json
from mysql.connector import Error
from dotenv import load_dotenv
import os


load_dotenv()


MYSQL_HOST = os.getenv('MYSQL_HOST')
MYSQL_USER = os.getenv('MYSQL_USER')
MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD')
MYSQL_DATABASE = os.getenv('MYSQL_DATABASE')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
ORG_ID = os.getenv('ORG_ID')


openAiClient = OpenAI(
    api_key=OPENAI_API_KEY,
    organization=ORG_ID
)

db_connection = mysql.connector.connect(
    host=MYSQL_HOST,
    user=MYSQL_USER,
    password=MYSQL_PASSWORD,
    database=MYSQL_DATABASE
)
cursor = db_connection.cursor()


def get_sql_from_natural_language(natural_language_query):
    schema = """
    The database contains the following tables:

    1. employees
       - employee_id: INT, AUTO_INCREMENT, PRIMARY KEY
       - first_name: VARCHAR(50)
       - last_name: VARCHAR(50)
       - email: VARCHAR(100)
       - phone_number: VARCHAR(15)
       - department: VARCHAR(50)

    2. tools
       - tool_id: INT, AUTO_INCREMENT, PRIMARY KEY
       - serial_number: VARCHAR(50), UNIQUE
       - common_name: VARCHAR(100)
       - brand: VARCHAR(50)
       - purchase_date: DATE
       - condition_status: ENUM('new', 'good', 'fair', 'poor') DEFAULT 'good'

    3. tool_checkouts
       - checkout_id: INT, AUTO_INCREMENT, PRIMARY KEY
       - employee_id: INT, FOREIGN KEY REFERENCES employees(employee_id)
       - tool_id: INT, FOREIGN KEY REFERENCES tools(tool_id)
       - checkout_date: DATE
       - return_date: DATE
       - status: ENUM('checked_out', 'returned') DEFAULT 'checked_out'

    4. tool_maintenance
       - maintenance_id: INT, AUTO_INCREMENT, PRIMARY KEY
       - tool_id: INT, FOREIGN KEY REFERENCES tools(tool_id)
       - maintenance_date: DATE
       - performed_by: VARCHAR(100)
       - maintenance_details: TEXT

    5. tool_locations
       - location_id: INT, AUTO_INCREMENT, PRIMARY KEY
       - tool_id: INT, FOREIGN KEY REFERENCES tools(tool_id)
       - location_name: VARCHAR(100)
       - shelf_number: VARCHAR(50)
    """

    
    prompt = f"{schema}\nTranslate the following natural language query into mySQL:\n{natural_language_query}. Do not give any explanation, jus the mySQL."

   
    stream = openAiClient.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        stream=True
    )

    sql_query = ""
    for chunk in stream:
        if chunk.choices[0].delta.content is not None:
            sql_query += chunk.choices[0].delta.content

    return sql_query.strip()


def sanitize_sql(value):
    gpt_start_sql_marker = "```sql"
    gpt_end_sql_marker = "```"
    if gpt_start_sql_marker in value:
        value = value.split(gpt_start_sql_marker)[1]
    if gpt_end_sql_marker in value:
        value = value.split(gpt_end_sql_marker)[0]

    return value.strip() 


def get_natural_language_from_sql_result(sql_result, question):
    result_str = str(sql_result)

    
    prompt = f"I asked {question} and the response was: \"{result_str}\". Please provide a concise and friendly answer to the question. Only answer the question and give no further explanation."

    stream = openAiClient.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        stream=True
    )

    natural_language_response = ""
    for chunk in stream:
        if chunk.choices[0].delta.content is not None:
            natural_language_response += chunk.choices[0].delta.content

    return natural_language_response.strip()


def execute_sql_query(sql_query):
    cursor.execute(sql_query)
    result = cursor.fetchall()
    return result


def load_questions_from_json(json_file_path):
    with open(json_file_path, 'r') as file:
        data = json.load(file)
        return data['questions']


def handle_natural_language_questions(questions):
    for question in questions:
        print(f"Question: {question}")
        
        
        sql_query = get_sql_from_natural_language(question)
        # print(f"Generated SQL (raw): {sql_query}")
        
        
        sanitized_sql_query = sanitize_sql(sql_query)
        # print(f"Sanitized SQL: {sanitized_sql_query}")
        
       
        try:
            result = execute_sql_query(sanitized_sql_query)
            # print(f"SQL Result: {result}")
            
            
            natural_language_response = get_natural_language_from_sql_result(result,question)
            print(f"Friendly Response: {natural_language_response}")
        except mysql.connector.Error as err:
            print(f"Error: {err}")
        print("\n")

def handle_natural_language_questions_single_domain(questions):
    for question in questions:
        print(f"Question: {question}")
        question = question + prompt_assist
        
       
        sql_query = get_sql_from_natural_language(question)
        # print(f"Generated SQL (raw): {sql_query}")
        
        
        sanitized_sql_query = sanitize_sql(sql_query)
        # print(f"Sanitized SQL: {sanitized_sql_query}")
        
        # Execute the sanitized SQL query
        try:
            result = execute_sql_query(sanitized_sql_query)
            # print(f"SQL Result: {result}")
            
            
            natural_language_response = get_natural_language_from_sql_result(result,question)
            print(f"Friendly Response: {natural_language_response}")
        except mysql.connector.Error as err:
            print(f"Error: {err}")
        print("\n")


questions = load_questions_from_json('questions.json')
prompt_assist = """An example of how this might look: 
                Question: Where can I find the tools that need to be serviced? 
                SQL: SELECT t.tool_id, t.serial_number, t.common_name, t.brand, t.condition_status, 
                    tl.location_name, tl.shelf_number, 
                    tc.status AS checkout_status,
                    e.first_name, e.last_name, e.email
                FROM tools t
                LEFT JOIN tool_locations tl ON t.tool_id = tl.tool_id
                LEFT JOIN tool_checkouts tc ON t.tool_id = tc.tool_id AND tc.status = 'checked_out'
                LEFT JOIN employees e ON tc.employee_id = e.employee_id
                WHERE t.condition_status IN ('fair', 'poor'); 
                Natrual language answer: The Dewalt Hammer (SN002) needs to be serviced and his currently checked out by Alice Jenkins."""


handle_natural_language_questions(questions)
handle_natural_language_questions_single_domain(questions)


db_connection.close()

