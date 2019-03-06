const WebSocket = require('ws');
const msgpack = require('msgpack');
const fs = require('fs');
const path = require('path');
const argv = require('yargs')
      .usage('Usage: $0 --ip [ip] --log-path [log-path] --event-log --print')
      .argv;

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

if (argv.logPath) {
    logPath = argv.logPath;
}

if (!fs.existsSync(logPath)) {
    fs.mkdirSync(logPath);
}

let eventLog = null;
if (argv.eventLog) {
    topics.push('runtime.event');
    eventLog = fs.openSync(path.join(logPath, 'event-'+getTime()+'.log'), 'w+');
}
const timeLog = fs.openSync(path.join(logPath, 'time-'+getTime()+'.log'), 'w+');

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

let new_pack = null;
let new_id = -1;
let is_ok = 0;
const eventMap = new Map();

const PackData = (new_pack, data) => {
  if (data.message == 'LoopTime') {
    new_pack.frame_time_cost = data.time_cost_us;
  } else {
    new_pack.node_time_cost.push([data.node_index, data.node_name, data.time_cost_us])
  }
}

ws.on('message', function incoming(data) {
  //console.log(data.toString('hex'));
  if (data instanceof Buffer) {
    const obj = msgpack.unpack(data);
    //console.log(msgpack.unpack(obj.data))
    //console.log(obj)

    data = msgpack.unpack(obj.data)
    if (obj.topic == 'runtime.time_cost') {
      const frame_id = data.loop_index;
      if (new_id != frame_id) {
        if (new_pack) {
          if (is_ok) {
            let temp = JSON.stringify(new_pack)
            if (argv.print) {
              console.log(temp);
            }
            fs.writeSync(timeLog, temp+'\n');
          } else {
            is_ok = 1;
          }
        }
        new_pack = {
          "frame_id": frame_id,
          "frame_time_cost": 0,
          "node_time_cost": []
        }
        PackData(new_pack, data);
        new_id = frame_id;
      }
      else if (new_id == frame_id) {
        PackData(new_pack, data);
      }
    } else if (obj.topic == 'runtime.event') {
      let msgTime = obj.time;
    
      //console.log(obj);
      //console.log(msgTime);
      let data = msgpack.unpack(obj.data);
      data['time'] = msgTime;
      let key = data.graph_index.toString() + data.loop_index.toString() + data.node_name;
      if (data.message == 'NodeBegin') {
        eventMap.set(key, data);
      } else if (data.message == 'NodeEnd') {
        if (eventMap.get(key)) {
          let temp = JSON.stringify([eventMap.get(key), data]);
          if (argv.print) {
            console.log(temp);
          }
          fs.writeSync(eventLog, temp+'\n');
          eventMap.delete(key);
        }
      }
    }
  } else {
    console.log('text:', data);
  }
});
