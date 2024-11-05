### 一、UE5 像素流技术
#### 1.1 概述
UE5 像素流技术是一种将 UE5 游戏画面传输到其他设备的技术。它允许用户在不同的设备上实时查看和操作 UE5 游戏画面。

#### 1.2 实现原理
UE5 像素流技术基于 UE5 引擎的网络功能，通过将游戏画面编码为视频流，然后通过网络传输到其他设备，再解码显示。

#### 1.3 实现步骤
1. 在 UE5 中创建一个新项目
-   编辑 - 插件
-   搜索 pixel streaming 选择 pixel streaming  插件
-   重启项目
2. 编辑 - 项目设置 - 搜索 帧率
- 引擎 -> 一般设置
 使用固定帧率
 设置帧率 30
 
 打包项目
像素流技术文档 UE5
https://dev.epicgames.com/documentation/zh-cn/unreal-engine/pixel-streaming-in-unreal-engine 
 

### 二、UE5.4 像素流设置
官方地址
https://dev.epicgames.com/documentation/zh-cn/unreal-engine/pixel-streaming-in-editor?application_version=5.4

下载对应的版本
https://github.com/EpicGamesExt/PixelStreamingInfrastructure/releases

### 解压到安装目录下面的
D:\Program Files\Epic Games\UE_5.4\Engine\Plugins\Media\PixelStreaming\Resources\WebServers

### 启动项目
编辑 - 项目设置 - 搜索 pixel streaming
- 视频流
- 启用像素流
- 选择对应的 Web 服务器

### 浏览器访问
-   请一定用ip 址址，不要用localhost和127.0.0.1
-   http://192.168.1.10:8080/
