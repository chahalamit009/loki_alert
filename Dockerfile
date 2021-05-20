FROM alpine

RUN apk --update add python3 py3-pip
WORKDIR /app


COPY requirements.txt requirements.txt

RUN pip3 install -r requirements.txt

EXPOSE 5000

COPY . .
CMD [ "python3", "index.py"]