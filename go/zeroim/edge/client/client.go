package client

import (
	"context"
	"time"

	"zeroim/common/libnet"
	"zeroim/imrpc/imrpcclient"

	"github.com/zeromicro/go-zero/core/logx"
	"google.golang.org/protobuf/proto"
)

type Client struct {
	Session   *libnet.Session
	Manager   *libnet.Manager
	IMRpc     imrpcclient.Imrpc
	heartbeat chan *libnet.Message
}

func NewClient(manager *libnet.Manager, session *libnet.Session, imrpc imrpcclient.Imrpc) *Client {
	return &Client{
		Session:   session,
		Manager:   manager,
		IMRpc:     imrpc,
		heartbeat: make(chan *libnet.Message),
	}
}

func (c *Client) Login(msg *libnet.Message) error {
	loginReq, err := makeLoginMessage(msg)
	if err != nil {
		return err
	}

	c.Session.SetToken(loginReq.Token)
	c.Manager.AddSession(c.Session)

	_, err = c.IMRpc.Login(context.Background(), &imrpcclient.LoginRequest{
		Token:         loginReq.Token,
		Authorization: loginReq.Authorization,
		SessionId:     c.Session.Session().String(),
	})
	if err != nil {
		msg.Status = 1
		msg.Body = []byte(err.Error())
		e := c.Send(*msg)
		if e != nil {
			logx.Errorf("[Login] client.Send error: %v", e)
		}
		return err
	}

	msg.Status = 0
	msg.Body = []byte("登录成功")
	err = c.Send(*msg)
	if err != nil {
		logx.Errorf("[Login] client.Send error: %v", err)
	}

	return err
}

func (c *Client) Receive() (*libnet.Message, error) {
	return c.Session.Receive()
}

func (c *Client) Send(msg libnet.Message) error {
	return c.Session.Send(msg)
}

func (c *Client) Close() error {
	return c.Session.Close()
}

// HandlePackage 处理接收到的消息包，将消息转发到IM服务
// 参数:
//   - msg: 需要处理的消息对象，包含具体的消息内容
//
// 返回值:
//   - error: 消息转发过程中可能产生的错误，如果转发成功则返回nil
func (c *Client) HandlePackage(msg *libnet.Message) error {
	// 构造转发消息请求
	req := makePostMessage(c.Session.Session().String(), msg)
	if req == nil {
		return nil
	}

	// 调用IM服务的PostMessage接口转发消息
	_, err := c.IMRpc.PostMessage(context.Background(), req)
	if err != nil {
		logx.Errorf("[HandlePackage] client.PostMessage error: %v", err)
	}

	return err
}

const heartBeatTimeout = time.Second * 60

func (c *Client) HeartBeat() error {
	timer := time.NewTimer(heartBeatTimeout)
	for {
		select {
		case heaetbeat := <-c.heartbeat:
			c.Session.SetReadDeadline(time.Now().Add(heartBeatTimeout * 5))
			c.Send(*heaetbeat)

		case <-timer.C:
		}
	}
}

func makeLoginMessage(msg *libnet.Message) (*imrpcclient.LoginRequest, error) {
	// 登录功能还没做
	// 这里临时处理，先把PostMsg中的Msg转换成LoginRequest中的Token和Authorization用于登录处理
	var postMsg imrpcclient.PostMsg
	err := proto.Unmarshal(msg.Body, &postMsg)
	if err != nil {
		return nil, err
	}
	loginReq := imrpcclient.LoginRequest{
		Token:         postMsg.Msg,
		Authorization: postMsg.Msg,
	}

	return &loginReq, nil
}

// makePostMessage 将libnet.Message转换为imrpcclient.PostMsg结构体
// sessionId: 会话ID，用于标识当前会话
// msg: 原始消息对象，包含需要转换的数据
// 返回值: 转换后的PostMsg指针，如果转换失败则返回nil
func makePostMessage(sessionId string, msg *libnet.Message) *imrpcclient.PostMsg {
	var postMessageReq imrpcclient.PostMsg

	// 反序列化消息体到PostMsg结构体
	err := proto.Unmarshal(msg.Body, &postMessageReq)
	if err != nil {
		logx.Errorf("[makePostMessage] proto.Unmarshal msg: %v error: %v", msg, err)
		return nil
	}

	// 将原始消息的元数据复制到PostMsg结构体中
	postMessageReq.Version = uint32(msg.Version)
	postMessageReq.Status = uint32(msg.Status)
	postMessageReq.ServiceId = uint32(msg.ServiceId)
	postMessageReq.Cmd = uint32(msg.Cmd)
	postMessageReq.Seq = msg.Seq
	postMessageReq.SessionId = sessionId

	return &postMessageReq
}
