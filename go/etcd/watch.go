package main

import (
	"context"
	"fmt"
	"time"

	"go.etcd.io/etcd/client/v3"
)

// watch demo

// main函数是程序的入口点，用于连接到etcd服务器并监听指定键的变化
// 该函数没有参数和返回值
func main() {
	// 创建etcd客户端连接，配置连接地址和超时时间
	cli, err := clientv3.New(clientv3.Config{
		Endpoints:   []string{"127.0.0.1:2379"},
		DialTimeout: 5 * time.Second,
	})
	if err != nil {
		fmt.Printf("connect to etcd failed, err:%v\n", err)
		return
	}
	fmt.Println("connect to etcd success")
	defer cli.Close()

	// 监听键"lmh"的变化，当该键发生变更时会通过通道返回事件
	rch := cli.Watch(context.Background(), "lmh") // <-chan WatchResponse
	for wresp := range rch {
		for _, ev := range wresp.Events {
			fmt.Printf("Type: %s Key:%s Value:%s\n", ev.Type, ev.Kv.Key, ev.Kv.Value)
		}
	}
}
