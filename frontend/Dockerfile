FROM node:20-alpine

WORKDIR /app

COPY package.json package-lock.json* ./
RUN npm install

COPY . .

ARG BACKEND_URL=http://localhost:8030
ENV BACKEND_URL=$BACKEND_URL
# Navbar social links — NEXT_PUBLIC_* must exist at build time to be inlined into the bundle
ARG NEXT_PUBLIC_LINKEDIN_URL=
ARG NEXT_PUBLIC_TWITTER_URL=
ENV NEXT_PUBLIC_LINKEDIN_URL=$NEXT_PUBLIC_LINKEDIN_URL
ENV NEXT_PUBLIC_TWITTER_URL=$NEXT_PUBLIC_TWITTER_URL

RUN npm run build

EXPOSE 3000

CMD ["npm", "start"]
