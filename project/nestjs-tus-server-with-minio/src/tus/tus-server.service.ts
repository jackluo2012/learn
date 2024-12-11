import { Server } from '@tus/server';
import { FileStore } from '@tus/file-store';
import { Request, Response } from 'express';
import { join } from 'path';
import { Injectable, OnModuleInit } from '@nestjs/common';
import { S3Store } from '@tus/s3-store';

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
    const s3Store = new S3Store({
        partSize: 8 * 1024 * 1024, // Each uploaded part will have ~8MiB,
        s3ClientConfig: {
          bucket: process.env.AWS_BUCKET,
          region: process.env.AWS_REGION,
          credentials: {
            accessKeyId: process.env.AWS_ACCESS_KEY_ID,
            secretAccessKey: process.env.AWS_SECRET_ACCESS_KEY,
          },
        },
      })
  }


  handleTusRequest(req: Request, res: Response) {
    this.server.handle(req, res);
  }
}
