import { Controller, Get, Inject, Post, Req } from '@nestjs/common';
import { AppService } from './app.service';
import { ClientProxy } from '@nestjs/microservices';

@Controller('api/')
export class AppController {
  constructor(private appService: AppService,
    @Inject('NATS_SERVICE') private natsClient: ClientProxy
  ) {}
  
  @Post('/save-reader')
  saveReader(@Req() req: Request){
    return this.natsClient.send({ cmd: 'SAVE_READER' }, req.body);
  }
  @Get('/get-all-readers')
  getReaders(){
    return this.natsClient.send({ cmd: 'GET_ALL_READERS' }, {});
  }
  @Post('/save-article')
  saveArticle(@Req() req: Request){
    return this.natsClient.send({ cmd: 'SAVE_ARTICLE' }, req.body);
  }
  @Get('/get-all-articles')
  getArticles(){
    return this.natsClient.send({ cmd: 'GET_ALL_ARTICLES' }, {});
  }
  @Post('delete-article')
  deleteArticle(@Req() req: Request){
    return this.natsClient.send({ cmd: 'DELETE_ARTICLE' }, req.body);
  }
  @Get()
  getHello(): string {
    return this.appService.getHello();
  }
}
