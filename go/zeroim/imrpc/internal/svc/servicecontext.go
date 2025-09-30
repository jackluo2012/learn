package svc

import (
	"context"
	"encoding/json"
	"sync"
	"time"

	"zeroim/common/discovery"
	"zeroim/imrpc/internal/config"

	"github.com/zeromicro/go-queue/kq"
	"github.com/zeromicro/go-zero/core/discov"
	"github.com/zeromicro/go-zero/core/logx"
	"github.com/zeromicro/go-zero/core/stores/redis"
	"github.com/zeromicro/go-zero/core/threading"
	clientv3 "go.etcd.io/etcd/client/v3"
)

type ServiceContext struct {
	Config    config.Config
	BizRedis  *redis.Redis
	QueueList *QueueList
}

// NewServiceContext 创建一个新的服务上下文实例
// 参数:
//   - c: 配置信息结构体，包含服务所需的各项配置
//
// 返回值:
//   - *ServiceContext: 返回初始化完成的服务上下文指针
func NewServiceContext(c config.Config) *ServiceContext {
	// 初始化队列列表
	queueList := GetQueueList(c.QueueEtcd)

	// 启动协程安全地执行队列发现流程
	threading.GoSafe(func() {
		discovery.QueueDiscoveryProc(c.QueueEtcd, queueList)
	})

	// 初始化业务Redis连接
	rds, err := redis.NewRedis(redis.RedisConf{
		Host: c.BizRedis.Host,
		Pass: c.BizRedis.Pass,
		Type: c.BizRedis.Type,
	})
	if err != nil {
		panic(err)
	}

	// 构造并返回服务上下文
	return &ServiceContext{
		Config:    c,
		QueueList: queueList,
		BizRedis:  rds,
	}
}

type QueueList struct {
	kqs map[string]*kq.Pusher
	l   sync.Mutex
}

func NewQueueList() *QueueList {
	return &QueueList{
		kqs: make(map[string]*kq.Pusher),
	}
}

// Update 更新队列列表中指定key的队列配置
// key: 队列的唯一标识符
// data: 新的队列配置信息，包含Brokers和Topic等参数
func (q *QueueList) Update(key string, data kq.KqConf) {
	// 创建新的推送队列实例
	edgeQueue := kq.NewPusher(data.Brokers, data.Topic)

	// 加锁更新队列映射
	q.l.Lock()
	q.kqs[key] = edgeQueue
	q.l.Unlock()
}

func (q *QueueList) Delete(key string) {
	q.l.Lock()
	delete(q.kqs, key)
	q.l.Unlock()
}

func (q *QueueList) Load(key string) (*kq.Pusher, bool) {
	q.l.Lock()
	defer q.l.Unlock()

	edgeQueue, ok := q.kqs[key]
	return edgeQueue, ok
}

// GetQueueList 根据Etcd配置获取队列列表
// 参数:
//
//	conf: Etcd配置信息，包含连接地址和键前缀
//
// 返回值:
//
//	*QueueList: 包含从Etcd获取的队列配置信息的队列列表
func GetQueueList(conf discov.EtcdConf) *QueueList {
	ql := NewQueueList()

	// 创建Etcd客户端连接
	cli, err := clientv3.New(clientv3.Config{
		Endpoints:   conf.Hosts,
		DialTimeout: time.Second * 3,
	})
	if err != nil {
		panic(err)
	}

	// 从Etcd获取指定前缀的所有键值对
	ctx, cancel := context.WithTimeout(context.Background(), time.Second)
	defer cancel()
	// 模糊反回 edge_1,edge_2,edge_3的值
	res, err := cli.Get(ctx, conf.Key, clientv3.WithPrefix())
	if err != nil {
		panic(err)
	}

	// 遍历Etcd返回的结果，解析队列配置并创建对应的推送器
	for _, kv := range res.Kvs {
		var data kq.KqConf
		if err := json.Unmarshal(kv.Value, &data); err != nil {
			logx.Errorf("invalid data key is: %s value is: %s", string(kv.Key), string(kv.Value))
			continue
		}
		if len(data.Brokers) == 0 || len(data.Topic) == 0 {
			continue
		}
		edgeQueue := kq.NewPusher(data.Brokers, data.Topic)

		ql.l.Lock()
		ql.kqs[string(kv.Key)] = edgeQueue
		ql.l.Unlock()
	}

	return ql
}
