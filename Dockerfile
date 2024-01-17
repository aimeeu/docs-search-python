# For more information, please refer to https://aka.ms/vscode-docker-python
FROM python:3.8.1

WORKDIR /docs-search
# Setup env
COPY . .

# Install pipenv and compilation dependencies
RUN python -m pip install -r requirements.txt

ENTRYPOINT ["/docs-search/entrypoint.sh"]
