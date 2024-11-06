import { ArgumentsHost, CallHandler, Catch ,ExecutionContext,NestInterceptor} from "@nestjs/common";
import { BaseWsExceptionFilter } from "@nestjs/websockets";
import { map, Observable } from "rxjs";
import { SUCCESS } from "src/common/return-code";
import { ServerResponseWrapper } from "src/common/server-response-wrapper";

export class WsServiceResponseInterceptor implements NestInterceptor {
    intercept(
        context: ExecutionContext, 
        next: CallHandler<any>): Observable<any> | Promise<Observable<any>> {
       return next.handle().pipe(map(data => {
            const resp:ServerResponseWrapper ={
                returnCode: SUCCESS.codeString,
                data: data,
                errorMessage: ""
            };
            return resp;
       }
       ));
    }
  }