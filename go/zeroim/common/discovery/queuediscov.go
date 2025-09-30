package discovery

import (
	"github.com/zeromicro/go-queue/kq"
	"github.com/zeromicro/go-zero/core/discov"
)

type QueueObserver interface {
	Update(string, kq.KqConf)
	Delete(string)
}

// QueueDiscoveryProc 是队列发现处理函数，用于初始化队列主节点并监控队列工作节点
// conf: Etcd配置信息，包含键值和主机地址列表
// observer: 队列观察者，用于接收队列状态变化通知
func QueueDiscoveryProc(conf discov.EtcdConf, observer QueueObserver) {
	// 创建新的队列主节点实例
	master, err := NewQueueMaster(conf.Key, conf.Hosts)
	if err != nil {
		panic(err)
	}

	// 注册观察者并开始监控队列工作节点
	master.register(observer)
	master.WatchQueueWorkers()
}
