const k8s = require('@kubernetes/client-node');
// ### kubectl config view
// 定义集群配置
const cluster = {
    name: 'cluster.local',
    server: 'http://192.168.110.108:30294', // 修改为你的 Kubernetes API 服务器地址和端口
  };
  
  const user = {
    username: 'admin',
    password: 'xxxxx',
    // 如果需要，添加认证信息，例如客户端证书或令牌
  };
  const context = {
    name: 'cluster.local',
    user: user.name,
    cluster: cluster.name,
  };

// 设置Kubernetes配置，加载kubeconfig文件
const kc = new k8s.KubeConfig();
// 加载配置
kc.loadFromOptions({
  clusters: [cluster],
  users: [user],
  contexts: [context],
  currentContext: context.name,
});

// 创建API实例
const k8sApi = kc.makeApiClient(k8s.AppsV1Api);
//用yaml文件 创建 deployment
//*
k8sApi.createNamespacedDeployment("iotree3d", {
    apiVersion: "apps/v1",
    kind: "Service",
    metadata: {
      name: "io-render-service",
    },
    spec: {
      selector: {
        app: "io-render",
      },
      ports:
      [
        - {
          protocol: "TCP",
        }
      ]
    }
  })
  .then((response) => {
    console.log("Deployment created successfully:", response.body);
      
    })
  .catch((error) => {
    console.error("Error creating deployment:", error);
  })
//*/    
// 删除deployment
/*
const deleteOptions = new k8s.V1DeleteOptions();
deleteOptions.gracePeriodSeconds = 0;
k8sApi.deleteNamespacedDeployment("iotree3d-deployment-render", "iotree3d", deleteOptions)
  .then((response) => {
    console.log("Deployment deleted successfully:", response.body);
  })
  .catch((error) => {  
      console.error("Error deleting deployment:", error);
  });
//*/
//




  