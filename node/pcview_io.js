const fs = require("fs");
const path = require("path")

const express = require('express');
const app = express();
const httpServer = require('http').createServer(app);
const io = require('socket.io')(httpServer);

const PcivewSink = require('./pcvc')

app.use(express.static('static_web'))
app.get('/', function(req, res){
    res.sendFile(__dirname + "/static_web/index.html")
})

let CoreConfig = null;
const file = path.join(__dirname, 'config/pcview.json');
if (fs.existsSync(file)) {
  CoreConfig = JSON.parse(fs.readFileSync(file));
}

io.on('connection', (socket)=>{
    console.log('new connetcion');
});

pcviewsink = new PcivewSink(CoreConfig)
pcviewsink.on('pcview', data => {
  io.emit('pcview', data)
})
pcviewsink.open();
httpServer.listen(3457);
