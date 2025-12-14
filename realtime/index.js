const { Server } = require("socket.io");
const { createClient } = require("redis");
const { createAdapter } = require("@socket.io/redis-adapter");
const amqp = require("amqplib");
require("dotenv").config();

const REDIS_URL = process.env.REDIS_URL || "redis://localhost:6379";
const RABBITMQ_URL = process.env.RABBITMQ_URL || "amqp://user:password@localhost:5672";

(async () => {
    // 1. Setup Redis Adapter
    const pubClient = createClient({ url: REDIS_URL });
    const subClient = pubClient.duplicate();
    await Promise.all([pubClient.connect(), subClient.connect()]);

    // 2. Setup Socket.IO
    const io = new Server(3001, {
        cors: { origin: "*" },
        adapter: createAdapter(pubClient, subClient)
    });

    console.log("Realtime server starting on port 3001...");

    io.on("connection", (socket) => {
        console.log("Client connected:", socket.id);
        socket.join("global_notifications");

        socket.on("disconnect", () => {
            console.log("Client disconnected:", socket.id);
        });
    });

    // 3. Connect to RabbitMQ & Consume Notifications
    try {
        const conn = await amqp.connect(RABBITMQ_URL);
        const channel = await conn.createChannel();
        const queue = "notifications";

        await channel.assertQueue(queue, { durable: true });
        console.log("Connected to RabbitMQ, waiting for notifications...");

        channel.consume(queue, (msg) => {
            if (msg !== null) {
                const content = msg.content.toString();
                console.log("Received Notification:", content);

                try {
                    const payload = JSON.parse(content);
                    // Broadcast to all connected clients (for MVP)
                    // In real app, filter by payload.user_id
                    io.to("global_notifications").emit("notification", payload);
                } catch (e) {
                    console.error("Error parsing msg:", e);
                }

                channel.ack(msg);
            }
        });
    } catch (e) {
        console.error("RabbitMQ Connection Error:", e);
    }

    // Health check
    setInterval(() => {
        console.log("Realtime server alive. Clients:", io.engine.clientsCount);
    }, 60000);

})();
