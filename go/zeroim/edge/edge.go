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

func main() {
	flag.Parse()

	var (
		c   config.Config
		err error
	)
	conf.MustLoad(*configFile, &c)
	ctx := svc.NewServiceContext(c)

	logx.DisableStat()

	tcpServer := server.NewTCPServer(ctx)
	wsServer := server.NewWSServer(ctx)
	protobuf := libnet.NewIMProtocol()

	tcpServer.Server, err = socket.NewServe(c.Name, c.TCPListenOn, protobuf, c.SendChanSize)
	if err != nil {
		panic(fmt.Sprintf("new tcp server error: %v", err))
	}
	wsServer.Server, err = socketio.NewServe(c.Name, c.WSListenOn, protobuf, c.SendChanSize)
	if err != nil {
		panic(fmt.Sprintf("new ws server error: %v", err))
	}

	http.Handle("/ws", websocket.Handler(func(conn *websocket.Conn) {
		conn.PayloadType = websocket.BinaryFrame
		wsServer.HandleRequest(conn)
	}))

	go wsServer.Start()
	go tcpServer.HandleRequest()
	go tcpServer.KqHeart()

	fmt.Printf("Starting server at %s...\n", c.TCPListenOn)
	serviceGroup := zeroservice.NewServiceGroup()
	defer serviceGroup.Stop()

	for _, mq := range logic.Consumers(context.Background(), ctx, tcpServer.Server, wsServer.Server) {
		serviceGroup.Add(mq)
	}
	serviceGroup.Start()
}
