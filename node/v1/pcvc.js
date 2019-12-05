const nano = require("nanomsg");
const WebSocket = require("ws");
const msgpack = require("msgpack");
const fs = require("fs");
const path = require("path")
const server = require("./server");
const ConvertMap = require("./convert").ConvertMap

let CoreConfig = null;

const file = path.join(__dirname, 'config/minieye666.json');
if (fs.existsSync(file)) {
  CoreConfig = JSON.parse(fs.readFileSync(file));
}

const tcpServer = new server.BlockServer('tcpServer', CoreConfig.export.addr);
tcpServer.client = null

const startTcpServer = function () {
  tcpServer.open();
  tcpServer.on('connection', (conn) => {
    console.log('client connect');
    if (tcpServer.client && !tcpServer.client.closed) {
      //抢占式
      //tcpServer.client.close();
      //SyncNode.CloseMsgSink();
      //独占式
      conn.close()
      return
    }
    //console.log('close old connect');
    tcpServer.client = conn;

    tcpServer.client.conn.on('close', () => {
      console.log('client close');
      tcpServer.client.close();
      SyncNode.CloseMsgSink();
    })
    tcpServer.client.conn.on('error', () => {
      console.log('client error');
    })
    //setTimeout(() => {
    SyncNode.OpenMsgSink();
    console.log('open msg sink');
    //}, 50)
  });
}

const packMessage = function (source, topic, data) {
  const obj = {source, topic, data};
  return msgpack.pack(obj);
};

class WebSocketSink {
  constructor(addr) {
    this.addr = addr;
    this.ws = null;
    this.init();
  }

  init() {
    this.ws = new WebSocket(this.addr);
    this.ws.on('open', () => {
      SyncNode.msgList.forEach( msgType => {
        let topic = 'pcview.' + msgType;
        //console.log('sub topic', topic)
        let msg = packMessage('syncnode', 'subscribe', topic);
        this.ws.send(msg);
      })
    });
    this.ws.on('message', (data) => {
      if (data instanceof Buffer) {
        const obj = msgpack.unpack(data);
        SyncNode.ParseMsg(0, obj.topic.split('.')[1], obj.data);
      }
    });
    this.ws.on('close', () => {
      console.log('ws close');
    });
    this.ws.on('error', (err) => {
      console.log('ws error');
      setTimeout(() => {
        this.ws.close();
        SyncNode.OpenMsgSink();
      }, 1000)
    });
  }

  close() {
    if (this.ws) {
      SyncNode.msgList.forEach( msgType => {
        let topic = 'pcview.' + msgType;
        let msg = packMessage('syncnode', 'unsubscribe', topic);
        this.ws.send(msg);
      })
      this.ws.close();
    }
  }
}

class NanoSink {
  constructor(addr, msgType) {
    this.addr = addr;
    this.msgType = msgType;
    this.sub = null;
    SyncNode.cache[msgType] = []
    this.init();
  }

  init() {
    this.sub = nano.socket("sub");
    this.sub.reconn(500);
    this.sub.maxreconn(60000);
    this.sub.connect(this.addr);
    this.sub.on("data", (buf) => {
      SyncNode.ParseMsg(0, this.msgType, buf);
    });
  }

  close() {
    this.sub.close();
  }
}

class SyncNode {
  static OpenMsgSink() {
    SyncNode.msgList = [];
    SyncNode.sinkList = [];
    for (let index in CoreConfig.sink) {
        SyncNode.cache[CoreConfig.sink[index].type] = [];
        SyncNode.msgList.push(CoreConfig.sink[index].type);
    }

    if (CoreConfig.proxy == 'ws') {
      let addr = 'ws://' + CoreConfig.ip + ':' + CoreConfig.port;
      SyncNode.sinkList.push(new WebSocketSink(addr));
    } else {
      const sinks = CoreConfig.sink
      for (let index in sinks) {
        let sink = sinks[index];
        let addr = "tcp://" + CoreConfig.ip + ":" + sink.port;
        SyncNode.sinkList.push(new NanoSink(addr, sink.type));
      }
    }
  }

  static CloseMsgSink() {
    SyncNode.sinkList.forEach( sink => {
      sink.close();
    })
    SyncNode.msgList = [];
    SyncNode.sinkList = [];
  }

  static ParseMsg(ts, msgType, buf) {
    let frame_id = -1;
    [frame_id, buf] = SyncNode.ParseBuf(msgType, buf);
    //console.log(frame_id, 'msgType', msgType);
    SyncNode.cache[msgType].push(
      [ts, frame_id, msgType, buf]
    )
    SyncNode.SyncMsg();
  }

  static SyncMsg() {
    let delay = 0
    let min_id = -1
    const res = {}
    let all_have = true
    for (let key in SyncNode.cache) {
        let len = SyncNode.cache[key].length
        if (len > 0) {
            let new_delay = SyncNode.cache[key][len-1][1] - SyncNode.cache[key][0][1];
            if (new_delay > delay) delay = new_delay;
            if (min_id == -1 || SyncNode.cache[key][0][1]<min_id) {
              min_id = SyncNode.cache[key][0][1];
            }
        } else all_have = false;
    }
    if (all_have || delay>CoreConfig.max_delay) {
      for (let key in SyncNode.cache) {
          let len = SyncNode.cache[key].length
          while (len>0 && SyncNode.cache[key][0][1]<=min_id) {
              if (SyncNode.cache[key][0][1] == min_id) {
                  res[key] = SyncNode.cache[key][0]
              }
              SyncNode.cache[key].shift();
              len -= 1;
          }
      }
    }
    // console.log('get msg')
    if (res.length == 0 || !('camera' in res)) {
      return
    }
    if (CoreConfig.export.requireCamera && !('camera' in res)) {
      return
    }
    // console.log(res)
    if (tcpServer.client && !tcpServer.client.closed){
      console.log('send', min_id, 'frame msg')
      const exportList = SyncNode.msgList;
      let sendBuf = null;
      for (let index in exportList) {
        let key = exportList[index];
        if (key in res) sendBuf = res[key][3]
        else {
          sendBuf = Buffer.from('{}');
        }
        tcpServer.client.send(sendBuf);
      }
    }
  }
}
SyncNode.cache = {};
SyncNode.msgList = [];
SyncNode.sinkList = [];
SyncNode.ParseBuf = (msgType, buf) => {
  let frame_id;
  if (msgType == 'camera') {
    frame_id = buf.readUInt32LE(4, 8)
    if (CoreConfig.export.proxy == 'tcp') {
      buf = Buffer.concat([buf.slice(4, 8), buf.slice(24)])
    }
    return [frame_id, buf]
  } else {
    const convert = ConvertMap[msgType];
    const obj = msgpack.unpack(buf);
    frame_id = parseInt(obj['frame_id']);
    //console.log('convert:', msgType, obj, frame_id)
    if (CoreConfig.export.proxy == 'origin') {
      return [frame_id, buf]
    }
    const res = {};
    convert[0].forEach((key) => {
      if (key in obj) res[key] = obj[key];
      else res[key] = null; 
    })
    const dets = convert[1][0];
    if (dets in obj) {
      res[dets] = []
      const keyList = convert[1].slice(1)
      obj[dets].forEach((ret) => {
        let one = {}
        keyList.forEach((key) => {
          if (key in ret) one[key] = ret[key];
          else one[key] = null
        })
        res[dets].push(one)
      })
    } else res[dets] = null;
    /*
    console.log('obj', obj)
    console.log('res', res)
    console.log('json', JSON.stringify(res))
    */
    return [frame_id, Buffer.from(JSON.stringify(res))]
  }
}

startTcpServer();
if (CoreConfig.export.proxy == 'test') {
  SyncNode.OpenMsgSink()
}
