/*
node pcview core driver
提供PcviewSink
功能 open
    close
    reopen
事件 pcview
    error
    close
*/

const nano = require("nanomsg");
const WebSocket = require("ws");
const msgpack = require("msgpack");
const events = require('events');


const packMessage = function (source, topic, data) {
  const obj = {source, topic, data};
  return msgpack.pack(obj);
};

class LibflowSink extends events.EventEmitter {
  constructor(addr, msgList) {
    super();
    this.addr = addr;
    this.msgList = msgList;
    this.ws = null;
    this.init();
  }

  init() {
  }

  open() {
    this.ws = new WebSocket(this.addr);
    this.ws.on('open', () => {
      this.msgList.forEach( msgType => {
        const topic = 'pcview.' + msgType;
        //console.log('sub topic', topic)
        const msg = packMessage('syncnode', 'subscribe', topic);
        this.ws.send(msg);
      })
    });
    this.ws.on('message', (data) => {
      if (data instanceof Buffer) {
        const obj = msgpack.unpack(data);
        this.emit("data", Date.now(), obj.topic.split('.')[1], obj.data); // recv_ts, type, buf
      }
    });
    this.ws.on('close', (data) => {
      console.log("libflow sink on close", data);
      this.emit("close"); // recv_ts, type, buf
    });
    this.ws.on('error', (err) => {
      console.log("libflow sink on error", err.message);
      this.emit("error", err);
    });
  }

  reopen() {
    console.log("reopen libflow sink")
    this.close();
    //待完全关闭后再重启
    setTimeout(()=>{
      this.open()
    }, 5000);
  }

  close() {
    if (this.ws) {
      this.msgList.forEach( msgType => {
        let topic = 'pcview.' + msgType;
        let msg = packMessage('syncnode', 'unsubscribe', topic);
        this.ws.send(msg);
      })
    }
    setTimeout(()=>{
        this.ws.close();
    }, 2000);
  }
}

class NanoSink extends events.EventEmitter {
  constructor(msgList) {
    /*
    msgList = [
      {
        type: "camera",
        addr:  "tcp://192.168.0.233:1200"
      },
      ... etc
    ]
    */
    super();
    this.msgList = msgList;
    this.init();
    // this.msgCnt = 0;
  }

  init() {
    this.msgList.forEach( msg => {
      msg['sub'] = null;
    })
  }

  open() {
    console.log("open nanosink")
    this.msgList.forEach( msg => {
      msg.sub = nano.socket("sub");
      msg.sub.connect(msg.addr);
      msg.sub.on("data", (buf) => {
        // console.log('get data')
        // this.msgCnt += 1; 
        // console.log(this.msgCnt)
        this.emit("data", Date.now(), msg.type, buf); // recv_ts, type, buf
      });
      msg.sub.on("close", (data) => {
        console.log("nanosink on close", data);
        this.emit("close"); // recv_ts, type, buf
      });
      msg.sub.on("error", (err) => {
        console.log("nanosink on error", err.message);
        this.emit("error", err);
      });
    })
  }

  reopen() {
    console.log("reopen nanosink")
    this.close();
    //待完全关闭后再重启
    setTimeout(()=>{
      this.open()
    }, 5000);
  }

  close() {
    console.log("close nanosink")
    this.msgList.forEach( msg => {
      if (msg.sub) {
        msg.sub.close();
        msg.sub = null;
      }
    })
  }
}


class PcviewSink extends events.EventEmitter {
  constructor(coreConfig) {
    super();
    const msgList = [];
    const addr = 'ws://' + coreConfig.ip + ':' + coreConfig.port;
    this.sink = null;
    this.cache = {};
    this.max_delay = coreConfig.max_delay;
    this.requireCamera = coreConfig.requireCamera;
    coreConfig.sink.forEach( sink =>{
      msgList.push({
        "type": sink.type,
        "addr": 'tcp://' + coreConfig.ip + ':' + sink.port
      });
      this.cache[sink.type] = [];
    })
    if (coreConfig.proxy == "nanomsg") {
      this.sink = new NanoSink(msgList);
    } else if (coreConfig.proxy == "libflow") {
      this.sink = new LibflowSink(addr, msgList);
    }
    this.init();
  }

  init() {
    this.sink.on("error", (err) => {
      this.emit("error", err)
    })
    this.sink.on("close", () => {
      this.emit("close")
    })
    this.sink.on("data", (recv_ts, msgType, msgBuf) => {
      let [frame_id, msgData] = PcviewSink.ParseBuf(recv_ts, msgType, msgBuf);
      this.cache[msgType].push(
        [frame_id, msgData]
      )
      this.syncMsg();
    })
  }

  syncMsg() {
    let delay = 0
    let min_id = -1
    const res = {}
    let all_have = true
    for (let key in this.cache) {
        let len = this.cache[key].length
        if (len > 0) {
            let new_delay = this.cache[key][len-1][0] - this.cache[key][0][0];
            if (new_delay > delay) delay = new_delay;
            if (min_id == -1 || this.cache[key][0][0]<min_id) {
              min_id = this.cache[key][0][0];
            }
        } else all_have = false;
    }
    if (all_have || delay>this.max_delay) {
      for (let key in this.cache) {
          let len = this.cache[key].length
          while (len>0 && this.cache[key][0][0]<=min_id) {
              if (this.cache[key][0][0] == min_id) {
                  res[key] = this.cache[key][0][1]
              }
              this.cache[key].shift();
              len -= 1;
          }
      }
    } else return;

    if (this.requireCamera && !('camera' in res)) {
      return
    }
    // console.log(res)
    this.emit('pcview', res);
    // console.log('pcview sync', min_id, 'frame msg')
  }

  reopen() {
    this.sink.reopen();
  }

  open() {
    this.sink.open();
  }
  
  close() {
    this.sink.close();
  }
}

PcviewSink.ParseBuf = (recv_ts, msgType, buf) => {
  let frame_id;
  if (msgType == 'camera') {
    frame_id = buf.readUInt32LE(4, 8)
    create_ts = buf.readUInt32LE(16, 20) + buf.readUInt32LE(20, 24)*(256**4);
    return [frame_id, {
      'frame_id':frame_id,
      'timestamp':create_ts,
      'recv_ts':recv_ts,
      'image': buf.slice(24)}
    ]
  } else {
    const obj = msgpack.unpack(buf);
    frame_id = parseInt(obj['frame_id']);
    obj['recv_ts'] = recv_ts;
    return [frame_id, obj];
  }
}

// pcviewsink unit test
/*
let CoreConfig = null;

const file = path.join(__dirname, 'config/minieye666.json');
if (fs.existsSync(file)) {
  CoreConfig = JSON.parse(fs.readFileSync(file));
}
const pcviewSink = new PcviewSink(CoreConfig);
pcviewSink.open();
*/

// nanomsg unit test
/*
const msgList = [
    {
      type: "lane",
      addr:  "tcp://192.168.0.233:1203"
    },
    {
      type: "tsr",
      addr:  "tcp://192.168.0.233:1206"
    }
  ]
const nanoSink = new NanoSink(msgList);
nanoSink.open();
setInterval(()=>{
  nanoSink.reopen();
}, 20000);
*/

exports = module.exports = PcviewSink;