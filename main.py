import os
import config
from langchain_community.vectorstores import FAISS
from langchain_openai.embeddings import OpenAIEmbeddings
from create_vector_store import create_index
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain.chains.combine_documents import create_stuff_documents_chain

embeddings = OpenAIEmbeddings(model = "text-embedding-3-small")
os.environ["OPENAI_API_KEY"] = config.open_ai_key

def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)
try:
    try:
        vectorstore = FAISS.load_local("vector_store", embeddings, allow_dangerous_deserialization = True)
        retriever = vectorstore.as_retriever(search_type="similarity_score_threshold", search_kwargs={"score_threshold": 0.5})
    except Exception as e:
        print(e)
        print("Index not found")
        create_index()
        print("Index created with data")
    print("X")

    llm = ChatOpenAI(model = 'gpt-4o-mini')

    prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a helpful representative providing information on behalf of Artisan AI. You only know information relevant to this knowledge base. Do not answer unrelated questions and try to find the most related answer."),
    ("user", "{input}")   
])
    
    output_parser = StrOutputParser()

    rag_chain = (
    {"context": retriever | format_docs, "input": RunnablePassthrough()}
    | prompt
    | llm
    | StrOutputParser()
)   
    
    print(rag_chain.invoke("What services do you offer?"))

except Exception as m:
    print(m)
    









