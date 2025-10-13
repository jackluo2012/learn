package main

import (
	"fmt"
	"time"
)

// etcd lease

import (
	"context"
	"log"

	"go.etcd.io/etcd/client/v3"
)

// main函数是程序的入口点，用于演示etcd客户端的基本操作
// 该函数创建etcd连接，设置租约并存储带租约的键值对
func main() {
	// 创建etcd客户端连接
	// Endpoints: etcd服务器地址列表
	// DialTimeout: 连接超时时间设置为5秒
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

	// 5秒钟之后, /lmh/ 这个key就会被移除
	_, err = cli.Put(context.TODO(), "/lmh/", "lmh", clientv3.WithLease(resp.ID))
	if err != nil {
		log.Fatal(err)
	}
}
