const { Server } = require("socket.io");

const io = new Server(5000, {
  cors: {
    origin: "*", // 모든 출처 허용 (테스트용)
  },
});

console.log("=== Dummy Socket Server Running on Port 5000 ===");
console.log("Waiting for connection...");

io.on("connection", (socket) => {
  console.log(`Client Connected: ${socket.id}`);

  // update_location 이벤트 수신 시 로그 출력
  socket.on("update_location", (data) => {
    console.log("Received [update_location]:");
    console.log(JSON.stringify(data, null, 2));
    console.log("------------------------------------------------");
  });

  socket.on("disconnect", () => {
    console.log(`Client Disconnected: ${socket.id}`);
  });
});
