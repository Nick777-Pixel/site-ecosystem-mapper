FROM python:3.8-slim-buster

COPY requirements.txt requirements.txt

RUN pip install -r requirements.txt

COPY . .

CMD sh setup.sh && streamlit run app/main.py
