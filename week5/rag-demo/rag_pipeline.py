import os
from dotenv import load_dotenv
load_dotenv()

# 关闭 LangChain 遥测警告
os.environ["LANGCHAIN_TRACING_V2"] = "false"

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from FlagEmbedding import FlagReranker

# ============ 1. 加载 PDF ============
print("📄 正在加载 PDF...")
loader = PyPDFLoader("sample.pdf")
docs = loader.load()
print(f"   共加载 {len(docs)} 页")

# ============ 2. 文本切片 ============
print("✂️ 正在切片...")
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200,
    separators=["\n\n", "\n", "。", "！", "？", " ", ""]
)
splits = text_splitter.split_documents(docs)
print(f"   共切成 {len(splits)} 块")

# ============ 3. 向量化（换用中文专用模型）============
print("🧠 正在生成向量并存入 ChromaDB...")
embeddings = HuggingFaceEmbeddings(model_name="BAAI/bge-small-zh-v1.5")
vectordb = Chroma.from_documents(
    documents=splits,
    embedding=embeddings,
    persist_directory="./chroma_db"
)
print("✅ 向量数据库创建完成！")

# ============ 4. 初始化重排序模型 ============
print("🔄 初始化重排序模型（首次运行会下载模型）...")
reranker = FlagReranker("BAAI/bge-reranker-v2-m3", use_fp16=False)

# ============ 5. 构建 LLM ============
print("🤖 构建 RAG 问答链...")
llm = ChatOpenAI(
    model="deepseek-chat",
    openai_api_key=os.getenv("DEEPSEEK_API_KEY"),
    openai_api_base="https://api.deepseek.com/v1",
    temperature=0
)

# ============ 6. 交互式问答（极简直调版） ============
print("\n💬 RAG 知识库已就绪！输入问题（输入 'quit' 退出）：")

while True:
    query = input("\n❓ 请输入问题: ").strip()
    if query.lower() == 'quit':
        break

    print("🔍 正在检索相关文档...")
    
    # 1. 粗筛
    candidate_docs = vectordb.similarity_search(query, k=10)
    
    # 2. Rerank 精排
    pairs = [(query, doc.page_content) for doc in candidate_docs]
    scores = reranker.compute_score(pairs, normalize=True)
    ranked = sorted(zip(scores, candidate_docs), key=lambda x: x[0], reverse=True)
    
    print("🔍 [Debug] Rerank 分数:")
    for score, doc in ranked[:5]:
        # 打印更多内容方便排查
        print(f"   分数: {score:.4f} | 内容: {doc.page_content[:100]}...") 
        
    # 3. 提取精排文档（放宽阈值到 0.1）
    top_docs = [doc for score, doc in ranked[:3] if score >= 0.1]
    
    if not top_docs:
        print("⚠️ 警告：Rerank 分数过低，启用兜底策略！")
        # 如果连0.1都没有，强行拿分数最高的1个给LLM看看
        top_docs = [ranked[0][1]] if ranked else []
        
    # 4. 手动拼接上下文
    context_str = "\n\n".join([doc.page_content for doc in top_docs])
    print(f"📝 注入上下文长度: {len(context_str)} 字符")
    if len(context_str) < 50:
        print("🚨 严重告警：注入上下文极短，检索阶段失败！请检查PDF内容和切片。")
    
    # 5. 直接构造消息并调用 LLM
    messages = [
        SystemMessage(content="你是一个知识库问答助手。请严格基于【上下文】回答【问题】。即使上下文信息不完整，也请尝试提取相关信息回答。只有在上下文完全为空或与问题毫无关联时，才回答'未找到相关信息'。"),
        HumanMessage(content=f"【上下文】\n{context_str}\n\n【问题】\n{query}\n\n请回答：")
    ]
    
    response = llm.invoke(messages)
    print("\n🤖 AI 回答：", response.content)