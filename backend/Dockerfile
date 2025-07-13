FROM public.ecr.aws/lambda/python:3.12

# Install Poetry using official installer
RUN curl -sSL https://install.python-poetry.org | python3 -

# Add Poetry to PATH
ENV PATH="/root/.local/bin:$PATH"

# Copy Poetry configuration files
COPY pyproject.toml .
COPY poetry.lock .

# Install dependencies
RUN poetry config virtualenvs.create false && \
    poetry install --no-interaction --no-ansi --no-root

# Copy the application code
COPY app/ ./app/
 
# Set entrypoint
CMD [ "app.main.handler" ]