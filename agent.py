from langchain.agents import tool, AgentExecutor, create_react_agent
from langchain.prompts import PromptTemplate
from langchain_ollama import ChatOllama
from tools import (
    answer_student_question,
    create_revision_plan,
    generate_quiz,
    give_motivation,
    save_quiz_result,
    get_topic_performance,
    generate_performance_chart
)


@tool
def student_question_tool(query: str) -> str:
    """Use this tool to answer a student's specific question about their study material."""
    return answer_student_question(query)


@tool
def revision_plan_tool(weak_topics: list, exam_date: str) -> str:
    """Use this tool to create a study plan when a student provides their weak topics and an exam date."""
    return create_revision_plan(weak_topics, exam_date)


@tool
def quiz_tool(user_sentence: str) -> str:
    """
    Use this tool to generate a quiz for a student. The user's entire sentence should be passed as input.
    The tool will determine the topic and difficulty from the text.
    For example: 'Quiz me on Market Analysis hard' or 'give me an easy quiz on sales'
    """
    return generate_quiz(details_string=user_sentence)


@tool
def motivation_tool(student_name: str) -> str:
    """Use this tool to give a motivational message. Use 'student' if the name is not known."""
    return give_motivation(student_name)


@tool
def grade_and_save_quiz_tool(user_sentence: str) -> str:
    """
    Use this tool ONLY when a student explicitly tells you the score they received on a quiz.
    Pass the user's entire sentence as the input to this tool.
    For example: "I scored 97 in market analysis" or "my score was 85 on the test".
    """
    return save_quiz_result(details_string=user_sentence)


@tool
def get_topic_performance_tool(topic: str) -> str:
    """
    Use this tool BEFORE generating a quiz to check the student's past performance
    and average score on a specific topic. This helps decide the quiz difficulty.
    """
    return get_topic_performance(topic=topic)


@tool
def performance_chart_tool(query: str) -> str:
    """
    Use this tool when a student asks for a visual report, chart, graph, or dashboard of their progress.
    The input query is not used, it just triggers the chart generation.
    """
    return generate_performance_chart()


tools = [
    student_question_tool,
    revision_plan_tool,
    quiz_tool,
    motivation_tool,
    grade_and_save_quiz_tool,
    get_topic_performance_tool,
    performance_chart_tool,
]

llm = ChatOllama(model="llama3", temperature=0)

# --- NEW, STRICTER CUSTOM PROMPT ---
template = """Answer the user's request using the available tools. Your primary goal is to answer the user's question or fulfill their request.
Once the request is fulfilled, you MUST use the 'Final Answer' format to give the user the result and stop.
Do not perform any actions that the user did not explicitly ask for.

You have access to the following tools:
{tools}

Use the following format:

Thought: you should always think about what to do
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question

Begin!

Question: {input}
Thought:{agent_scratchpad}"""

prompt = PromptTemplate.from_template(template)

agent = create_react_agent(llm, tools, prompt)

agent_executor = AgentExecutor(
    agent=agent, tools=tools, verbose=True, max_iterations=5)
