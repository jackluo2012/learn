import { Body, Controller, Get, Post, Query, UploadedFile, UploadedFiles, UseInterceptors } from '@nestjs/common';
import { AppService } from './app.service';
import { FilesInterceptor } from '@nestjs/platform-express';
import * as fs from 'fs';
@Controller()
export class AppController {
  constructor(private readonly appService: AppService) { }

  @Post('upload')
  @UseInterceptors(
    FilesInterceptor('files', 20, {
      dest: 'uploads',
    }),
  )
  uploadFiles(
    @UploadedFiles() files: Array<Express.Multer.File>,
    @Body() body,
  ) {
    console.log('body', body);
    console.log('files', files);
    const fileName = body.name.match(/(.+)\-\d+$/)[1];
    const chunkDir = 'uploads/chunks_' + fileName;
    if (!fs.existsSync(chunkDir)) {
      fs.mkdirSync(chunkDir);
    }
    fs.cpSync(files[0].path, chunkDir + '/' + body.name);//将文件复制到chunks目录下
    fs.rmSync(files[0].path); // 删除临时文件
  }
  @Get('merge')
  mergeFiles(@Query('name') name: string) {
    // 构建存储文件 片段的目录路径
    const chunkDir = `uploads/chunks_${name}`;

    // 读取文件 片段目录中的所有文件
    const files = fs.readdirSync(chunkDir);
    // 初始化用于跟踪已合并文件大小的变量
    let totalSize = 0;
    let count = 0;
    //遍历文件片段，逐个进行合并
    let startPos = 0;

    // 遍历文件片段，逐个进行合并
    files.map((file) => {
      // 构建当前文件 片段的路径
      const filePath = `${chunkDir}/${file}`;
      // 获取当前文件 片段的流
      const fileStream = fs.createReadStream(filePath);
      // 将文件 片段流写入目标文件，从上一个片段的结束位置开始写入
      fileStream.pipe(
        fs.createWriteStream(`uploads/${name}`,
          { start: startPos }))
        .on('finish', () => {
          // 删除当前文件 片段
          fs.unlinkSync(filePath);
          // 更新已合并文件的大小
          totalSize += fileStream.bytesRead;
          count++;
          if (count === files.length) {
            fs.rmSync(chunkDir,{recursive: true});
            console.log('合并完成');
          }
        })
        //更新下一个片段的起始位置
        startPos += fs.statSync(filePath).size;
    });
  }
  @Get()
  getHello(): string {
    return this.appService.getHello();
  }
}
