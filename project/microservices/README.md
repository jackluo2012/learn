### NestJS 微服务架构

#### 1. 创建项目

```bash
nest new api-gateway
```

#### 2. 创建服务 -用于管理读者

```bash
nest new reader-mgt
cd reader-mgt
npm run start
```

#### 3. 创建服务 -用于管理图书

```bash
nest new article-mgt
cd article-mgt
npm run start
```

#### 4. 安装api 网关

```bash
npm install @nestjs/microservices nats
```

#### 5. 创建实体

```bash