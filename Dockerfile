FROM python:3.13
WORKDIR /app
COPY PythonProject/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY PythonProject/ .
EXPOSE 9999
CMD ["python", "main.py"]
