import { ReturnCode } from "src/common/return-code";

export class BizException {
    private readonly _errorCode: ReturnCode;
    private readonly _errorMessage: string;

    get errorCode(): ReturnCode {
        return this._errorCode;
    }

    get errorMessage(): string {
        return this._errorMessage;
    }

    constructor(errorCode: ReturnCode, errorMessage: string) {
        this._errorCode = errorCode;
        this._errorMessage = errorMessage;
    }
    static create(errorCode: ReturnCode, errorMessage?: string) {
        return new BizException(errorCode, errorMessage);
    }
}