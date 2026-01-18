FROM oven/bun:1-alpine

WORKDIR /app

COPY package.json bun.lockb* ./

RUN bun install

COPY . .

# Build for production (pre-compiles everything)
RUN bun run build

ENV HOST=0.0.0.0
ENV PORT=3000
ENV NODE_ENV=production

EXPOSE 3000

# Run production server (pre-built, fast startup)
CMD ["bun", "run", "preview"]
