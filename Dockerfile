FROM python:3.12-slim
WORKDIR /app
COPY . .
RUN pip install --no-cache-dir -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt

EXPOSE 8000

ENTRYPOINT ["python3", "main.py"]