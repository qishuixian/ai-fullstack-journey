# 1. Build stage
FROM node:20-alpine AS builder

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .
COPY .env.production ./.env.production

RUN npm run build

# 2. Runtime stage
FROM nginx:alpine

# Publish the built frontend under /ask/ to match the production subpath.
COPY --from=builder /app/dist /usr/share/nginx/html/ask/
COPY frontend-ask.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
