/***************************
 初始化libflow的socket连接， 封装发送及接收消息接口
Usage:

var msghandler = new MsgHandler(<libflow服务器地址>, <需要订阅的topic>);
msghandler.onrecv = function(data, topic){
    console.log(data);
}
msghandler.send(<发送的数据>， <tpoic>);
******************************/

function MsgHandler(url="ws://localhost:8000", scribe_topic="*.*"){
    const _this = this;
    this.ws = new WebSocket(url);

    //判断是否连接
    this.isOpen = function(){
        return this.ws.readyState === this.ws.OPEN;
    }
    
    //直接发送
    this.directSend = function(msg){
        msg = msgpack.encode(msg);
        this.ws.send(msg);
    }

    //等待socket状态为open再发送
    this.send = function(data, topic){
        data = msgpack.encode(data);
        var msg = {
            'source': 'client1234',
            'topic': topic,
            'data': data,
        };
        _this.directSend(msg)
        //this.ws.addEventListener('open', function(){
        //    _this.directSend(msg)
        //})
    }

    //接收消息处理函数，需要重载
    this.onrecv = function(data, topic){
        
    };

    this.ws.onopen = function(evt){
        var msg = {
            'source': 'client1234',
            'topic': 'subscribe',
            'data': scribe_topic,
        }
        _this.directSend(msg);
        console.log("opened ...");
    }

    this.ws.onmessage = function(evt){
        var data = evt.data;
        var reader = new FileReader();
        reader.readAsArrayBuffer(data);
        reader.onload = function(){
            var buffer = new Uint8Array(reader.result);
            var msg = msgpack.decode(buffer);      
            topic = msg.topic;
            data = msg.data;
            data = msgpack.decode(data);
            _this.onrecv(data, topic);
        }
    }
    
    this.ws.onclose = function(evt){
        console.log("closed ...");
    }
}



