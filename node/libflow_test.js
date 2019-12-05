const path = require("path");

const express = require("express");
const app = express();
const httpServer = require("http").createServer(app);
const io = require("socket.io")(httpServer);

const PcivewSink = require("./pcvc");

app.use(express.static("static_web"));
app.get("/", function(req, res) {
  res.sendFile(__dirname + "/static_web/index.html");
});

let CoreConfig = {
  proxy: "libflow",
  ip: "192.168.0.233",
  port: "24011",
  sink: [
    {
      type: "camera",
      port: 1200
    },
    {
      type: "lane",
      port: 1203
    },
    {
      type: "vehicle",
      port: 1204
    },
    {
      type: "tsr",
      port: 1206
    },
    {
      type: "pcw",
      port: 1205
    }
  ],
  max_delay: 5,
  requireCamera: true
};

io.on("connection", socket => {
  console.log("new connetcion");
});

pcviewsink = new PcivewSink(CoreConfig);
pcviewsink.on("pcview", data => {
  console.log(data);
  io.emit("pcview", data);
});
pcviewsink.open();
httpServer.listen(3457);
