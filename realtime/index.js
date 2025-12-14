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

                    // Determine target room based on payload
                    if (payload.tenant_id) {
                        // Send to specific tenant room only
                        const tenantRoom = `room_tenant_${payload.tenant_id}`;
                        io.to(tenantRoom).emit("notification", payload);
                        console.log(`Notification sent to ${tenantRoom}`);
                    } else if (payload.user_id) {
                        // Send to specific user only
                        const userRoom = `room_user_${payload.user_id}`;
                        io.to(userRoom).emit("notification", payload);
                        console.log(`Notification sent to ${userRoom}`);
                    } else {
                        // Broadcast to all (system announcement)
                        io.to("global_notifications").emit("notification", payload);
                        console.log("Notification broadcast globally");
                    }
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
        const roomCounts = {};
        for (const [room, sockets] of io.sockets.adapter.rooms) {
            if (room.startsWith("room_tenant_")) {
                roomCounts[room] = sockets.size;
            }
        }
        console.log("Realtime server alive. Clients:", io.engine.clientsCount, "Tenant rooms:", roomCounts);
    }, 60000);

})();
