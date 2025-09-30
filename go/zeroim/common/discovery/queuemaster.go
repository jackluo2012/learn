package discovery

import (
	"context"
	"encoding/json"
	"time"

	"github.com/zeromicro/go-queue/kq"
	"github.com/zeromicro/go-zero/core/logx"
	clientv3 "go.etcd.io/etcd/client/v3"
)

// QueueMaster 队列管理器结构体，用于管理多个队列的配置和状态
// members: 存储队列成员配置的映射表，key为队列名称，value为队列配置
// cli: etcd客户端实例，用于与etcd进行交互
// rootPath: 在etcd中的根路径前缀
// observer: 队列观察者，用于监听队列状态变化
type QueueMaster struct {
	members  map[string]kq.KqConf
	cli      *clientv3.Client
	rootPath string
	observer QueueObserver
}

func NewQueueMaster(rootPath string, address []string) (*QueueMaster, error) {
	cfg := clientv3.Config{
		Endpoints:   address,
		DialTimeout: time.Second * 3,
	}

	cli, err := clientv3.New(cfg)
	if err != nil {
		return nil, err
	}

	return &QueueMaster{
		members:  make(map[string]kq.KqConf),
		cli:      cli,
		rootPath: rootPath,
	}, nil
}

func (m *QueueMaster) register(o QueueObserver) {
	m.observer = o
}
func (m *QueueMaster) notifyUpdate(key string, conf kq.KqConf) {
	m.observer.Update(key, conf)
}

// 删除
func (m *QueueMaster) notifyDelete(key string) {
	m.observer.Delete(key)
}
func (m *QueueMaster) addQueueWorker(key string, conf kq.KqConf) {
	if len(conf.Brokers) == 0 || len(conf.Topic) == 0 {
		logx.Errorf("invalid kq conf: %v", conf)
		return
	}
	m.members[key] = conf
	m.notifyUpdate(key, conf)
}

func (m *QueueMaster) updateQueueWorker(key string, conf kq.KqConf) {
	if len(conf.Brokers) == 0 || len(conf.Topic) == 0 {
		logx.Errorf("invalid kq conf: %v", conf)
		return
	}
	m.members[key] = conf
	m.notifyUpdate(key, conf)
}
func (m *QueueMaster) deleteQueueWorker(key string) {
	delete(m.members, key)
	m.notifyDelete(key)
}

// WatchQueueWorkers 监听队列工作节点的变化
// 该函数会持续监听指定路径下的etcd键值变化，当检测到工作节点的配置发生变化时，
// 会根据事件类型执行相应的处理操作（添加、更新或删除队列工作节点）
// 参数：无
// 返回值：无
func (m *QueueMaster) WatchQueueWorkers() {
	// 创建监听通道，监听rootPath路径下所有前缀匹配的键值变化
	watchChan := m.cli.Watch(context.Background(), m.rootPath, clientv3.WithPrefix())

	// 持续处理监听到的事件
	for watchResp := range watchChan {
		// 处理监听错误情况
		if watchResp.Err() != nil {
			logx.Errorf("watch queue workers error: %v", watchResp.Err())
			return
		}

		// 处理监听被取消的情况
		if watchResp.Canceled {
			logx.Error("watch queue workers canceled")
			return
		}

		// 遍历处理所有监听到的事件
		for _, event := range watchResp.Events {
			key := string(event.Kv.Key)

			// 根据事件类型进行不同的处理
			switch event.Type {
			case clientv3.EventTypePut:
				// 解析配置数据
				var conf kq.KqConf
				if err := json.Unmarshal(event.Kv.Value, &conf); err != nil {
					logx.Errorf("unmarshal kq conf error: %v", err)
					continue
				}

				// 根据是新建还是更新事件调用相应的处理方法
				if event.IsCreate() {
					m.addQueueWorker(key, conf)
				} else {
					m.updateQueueWorker(key, conf)
				}
			case clientv3.EventTypeDelete:
				// 处理删除事件
				m.deleteQueueWorker(key)
			}
		}
	}
}
