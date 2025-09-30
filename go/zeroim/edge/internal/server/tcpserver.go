package server

import (
	"zeroim/common/discovery"
	"zeroim/common/socket"
	"zeroim/edge/client"
	"zeroim/edge/internal/svc"

	"github.com/zeromicro/go-zero/core/logx"
)

type TCPServer struct {
	svcCtx *svc.ServiceContext
	Server *socket.Server
}

func NewTCPServer(svcCtx *svc.ServiceContext) *TCPServer {
	return &TCPServer{svcCtx: svcCtx}
}

// HandleRequest 处理TCP服务器的请求连接
// 该函数会持续监听并接受新的客户端连接，为每个连接创建客户端实例并启动会话循环
// 无参数
// 无返回值
func (srv *TCPServer) HandleRequest() {
	// 持续监听新的客户端连接
	for {
		// 接受新的客户端会话连接
		session, err := srv.Server.Accept()
		if err != nil {
			panic(err)
		}
		// 创建新的客户端实例并启动独立的会话处理协程
		cli := client.NewClient(srv.Server.Manager, session, srv.svcCtx.IMRpc)
		go srv.sessionLoop(cli)
	}
}

func (srv *TCPServer) sessionLoop(client *client.Client) {
	message, err := client.Receive()
	if err != nil {
		logx.Errorf("[sessionLoop] client.Receive error: %v", err)
		_ = client.Close()
		return
	}

	// 登录校验
	err = client.Login(message)
	if err != nil {
		logx.Errorf("[sessionLoop] client.Login error: %v", err)
		_ = client.Close()
		return
	}

	go client.HeartBeat()

	for {
		message, err := client.Receive()
		if err != nil {
			logx.Errorf("[sessionLoop] client.Receive error: %v", err)
			_ = client.Close()
			return
		}
		err = client.HandlePackage(message)
		if err != nil {
			logx.Errorf("[sessionLoop] client.HandleMessage error: %v", err)
		}
	}
}

// KqHeart 向ETCD注册中心发送心跳信号，维持服务注册状态
// 该方法创建一个队列工作者实例，并执行心跳检测操作
// 参数: 无
// 返回值: 无
func (srv *TCPServer) KqHeart() {
	// 创建新的队列工作者实例，用于与ETCD进行交互
	work := discovery.NewQueueWorker(srv.svcCtx.Config.Etcd.Key, srv.svcCtx.Config.Etcd.Hosts, srv.svcCtx.Config.KqConf)
	// 执行心跳检测，向ETCD注册中心发送心跳信号
	work.HeartBeat()
}
