import { Module } from "@nestjs/common";
import { IotreeWebSocketGateway } from "./iotree-websocket.gateway";

@Module({
    providers: [
        IotreeWebSocketGateway
    ],
    
})
export class IotreeWebSocketModule {
    
}