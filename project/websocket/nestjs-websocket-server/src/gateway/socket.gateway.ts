import { OnGatewayConnection, OnGatewayDisconnect, OnGatewayInit, WebSocketGateway,WebSocketServer } from "@nestjs/websockets";

import { Inject } from "@nestjs/common";
import { CACHE_MANAGER } from "@nestjs/cache-manager";
import { Server, Socket } from "socket.io";


@WebSocketGateway()
export class SocketGateway implements OnGatewayInit,OnGatewayConnection, OnGatewayDisconnect {
    
    @WebSocketServer()
    server: Server;

    constructor(@Inject(CACHE_MANAGER) private readonly cacheManager: Cache) {}
    
    
    afterInit(server: any) {
        console.log("Method not implemented.");
    }
    //当用户 连接时
    async handleConnection(client: Socket, ...args: any[]) {
        const userId = client.handshake.query.userId;
        await this.addSocketId(userId, client.id);
        console.log("Connection with:",userId);
        const receiverSocketId = await this.getSocketId(userId);
        if (receiverSocketId) {
            this.server.to(receiverSocketId).emit('connected_instance', {
                instance: process.env.NODE_APP_INSTANCE_ID,
            });
        }
    }
    
    getSocketId(userId: string | string[]) {
        return this.cacheManager.get(userId);
    }
    addSocketId(userId: string | string[], id: string) {
        return this.cacheManager.set(userId, id);
    }
    // On User Disconnect
    handleDisconnect(client: any) {
        const userId = await this.removeUserId(client.id);
        console.log("Disconnected with:",userId);
    }
    // @SubscribeMessage('message')
    // handleMessage(client: Socket, payload: string): void {
    //     console.log('message', payload);
    // }
    
}