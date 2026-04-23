# Multi-stage build for Frontend

# Stage 1: Build
FROM node:20-alpine AS builder

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci

# Copy source code
COPY . .

# Build the application
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

# Copy Apache config
COPY apache.conf /usr/local/apache2/conf/extra/httpd-vhosts.conf

# Include vhosts config
RUN echo "Include conf/extra/httpd-vhosts.conf" >> /usr/local/apache2/conf/httpd.conf

# Copy built files from builder stage
COPY --from=builder /app/dist /usr/local/apache2/htdocs/

# Expose port
EXPOSE 8766

# Start Apache
CMD ["httpd-foreground"]
