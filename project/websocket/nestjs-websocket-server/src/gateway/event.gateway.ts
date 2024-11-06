import { ConnectedSocket, MessageBody, SubscribeMessage, WebSocketGateway, WebSocketServer } from "@nestjs/websockets";
import { Server,Socket } from "socket.io";

@WebSocketGateway({cors:{origin: '*'}})
export class EventGateway {
   // 直接访问原生的、特定于平台的服务器实例
  @WebSocketServer()
  server:Server;
  // 如果有人发消息 就会触发 这个 handler
  @SubscribeMessage('events')
  handleEvent(
    @MessageBody() boday:any,
    @ConnectedSocket() client:Socket  
  ):any {
        // client.emit('newMessage', boday);
        this.server.emit('newMessage', {
          msg: 'new Message',
          content: boday
        });
        console.log(boday);
  }
}