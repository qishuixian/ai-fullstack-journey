cd backend
 # 创建虚拟环境（只需一次）
python -m venv venv         
 # 激活虚拟环境（每次打开终端都要执行）
.\venv\Scripts\activate     
  # 安装依赖

# 安装依赖（确保已安装 flagembedding、langchain-huggingface 等）
python -m pip install -r requirements.txt
# 启动服务（端口 8001）
uvicorn main:app --reload --port 8001
# 查看接口文档
http://localhost:8001/docs