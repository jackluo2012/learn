import { All, Controller, Get, Req, Res } from '@nestjs/common';
import { TusService } from 'src/config/tus.service';

@Controller('upload')
export class UploadController {

    constructor(
      private tusService: TusService,
      ) {}

    @All("*")
    async tus(@Req() req, @Res() res) {
        return this.tusService.handleTusRequest(req, res);
    }
}
