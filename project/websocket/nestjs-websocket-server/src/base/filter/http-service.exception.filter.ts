import { ArgumentsHost, Catch, ExceptionFilter, HttpException } from "@nestjs/common";
import { ServerResponseWrapper } from "src/common/server-response-wrapper";
import { BizException } from "../biz-exception";
/**
 * 拦截HTTP服务的异常
 * 
 */
@Catch()
export class HttpServiceExceptionFilter implements ExceptionFilter {
    catch(exception: any, host: ArgumentsHost) {
        console.log('HttpServiceExceptionFilter=',exception);
        let responseWrapper: ServerResponseWrapper;
        let httpStatusCode: number;
        if (exception instanceof BizException) {
            // 业务异常
            responseWrapper = {
                returnCode: exception.errorCode.codeString,
                errorMessage: exception.errorMessage,
            }
            httpStatusCode = exception.errorCode.statusCode;
        } else if (exception instanceof HttpException) {
            // 框架层的http异常
            responseWrapper = {
                returnCode: 'IM9009',
                errorMessage: exception.message,
            }
            httpStatusCode = exception.getStatus();
        } else {
            
            console.log('HttpServiceExceptionFilter=',exception);
            // 其他异常
            responseWrapper = {
                returnCode: 'IM9009',
                errorMessage: exception.message,
            }
            httpStatusCode = 500;
            
        }
        // 该拦截器处理HTTP服务的异常，所以手动切换到HTTP Host
        const httpHost = host.switchToHttp();
        const response = httpHost.getResponse();
        response.status(httpStatusCode).json(responseWrapper);
    }
    
}