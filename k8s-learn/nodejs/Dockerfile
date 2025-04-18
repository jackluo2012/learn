###################

# BUILD FOR LOCAL DEVELOPMENT

###################

FROM node:20.18.1-alpine AS development

# Create app directory

WORKDIR /app

# Copy application dependency manifests to the container image.

# A wildcard is used to ensure copying both package.json AND package-lock.json (when available).

# Copying this first prevents re-running npm install on every code change.

COPY --chown=node:node package*.json ./

RUN npm config set registry https://registry.npmmirror.com/
# Install app dependencies using the `npm ci` command instead of `npm install`

RUN npm ci --omit=dev

# Bundle app source

COPY --chown=node:node . .

# Use the node user from the image (instead of the root user)

USER node

## 初始化数据库
#RUN npm run prisma:generate
###################

# BUILD FOR PRODUCTION

###################

FROM node:20.18.1-alpine AS build

WORKDIR /app

RUN npm config set registry https://registry.npmmirror.com/

COPY --chown=node:node package*.json ./

# In order to run `npm run build` we need access to the Nest CLI which is a dev dependency. In the previous development stage we ran `npm ci` which installed all dependencies, so we can copy over the node_modules directory from the development image

COPY --chown=node:node --from=development /app/node_modules ./node_modules

COPY --chown=node:node . .

# Run the build command which creates the production bundle

#RUN npm run build

# Set NODE_ENV environment variable

ENV NODE_ENV=production

# Running `npm ci` removes the existing node_modules directory and passing in --only=production ensures that only the production dependencies are installed. This ensures that the node_modules directory is as optimized as possible

RUN npm ci --only=production && npm cache clean --force

USER node

###################

# PRODUCTION

###################

FROM node:20.18.1-alpine AS production

# 安装 Docker 客户端所需的依赖
RUN apk add --no-cache \
    docker-cli \
    curl \
    bash

# 配置 Docker 客户端支持 HTTP 镜像仓库
RUN mkdir -p /etc/docker && \
    echo '{ "insecure-registries":["192.168.110.116:30500"] }' > /etc/docker/daemon.json


# Copy the bundled code from the build stage to the production image
WORKDIR /app

COPY --chown=node:node --from=build /app/node_modules /app/node_modules
#COPY --chown=node:node --from=build /app/dist /app/dist


# Start the server using the production build
EXPOSE 8100
COPY app.js .
# CMD [ "node", "test.js" ]
CMD [ "node", "/app/app.js" ]