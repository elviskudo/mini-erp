import { Server } from "socket.io";
import { createClient } from "redis";
import { createAdapter } from "@socket.io/redis-adapter";
import { Kafka } from "kafkajs";
import dotenv from "dotenv";

dotenv.config();

const REDIS_URL = process.env.REDIS_URL || "redis://localhost:6379";
const KAFKA_BROKERS = (process.env.KAFKA_BROKERS || "localhost:9092").split(",");

// Initialize Kafka
const kafka = new Kafka({
    clientId: "mini-erp-realtime",
    brokers: KAFKA_BROKERS,
    retry: {
        initialRetryTime: 100,
        retries: 8
    }
});

const consumer = kafka.consumer({ groupId: "realtime-notifications" });

(async () => {
    // 1. Setup Redis Adapter for horizontal scaling
    const pubClient = createClient({ url: REDIS_URL });
    const subClient = pubClient.duplicate();
    await Promise.all([pubClient.connect(), subClient.connect()]);
    console.log("✓ Connected to Redis");

    // 2. Setup Socket.IO
    const io = new Server(3001, {
        cors: { origin: "*" },
        adapter: createAdapter(pubClient, subClient)
    });

    console.log("✓ Realtime server starting on port 3001...");

    io.on("connection", (socket) => {
        console.log("Client connected:", socket.id);

        // Get tenant_id from auth handshake
        const tenantId = socket.handshake.auth?.tenantId || socket.handshake.query?.tenant_id;
        const userId = socket.handshake.auth?.userId || socket.handshake.query?.user_id;

        // Join tenant-specific room
        if (tenantId) {
            const tenantRoom = `room_tenant_${tenantId}`;
            socket.join(tenantRoom);
            console.log(`Socket ${socket.id} joined tenant room: ${tenantRoom}`);
        }

        // Join user-specific room for direct messages
        if (userId) {
            const userRoom = `room_user_${userId}`;
            socket.join(userRoom);
            console.log(`Socket ${socket.id} joined user room: ${userRoom}`);
        }

        // Also join global room for system-wide announcements
        socket.join("global_notifications");

        socket.on("disconnect", () => {
            console.log("Client disconnected:", socket.id);
        });

        // Handle switching tenant rooms (for users with multiple tenants)
        socket.on("switch_tenant", (newTenantId) => {
            // Leave old tenant room
            for (const room of socket.rooms) {
                if (room.startsWith("room_tenant_")) {
                    socket.leave(room);
                }
            }
            // Join new tenant room
            if (newTenantId) {
                const tenantRoom = `room_tenant_${newTenantId}`;
                socket.join(tenantRoom);
                console.log(`Socket ${socket.id} switched to tenant room: ${tenantRoom}`);
            }
        });
    });

    // 3. Connect to Kafka & Consume Notifications
    try {
        await consumer.connect();
        console.log("✓ Connected to Kafka");

        // Subscribe to notification topics
        await consumer.subscribe({
            topics: ["mini-erp.notifications"],
            fromBeginning: false
        });

        console.log("✓ Subscribed to Kafka topics, waiting for messages...");

        await consumer.run({
            eachMessage: async ({ topic, partition, message }) => {
                try {
                    const content = message.value.toString();
                    console.log(`Received from ${topic}:`, content);

                    const payload = JSON.parse(content);

                    // Determine target room based on payload
                    if (payload.tenant_id) {
                        const tenantRoom = `room_tenant_${payload.tenant_id}`;
                        io.to(tenantRoom).emit("notification", payload);
                        console.log(`Notification sent to ${tenantRoom}`);
                    } else if (payload.user_id) {
                        const userRoom = `room_user_${payload.user_id}`;
                        io.to(userRoom).emit("notification", payload);
                        console.log(`Notification sent to ${userRoom}`);
                    } else {
                        io.to("global_notifications").emit("notification", payload);
                        console.log("Notification broadcast globally");
                    }
                } catch (e) {
                    console.error("Error processing message:", e);
                }
            },
        });
    } catch (e) {
        console.error("Kafka Connection Error:", e);
        setTimeout(() => {
            console.log("Retrying Kafka connection...");
            process.exit(1);
        }, 5000);
    }

    // 4. Subscribe to other event topics for real-time updates
    try {
        const eventConsumer = kafka.consumer({ groupId: "realtime-events" });
        await eventConsumer.connect();

        await eventConsumer.subscribe({
            topics: [
                "mini-erp.inventory",
                "mini-erp.finance",
                "mini-erp.procurement",
                "mini-erp.hr"
            ],
            fromBeginning: false
        });

        await eventConsumer.run({
            eachMessage: async ({ topic, partition, message }) => {
                try {
                    const payload = JSON.parse(message.value.toString());
                    const eventType = topic.replace("mini-erp.", "");

                    if (payload.tenant_id) {
                        const tenantRoom = `room_tenant_${payload.tenant_id}`;
                        io.to(tenantRoom).emit(`event:${eventType}`, payload);
                    }
                } catch (e) {
                    console.error("Error processing event:", e);
                }
            }
        });

        console.log("✓ Subscribed to event topics for real-time updates");
    } catch (e) {
        console.error("Failed to setup event consumer:", e);
    }

    // Health check
    setInterval(() => {
        const roomCounts = {};
        for (const [room, sockets] of io.sockets.adapter.rooms) {
            if (room.startsWith("room_tenant_")) {
                roomCounts[room] = sockets.size;
            }
        }
        console.log("♥ Realtime server alive. Clients:", io.engine.clientsCount, "Tenant rooms:", roomCounts);
    }, 60000);

})();
