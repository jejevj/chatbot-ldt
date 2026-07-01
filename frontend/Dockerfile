# Multi-stage build for Frontend

# Stage 1: Build
FROM node:20-alpine AS builder

WORKDIR /app

# Accept build args
ARG VITE_API_BASE_URL
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci

# Copy source code
COPY . .

# Build the application with production env
RUN npm run build

# Stage 2: Production with Apache
FROM httpd:2.4-alpine

# Enable required modules
RUN sed -i \
    -e 's/^#\(LoadModule .*mod_rewrite.so\)/\1/' \
    -e 's/^#\(LoadModule .*mod_deflate.so\)/\1/' \
    -e 's/^#\(LoadModule .*mod_expires.so\)/\1/' \
    -e 's/^#\(LoadModule .*mod_headers.so\)/\1/' \
    /usr/local/apache2/conf/httpd.conf

# Copy Apache vhost config
COPY apache.conf /usr/local/apache2/conf/extra/httpd-vhosts.conf

# Include vhosts config (idempotent)
RUN grep -q 'httpd-vhosts.conf' /usr/local/apache2/conf/httpd.conf \
    || echo 'Include conf/extra/httpd-vhosts.conf' >> /usr/local/apache2/conf/httpd.conf

# Copy built files — taruh di subfolder /chatbot/ sesuai vite base
COPY --from=builder /app/dist /usr/local/apache2/htdocs/chatbot/

# Apache listen 80 di dalam container, Docker mapping ke 8766 di luar
EXPOSE 80

# Start Apache
CMD ["httpd-foreground"]
