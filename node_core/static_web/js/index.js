
const host = "http://192.168.10.174:3457";
//const host = "http://127.0.0.1:3457";
const socket = io.connect(host);
socket.on('connect', ()=>{console.log('connected.')});

socket.on('pcview', function(data){
    //console.log(data)
    //console.log(data['vehicle']['frame_id'])
    //console.log(data['vehicle']);
    //console.log(data['lane']);
    const img = new Image();
    const blob = new Blob([data['camera']['image']]);
    // app.frame_id = data['camera']['frame_id'];
    const dataUrl = URL.createObjectURL(blob);
    img.src = dataUrl;
    img.onload = function(){
        var canvas = document.getElementById("show-pcview");
        var ctx = canvas.getContext('2d');
        ctx.clearRect(0,0, canvas.clientWidth, canvas.height);
        ctx.drawImage(img, 0, 0);
        DrawLabel.draw(ctx, data);
        URL.revokeObjectURL(this.src);
        this.removeEventListener('load', onload);
        this.removeEventListener('error', onerror);

        delete blob;
        delete data;
    }
});

