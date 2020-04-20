//const host = "http://127.0.0.1:3457";
const host = "http://localhost:3457";
const socket = io.connect(host);

socket.on('connect', ()=>{console.log('connected.')});

socket.on('log', function(data){
  console.log(data)
});

