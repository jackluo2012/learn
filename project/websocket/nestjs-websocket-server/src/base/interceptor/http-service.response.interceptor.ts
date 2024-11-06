import { CallHandler, ExecutionContext, NestInterceptor } from "@nestjs/common";
import { map, Observable } from "rxjs";
import { SUCCESS } from "src/common/return-code";
import { ServerResponseWrapper } from "src/common/server-response-wrapper";




export class HttpServiceResponseInterceptor implements NestInterceptor {
    intercept(context: ExecutionContext, next: CallHandler): Observable<any>|Promise<Observable<any>> {
        // do something before
        return next.handle().pipe(
            map(data => {
                const resp: ServerResponseWrapper = {
                    returnCode: SUCCESS.codeString,
                    data: data,
                    errorMessage: ""
                };
                return resp;
            }
            )
        );
    }
    
}