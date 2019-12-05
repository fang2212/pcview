const fs = require("fs");
const path = require("path")
const readline = require('readline')

const express = require('express');
const app = express();
const httpServer = require('http').createServer(app);
const io = require('socket.io')(httpServer);

app.use(express.static('static_web'))
app.get('/', function(req, res){
    res.sendFile(__dirname + "/static_web/index.html")
})


io.on('connection', (socket)=>{
    console.log('new connetcion')
});

httpServer.listen(3457)

const r1 = readline.createInterface({
  input: fs.createReadStream("time.log")
});

let size = 0
const logContent = []
r1.on('line', function(line){ //事件监听
　//console.log(JSON.parse(line))
  size = size+1
  // console.log('get', i)
  logContent.push(line)
})

let index = 0
setInterval(()=>{
  io.emit('log', logContent[index])
  index = (index+1)%size
}, 50)