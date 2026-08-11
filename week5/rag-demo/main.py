from fastapi import FastAPI, UploadFile, File
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain.chains import RetrievalQA

app = FastAPI()

# 1. 初始化模型和数据库
embeddings = OpenAIEmbeddings()
llm = ChatOpenAI(model="gpt-3.5-turbo")
vectordb = Chroma(embedding_function=embeddings, persist_directory="./chroma_db")

@app.post("/upload")
async def upload_pdf(file: UploadFile = File(...)):
    # 保存临时文件
    with open(file.filename, "wb") as f:
        f.write(await file.read())
    
    # LangChain 管道开始
    loader = PyPDFLoader(file.filename)
    docs = loader.load()
    
    # 切片
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    splits = text_splitter.split_documents(docs)
    
    # 存入 ChromaDB
    vectordb.add_documents(splits)
    
    return {"status": "PDF processed and stored"}

@app.get("/ask")
async def ask_question(query: str):
    # 构建 RAG 链
    qa_chain = RetrievalQA.from_chain_type(
        llm, retriever=vectordb.as_retriever(), return_source_documents=True
    )
    
    result = qa_chain.invoke({"query": query})
    return {
        "answer": result["result"],
        "sources": [doc.page_content for doc in result["source_documents"]] # 溯源关键
    }