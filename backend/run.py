"""一键启动：起后端 FastAPI(8000)。前端另开静态服务即可托管。

用法:
    python backend/run.py
"""
import subprocess, sys, os

def main():
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    print("启动 知危鉴 后端 API ... http://127.0.0.1:8000/docs")
    subprocess.call([sys.executable, "-m", "uvicorn", "app.main:app", "--reload", "--port", "8000"])

if __name__ == "__main__":
    main()
