import { Global } from "@nestjs/common";


@Global()
@Module({
  providers: [WsAdapter],
  exports: [WsAdapter],

})
export class AdaptersModule {}