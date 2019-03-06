const WebSocket = require('ws');
const msgpack = require('msgpack');

const ip = process.argv[2]
const addr = 'ws://'+ip+':24010'
const ws = new WebSocket(addr);


const packMessage = function (source, topic, data) {
  const obj = {source, topic, data};
  return msgpack.pack(obj);
};

ws.on('open', function open() {
  let msg = packMessage('recorder', 'subscribe', 'runtime.event');
  ws.send(msg);
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
            console.log(JSON.stringify(new_pack));
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
          console.log(JSON.stringify([
            eventMap.get(key), data
          ]));
          eventMap.delete(key);
        }
      }
    }
  } else {
    console.log('text:', data);
  }
});
