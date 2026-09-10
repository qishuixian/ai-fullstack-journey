FROM node:22-alpine AS builder
WORKDIR /app/frontend
COPY package*.json ./
RUN npm ci
COPY . .
ENV VITE_BASE_URL=/messageAgent/ VITE_API_BASE_URL=/messageAgent/api/
RUN npm run build

FROM nginx:stable-alpine
COPY --from=builder /app/backend/static/ /usr/share/nginx/html/messageAgent/
COPY nginx.message-agent.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
