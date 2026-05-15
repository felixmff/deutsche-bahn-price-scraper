FROM apify/actor-python:3.12

WORKDIR /usr/src/app

COPY pyproject.toml README.md ./
COPY src ./src
COPY openapi ./openapi

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir "apify>=2.0.0" "httpx>=0.28.1" "pydantic>=2.0"

CMD ["python", "-m", "src"]
