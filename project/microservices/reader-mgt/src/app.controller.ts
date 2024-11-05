import { Controller, Get } from '@nestjs/common';
import { AppService } from './app.service';
import { MessagePattern, Payload } from '@nestjs/microservices';
import { saveReaderDto } from './dto/dto';

@Controller()
export class AppController {
  constructor(private readonly appService: AppService) {}

  @MessagePattern({ cmd: 'SAVE_READER' })
  async saveReader(@Payload() data: saveReaderDto): Promise<any> {
    return this.appService.saveReader(data);
  }
  
  @MessagePattern({'cmd': 'GET_ALL_READERS'})
  async getReader(): Promise<any> {
    return this.appService.getAllReaders();
  }
  @Get()
  getHello(): string {
    return this.appService.getHello();
  }
}
