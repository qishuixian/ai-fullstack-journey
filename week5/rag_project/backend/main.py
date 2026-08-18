import os
from dotenv import load_dotenv
load_dotenv()

os.environ["LANGCHAIN_TRACING_V2"] = "false"

from fastapi import FastAPI, UploadFile, File, HTTPException
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

app = FastAPI(title="RAG Knowledge Base (DeepSeek)")

# ============ 全局初始化 ============
print("🚀 初始化 RAG 组件...")

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1200,
    chunk_overlap=300,
    separators=["\n\n", "\n", "。", "！", "？", " ", ""]
)

embeddings = HuggingFaceEmbeddings(model_name="BAAI/bge-small-zh-v1.5")
vectordb = Chroma(embedding_function=embeddings, persist_directory="./chroma_db")

llm = ChatOpenAI(
    model="deepseek-chat",
    openai_api_key=os.getenv("DEEPSEEK_API_KEY"),
    openai_api_base="https://api.deepseek.com/v1",
    temperature=0
)

print("✅ RAG 组件初始化完成")

@app.post("/upload")
async def upload_pdf(file: UploadFile = File(...)):
    safe_filename = file.filename.replace(" ", "_").replace("(", "").replace(")", "")
    temp_path = f"temp_{safe_filename}"
    try:
        content = await file.read()
        with open(temp_path, "wb") as f:
            f.write(content)

        loader = PyPDFLoader(temp_path)
        docs = loader.load()
        splits = text_splitter.split_documents(docs)

        vectordb.add_documents(splits)
        # Chroma 0.4.x 自动持久化，无需手动 persist

        return {"status": "success", "chunks": len(splits)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"处理 PDF 失败：{str(e)}")
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

@app.get("/ask")
async def ask_question(query: str):
    if not query.strip():
        raise HTTPException(status_code=400, detail="问题不能为空")

    # 1. 直接检索（取前10个最相关文档）
    candidate_docs = vectordb.similarity_search(query, k=10)

    if not candidate_docs:
        return {
            "answer": "知识库中暂无相关文档，请先上传 PDF 文件。",
            "sources": []
        }

    # 2. 拼接上下文
    context_str = "\n\n".join([doc.page_content for doc in candidate_docs])

    # 3. 调用 LLM
    messages = [
        SystemMessage(content="你是一个知识库问答助手。请严格基于【上下文】回答【问题】。如果上下文中有相关信息，请直接提取并回答；如果上下文信息不足以回答，请结合上下文合理推断。绝对不要直接回复'未找到相关信息'。"),
        HumanMessage(content=f"【上下文】\n{context_str}\n\n【问题】\n{query}\n\n请回答：")
    ]
    response = llm.invoke(messages)

    sources = [doc.page_content[:200] for doc in candidate_docs[:3]]
    return {
        "answer": response.content,
        "sources": sources
    }

@app.get("/")
def root():
    return {"message": "RAG API (DeepSeek) is running on port 8001"}