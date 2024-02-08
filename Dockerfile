FROM python:3.12

ENV PYTHONUNBUFFERED 1
RUN apt-get update && apt-get install supervisor -y

# Set work directory
WORKDIR /home/app

# Install dependencies
RUN pip install --upgrade pip
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

# Copy project
COPY creditApproval.conf /etc/supervisor/conf.d/
COPY . .
