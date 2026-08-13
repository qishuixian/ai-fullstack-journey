import os
from dotenv import load_dotenv
load_dotenv()

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_openai import ChatOpenAI
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate
from FlagEmbedding import FlagReranker

# ============ 1. 加载 PDF ============
print("📄 正在加载 PDF...")
loader = PyPDFLoader("sample.pdf")
docs = loader.load()
print(f"   共加载 {len(docs)} 页")

# ============ 2. 文本切片 ============
print("✂️ 正在切片...")
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,
    chunk_overlap=50,
    separators=["\n\n", "\n", " ", ""]
)
splits = text_splitter.split_documents(docs)
print(f"   共切成 {len(splits)} 块")

# ============ 3. 向量化（HuggingFace 本地模型）============
print("🧠 正在生成向量并存入 ChromaDB...")
embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
vectordb = Chroma.from_documents(
    documents=splits,
    embedding=embeddings,
    persist_directory="./chroma_db"
)
print("✅ 向量数据库创建完成！")

# ============ 初始化重排序模型 ============
print("🔄 初始化重排序模型（首次运行会下载模型）...")
reranker = FlagReranker(
    "BAAI/bge-reranker-v2-m3",
    use_fp16=False  # CPU 设为 False，有 GPU 可设为 True
)

def rerank_documents(query: str, docs: list, top_n: int = 3):
    """对检索到的文档进行重排序"""
    pairs = [(query, doc.page_content) for doc in docs]
    scores = reranker.compute_score(pairs, normalize=True)
    ranked = sorted(zip(scores, docs), key=lambda x: x[0], reverse=True)
    return [doc for _, doc in ranked[:top_n]]

# ============ 4. 构建 RAG 问答链（使用 DeepSeek）============
print("🤖 构建 RAG 问答链...")
llm = ChatOpenAI(
    model="deepseek-chat",
    openai_api_key=os.getenv("DEEPSEEK_API_KEY"),
    openai_api_base="https://api.deepseek.com/v1",
    temperature=0
)

prompt = ChatPromptTemplate.from_messages([
    ("system", "你是一个知识库助手，请根据上下文回答问题。如果上下文信息不足，请基于上下文进行合理推断；如果完全无关，再回答'未找到相关信息'。")
    ("human", "上下文：{context}\n\n问题：{input}")
])

combine_docs_chain = create_stuff_documents_chain(llm, prompt)
retrieval_chain = create_retrieval_chain(vectordb.as_retriever(), combine_docs_chain)

# ============ 5. 交互式问答（流式 + Rerank）============
print("\n💬 RAG 知识库已就绪！输入问题（输入 'quit' 退出）：")
while True:
    query = input("\n❓ 请输入问题: ")
    if query.lower() == 'quit':
        break

    print("🔍 正在检索相关文档...")
    # 1. 先用 ChromaDB 粗筛（召回 Top 10）
    candidate_docs = vectordb.similarity_search(query, k=10)
    print(f"   召回 {len(candidate_docs)} 个候选片段")

    print("🎯 正在重排序...")
    # 2. 用 BGE 精排（取 Top 3）
    top_docs = rerank_documents(query, candidate_docs, top_n=3)
    print(f"   精排出 {len(top_docs)} 个最相关片段")

    print("\n🤖 AI 回答：", end="", flush=True)
    # 3. 将精排后的文档作为 context 注入（需要构造一个临时检索器）
    # 这里采用最直接的方式：手动构造一个包含精排文档的列表，传给 chain
    # 注意：create_retrieval_chain 的 stream 输出中 context 来自检索器，
    # 但我们已手动筛选，所以直接使用 llm + prompt 生成即可
    from langchain_core.runnables import RunnablePassthrough
    from langchain_core.output_parsers import StrOutputParser

    # 构建一个简单的 chain：prompt -> llm -> str_output
    chain = (
        {"context": lambda x: "\n\n".join([doc.page_content for doc in top_docs]),
         "input": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )

    for chunk in chain.stream(query):
        print(chunk, end="", flush=True)
    print()