const path = require("path")
const fs = require("fs")
const server = require("./server");
const ConvertMap = require("./convert").ConvertMap
const PcviewSink = require('./pcvc')

let CoreConfig = null;
const file = path.join(__dirname, 'config/pcview.json');
if (fs.existsSync(file)) {
  CoreConfig = JSON.parse(fs.readFileSync(file));
  CoreConfig.ip = "192.168.0.233";
  CoreConfig.proxy = "nanomsg";
}

const tcpServer = new server.BlockServer('tcpServer', "0.0.0.0:12032");
const pcviewSink = new PcviewSink(CoreConfig);

pcviewSink.on('pcview', data => {
  const exportList = ['camera', 'lane', 'vehicle', 'tsr', 'pcw'];
  exportList.forEach( msgType => {
    if (msgType in data){
      sendBuf(proxyConvert(msgType, data[msgType]));
    } else {
      sendBuf(Buffer.from('{}'));
    }
  })
})

const sendBuf = (buf) => {
  tcpServer.clients.forEach( conn => {
    if (!conn.closed) conn.send(buf);
  })
}

const proxyConvert = (msgType, buf) => {
  if (msgType == 'camera') {
    return buf.image;
  } else {
    const convert = ConvertMap[msgType];
    const obj = buf;
    const frame_id = parseInt(obj['frame_id']);
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
    return Buffer.from(JSON.stringify(res));
  }
}

const startTcpServer = () => {
  tcpServer.open();
  pcviewSink.open();
}
startTcpServer();