import {  Injectable } from "@nestjs/common";
import { UserDto } from "src/entity/user/user.dto";

@Injectable()
export class UserService {
    async getUserById(id: number): Promise<UserDto>{
        console.log("get user by id=",id);
        //测试数据
        const demoData : UserDto[] = [
            {
                id: 1,
                name: "John Doe",
                age: 20,
                email: "",
                password: ""
            }, 
            {
                id: 2,
                name: "Jane Doe",
                age: 22,
                email: "",
                password: ""
            }
        ];
        return demoData.find(user => user.id === Number(id));
    }
}