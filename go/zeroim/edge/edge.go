package main

import (
	"context"
	"flag"
	"fmt"
	"net/http"

	"zeroim/common/libnet"
	"zeroim/common/socket"
	"zeroim/common/socketio"
	"zeroim/edge/internal/config"
	"zeroim/edge/internal/logic"
	"zeroim/edge/internal/server"
	"zeroim/edge/internal/svc"

	"github.com/zeromicro/go-zero/core/conf"
	"github.com/zeromicro/go-zero/core/logx"
	zeroservice "github.com/zeromicro/go-zero/core/service"
	"golang.org/x/net/websocket"
)

var configFile = flag.String("f", "etc/edge.yaml", "the config file")

// main 函数是程序的入口点，负责初始化配置、启动TCP和WebSocket服务器，
// 并启动消息队列消费者来处理业务逻辑。
// 该函数不接受参数，也不返回值。
func main() {
	// 解析命令行参数
	flag.Parse()

	// 声变量用于存储配置和错误信息
	var (
		c   config.Config
		err error
	)

	// 加载配置文件到配置结构体中
	conf.MustLoad(*configFile, &c)

	// 创建服务上下文，包含配置和其他共享资源
	ctx := svc.NewServiceContext(c)

	// 禁用日志统计功能
	logx.DisableStat()

	// 创建TCP服务器和WebSocket服务器实例
	tcpServer := server.NewTCPServer(ctx)
	wsServer := server.NewWSServer(ctx)

	// 创建IM协议处理器
	protobuf := libnet.NewIMProtocol()

	// 初始化TCP服务器，绑定到指定端口并配置协议处理器
	tcpServer.Server, err = socket.NewServe(c.Name, c.TCPListenOn, protobuf, c.SendChanSize)
	if err != nil {
		panic(fmt.Sprintf("new tcp server error: %v", err))
	}

	// 初始化WebSocket服务器，绑定到指定端口并配置协议处理器
	wsServer.Server, err = socketio.NewServe(c.Name, c.WSListenOn, protobuf, c.SendChanSize)
	if err != nil {
		panic(fmt.Sprintf("new ws server error: %v", err))
	}

	// 配置WebSocket处理函数，设置二进制帧格式并处理连接请求
	http.Handle("/ws", websocket.Handler(func(conn *websocket.Conn) {
		conn.PayloadType = websocket.BinaryFrame
		wsServer.HandleRequest(conn)
	}))

	// 启动WebSocket服务器
	go wsServer.Start()

	// 启动TCP服务器处理请求
	go tcpServer.HandleRequest()

	// 启动TCP服务器心跳检测
	go tcpServer.KqHeart()

	// 打印服务器启动信息
	fmt.Printf("Starting server at %s...\n", c.TCPListenOn)

	// 创建服务组用于管理多个服务的生命周期
	serviceGroup := zeroservice.NewServiceGroup()
	defer serviceGroup.Stop()

	// 获取并添加消息队列消费者到服务组中
	for _, mq := range logic.Consumers(context.Background(), ctx, tcpServer.Server, wsServer.Server) {
		serviceGroup.Add(mq)
	}

	// 启动所有服务
	serviceGroup.Start()
}
