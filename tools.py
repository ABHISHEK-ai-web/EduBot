import os
import json
import re
import random
from datetime import datetime
from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader, DirectoryLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings
from langchain_ollama import ChatOllama
from langchain.chains import RetrievalQA
import matplotlib.pyplot as plt
import pandas as pd

load_dotenv()


def setup_rag_knowledge_base():
    persist_directory = 'chroma_db_ollama'
    embeddings = OllamaEmbeddings(model="llama3")
    if os.path.exists(persist_directory):
        print("Loading knowledge base from disk...")
        vector_db = Chroma(persist_directory=persist_directory,
                           embedding_function=embeddings)
    else:
        print(
            "Building knowledge base... This will take a few minutes but only happens once.")
        loader = DirectoryLoader(
            './data/', glob="*.pdf", loader_cls=PyPDFLoader)
        documents = loader.load()
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000, chunk_overlap=200)
        texts = text_splitter.split_documents(documents)
        vector_db = Chroma.from_documents(
            documents=texts, embedding=embeddings, persist_directory=persist_directory)
        vector_db.persist()
        print("Knowledge base built and saved to disk.")
    return vector_db


db = setup_rag_knowledge_base()


def get_all_progress() -> list:
    try:
        with open('progress.json', 'r') as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        data = []
    return data


def save_quiz_result(details_string: str):
    try:
        score = 0
        out_of_match = re.search(
            r'(\d+)\s*out of\s*(\d+)', details_string, re.IGNORECASE)
        if out_of_match:
            score = int((int(out_of_match.group(1)) /
                        int(out_of_match.group(2))) * 100)
        else:
            score_match = re.search(r'(\d+)', details_string)
            if score_match:
                score = int(score_match.group(0))
            else:
                return "Error: Could not find a score in the provided text."
        topic_match = re.search(
            r'\s(in|on)\s(.+)', details_string, re.IGNORECASE)
        if topic_match:
            topic = topic_match.group(2)
        else:
            topic_match = re.search(
                r'(.*?)\s(quiz|test|score)', details_string, re.IGNORECASE)
            if topic_match:
                topic = topic_match.group(1)
            else:
                return "Error: Could not determine the topic from the text."
        topic = topic.strip().strip('"').strip("'")
        new_result = {"topic": topic, "score": score,
                      "date": datetime.now().strftime("%Y-%m-%d")}
        data = get_all_progress()
        data.append(new_result)
        with open('progress.json', 'w') as f:
            json.dump(data, f, indent=4)
        return f"Success. The score for '{topic}' has been saved as {score}%. The user's request is complete."
    except Exception as e:
        return f"An error occurred while trying to save the score: {e}"


def get_topic_performance(topic: str) -> str:
    all_progress = get_all_progress()
    topic_scores = [entry.get('score', 0) for entry in all_progress if entry.get(
        'topic', '').lower() == topic.lower()]
    if not topic_scores:
        return f"The student has not taken any quizzes on the topic '{topic}' yet."
    average_score = sum(topic_scores) / len(topic_scores)
    return (f"The student has taken {len(topic_scores)} quiz(zes) on '{topic}' with an average score of {average_score:.0f}%.")


def generate_performance_chart() -> str:
    progress_data = get_all_progress()
    if not progress_data:
        return "No progress data available to generate a chart. Take some quizzes first!"
    df = pd.DataFrame(progress_data)
    if 'score' not in df.columns or df.empty:
        return "Progress data is empty or contains no scores."
    df['quiz_instance'] = df.groupby('topic').cumcount() + 1
    df['chart_label'] = df['topic'] + '-' + df['quiz_instance'].astype(str)
    plt.figure(figsize=(10, 6))
    plt.bar(df['chart_label'], df['score'], color='skyblue')
    plt.ylabel('Score (%)')
    plt.xlabel('Quizzes')
    plt.title('Quiz Performance Over Time')
    plt.xticks(rotation=45, ha="right")
    plt.ylim(0, 100)
    plt.tight_layout()
    chart_filename = "progress_chart.png"
    plt.savefig(chart_filename)
    return f"I have generated a chart of your progress and saved it as '{chart_filename}'."


def answer_student_question(query: str) -> str:
    retriever = db.as_retriever(search_kwargs={"k": 3})
    llm = ChatOllama(model="llama3", temperature=0.5)
    qa_chain = RetrievalQA.from_chain_type(
        llm=llm, retriever=retriever, chain_type="stuff", return_source_documents=False)
    response = qa_chain.invoke({"query": query})
    return response['result']


def create_revision_plan(weak_topics: list, exam_date: str) -> str:
    llm = ChatOllama(model="llama3", temperature=0.8)
    prompt = f"""
    You are an expert academic coach. A student's exam is on: {exam_date}.
    Their weakest topics are: {', '.join(weak_topics)}.
    Today's date is {datetime.now().strftime('%Y-%m-%d')}.
    Create a clear, day-by-day revision plan to help them prepare.
    """
    response = llm.invoke(prompt)
    return response.content


def generate_quiz(details_string: str) -> str:
    topic = details_string
    difficulty = "medium"
    num_questions = 5
    num_match = re.search(r'(\d+)\s*questions', details_string, re.IGNORECASE)
    if num_match:
        num_questions = int(num_match.group(1))
    if "easy" in details_string.lower():
        difficulty = "easy"
    elif "hard" in details_string.lower():
        difficulty = "hard"
    topic = re.sub(r'\d+\s*questions', '', topic, flags=re.IGNORECASE)
    topic = topic.lower().replace("quiz", "").replace("on", "").replace(
        "me", "").replace("about", "").replace(difficulty, "").strip()

    llm = ChatOllama(model="llama3", temperature=0.5)
    prompt = f"""
    You are a quiz master. Create a {num_questions}-question multiple-choice quiz on the topic: '{topic}'.
    The difficulty should be: {difficulty}.
    IMPORTANT: You MUST follow all these rules:
    1. You must ensure all information in the questions, options, and rationales is 100% factually accurate. Do not invent facts.
    2. Format your output as a single, raw JSON string. The JSON should be a list of objects.
    3. Each object must have four keys: "question", "options" (a list of 4 strings), "correct_answer", and "rationale".
    4. The value for the "correct_answer" key MUST be the full text of the correct option, NOT its index number.
    5. Do not include any text or formatting like ```json before or after the JSON string.
    """
    response_content = llm.invoke(prompt).content

    # --- NEW ROBUST PARSING AND SHUFFLING LOGIC ---
    try:
        # Find the JSON list within the AI's response
        json_match = re.search(r'\[.*\]', response_content, re.DOTALL)
        if not json_match:
            # If no JSON is found, return an error message string
            return json.dumps([{"question": "Error: Could not generate a valid quiz. Please try again.", "options": [], "correct_answer": "", "rationale": ""}])

        quiz_list = json.loads(json_match.group(0))

        # Manually shuffle the options for each question to guarantee randomness
        for question in quiz_list:
            if isinstance(question.get("options"), list):
                random.shuffle(question["options"])

        # Return the modified, truly randomized quiz as a JSON string
        return json.dumps(quiz_list)
    except Exception as e:
        print(f"Error processing quiz JSON: {e}")
        # Return an error message in the expected JSON format
        return json.dumps([{"question": "Error: Failed to process the generated quiz. Please try again.", "options": [], "correct_answer": "", "rationale": ""}])


def give_motivation(student_name: str) -> str:
    llm = ChatOllama(model="llama3", temperature=1.0)
    prompt = f"Create a short, powerful, and friendly motivational message for a student named {student_name} who is preparing for an exam."
    response = llm.invoke(prompt)
    return response.content
