import { Controller, Get, Query } from "@nestjs/common";
import { UserService } from "./user.service";
import * as _ from 'lodash';
import { UserDto } from "src/entity/user/user.dto";
import { BizException } from "src/base/biz-exception";
import { ERROR_REQ_FIELD_ERROR } from "src/common/return-code";

@Controller("user")
export class UserController {
    constructor(private readonly userService: UserService) {}

    @Get()
    async getHello(@Query('id') id: number): Promise<UserDto> {
        if(_.isEmpty(id)){
            throw BizException.create(ERROR_REQ_FIELD_ERROR, 'id is empty');
        }
        return this.userService.getUserById(id);
    }
}