FROM python:3.11.5

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip install -r requirements.txt
RUN pip install streamlit_mic_recorder gnews newspaper3k gtts


COPY . .
COPY ./.env.fastapi.example ./.env.fastapi

EXPOSE 8000

# Run app.py when the container launches
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]