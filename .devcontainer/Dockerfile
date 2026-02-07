FROM mcr.microsoft.com/devcontainers/python:3.11-bullseye

# Install Node.js
RUN curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
    && apt-get install -y nodejs

# Create a non-root user (already exists in the base image as 'vscode')
USER vscode

# Set the working directory
WORKDIR /workspaces/TrendsAI
