import { Module } from '@nestjs/common';
import { AppController } from './app.controller';
import { AppService } from './app.service';
import { SocketModule } from './socket/socket.module';

@Module({
  imports: [],
  controllers: [AppController],
  providers: [AppService,SocketModule],
})
export class AppModule {}
