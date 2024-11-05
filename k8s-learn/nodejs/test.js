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
    kind: "Deployment",
    metadata: {
      name: "io-render-deployment",
    },
    spec: {
      replicas: 1,
      selector: {
        matchLabels: {
          app: "io-render",
        },
      },
      template: {
        metadata: {
          labels: {
            app: "io-render",
          },
        },
        spec: {
          hostNetwork: true,
          dnsPolicy: "ClusterFirstWithHostNet",
          containers: [
            {
              name: "io-render",
              image: "io-render",
              imagePullPolicy: "IfNotPresent",
              env: [
                {
                  name: "EXECUTE",
                  value: "IOUnrealShell/Binaries/Linux/IOUnrealShell",
                },
                {
                  name: 'ARGUMENTS',
                  value:
                    '-RenderUrl="ws://io-manager-service:8300/render?uuid=192.168.110.108_1&engineId=74e0196b7b79ae847fe0d2ae4ce56f26_ec896625f2ca2e870f924ac91cecf86c&container=true" -StreamUrl="ws://io-server-service:8100/stream?uuid=192.168.110.108_1&engineId=74e0196b7b79ae847fe0d2ae4ce56f26_ec896625f2ca2e870f924ac91cecf86c" -RootPath="/app/assets" -PixelStreamingID="192.168.110.108_1" -PixelStreamingWebRTCMinBitrate=15000000 -PixelStreamingWebRTCStartBitrate=15000000 -PixelStreamingWebRTCMaxBitrate=30000000 -PixelStreamingEncoderRateControl=VBR -log -LogCmds="Log LogRenderNodeConnection Verbose" -RenderOffscreen -nosound',
                },
              ],
              volumeMounts:[
                {
                  name: 'io-render-engines-pvc',
                  mountPath: '/app/engine',
                },
                {
                  name: 'io-render-pvc',
                  mountPath: '/app/assets',
                  subPath: 'assets',
                },
                {
                  name: 'io-render-hostpath-pvc',
                  mountPath: '/tmp/.X11-unix',
                  subPath: '.X11-unix',
                },
              ],
            },
          ],
          volumes: [
            {
            name: 'io-render-pvc',
            nfs: {
              server: '192.168.110.108',
              path: '/home/data/io3d/workspace/',
            },
          },
          {
            name: 'io-render-engines-pvc',
            nfs: {
              server: '192.168.110.108',
              path:
                '/home/data/io3d/workspace/engines/74e0196b7b79ae847fe0d2ae4ce56f26_ec896625f2ca2e870f924ac91cecf86c/',
            },
          },
          {
            name: 'io-render-hostpath-pvc',
            hostPath: {
              path: '/tmp',
            },
          },]
        },
      },
    },
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
k8sApi.deleteNamespacedDeployment("io-render-deployment", "iotree3d", deleteOptions)
  .then((response) => {
    console.log("Deployment deleted successfully:", response.body);
  })
  .catch((error) => {  
      console.error("Error deleting deployment:", error);
  });
//*/
//




  