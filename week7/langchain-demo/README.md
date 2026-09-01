cd langchain-demo
python -m venv venv          # 创建虚拟环境（只需一次）
.\venv\Scripts\activate      # 激活虚拟环境（每次打开终端都要执行）
python -m pip install -r requirements.txt  # 安装依赖

# 配置模型凭证（二选一）
Copy-Item .env.example .env
# 然后把 .env 里的 your_deepseek_api_key 改成你自己的 key

# 或者只在当前 PowerShell 会话里临时设置
$env:DEEPSEEK_API_KEY="你的 DeepSeek API Key"

python agent_day1.py

