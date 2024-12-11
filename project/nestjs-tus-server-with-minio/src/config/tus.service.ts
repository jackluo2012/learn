import { Server } from '@tus/server';
import { FileStore } from '@tus/file-store';
import { Request, Response } from 'express';
import { join } from 'path';
import { Injectable, OnModuleInit } from '@nestjs/common';
import { S3Store } from '@tus/s3-store';

@Injectable()
export class TusService implements OnModuleInit {
  public server: Server;

  onModuleInit() {
    
    const s3Store = new S3Store({
        partSize: 8 * 1024 * 1024, // Each uploaded part will have ~8MiB,
        s3ClientConfig: {
          bucket: process.env.AWS_BUCKET,
          endpoint: '192.168.110.108:31833',
        //   region: process.env.AWS_REGION,
        //   credentials: {
        //     accessKeyId: process.env.AWS_ACCESS_KEY_ID,
        //     secretAccessKey: process.env.AWS_SECRET_ACCESS_KEY,
        //   },
        },
      })
    const fileStore = new FileStore({
        directory: join(process.cwd(), 'uploads'), // 设置文件上传目录
    })
    this.server = new Server({
    path: '/upload/files', // tus 服务的 API 路径
    datastore: s3Store,
    onUploadCreate: (upload) => {
        // 上传开始时执行的操作
        console.log(`Upload created with ID: ${upload.id}`);
        // 这里可以进行一些初始化操作，例如记录数据库上传的信息，初始化上传日志等
      },
      onUploadFinish: (upload) => {
        // 上传完成时执行的操作
        console.log(`Upload finished with ID: ${upload.id}`);
        // 这里可以执行一些清理工作，例如将上传记录标记为完成
      },
      onResponseError: (error, req, res) => {
        // 处理上传过程中发生的错误
        console.error(`Error during upload: ${error.message}`);
        res.status(500).json({
          error: 'Upload failed',
          message: error.message,
        });
      },
    })
  }


  handleTusRequest(req: Request, res: Response) {
    this.server.handle(req, res);
  }
}