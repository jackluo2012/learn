/**
 // 获取用户基本信息成功
{
    "returnCode": "SUC00000",
    "data": {
        "username": "w4ngzhen",
        "lastLoginTime": "2022-11-22 11:50:22.000"
    }
}
// 获取用户名称出错（没有提供对应的userId）
{
    "returnCode": "ERR40000",
    "errorMessage": "user id is empty.",
}
// 获取服务端时间
{
    "returnCode": "SUC0000",
    "data": "2022-11-22 11:22:33.000"
}

 */


export interface ServerResponseWrapper {
    
    returnCode: string;
    errorMessage: string;
    data?: any;
}