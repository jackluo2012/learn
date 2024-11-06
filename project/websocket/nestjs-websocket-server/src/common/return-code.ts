export class ReturnCode{
    private readonly _preCode: 'SUC'|'ERR'
    private readonly _subCode: string;
    private readonly _statusCode: number;

    get codeString(): string{
        return `${this._preCode}${this._subCode}`;
    }

    get statusCode(): number{
        return this._statusCode;
    }

    constructor(preCode: 'SUC'|'ERR', subCode: string, statusCode: number){
        this._preCode = preCode;
        this._subCode = subCode;
        this._statusCode = statusCode;
    }
}
export const SUCCESS = new ReturnCode('SUC', '0000', 200);
export const ERROR = new ReturnCode('ERR', '0000', 500);
export const ERROR_NOT_FOUND = new ReturnCode('ERR', '40400', 404);
export const ERROR_REQ_FIELD_ERROR = new ReturnCode('ERR', '40000', 400);