import os
# import config
from fastapi import FastAPI
from langserve.server import add_routes
from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_community.vectorstores import FAISS
from langchain_openai.embeddings import OpenAIEmbeddings

from langchain_core.runnables import RunnableLambda
from langchain.chains import create_history_aware_retriever, create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
from typing import Any
from langchain.pydantic_v1 import BaseModel


# os.environ["OPENAI_API_KEY"] = config.open_ai_key

# Define model
model = ChatOpenAI(model="gpt-4o-mini", temperature = 0.2)

# Define vector embeddings for similarity search in the index
embeddings = OpenAIEmbeddings(model = "text-embedding-3-small")

# Load vectorstore with scraped data
vectorstore = FAISS.load_local("vector_store", embeddings, allow_dangerous_deserialization = True)

# Convert vectorstore into retriever
retriever = vectorstore.as_retriever()

SYSTEM_PROMPT = "You are a friendly, helpful AI representative of Artisan AI. \n \
    You will answer the sentences using the provided context {context}.  You will answer in at most five sentences. If the response is long or the information is complex, you will answer in points. \
    You will not hallucinate. If the user makes small talk, be friendly! Do not answer from privacy policy documents unless the user specifically asks about it."

CONTEXT_PROMPT = "Given chat history and latest user prompt, check if the user prompt references anything in chat history. If yes, forumlate a standalone question which can be understood without the chat history: combine information from chat history and reference what the user mentioned before. If no, use the same user prompt. If unsure, ask the user to repeat their question. Do not answer the user prompt."

# Prompt to include chat history
contextualized_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", CONTEXT_PROMPT),
        MessagesPlaceholder("chat_history"),
        ("human", "{input}"),
    ]
)

# Create the history aware retriever
history_aware_retriever = create_history_aware_retriever(
    model, retriever, contextualized_prompt
)

# Create final user prompt which takes into account chat history and instructions
user_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", SYSTEM_PROMPT),
        MessagesPlaceholder("chat_history"),
        ("human", "{input}"),
    ]
)

# Chain the LLM and the main prompt
question_answer_chain = create_stuff_documents_chain(model, user_prompt)

# Add the history awareness of chats to the main model
rag_chain = create_retrieval_chain(history_aware_retriever, question_answer_chain)

store = {}

# Used to store chat history sessions
def get_session_history(session_id: str) -> BaseChatMessageHistory:
    if session_id not in store:
        store[session_id] = ChatMessageHistory()
    return store[session_id]

# Define input and output type for the playground to work
class Input(BaseModel):
    input: str

class Output(BaseModel):
    answer: Any

# Final chain
conversational_rag_chain = RunnableWithMessageHistory(
    rag_chain,
    get_session_history,
    input_messages_key="input",
    history_messages_key="chat_history",
    output_messages_key="answer",
).with_types(input_type=Input, output_type=Output)

# Deploy application using FastAPI and extract the answer parameter to print out
app = FastAPI()

# Add route /chat
add_routes(app, conversational_rag_chain | RunnableLambda(lambda x: x["answer"]) , path="/chat", playground_type="default")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)