
FROM node:lts-slim as builder

WORKDIR /app


COPY package.json package-lock.json ./
RUN npm install


COPY . .


RUN npm run tailwind:build


FROM python:3.9-slim

WORKDIR /app


COPY requirements.txt /
RUN pip install --no-cache-dir -r /requirements.txt


COPY . /app/


COPY --from=builder /app/catering_app/static/catering_app/css /app/catering_app/static/catering_app/css


EXPOSE 8081


CMD ["python", "manage.py", "runserver", "0.0.0.0:8081"] 