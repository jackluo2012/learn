const k8s = require('@kubernetes/client-node');

async function createService(name, ports) {
  const kc = new k8s.KubeConfig();
  kc.loadFromDefault(); // 加载本地 kubeconfig 文件

  const k8sApi = kc.makeApiClient(k8s.CoreV1Api);

  // 创建 Service 的定义
  const serviceManifest = {
    apiVersion: 'v1',
    kind: 'Service',
    metadata: {
      name: name, // 对象名
    },
    spec: {
      selector: {
        app: name, // 你可以根据需要调整 selector
      },
      ports: ports.map((port, index) => ({
        name: `port-${port}`, // 生成端口的名称
        port: port, // 端口
        targetPort: port, // targetPort 也是该端口
        protocol: 'TCP', // 协议
      })),
      type: 'ClusterIP', // Service 类型，你可以根据需求调整
    },
  };

  try {
    // 调用 Kubernetes API 创建 Service
    const response = await k8sApi.createNamespacedService('default', serviceManifest); // 默认命名空间是 'default'
    console.log('Service created:', response.body);
  } catch (error) {
    console.error('Error creating service:', error);
  }
}

// 示例使用
createService('my-service', [80, 443, 8080]);
