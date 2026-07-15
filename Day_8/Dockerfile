FROM node:22-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 python3-pip curl git \
    && rm -rf /var/lib/apt/lists/*

RUN npm install -g live-server

WORKDIR /app

CMD ["tail", "-f", "/dev/null"]
