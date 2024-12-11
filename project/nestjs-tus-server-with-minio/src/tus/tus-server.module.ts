import { Module } from '@nestjs/common';
import { TusServerService } from './tus-server.service';

@Module({
  providers: [TusServerService],
  exports: [TusServerService],
})
export class TusServerModule {}
