package main

import (
	"fmt"
	"sync"
	"time"
)

var (
	counter int
	mutex   sync.Mutex
	rwMutex sync.RWMutex
	wg      sync.WaitGroup
)

// stringToRunes 将字符串转换为 rune 切片，便于处理多字节字符（如中文）。
func stringToRunes(s string) []rune {
	return []rune(s)
}

// reverseString 反转字符串，支持包含多字节字符的字符串。
func reverseString(s string) string {
	runes := []rune(s)
	for i, j := 0, len(runes)-1; i < j; i, j = i+1, j-1 {
		runes[i], runes[j] = runes[j], runes[i]
	}
	return string(runes)
}

// binarySearch 实现二分查找算法，返回目标值在数组中的索引，若未找到则返回 -1。
// 参数:
//   arr: 已排序的整数切片
//   target: 要查找的目标值
// 二分查找的核心思想是通过不断缩小搜索范围来快速定位目标值。
func binarySearch(arr []int, target int) int {
	left, right := 0, len(arr)-1

	for left <= right {
		// 计算中间索引，避免直接相加可能的溢出问题
		mid := left + (right-left)/2

		if arr[mid] == target {
			return mid // 找到目标值，返回索引
		} else if arr[mid] < target {
			left = mid + 1 // 目标值在右半部分
		} else {
			right = mid - 1 // 目标值在左半部分
		}
	}

	return -1 // 未找到目标值
}

// quickSort 实现快速排序算法，用于对整数切片进行排序。
// 快速排序是一种分治算法，通过选择一个基准值将数组分为两部分，递归地对两部分进行排序。
// 参数:
//   arr: 待排序的整数切片
//   low: 当前排序区间的起始索引
//   high: 当前排序区间的结束索引
func quickSort(arr []int, low, high int) {
	if low < high {
		// 找到分区点，将数组分为两部分
		pivot := partition(arr, low, high)

		// 对左半部分递归排序
		quickSort(arr, low, pivot-1)

		// 对右半部分递归排序
		quickSort(arr, pivot+1, high)
	}
}

// partition 是快速排序的辅助函数，用于找到分区点并调整元素位置。
// 选择最后一个元素作为基准值，将小于基准值的元素放在左侧，大于基准值的元素放在右侧。
func partition(arr []int, low, high int) int {
	pivot := arr[high] // 选择最后一个元素作为基准值
	i := low - 1       // i 指向小于基准值的最后一个元素

	for j := low; j < high; j++ {
		if arr[j] < pivot { // 如果当前元素小于基准值
			i++                     // 移动 i 指针
			arr[i], arr[j] = arr[j], arr[i] // 交换元素
		}
	}

	// 将基准值放到正确的位置
	arr[i+1], arr[high] = arr[high], arr[i+1]
	return i + 1 // 返回分区点索引
}

// mergeSort 实现归并排序算法，用于对整数切片进行排序。
// 归并排序是一种分治算法，通过递归地将数组分成两部分，分别排序后再合并。
// 参数:
//   arr: 待排序的整数切片
// 返回值:
//   排序后的整数切片
func mergeSort(arr []int) []int {
	if len(arr) <= 1 {
		return arr // 基础情况：长度为 1 或 0 的数组已排序
	}

	// 将数组分为两部分
	mid := len(arr) / 2
	left := mergeSort(arr[:mid])  // 对左半部分递归排序
	right := mergeSort(arr[mid:]) // 对右半部分递归排序

	// 合并两个有序数组
	return merge(left, right)
}

// merge 是归并排序的辅助函数，用于合并两个有序数组。
func merge(left, right []int) []int {
	result := []int{}
	i, j := 0, 0

	// 比较两个数组的元素，按顺序合并
	for i < len(left) && j < len(right) {
		if left[i] < right[j] {
			result = append(result, left[i])
			i++
		} else {
			result = append(result, right[j])
			j++
		}
	}

	// 将剩余元素追加到结果数组
	result = append(result, left[i:]...)
	result = append(result, right[j:]...)

	return result
}

// depthFirstSearch 实现深度优先搜索（DFS）算法，用于遍历或搜索图结构。
// 深度优先搜索从起始节点开始，递归访问其所有邻居节点，直到无法继续为止。
// 参数:
//   graph: 图的邻接表表示
//   start: 起始节点
//   visited: 记录节点是否已访问的布尔切片
func depthFirstSearch(graph map[int][]int, start int, visited []bool) {
	// 标记当前节点为已访问
	visited[start] = true
	fmt.Printf("Visited node: %d\n", start)

	// 遍历当前节点的所有邻居
	for _, neighbor := range graph[start] {
		if !visited[neighbor] { // 如果邻居未访问
			depthFirstSearch(graph, neighbor, visited) // 递归访问邻居
		}
	}
}

// breadthFirstSearch 实现广度优先搜索（BFS）算法，用于遍历或搜索图结构。
// 广度优先搜索从起始节点开始，逐层访问其所有邻居节点，直到无法继续为止。
// 参数:
//   graph: 图的邻接表表示
//   start: 起始节点
func breadthFirstSearch(graph map[int][]int, start int) {
	visited := make(map[int]bool) // 记录节点是否已访问
	queue := []int{start}         // 使用队列实现 BFS

	for len(queue) > 0 {
		node := queue[0]      // 取出队首节点
		queue = queue[1:]     // 移除队首节点
		if visited[node] {
			continue // 如果节点已访问，跳过
		}

		visited[node] = true
		fmt.Printf("Visited node: %d\n", node)

		// 将当前节点的所有未访问邻居加入队列
		for _, neighbor := range graph[node] {
			if !visited[neighbor] {
				queue = append(queue, neighbor)
			}
		}
	}
}

func main() {
	// 使用 WaitGroup 来等待所有 goroutine 完成
	for i := 0; i < 10; i++ {
		wg.Add(1)
		go incrementCounter()
	}

	wg.Wait()
	fmt.Printf("Final counter value: %d\n", counter)

	// 使用 RWMutex 来演示读写锁
	for i := 0; i < 10; i++ {
		wg.Add(1)
		go readCounter()
	}

	for i := 0; i < 5; i++ {
		wg.Add(1)
		go writeCounter(i)
	}

	wg.Wait()

	// 使用 stringToRunes 函数示例
	str := "Hello, 世界"
	runes := stringToRunes(str)
	fmt.Printf("Runes: %v\n", runes)

	// 使用 reverseString 函数示例
	str = "Hello, 世界"
	reversedStr := reverseString(str)
	fmt.Printf("Reversed String: %s\n", reversedStr)
}

// incrementCounter 增加全局计数器的值，并使用互斥锁确保线程安全。
func incrementCounter() {
	defer wg.Done() // 确保 WaitGroup 计数器在函数结束时减少
	mutex.Lock()     // 获取互斥锁以保护共享资源
	counter++
	mutex.Unlock() // 释放互斥锁
}

// readCounter 读取全局计数器的值，并使用读写锁确保线程安全。
func readCounter() {
	defer wg.Done()    // 确保 WaitGroup 计数器在函数结束时减少
	rwMutex.RLock()    // 获取读锁以保护共享资源
	fmt.Printf("Read counter: %d\n", counter)
	rwMutex.RUnlock()  // 释放读锁
}

// writeCounter 写入全局计数器的值，并使用读写锁确保线程安全。
func writeCounter(value int) {
	defer wg.Done() // 确保 WaitGroup 计数器在函数结束时减少
	rwMutex.Lock()  // 获取写锁以保护共享资源
	counter = value
	fmt.Printf("Write counter: %d\n", counter)
	rwMutex.Unlock() // 释放写锁
	time.Sleep(time.Millisecond * 100) // 模拟写操作耗时
}