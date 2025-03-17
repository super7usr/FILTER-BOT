FROM python:3.10.8-slim-buster

# Update package list and install ffmpeg
RUN apt-get update -qq && apt-get -y install ffmpeg

# Install git
RUN apt-get install git -y

# Copy requirements file
COPY requirements.txt /requirements.txt

# Install Python dependencies
RUN pip3 install -U pip && pip3 install -U -r /requirements.txt

# Create and set the working directory
RUN mkdir /VJ-FILTER-BOT
WORKDIR /VJ-FILTER-BOT

# Copy all files into the container
COPY . /VJ-FILTER-BOT

# Ensure ffprobe is in the PATH
RUN ln -s /usr/bin/ffprobe /usr/local/bin/ffprobe

# Start the bot
CMD ["python", "bot.py"]
