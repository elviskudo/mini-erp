FROM node:22-alpine

WORKDIR /app

COPY package.json .

RUN npm install

COPY . .

ENV HOST=0.0.0.0
ENV PORT=3000
ENV NUXT_PUBLIC_API_BASE=http://backend_api:8000

EXPOSE 3000

CMD ["npm", "run", "dev"]
