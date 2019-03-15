const net = require('net');
const events = require('events');

//----------------------------------------------------------
// class BaseDecoder
//----------------------------------------------------------

// event: error, err
// event: message, msg
class BaseDecoder extends events.EventEmitter {
  constructor() {
    super();
  }

  push(chunk) {
    this.emit('message', chunk);
  }

  end() {
    this.emit('end');
  }
}

//----------------------------------------------------------
// class FileDecoder
//----------------------------------------------------------

class FileDecoder extends BaseDecoder {
  constructor() {
    super();
    this.buffers = [];
  }

  push(chunk) {
    if (chunk && chunk.byteLength > 0) {
      this.buffers.push(chunk);
    }
  }

  end() {
    const data = Buffer.concat(this.buffers);
    if (data.byteLength > 0) {
      this.emit('message', data);
    }

    this.emit('end');
  }
}

//----------------------------------------------------------
// class BlockDecoder
//----------------------------------------------------------

function packUint32BE(num) {
  const d3 = num % 256;
  num /= 256;
  const d2 = num % 256;
  num /= 256;
  const d1 = num % 256;
  num /= 256;
  const d0 = num % 256;

  let buf = Buffer.alloc(4);
  buf[0] = d0;
  buf[1] = d1;
  buf[2] = d2;
  buf[3] = d3;
  return buf;
}

function unpackUint32BE(buf) {
  const d0 = buf[0] * 256 * 256 * 256;
  const d1 = buf[1] * 256 * 256;
  const d2 = buf[2] * 256;
  const d3 = buf[3];
  return d0 + d1 + d2 + d3;
}

class BlockDecoder extends BaseDecoder {
  constructor() {
    super();
    this.init();
  }

  init() {
    this.state = BlockDecoder.WAIT_SIZE;
    this.buffers = [];
    this.bufferedSize = 0;
    this.dataSize = 0;
  }

  push(chunk) {
    if (chunk && chunk.byteLength > 0) {
      this.buffers.push(chunk);
      this.bufferedSize += chunk.byteLength;
      this.digest();
    }
  }

  end() {
    const data = Buffer.concat(this.buffers);
    if (data.byteLength > 0) {
      this.emit('error', 'incomplete message', data);
    }

    this.emit('end');
  }

  pull(size) {
    if (this.bufferedSize < size) {
      return null;
    }

    let wanted = size;
    let buffers = [];

    while (true) {
      // 从队列里取出一个数据块
      const buf = this.buffers.shift();
      this.bufferedSize -= buf.byteLength;

      // 判断是否全部拿走
      if (buf.byteLength <= wanted) { // 全部拿走
        buffers.push(buf);
        wanted -= buf.byteLength;
      } else { // 割走一部分
        const head = buf.slice(0, wanted);
        const tail = buf.slice(wanted);
        buffers.push(head); // 拿走一部分
        wanted = 0;
        this.buffers.unshift(tail); // 归还剩余部分
        this.bufferedSize += tail.byteLength;
      }

      if (wanted <= 0) {
        break;
      }
    }

    if (buffers.length === 1) {
      return buffers[0];
    } else {
      return Buffer.concat(buffers);
    }
  }

  digest() {
    while (true) {
      if (this.state === BlockDecoder.WAIT_SIZE) {
        const bufSize = this.pull(BlockDecoder.SizeLength);
        if (bufSize === null) {
          return;
        }

        const size = unpackUint32BE(bufSize);
        if (size > BlockDecoder.MaxDataSize) {
          this.init();
          this.emit('error', new Error('data size limit exceeded'));
          return;
        }

        this.dataSize = size;
        this.state = BlockDecoder.WAIT_DATA;
      } else if (this.state === BlockDecoder.WAIT_DATA) {
        const bufData = this.pull(this.dataSize);
        if (bufData === null) {
          return;
        }

        const data = this.process(bufData);
        if (data === null) {
          return;
        }

        this.emit('message', data);

        this.dataSize = 0;
        this.state = BlockDecoder.WAIT_SIZE;
        break;
      }
    }
  }

  process(data) {
    return data;
  }
}

BlockDecoder.WAIT_SIZE = 1;
BlockDecoder.WAIT_DATA = 2;

BlockDecoder.SizeLength = 4;
BlockDecoder.MaxDataSize = 16 * 1024 * 1024;

//----------------------------------------------------------
// class BlockJSONDecoder
//----------------------------------------------------------

class BlockJSONDecoder extends BlockDecoder {
  constructor() {
    super();
  }

  process(data) {
    try {
      return JSON.parse(data);
    } catch (err) {
      this.emit('error', err);
      return null;
    }
  }
}

//----------------------------------------------------------
// class LineTextDecoder
//----------------------------------------------------------

class LineTextDecoder extends BaseDecoder {
  constructor() {
    super();
    this.buffers = [];
  }

  push(chunk) {
    if (chunk && chunk.byteLength > 0) {
      this.buffers.push(chunk);
      this.digest();
    }
  }

  end() {
    const data = Buffer.concat(this.buffers);
    if (data.byteLength > 0) {
      this.emit('error', 'incomplete message', data);
    }

    this.emit('end');
  }

  pull() {
    let nlIndex = -1;
    let nlCutPos = -1;

    for (let i = 0; i < this.buffers.length; i += 1) {
      const buf = this.buffers[i];
      const idx = buf.indexOf(0xa);
      if (idx >= 0) { // '\n' found
        nlIndex = i;
        nlCutPos = idx + 1;
        break;
      }
    }

    if (nlIndex === -1) {
      return null;
    }

    const buffers = [];
    for (let i = 0; i <= nlIndex; i += 1) {
      const buf = this.buffers.shift();
      if (i < nlIndex) {
        buffers.push(buf);
      } else {
        const head = buf.slice(0, nlCutPos);
        const tail = buf.slice(nlCutPos);
        buffers.push(head);
        this.buffers.unshift(tail);
      }
    }

    if (buffers.length === 1) {
      return buffers[0];
    } else {
      return Buffer.concat(buffers);
    }
  }

  digest() {
    while (true) {
      const line = this.pull();
      if (line === null) {
        return;
      }

      const data = this.process(line);
      if (data === null) {
        return;
      }

      this.emit('message', data);
    }
  }

  process(line) {
    return line.toString();
  }
}

//----------------------------------------------------------
// class LineJSONDecoder
//----------------------------------------------------------

class LineJSONDecoder extends LineTextDecoder {
  constructor() {
    super();
  }

  process(line) {
    line = line.toString().trim();
    if (line === '') {
      return null;
    }

    try {
      return JSON.parse(line);
    } catch (err) {
      this.emit('error', err);
      return null;
    }
  }
}

//----------------------------------------------------------
// class BaseEncoder
//----------------------------------------------------------

class BaseEncoder {
  constructor() {
  }

  encode(data, callback) {
    callback(null, data);
  }

  end(callback) {
    callback(null, null);
  }
}

//----------------------------------------------------------
// class FileEncoder
//----------------------------------------------------------

class FileEncoder extends BaseEncoder {
  constructor() {
    super();
    this.buffers = [];
  }

  encode(data, callback) {
    if (data instanceof Buffer) {
      this.buffers.push(data);
      callback(null, null);
    } else if (typeof data === 'string') {
      this.buffers.push(Buffer.from(data));
      callback(null, null);
    } else {
      const err = new Error('FileEncoder: invalid argument type');
      callback(err, null);
    }
  }

  end(callback) {
    const data = Buffer.concat(this.buffers);
    this.buffers = [];
    callback(null, data);
  }
}

//----------------------------------------------------------
// class BlockEncoder
//----------------------------------------------------------

class BlockEncoder extends BaseEncoder {
  constructor() {
    super();
  }

  encode(data, callback) {
    if (data instanceof Buffer) {
      callback(null, this.pack(data));
    } else if (typeof data === 'string') {
      callback(null, this.pack(Buffer.from(data)));
    } else {
      const err = new Error('BlockEncoder: invalid argument type');
      callback(err, null);
    }
  }

  pack(bufData) {
    const bufSize = packUint32BE(bufData.byteLength);
    return Buffer.concat([bufSize, bufData]);
  }
}

//----------------------------------------------------------
// class BlockJSONEncoder
//----------------------------------------------------------

class BlockJSONEncoder extends BlockEncoder {
  constructor() {
    super();
  }

  encode(data, callback) {
    const json = JSON.stringify(data);
    super.encode(json, callback);
  }
}

//----------------------------------------------------------
// class LineTextEncoder
//----------------------------------------------------------

class LineTextEncoder extends BaseEncoder {
  constructor() {
    super();
  }

  encode(data, callback) {
    if (typeof data === 'string') {
      const line = data.endsWith('\n') ? data : (data + '\n');
      callback(null, Buffer.from(line));
    } else {
      const err = new Error('LineTextEncoder: invalid argument type');
      callback(err, null);
    }
  }
}

//----------------------------------------------------------
// class LineJSONEncoder
//----------------------------------------------------------

class LineJSONEncoder extends LineTextEncoder {
  constructor() {
    super();
  }

  encode(data, callback) {
    const json = JSON.stringify(data);
    super.encode(json, callback);
  }
}

//----------------------------------------------------------
// class BaseConn
//----------------------------------------------------------

class BaseConn extends events.EventEmitter {
  constructor(conn) {
    super();
    this.conn = conn;
    this.decoder = new BaseDecoder();
    this.encoder = new BaseEncoder();
  }

  init() {
    this.closed = false;

    // Emitted once the socket is fully closed.
    this.conn.on('close', (had_error) => {
      console.log(`socket is closed, had_error = ${had_error}`);
      this.closed = true;
      this.decoder.end();
    });

    // Emitted when a socket connection is successfully established.
    // this.conn.on('connect', () => {
    //   console.log(`socket is connected: ${this.conn.remoteAddress}`);
    // });

    // Emitted when data is received.
    // The argument data will be a Buffer or String.
    this.conn.on('data', (data) => {
      this.decoder.push(data);
    });

    // Emitted when the write buffer becomes empty.
    // Can be used to throttle uploads.
    // this.conn.on('drain', () => {
    // });

    // Emitted when the other end of the socket sends a FIN packet.
    // this.conn.on('end', () => {
    //   console.log('socket is ended');
    // });

    // Emitted when an error occurs.
    // The 'close' event will be called directly following this event.
    this.conn.on('error', (err) => {
      console.error('socket error:', err);
    });

    // Emitted after resolving the hostname but before connecting.
    // this.conn.on('lookup', () => {
    //   console.log('received a lookup event');
    // });

    // Emitted if the socket times out from inactivity.
    // This is only to notify that the socket has been idle.
    // The user must manually close the connection.
    this.conn.on('timeout', () => {
      console.error('socket has timed out');
    });

    // Emitted if the decoder had finished.
    this.decoder.on('end', () => {
      this.emit('close');
    });

    // Emitted if the decoder had encountered an error.
    this.decoder.on('error', (err, data) => {
      console.error(err);
      this.conn.end();
      this.emit('error', err, data);
    });

    // Emitted if the decoder had successfully decoded a message.
    this.decoder.on('message', (msg) => {
      this.emit('message', msg);
    });
  }

  send(data, callback) {
    if (typeof callback !== 'function') {
      callback = () => {}
    }

    this.encoder.encode(data, (err, buf) => {
      if (err) {
        console.error(err);
      }

      if (buf && buf.byteLength > 0) {
        this.conn.write(buf, callback);
      } else {
        callback();
      }
    });
  }

  close(callback) {
    if (typeof callback !== 'function') {
      callback = () => {}
    }

    if (this.closed) {
      callback();
      return;
    }

    this.encoder.end((err, buf) => {
      if (err) {
        console.error(err);
      }

      if (buf && buf.byteLength) {
        this.conn.end(buf, callback);
      } else {
        this.conn.end(callback);
      }
    });
  }
}

//----------------------------------------------------------
// class FileConn
//----------------------------------------------------------

class FileConn extends BaseConn {
  constructor(conn) {
    super(conn);
    this.decoder = new FileDecoder();
    this.encoder = new FileEncoder();
  }
}

//----------------------------------------------------------
// class BlockConn
//----------------------------------------------------------

class BlockConn extends BaseConn {
  constructor(conn) {
    super(conn);
    this.decoder = new BlockDecoder();
    this.encoder = new BlockEncoder();
  }
}

//----------------------------------------------------------
// class BlockJSONConn
//----------------------------------------------------------

class BlockJSONConn extends BaseConn {
  constructor(conn) {
    super(conn);
    this.decoder = new BlockJSONDecoder();
    this.encoder = new BlockJSONEncoder();
  }
}

//----------------------------------------------------------
// class LineTextConn
//----------------------------------------------------------

class LineTextConn extends BaseConn {
  constructor(conn) {
    super(conn);
    this.decoder = new LineTextDecoder();
    this.encoder = new LineTextEncoder();
  }
}

//----------------------------------------------------------
// class LineJSONConn
//----------------------------------------------------------

class LineJSONConn extends BaseConn {
  constructor(conn) {
    super(conn);
    this.decoder = new LineJSONDecoder();
    this.encoder = new LineJSONEncoder();
  }
}

//----------------------------------------------------------
// class BaseServer
//----------------------------------------------------------

class BaseServer extends events.EventEmitter {
  constructor(name, listen) {
    super();

    this.name = name;

    const [host, port] = listen.split(':');
    this.host = host;
    this.port = parseInt(port);

    this.server = null;
    this.clients = [];
    this.connClass = BaseConn;
  }

  open() {
    if (this.server) { // no need to open
      console.log(`${this.name} is running, no need to open`);
      return;
    }

    this.server = net.createServer();
    this.server.listen(this.port, this.host);

    this.server.on('listening', () => {
      const addr  = this.server.address();
      const addr2 = `${addr.address}:${addr.port}`;
      console.log(`${this.name} is listening on ${addr2} ...`);
      this.emit('listening');
    });

    this.server.on('close', () => {
      console.log(`${this.name} is closed`);
      this.server = null;
      this.emit('close');
    });

    this.server.on('error', (err) => {
      console.error(`${this.name} error:`, err);
    });

    this.server.on('connection', (sock) => {
      const host = sock.remoteAddress;
      const port = sock.remotePort;
      console.log(`${this.name} accepted a new connection from ${host}:${port}`);

      const conn = new this.connClass(sock);
      conn.init();

      // add the new client
      this.clients.push(conn);

      // remove the client when it is closed
      conn.on('close', () => {
        const idx = this.clients.indexOf(conn);
        if (idx >= 0) {
          this.clients.splice(idx, 1); // 从idx处开始删除1个元素
        }
      });

      this.emit('connection', conn);
    });
  }

  close() {
    if (!this.server) { // no need to close
      return;
    }

    this.server.close();
  }
}

//----------------------------------------------------------
// class FileServer
//----------------------------------------------------------

class FileServer extends BaseServer {
  constructor(name, listen) {
    super(name, listen);
    this.connClass = FileConn;
  }
}

//----------------------------------------------------------
// class BlockServer
//----------------------------------------------------------

class BlockServer extends BaseServer {
  constructor(name, listen) {
    super(name, listen);
    this.connClass = BlockConn;
  }
}

//----------------------------------------------------------
// class BlockJSONServer
//----------------------------------------------------------

class BlockJSONServer extends BaseServer {
  constructor(name, listen) {
    super(name, listen);
    this.connClass = BlockJSONConn;
  }
}

//----------------------------------------------------------
// class LineTextServer
//----------------------------------------------------------

class LineTextServer extends BaseServer {
  constructor(name, listen) {
    super(name, listen);
    this.connClass = LineTextConn;
  }
}

//----------------------------------------------------------
// class LineJSONServer
//----------------------------------------------------------

class LineJSONServer extends BaseServer {
  constructor(name, listen) {
    super(name, listen);
    this.connClass = LineJSONConn;
  }
}

module.exports = {
  // decoders
  BaseDecoder,
  FileDecoder,
  BlockDecoder,
  BlockJSONDecoder,
  LineTextDecoder,
  LineJSONDecoder,

  // encoders
  BaseEncoder,
  FileEncoder,
  BlockEncoder,
  BlockJSONEncoder,
  LineTextEncoder,
  LineJSONEncoder,

  // connections
  BaseConn,
  FileConn,
  BlockConn,
  BlockJSONConn,
  LineTextConn,
  LineJSONConn,

  // servers
  BaseServer,
  FileServer,
  BlockServer,
  BlockJSONServer,
  LineTextServer,
  LineJSONServer,
};
