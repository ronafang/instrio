FROM python:3.9

WORKDIR /server

COPY server/requirements.txt .

RUN if [ "$(uname -s)" = 'Linux' ]; then apt-get update && apt-get --yes install libsndfile1; fi

RUN pip install --no-cache-dir -r requirements.txt

COPY server/ .

ENV PYTHONPATH .

EXPOSE 8888

CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8888"]
