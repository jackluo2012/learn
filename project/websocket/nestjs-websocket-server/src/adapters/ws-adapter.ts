import { INestApplicationContext, WebSocketAdapter, WsMessageHandler } from "@nestjs/common";
import { Observable,filter,fromEvent, mergeMap } from "rxjs";
import * as WebSocket from "ws";

export class WsAdapter implements WebSocketAdapter{
    constructor(private app:INestApplicationContext) {}

    create(port: number, options: any={}): any {
        return new WebSocket.Server({ port, ...options });
    }
    bindClientConnect(server: any, callback: Function) {
        server.on('connection', callback);
    }
    bindClientDisconnect?(client: any, callback: Function) {
        client.on('close', callback);
    }
    bindMessageHandlers(client: any, handlers: WsMessageHandler[], transform: (data: any) => Observable<any>) {
        fromEvent(client, 'message')
        .pipe(
          mergeMap(async (data) => this.bindMessageHandler(data, handlers, process)),
          filter((result: any) => result)
        )
        .subscribe(response => client.send(JSON.stringify(response)));
    }
    bindMessageHandler(data: any, handlers: WsMessageHandler<string>[], process: NodeJS.Process) {
        throw new Error("Method not implemented.");
    }
    close(server: any) {
        server.close();
    }
    
}