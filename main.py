import os, config
from fastapi import FastAPI
from langserve.server import add_routes
from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_community.vectorstores import FAISS
from langchain_openai.embeddings import OpenAIEmbeddings
from langchain.memory import ConversationBufferWindowMemory
from langchain.chains import ConversationalRetrievalChain
from langchain_core.runnables import RunnableLambda


os.environ["OPENAI_API_KEY"] = config.open_ai_key

model = ChatOpenAI(model="gpt-4o-mini", temperature = 0.2)

embeddings = OpenAIEmbeddings(model = "text-embedding-3-small")

vectorstore = FAISS.load_local("vector_store", embeddings, allow_dangerous_deserialization = True)

retriever = vectorstore.as_retriever()

SYSTEM_PROMPT = "You are a friendly, helpful AI representative of Artisan AI. \n \
    You will answer the sentences using the provided context.  You will answer in at most five sentences. If the response is long or the information is complex, you will answer in points. \
        You will not hallucinate. If the user makes small talk, be friendly!"

memory = ConversationBufferWindowMemory(k=10, memory_key = "chat_history", output_key = "answer", input_key = "question", return_messages=True)

chain = ConversationalRetrievalChain.from_llm(
    llm=model,
    memory=memory,
    chain_type="stuff",
    retriever=retriever,
    return_source_documents=False,
    get_chat_history=lambda h : h,
    verbose=False)


app = FastAPI()


add_routes(app, chain | RunnableLambda(lambda x: x["answer"]) , path="/chat", playground_type="default")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)