cd backend
python -m venv venv          # 创建虚拟环境（只需一次）
venv\Scripts\activate        # 激活虚拟环境（每次打开终端都要执行）
pip install -r requirements.txt  # 安装依赖

uvicorn main:app --reload --port 8000
python -m pip install sqlalchemy aiosqlite