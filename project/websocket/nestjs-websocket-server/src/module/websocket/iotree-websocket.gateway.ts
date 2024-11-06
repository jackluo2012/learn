import { UseFilters, UseInterceptors } from "@nestjs/common";
import { ConnectedSocket, MessageBody, SubscribeMessage, WebSocketGateway } from "@nestjs/websockets";
import { Socket } from "dgram";
import { BizException } from "src/base/biz-exception";
import { WsServiceExceptionFilter } from "src/base/filter/ws-service.exception.filter";
import { WsServiceResponseInterceptor } from "src/base/interceptor/ws-service.response.interceptor";
import { ERROR_REQ_FIELD_ERROR } from "src/common/return-code";

// 安装WebSocket成功响应拦截器
@UseInterceptors(new WsServiceResponseInterceptor())
@UseFilters(new WsServiceExceptionFilter())
@WebSocketGateway({transports: ['websocket']})
export class IotreeWebSocketGateway {
   // 订阅事件 subscribeMessage
   @SubscribeMessage('hello')
   hello(@MessageBody() reqData: {name:string}) {
      if (!reqData || !reqData.name) {
        throw BizException.create(ERROR_REQ_FIELD_ERROR,'name is required');
      }
      console.log(JSON.stringify(reqData));
      return 'received reqData'
   }
   @SubscribeMessage('newMessage')
   handleMessage(@MessageBody() body: any,@ConnectedSocket() client: Socket) {
      client.emit('newMessage',body);
      console.log(body)
      return body
   }
}