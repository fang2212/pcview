const WebSocket = require('ws');
const msgpack = require('msgpack');

let ip = '192.168.0.233';
console.log(process.argv)
if (process.argv.length>2) {
  ip = process.argv[2];
}

const addr = 'ws://'+ip+':24011'
const ws = new WebSocket(addr);

ws.on('open', function open() {
  let msg = packMessage('test-js', 'subscribe', 'status');
  ws.send(msg);
});

const packMessage = function (source, topic, data) {
  const obj = {source, topic, data};
  return msgpack.pack(obj);
};

ws.on('message', function incoming(data) {
  if (data instanceof Buffer) {
    const obj = msgpack.unpack(data);
    //console.log('obj:', obj);
    /*
    console.log(obj.topic)
    console.log('data', obj.data)
    */
    // console.log('data', obj.data)
    console.log('data', msgpack.unpack(obj.data))

    //console.log('data', msgpack.unpack(obj.data))
    /*
    if (obj.topic == 'pcview.lane') {
      console.log('data', msgpack.unpack(obj.data))
    }
    */
  } else {
    console.log('text:', data);
  }
});
