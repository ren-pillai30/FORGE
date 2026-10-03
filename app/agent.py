import os
import sqlite3
from langchain_core.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "telemetry.db")

@tool
def query_telemetry_db(intent: str) -> str:
    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0)
    
    schema = """
    Table: telemetry
    Columns: id (INTEGER), player_id (TEXT), level_name (TEXT), gold_earned (INTEGER), enemies_defeated (INTEGER), item_drop_rate (REAL)
    """
    
    prompt = f"""
    Convert the following natural language intent into a valid SQLite query.
    Schema:
    {schema}
    Intent: {intent}
    Output ONLY the raw SQL query. Do not include markdown formatting or explanations.
    """
    
    sql_query = llm.invoke(prompt).content.strip()
    sql_query = sql_query.replace("```sql", "").replace("```", "").strip()
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(sql_query)
        results = cursor.fetchall()
        conn.close()
        return str(results)
    except Exception as e:
        return f"Error executing query: {str(e)}"

def get_agent():
    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0)
    tools = [query_telemetry_db]
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are Forge, an AI assistant for game designers. You query game telemetry databases and answer questions about player metrics."),
        ("human", "{input}"),
        ("placeholder", "{agent_scratchpad}")
    ])
    
    agent = create_tool_calling_agent(llm, tools, prompt)
    return AgentExecutor(agent=agent, tools=tools, return_intermediate_steps=True)