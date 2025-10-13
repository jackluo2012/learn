package main

import (
	"context"
	"fmt"
	"log"
	"time"

	"go.etcd.io/etcd/client/v3"
)

// etcd keepAlive

// main函数是程序的入口点，演示了etcd客户端的基本使用方法
// 包括连接etcd、创建租约、设置键值对、保持租约活跃等功能
func main() {
	// 创建etcd客户端连接，配置连接地址和超时时间
	cli, err := clientv3.New(clientv3.Config{
		Endpoints:   []string{"127.0.0.1:2379"},
		DialTimeout: time.Second * 5,
	})
	if err != nil {
		log.Fatal(err)
	}
	fmt.Println("connect to etcd success.")
	defer cli.Close()

	// 创建一个5秒的租约
	resp, err := cli.Grant(context.TODO(), 5)
	if err != nil {
		log.Fatal(err)
	}

	// 使用租约ID设置键值对，键为"/lmh/"，值为"lmh"
	_, err = cli.Put(context.TODO(), "/lmh/", "lmh", clientv3.WithLease(resp.ID))
	if err != nil {
		log.Fatal(err)
	}

	// 启动租约续期，保持键值对持久存在
	// 如果不进行续期，5秒后键值对将被自动删除
	ch, kaerr := cli.KeepAlive(context.TODO(), resp.ID)
	if kaerr != nil {
		log.Fatal(kaerr)
	}

	// 持续监听并打印租约的剩余生存时间
	for {
		ka := <-ch
		fmt.Println("ttl:", ka.TTL)
	}
}
