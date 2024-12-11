import { NestFactory } from '@nestjs/core';
import { AppModule } from './app.module';
import { INestApplication } from '@nestjs/common';
import { NestExpressApplication } from '@nestjs/platform-express';

  

async function bootstrap() {
  const app = await NestFactory.create<NestExpressApplication>(AppModule);
  app.enableCors();
  //增加之后，可以通过 本地访问http://localhost:3000/来访问

  app.useStaticAssets('client', {
    prefix: '/public',
  });
  await app.listen(process.env.PORT ?? 3000);
}

bootstrap();
