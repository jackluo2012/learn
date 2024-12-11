import { Controller, All, Req, Res } from '@nestjs/common';
import { TusServerService } from './tus/tus-server.service';
import { Request, Response } from 'express';

@Controller('upload')
export class UploadController {
  constructor(private readonly tusServerService: TusServerService) {}

  @All('/local/')
  handleTusUpload(@Req() req: Request, @Res() res: Response) {
    this.tusServerService.handleTusRequest(req, res);
  }


  @All('/files/:id')
  handleFiles(@Req() req: Request, @Res() res: Response) {
    this.tusServerService.handleTusRequest(req, res);
  }
}
