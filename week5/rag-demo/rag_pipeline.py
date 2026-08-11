import os
from dotenv import load_dotenv
load_dotenv()

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_openai import ChatOpenAI, OpenAIEmbeddings

# ============ 1. 加载 PDF ============
print("📄 正在加载 PDF...")
loader = PyPDFLoader("sample.pdf")  # 替换为你的 PDF
docs = loader.load()
print(f"   共加载 {len(docs)} 页")

# ============ 2. 文本切片 ============
print("✂️ 正在切片...")
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,
    chunk_overlap=100,
    separators=["\n\n", "\n", " ", ""]
)
splits = text_splitter.split_documents(docs)
print(f"   共切成 {len(splits)} 块")

# ============ 3. 向量化（使用 HuggingFace 本地模型，免费）============
print("🧠 正在生成向量并存入 ChromaDB...")
from langchain_community.embeddings import HuggingFaceEmbeddings
embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

vectordb = Chroma.from_documents(
    documents=splits,
    embedding=embeddings,
    persist_directory="./chroma_db"
)
vectordb.persist()
print("✅ 向量数据库创建完成！")

# ============ 4. 构建 RAG 问答链（使用 DeepSeek 的 OpenAI 兼容接口）============
print("🤖 构建 RAG 问答链...")
llm = ChatOpenAI(
    model="deepseek-chat",                # DeepSeek 的模型名
    openai_api_key=os.getenv("DEEPSEEK_API_KEY"),  # 你的 DeepSeek Key
    openai_api_base="https://api.deepseek.com/v1", # DeepSeek 的 API 地址
    temperature=0
)

from langchain.chains import RetrievalQA
qa_chain = RetrievalQA.from_chain_type(
    llm=llm,
    chain_type="stuff",
    retriever=vectordb.as_retriever(search_kwargs={"k": 3}),
    return_source_documents=True
)

# ============ 5. 交互式问答 ============
print("\n💬 RAG 知识库已就绪！输入问题（输入 'quit' 退出）：")
while True:
    query = input("\n❓ 请输入问题: ")
    if query.lower() == 'quit':
        break
    result = qa_chain.invoke({"query": query})
    print(f"\n📝 答案: {result['result']}")
    print("\n📚 参考来源:")
    for i, doc in enumerate(result['source_documents'], 1):
        print(f"   [{i}] {doc.page_content[:150]}...")