FROM python:3.11.5

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip install -r requirements.txt

COPY . .
COPY ./.env.streamlit.example ./.env.streamlit

EXPOSE 8501


CMD ["streamlit", "run", "index.py"]
