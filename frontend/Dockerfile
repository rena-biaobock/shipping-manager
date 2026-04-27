FROM node:24-slim AS builder

ARG API_BASE_URL=/web/api/v1

WORKDIR /app
COPY package.json ./
RUN npm install
COPY . .
RUN API_BASE_URL=${API_BASE_URL} npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
