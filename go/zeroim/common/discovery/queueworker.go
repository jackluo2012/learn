package discovery

import (
	"context"
	"encoding/json"
	"time"

	"github.com/zeromicro/go-queue/kq"
	"github.com/zeromicro/go-zero/core/logx"
	clinetv3 "go.etcd.io/etcd/client/v3"
)

type QueueWorker struct {
	key    string
	kqConf kq.KqConf
	client *clinetv3.Client
}

func NewQueueWorker(key string, endpoints []string, kqConf kq.KqConf) *QueueWorker {
	cfg := clinetv3.Config{
		Endpoints:   endpoints,
		DialTimeout: time.Second * 5,
	}
	client, err := clinetv3.New(cfg)
	if err != nil {
		panic(err)
	}
	return &QueueWorker{
		key:    key,
		kqConf: kqConf,
		client: client,
	}
}

func (q *QueueWorker) HeartBeat() {
	value, err := json.Marshal(q.kqConf)
	if err != nil {
		panic(err)
	}
	q.register(string(value))
}

// etcd中写入了kafka的连接信息，和不断地进行续约
func (q *QueueWorker) register(value string) {
	// 申请一个45秒的租约
	leaseGrantResp, err := q.client.Grant(context.TODO(), 45)
	if err != nil {
		panic(err)
	}
	// 拿到租约ID
	leaseId := leaseGrantResp.ID
	logx.Infof("查看leaseId: %x", leaseId)

	// 获取kv api子集
	kv := clinetv3.NewKV(q.client)

	// put 一个kv,让它与租约关系联起来，从而实现 10秒内自动过期
	putResp, err := kv.Put(context.TODO(), q.key, value, clinetv3.WithLease(leaseId))
	if err != nil {
		panic(err)
	}
	// 自动续更新租约，当我们申请了一个租约后，这个租约会自动过期，过期后，这个租约会自动更新，从而实现自动续费
	keepRespChan, err := q.client.KeepAlive(context.TODO(), leaseId)
	if err != nil {
		panic(err)
	}
	// 处理续租应答的协程
	go func() {
		for keepResp := range keepRespChan {
			if keepResp == nil {
				logx.Infof("租约已经失效:%x", leaseId)
				q.register(value)
				return
			}
			// 每秒会续租一次，所以就会受到一次应答
			logx.Infof("收到自动续租应答:%x", keepResp.ID)
		}
	}()
	logx.Info("写入成功:", putResp.Header.Revision)
}
