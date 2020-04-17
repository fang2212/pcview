const WebSocket = require('ws');
const msgpack = require('msgpack');
const fs = require('fs');
const path = require('path');
const argv = require('yargs')
      .usage('Usage: $0 --sync [loop_num] --ip [ip] --graph-num [num] --log-path [log-path] --event-log --print')
      .argv;
const Sync = require('./sync');
let sync = null;

// socket.io
const express = require('express');
const app = express();
const httpServer = require('http').createServer(app);
const io = require('socket.io')(httpServer);
io.on('connection', (socket)=>{
    console.log('new connetcion')
});

let syncSize = 20
if (argv.sync) {
  syncSize = new Sync(argv.sync, 'loop_index');
}

let graphNum = 1
if (argv.graphNum) {
  graphNum = argv.graphNum
}


Date.prototype.format = function(fmt) { 
  var o = { 
     "M+" : this.getMonth()+1,                 //月份 
     "d+" : this.getDate(),                    //日 
     "h+" : this.getHours(),                   //小时 
     "m+" : this.getMinutes(),                 //分 
     "s+" : this.getSeconds(),                 //秒 
     "q+" : Math.floor((this.getMonth()+3)/3), //季度 
     "S"  : this.getMilliseconds()             //毫秒 
 }; 
 if(/(y+)/.test(fmt)) {
         fmt=fmt.replace(RegExp.$1, (this.getFullYear()+"").substr(4 - RegExp.$1.length)); 
 }
  for(var k in o) {
     if(new RegExp("("+ k +")").test(fmt)){
          fmt = fmt.replace(RegExp.$1, (RegExp.$1.length==1) ? (o[k]) : (("00"+ o[k]).substr((""+ o[k]).length)));
      }
  }
 return fmt; 
}
const getTime = () => {
 return new Date().format('yyyyMMddhhmmss');
}

console.log(argv);
let ip = '192.168.0.233';
let logPath = 'rotor_data';
const topics = ['runtime.time_cost']

if (argv.eventLog) {
    topics.push('runtime.event');
}

if (argv.logPath) {
    logPath = argv.logPath;
}

if (!fs.existsSync(logPath)) {
    fs.mkdirSync(logPath);
}


if (argv.ip) {
    ip = argv.ip;
}


const addr = 'ws://'+ip+':24010'
const ws = new WebSocket(addr);

const packMessage = function (source, topic, data) {
  const obj = {source, topic, data};
  return msgpack.pack(obj);
};

ws.on('open', function open() {
  topics.forEach((topic) => {
    let msg = packMessage('recorder', 'subscribe', topic);
    ws.send(msg);
  })
});


const PackData = (new_pack, data) => {
  if (data.message == 'LoopTime') {
    new_pack.frame_time_cost = data.time_cost_us;
  } else {
    new_pack.node_time_cost.push([data.node_index, data.node_name, data.time_cost_us])
  }
}

class GraphCnt {
  constructor(graph_index) {
    // super();
    this.new_pack = null;
    this.new_id = -1;
    this.is_ok = 0;
    this.eventMap = new Map();
    this.sync = new Sync(syncSize, 'loop_index')
    this.eventLog = null;
    if (argv.eventLog) {
        this.eventLog = fs.openSync(path.join(logPath, 'event-'+getTime()+'-g'+graph_index+'.log'), 'w+');
    }
    this.timeLog = fs.openSync(path.join(logPath, 'time-'+getTime()+'-g'+graph_index+'.log'), 'w+');
  }

  push(data) {
    if (data instanceof Buffer) {
      const obj = msgpack.unpack(data);
      //console.log(msgpack.unpack(obj.data))
      //console.log(obj)
      data = msgpack.unpack(obj.data)

      if (obj.topic == 'runtime.time_cost') {
        const res = this.sync.push(data);
        for (let i in res) {
          data = res[i];
          const frame_id = data.loop_index;
          if (this.new_id != frame_id) {
            if (this.new_pack) {
              if (this.is_ok) {
                let temp = JSON.stringify(this.new_pack)
                io.emit('log', temp)
                if (argv.print) {
                  console.log(temp);
                }
                fs.writeSync(this.timeLog, temp+'\n');
              } else {
                this.is_ok = 1;
              }
            }
            this.new_pack = {
              "frame_id": frame_id,
              "frame_time_cost": 0,
              "node_time_cost": []
            }
            PackData(this.new_pack, data);
            this.new_id = frame_id;
          }
          else if (this.new_id == frame_id) {
            PackData(this.new_pack, data);
          }
        }
      } else if (obj.topic == 'runtime.event') {
        let msgTime = obj.time;
        data['time'] = msgTime;
        let key = data.graph_index.toString() + data.loop_index.toString() + data.node_name;
        if (data.message == 'NodeBegin') {
          this.eventMap.set(key, data);
        } else if (data.message == 'NodeEnd') {
          if (this.eventMap.get(key)) {
            let temp = JSON.stringify([this.eventMap.get(key), data]);
            if (argv.print) {
              console.log(temp);
            }
            fs.writeSync(this.eventLog, temp+'\n');
            this.eventMap.delete(key);
          }
        }
      }
    } else {
      console.log('text:', data);
    }
  }

  end() {
    this.emit('end');
  }
}

const graphCnt ={
} 

for (let i=0; i<graphNum; i++) {
  graphCnt[i] = new GraphCnt(i)
}

ws.on('message', function incoming(data) {
  const obj = msgpack.unpack(data);
  let temp = msgpack.unpack(obj.data);
  graphCnt[temp.graph_index].push(data)
});

httpServer.listen(12033)