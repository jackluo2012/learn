import { Module } from '@nestjs/common';
import { AppController } from './app.controller';
import { AppService } from './app.service';
import { GatewayModule } from './gateway/gateway.module';
import { UserModule } from './module/user/user.module';
import { IotreeWebSocketModule } from './module/websocket/iotree-websocket.module';

@Module({
  imports: [UserModule,IotreeWebSocketModule],
  controllers: [AppController],
  providers: [AppService],
})
export class AppModule {}
