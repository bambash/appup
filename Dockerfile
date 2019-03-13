FROM python:3.6-alpine

WORKDIR /opt/appup

COPY appup.py .

CMD python3 appup.py
