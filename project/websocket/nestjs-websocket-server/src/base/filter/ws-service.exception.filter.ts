import { ArgumentsHost, Catch, ExceptionFilter, HttpException, WsExceptionFilter } from "@nestjs/common";
import { ServerResponseWrapper } from "src/common/server-response-wrapper";
import { BizException } from "../biz-exception";
/**
 * 拦截HTTP服务的异常
 * WebSocket的异常过滤器中，想要继续后的数据处理，需要在方法返回前，从host中取到第三个参数对象（索引值为2），该值是一个回调函数，将处理后的数据作为参数，调用该callback方法，框架才能继续处理。—— WebSocket异常过滤器最终返回的关键点
 */
@Catch()
export class WsServiceExceptionFilter implements WsExceptionFilter {
    catch(exception: any, host: ArgumentsHost) {
        // 进入该拦截器，说明 http 调用 中存在导常
        let responseWrapper: ServerResponseWrapper;
        if (exception instanceof BizException) {
            // 业务层的Exception
            responseWrapper = {
                returnCode: exception.errorCode.codeString,
                errorMessage:exception.errorMessage,
            }
        } else {
            // 其他错误
            responseWrapper = {
                returnCode: 'IM9999',
                errorMessage: 'server unknown error: ' + exception.message,
            };
        }
        // 对异常进行封装以后，需要让框架继续进行调用处理，才能正确的响应给客户端
        // https://stackoverflow.com/questions/61795299/nestjs-return-ack-in-exception-filter
        const callback = host.getArgByIndex(2);
        if (callback && typeof callback === 'function') {
            callback(responseWrapper);
        }
    }
}