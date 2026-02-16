FROM python:3.11-slim

# Install all system dependencies and LaTeX in one step to reduce update calls
RUN apt-get update && apt-get install -y \
    wget \
    curl \
    git \
    texlive-latex-base \
    texlive-fonts-recommended \
    texlive-latex-extra \
    texlive-science \
    texlive-publishers \
    ghostscript \
    imagemagick \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Create artifact directories
RUN mkdir -p artifacts/sample_content artifacts/images artifacts/data artifacts/output

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV DEEPAGENTS_HOME=/app/.deepagents

# Default command
CMD ["bash"]
