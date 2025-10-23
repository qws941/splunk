/**
 * WebSocket Server for Real-time Event Streaming
 *
 * Features:
 * - Real-time security event broadcasting
 * - Connection management
 * - Heartbeat mechanism
 * - Zero external dependencies (Node.js built-in WebSocket)
 */

import { createHash } from 'crypto';

export class WebSocketServer {
  constructor(httpServer) {
    this.httpServer = httpServer;
    this.clients = new Set();
    this.services = null;
  }

  initialize(services) {
    this.services = services;

    this.httpServer.on('upgrade', (req, socket, head) => {
      if (req.url === '/ws' || req.url === '/') {
        this.handleUpgrade(req, socket, head);
      } else {
        socket.destroy();
      }
    });

    // Heartbeat to detect dead connections
    setInterval(() => {
      this.ping();
    }, 30000);

    console.log('✅ WebSocket server initialized');
  }

  handleUpgrade(req, socket, head) {
    const key = req.headers['sec-websocket-key'];
    const acceptKey = this.generateAcceptKey(key);

    const headers = [
      'HTTP/1.1 101 Switching Protocols',
      'Upgrade: websocket',
      'Connection: Upgrade',
      `Sec-WebSocket-Accept: ${acceptKey}`,
      '',
      ''
    ].join('\r\n');

    socket.write(headers);

    const client = {
      socket,
      id: this.generateClientId(),
      isAlive: true,
      subscriptions: new Set(['all'])
    };

    this.clients.add(client);
    console.log(`🔌 WebSocket client connected (ID: ${client.id}), total: ${this.clients.size}`);

    socket.on('data', (buffer) => {
      this.handleMessage(client, buffer);
    });

    socket.on('close', () => {
      this.clients.delete(client);
      console.log(`🔌 WebSocket client disconnected (ID: ${client.id}), total: ${this.clients.size}`);
    });

    socket.on('error', (error) => {
      console.error(`❌ WebSocket error (ID: ${client.id}):`, error.message);
      this.clients.delete(client);
    });

    // Send welcome message
    this.sendToClient(client, {
      type: 'connected',
      clientId: client.id,
      timestamp: new Date().toISOString()
    });
  }

  handleMessage(client, buffer) {
    try {
      const frame = this.decodeFrame(buffer);

      if (!frame) return;

      if (frame.opcode === 0x1) { // Text frame
        const message = JSON.parse(frame.payload);

        // Handle different message types
        switch (message.type) {
          case 'ping':
            client.isAlive = true;
            this.sendToClient(client, { type: 'pong', timestamp: new Date().toISOString() });
            break;

          case 'subscribe':
            if (message.channels) {
              message.channels.forEach(ch => client.subscriptions.add(ch));
              this.sendToClient(client, {
                type: 'subscribed',
                channels: Array.from(client.subscriptions)
              });
            }
            break;

          case 'unsubscribe':
            if (message.channels) {
              message.channels.forEach(ch => client.subscriptions.delete(ch));
              this.sendToClient(client, {
                type: 'unsubscribed',
                channels: Array.from(client.subscriptions)
              });
            }
            break;

          default:
            console.log(`📨 Received message from client ${client.id}:`, message.type);
        }
      } else if (frame.opcode === 0x8) { // Close frame
        client.socket.end();
      } else if (frame.opcode === 0x9) { // Ping frame
        this.sendPong(client);
      } else if (frame.opcode === 0xA) { // Pong frame
        client.isAlive = true;
      }
    } catch (error) {
      console.error('❌ Message handling error:', error.message);
    }
  }

  decodeFrame(buffer) {
    if (buffer.length < 2) return null;

    const firstByte = buffer[0];
    const secondByte = buffer[1];

    const fin = (firstByte & 0x80) !== 0;
    const opcode = firstByte & 0x0F;
    const masked = (secondByte & 0x80) !== 0;
    let payloadLength = secondByte & 0x7F;

    let offset = 2;

    if (payloadLength === 126) {
      payloadLength = buffer.readUInt16BE(2);
      offset += 2;
    } else if (payloadLength === 127) {
      payloadLength = Number(buffer.readBigUInt64BE(2));
      offset += 8;
    }

    let maskingKey;
    if (masked) {
      maskingKey = buffer.slice(offset, offset + 4);
      offset += 4;
    }

    const payload = buffer.slice(offset, offset + payloadLength);

    if (masked && maskingKey) {
      for (let i = 0; i < payload.length; i++) {
        payload[i] ^= maskingKey[i % 4];
      }
    }

    return {
      fin,
      opcode,
      masked,
      payload: payload.toString('utf8'),
      payloadLength
    };
  }

  encodeFrame(data) {
    const payload = Buffer.from(data);
    const payloadLength = payload.length;

    let frame;
    let offset = 0;

    if (payloadLength < 126) {
      frame = Buffer.allocUnsafe(2 + payloadLength);
      frame[1] = payloadLength;
      offset = 2;
    } else if (payloadLength < 65536) {
      frame = Buffer.allocUnsafe(4 + payloadLength);
      frame[1] = 126;
      frame.writeUInt16BE(payloadLength, 2);
      offset = 4;
    } else {
      frame = Buffer.allocUnsafe(10 + payloadLength);
      frame[1] = 127;
      frame.writeBigUInt64BE(BigInt(payloadLength), 2);
      offset = 10;
    }

    frame[0] = 0x81; // FIN + Text opcode
    payload.copy(frame, offset);

    return frame;
  }

  sendToClient(client, data) {
    if (client.socket.writable) {
      const message = JSON.stringify(data);
      const frame = this.encodeFrame(message);
      client.socket.write(frame);
    }
  }

  broadcast(data, channel = 'all') {
    const message = JSON.stringify(data);
    const frame = this.encodeFrame(message);

    let sent = 0;
    for (const client of this.clients) {
      if (client.socket.writable && client.subscriptions.has(channel)) {
        client.socket.write(frame);
        sent++;
      }
    }

    if (sent > 0) {
      console.log(`📡 Broadcast to ${sent} clients (channel: ${channel})`);
    }
  }

  ping() {
    for (const client of this.clients) {
      if (!client.isAlive) {
        console.log(`💀 Terminating dead connection: ${client.id}`);
        client.socket.terminate();
        this.clients.delete(client);
        continue;
      }

      client.isAlive = false;
      this.sendPing(client);
    }
  }

  sendPing(client) {
    if (client.socket.writable) {
      const frame = Buffer.from([0x89, 0x00]); // Ping frame
      client.socket.write(frame);
    }
  }

  sendPong(client) {
    if (client.socket.writable) {
      const frame = Buffer.from([0x8A, 0x00]); // Pong frame
      client.socket.write(frame);
    }
  }

  generateAcceptKey(key) {
    const GUID = '258EAFA5-E914-47DA-95CA-C5AB0DC85B11';
    const hash = createHash('sha1');
    hash.update(key + GUID);
    return hash.digest('base64');
  }

  generateClientId() {
    return `client_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  getConnectionCount() {
    return this.clients.size;
  }

  close() {
    for (const client of this.clients) {
      client.socket.end();
    }
    this.clients.clear();
    console.log('✅ WebSocket server closed');
  }
}
