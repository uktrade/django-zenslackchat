FROM python:3.8 as build
WORKDIR /app

ADD requirements.txt .
RUN pip install -r requirements.txt --no-cache-dir
COPY . /app

FROM build as prod
EXPOSE 8000
CMD ["python", "-c", "import time; print('NOOP'); time.sleep(500)"]

FROM build as test
ADD requirements-test.txt .
RUN pip install -r requirements-test.txt
CMD ["pytest"]
