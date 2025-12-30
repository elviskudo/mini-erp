FROM oven/bun:1-alpine

WORKDIR /app

COPY package.json bun.lockb* ./

RUN bun install

COPY . .

ENV HOST=0.0.0.0
ENV PORT=3000

EXPOSE 3000

CMD ["bun", "run", "dev"]
