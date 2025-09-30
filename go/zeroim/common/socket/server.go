package socket

import (
	"crypto/tls"
	"errors"
	"io"
	"net"
	"strings"
	"time"

	"zeroim/common/libnet"
)

type Server struct {
	Name         string
	Manager      *libnet.Manager
	Listener     net.Listener
	Protocol     libnet.Protocol
	SendChanSize int
}

func NewServer(name string, l net.Listener, p libnet.Protocol, sendChanSize int) *Server {
	return &Server{
		Name:         name,
		Manager:      libnet.NewManager(name),
		Listener:     l,
		Protocol:     p,
		SendChanSize: sendChanSize,
	}
}

// Accept 等待并接受一个新的网络连接，返回对应的会话对象
// 返回的会话对象封装了新建立的网络连接，可用于后续的通信处理
// 参数: 无
// 返回值:
//   - *libnet.Session: 新建立的会话对象，包含网络连接和编解码器
//   - error: 连接过程中发生的错误，如果监听器被关闭则返回io.EOF
func (s *Server) Accept() (*libnet.Session, error) {
	var tempDelay time.Duration
	for {
		// 尝试接受一个新的网络连接
		conn, err := s.Listener.Accept()
		if err != nil {
			// 处理网络超时错误，采用指数退避策略重试
			var ne net.Error
			if errors.As(err, &ne) && ne.Timeout() {
				if tempDelay == 0 {
					tempDelay = 5 * time.Millisecond
				} else {
					tempDelay *= 2
				}
				if maxDelay := 1 * time.Second; tempDelay > maxDelay {
					tempDelay = maxDelay
				}
				time.Sleep(tempDelay)
				continue
			}
			// 处理监听器被关闭的情况
			if strings.Contains(err.Error(), "use of closed network connection") {
				return nil, io.EOF
			}
			return nil, err
		}

		// 成功建立连接，创建并返回新的会话对象
		return libnet.NewSession(s.Manager, s.Protocol.NewCodec(conn), s.SendChanSize), nil
	}
}

func (s *Server) Close() {
	s.Listener.Close()
	s.Manager.Close()
}

func NewServe(name, address string, protocol libnet.Protocol, sendChanSize int) (*Server, error) {
	addr, err := net.ResolveTCPAddr("tcp", address)
	if err != nil {
		return nil, err
	}
	listener, err := net.ListenTCP("tcp", addr)
	if err != nil {
		return nil, err
	}
	return NewServer(name, listener, protocol, sendChanSize), nil
}

func NewTlsServe(name string, config *tls.Config, address string, protocol libnet.Protocol, sendChanSize int) (*Server, error) {
	addr, err := net.ResolveTCPAddr("tcp", address)
	if err != nil {
		return nil, err
	}
	listener, err := tls.Listen("tcp", addr.String(), config)
	if err != nil {
		return nil, err
	}
	return NewServer(name, listener, protocol, sendChanSize), nil
}
