export interface UserDto {
    id: number;
    name: string;
    email: string;
    password: string;
    age: number;
    // role: string;
    // avatar: string;
    // createdAt: Date;
    // updatedAt: Date;
}

export interface UserLoginDto {
    email: string;
    password: string;
}