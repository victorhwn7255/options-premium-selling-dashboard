FROM node:20-alpine

WORKDIR /app

COPY package.json package-lock.json* ./
RUN npm install

COPY . .

ARG BACKEND_URL=http://localhost:8030
ENV BACKEND_URL=$BACKEND_URL

RUN npm run build

EXPOSE 3000

CMD ["npm", "start"]
