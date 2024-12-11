import { Server } from '@tus/server';
import { FileStore } from '@tus/file-store';
import { Request, Response } from 'express';
import { join } from 'path';
import { Injectable, OnModuleInit } from '@nestjs/common';

@Injectable()
export class TusServerService implements OnModuleInit {
  public server: Server;

  onModuleInit() {
    this.server = new Server({
      path: '/upload/files', // tus 服务的 API 路径
      datastore: new FileStore({
        directory: join(process.cwd(), 'uploads'), // 设置文件上传目录
      }),
    });
  }
  handleTusRequest(req: Request, res: Response) {
    this.server.handle(req, res);
  }
}
