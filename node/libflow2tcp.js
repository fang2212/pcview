/*
*/

const nano = require("nanomsg");
const WebSocket = require("ws");
const msgpack = require("msgpack");
const events = require('events');
const server = require("./server");

const packMessage = function (source, topic, data) {
  const obj = {source, topic, data};
  return msgpack.pack(obj);
};

class LibflowSink extends events.EventEmitter {
  constructor(addr, topics) {
    super();
    this.addr = addr;
    this.topics = topics 
    this.ws = null;
    this.init();
  }

  init() {
  }

  open() {
    this.ws = new WebSocket(this.addr);
    this.ws.on('open', () => {
      this.topics.forEach( topic => {
        const msg = packMessage('fd', 'subscribe', topic);
        this.ws.send(msg);
      })
    });
    this.ws.on('message', (data) => {
      if (data instanceof Buffer) {
        this.emit("data", data); // recv_ts, type, buf
      }
    });
    this.ws.on('close', (data) => {
      console.log("libflow sink on close", data);
      this.emit("close"); // recv_ts, type, buf
    });
    this.ws.on('error', (err) => {
      console.log("libflow sink on error", err);
      this.emit("error", err);
    });
  }

  reopen() {
    console.log("reopen libflow sink")
    this.close();
    //待完全关闭后再重启
    setTimeout(()=>{
      this.open()
    }, 1000);
  }

  close() {
    if (this.ws) {
      this.topics.forEach( topic => {
        const msg = packMessage('syncnode', 'unsubscribe', topic);
        this.ws.send(msg);
      })
      setTimeout(()=>{
          this.ws.close();
          this.ws = null;
      }, 500);
    }
  }
}

const addr = 'ws://192.168.0.233:24011'
const topics = ['pcview']
const tcpServer = new server.BlockServer('tcpServer', "0.0.0.0:12032");
const sink = new LibflowSink(addr, topics);

sink.on('data', data => {
  sendBuf(data);
})

tcpServer.on('connection', conn => {
  sink.open();
})

const sendBuf = (buf) => {
  tcpServer.clients.forEach( conn => {
    if (!conn.closed) conn.send(buf);
  })
}

const startTcpServer = () => {
  tcpServer.open();
}

startTcpServer();
