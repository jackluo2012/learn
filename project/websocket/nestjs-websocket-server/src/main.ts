import { NestFactory } from '@nestjs/core';
import { AppModule } from './app.module';
import { HttpServiceResponseInterceptor } from './base/interceptor/http-service.response.interceptor';
import { HttpServiceExceptionFilter } from './base/filter/http-service.exception.filter';
import { RedisIoAdapter } from './adapters/redis-io-adapter';


async function bootstrap() {
  const app = await NestFactory.create(AppModule);
  // 增加全局拦截器
  app.useGlobalInterceptors(new HttpServiceResponseInterceptor());
  // 增加全局过滤器
  app.useGlobalFilters(new HttpServiceExceptionFilter());
  const redisIoAdapter = new RedisIoAdapter(app); // 使用redis作为adapter
  await redisIoAdapter.connectToRedis();
  app.useWebSocketAdapter(redisIoAdapter);
  
  await app.listen(process.env.PORT ?? 3000);
}
bootstrap();
