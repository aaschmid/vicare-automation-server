FROM python:3.12 as requirement-stage

WORKDIR /tmp
RUN pip install poetry
COPY ./pyproject.toml ./poetry.lock /tmp/
RUN poetry self add poetry-plugin-export
RUN poetry export -f requirements.txt --output requirements.txt --without-hashes

FROM python:3.12
WORKDIR /code
COPY --from=requirement-stage /tmp/requirements.txt /code/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt
COPY ./app /code/app
COPY ./log-config.json /code/

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "80", "--log-config", "log-config.json"]
