FROM python:3.8 as build
WORKDIR /app

ADD requirements.txt .
RUN pip install -r requirements.txt --no-cache-dir
COPY . /app

ENV DJANGO_SETTINGS_MODULE webapp.settings
ENV DB_HOST 127.0.0.1
ENV DB_PORT 5432
ENV DB_NAME service
ENV DB_USER service
ENV DB_PASSWORD service

FROM build as prod
EXPOSE 8000
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "webapp.wsgi"]`

FROM build as test
ADD requirements-test.txt .
RUN pip install -r requirements-test.txt
CMD ["pytest"]
