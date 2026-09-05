# Build stage
FROM node:24-alpine AS builder

WORKDIR /app

# Copy package files
COPY package.json package-lock.json ./

# Install dependencies
RUN npm ci

# Copy source code
COPY . .

# Public, browser-reachable API origin. Next.js inlines NEXT_PUBLIC_* values
# into the client bundle at build time, so it must be supplied here (e.g.
# docker build --build-arg NEXT_PUBLIC_API_URL=https://skillet.example.com).
# For the recommended single-origin topology this equals the public site origin;
# the reverse proxy routes /api to the API container.
ARG NEXT_PUBLIC_API_URL
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL

# Build the application
RUN npm run build

# Production stage
FROM node:24-alpine

WORKDIR /app

# Copy package files
COPY package.json package-lock.json ./

# Install production dependencies only
RUN npm ci --omit=dev

# Copy built application from builder
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/public ./public

# Expose port
EXPOSE 3000

# Start application
CMD ["npm", "start"]
