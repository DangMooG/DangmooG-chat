FROM python:3.8

#
WORKDIR /usr/src/app
RUN apt-get update
RUN apt-get -y install libgl1-mesa-glx
#
COPY ./requirements.txt .

#
RUN pip install --no-cache-dir --upgrade -r requirements.txt

#
COPY . .

#
CMD ["uvicorn", "app:chat_app", "--host", "0.0.0.0", "--port", "2024"]