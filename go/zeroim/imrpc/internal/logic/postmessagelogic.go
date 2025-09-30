package logic

import (
	"context"
	"zeroim/common/session"
	"zeroim/imrpc/imrpc"
	"zeroim/imrpc/internal/svc"

	"github.com/zeromicro/go-zero/core/collection"
	"github.com/zeromicro/go-zero/core/logx"
	"google.golang.org/protobuf/proto"
)

type PostMessageLogic struct {
	ctx    context.Context
	svcCtx *svc.ServiceContext
	logx.Logger
}

func NewPostMessageLogic(ctx context.Context, svcCtx *svc.ServiceContext) *PostMessageLogic {
	return &PostMessageLogic{
		ctx:    ctx,
		svcCtx: svcCtx,
		Logger: logx.WithContext(ctx),
	}
}

// PostMessage 处理消息发送逻辑，根据会话信息将消息推送到对应的设备队列中。
// 参数:
//   - in: 包含待发送消息及会话标识的请求结构体，类型为 *imrpc.PostMsg
//
// 返回值:
//   - *imrpc.PostReponse: 消息发送响应结构体，当前为空结构体
//   - error: 错误信息，如果处理过程中出现异常则返回错误
func (l *PostMessageLogic) PostMessage(in *imrpc.PostMsg) (*imrpc.PostReponse, error) {
	var (
		allDevice bool
		name      string
		token     string
		id        uint64
	)

	// 判断是否是全设备推送：若 Token 非空，则认为是向所有设备广播消息
	if len(in.Token) != 0 {
		allDevice = true
		token = in.Token
	} else {
		// 否则从 SessionId 中解析出用户名、Token 和设备 ID
		name, token, id = session.FromString(in.SessionId).Info()
	}

	// 从 Redis 获取该 Token 对应的所有在线设备 SessionId 列表
	sessionIds, err := l.svcCtx.BizRedis.Zrange(token, 0, -1)
	if err != nil {
		return nil, err
	}
	if len(sessionIds) == 0 {
		return nil, err
	}

	// TODO 此处编辑用户输入的信息，然后返回给客户端
	// 示例：在原始消息前加上反馈提示
	in.Msg = "feedback: " + in.Msg

	// 将修改后的消息序列化为字节数据，用于后续推送
	data, err := proto.Marshal(in)
	if err != nil {
		return nil, err
	}

	// 使用集合去重需要推送的目标设备名（仅在全设备推送时使用）
	set := collection.NewSet[string]()

	// 遍历所有在线设备 SessionId，判断是否为目标推送对象并执行推送或收集目标设备名
	for _, sessionId := range sessionIds {
		respName, _, respId := session.FromString(sessionId).Info()

		if allDevice {
			// 全设备推送模式下，记录目标设备名到集合中以供后续统一推送
			set.Add(respName)
		} else {
			// 单设备推送模式下，校验名称与 ID 是否匹配后再进行推送
			if name == respName && id == respId {
				edgeQueue, ok := l.svcCtx.QueueList.Load(respName)
				if !ok {
					logx.Severe("invalid session")
				} else {
					err = edgeQueue.Push(l.ctx, string(data))
					if err != nil {
						logx.Errorf("[PostMessage] push data: %s error: %v", string(data), err)
						return nil, err
					}
				}
			} else {
				logx.Severe("invalid session")
			}
		}
	}

	// 若存在多个目标设备需推送，则输出日志统计数量
	if set.Count() > 0 {
		logx.Infof("send to %d devices", set.Count())
	}

	// 执行实际的消息推送操作至各个目标设备队列
	for _, respName := range set.Keys() {
		edgeQueue, ok := l.svcCtx.QueueList.Load(respName)
		if !ok {
			logx.Errorf("invalid session")
		} else {
			err = edgeQueue.Push(l.ctx, string(data))
			if err != nil {
				return nil, err
			}
		}
	}

	// 返回成功响应
	return &imrpc.PostReponse{}, nil
}
