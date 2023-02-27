FROM python:3.10
RUN apt-get -y update
RUN apt-get install -y ffmpeg
WORKDIR /bot
COPY requirements.txt /bot/
RUN pip install -r requirements.txt
COPY . /bot
CMD python bot.py
