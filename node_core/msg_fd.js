/*
*/

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
      if (this.ws)
        this.ws.close();
      this.ws = null;
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

let ip = '192.168.0.233' ;
if (process.argv.length == 3) {
  ip = process.argv[2];
}

// const addr = 'ws://192.168.0.233:24011'
const addr = 'ws://'+ip+':24011'
const topics = ['pcview']
const tcpServer = new server.BlockServer('tcpServer', "0.0.0.0:12032");
let sink = null
// let sink = new LibflowSink(addr, topics);

tcpServer.on('connection', conn => {
  if (!sink) {
    sink = new LibflowSink(addr, topics);
    sink.on('error', (error) => {
      console.log('fd get error', error)
    })
    sink.on('close', (msg) => {
      console.log('fd get close', msg)
      if (sink) {
        sink = null;
      }
      tcpServer.clients.forEach( conn => {
        if (!conn.closed) conn.close();
      })
    })
    sink.on('data', data => {
      //console.log(data);
      if (tcpServer.clients.length) {
        sendBuf(data);
      } else if (sink) {
        sink.close();
        sink = null;
      }
    })
    sink.open();
  }
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
