FROM node:24-slim

WORKDIR /app

COPY package.json ./
RUN npm install --omit=dev

COPY src/ ./src/

ENV PORT=8080
ENV XLSX_PATH=/data/stock.xlsx
ENV CORS_ORIGINS=http://localhost

EXPOSE 8080
CMD ["node", "src/index.js"]
