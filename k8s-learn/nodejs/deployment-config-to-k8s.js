const { KubeConfig, AppsV1Api, CoreV1Api } = require('@kubernetes/client-node');
const fs = require('fs');

// 读取配置文件
const config = JSON.parse(fs.readFileSync('image-deployment-config-template.json', 'utf8'));

// Kubernetes 配置初始化
const kubeConfig = new KubeConfig();
kubeConfig.loadFromDefault();  // 加载默认的 kubeconfig 配置

const appsApi = kubeConfig.makeApiClient(AppsV1Api);
const coreApi = kubeConfig.makeApiClient(CoreV1Api);



// 获取已使用的端口
async function getUsedPorts() {
    const { body: pods } = await k8sApi.listNamespacedPod('default');
    const usedPorts = new Set();
  
    pods.items.forEach(pod => {
      pod.spec.containers.forEach(container => {
        container.ports?.forEach(port => {
          usedPorts.add(port.containerPort);
        });
      });
    });
  
    return usedPorts;
  }
  
// 替换占位符为端口
async function replacePlaceholders(config, usedPorts) {
    const portMap = {};
  
    // 遍历镜像配置，替换端口占位符
    for (let image of config.images) {
      const portMatches = image.ports.match(/\$\{([a-zA-Z0-9_]+)\}/g) || [];
  
      portMatches.forEach(match => {
        const placeholder = match.slice(2, -1);  // 去掉 ${ 和 }，提取占位符名称
  
        if (!portMap[placeholder]) {
          // 如果该占位符没有被处理过，生成一个随机端口
          let port;
          do {
            port = getRandomPort();
          } while (usedPorts.has(port)); // 确保端口未被使用
  
          portMap[placeholder] = port;
          usedPorts.add(port);
        }
  
        // 将占位符替换为生成的端口
        image.ports = image.ports.replace(match, portMap[placeholder]);
        image.env = image.env.replace(match, portMap[placeholder]);
      });
    }
  
    return { config, portMap };
  }
  
// 生成 Kubernetes Deployment 配置
function createDeploymentSpec(imageConfig) {
  const ports = imageConfig.ports.split(',').map(port => ({
    containerPort: parseInt(port, 10),
  }));

  const envVariables = imageConfig.env.split(' ').map(item => {
    const [name, value] = item.split('=');
    return { name, value };
  });

  return {
    apiVersion: 'apps/v1',
    kind: 'Deployment',
    metadata: {
      name: imageConfig.name,
    },
    spec: {
      replicas: 1,
      selector: {
        matchLabels: {
          app: imageConfig.name,
        },
      },
      template: {
        metadata: {
          labels: {
            app: imageConfig.name,
          },
        },
        spec: {
          containers: [
            {
              name: imageConfig.name,
              image: `${imageConfig.name}:latest`,
              ports: ports,
              env: envVariables,
              ...(imageConfig.network === 'host' && { hostNetwork: true }), // 设置host网络模式
            },
          ],
        },
      },
    },
  };
}

// 创建 Kubernetes Deployment
async function createDeployment(deploymentSpec) {
  try {
    const res = await appsApi.createNamespacedDeployment('default', deploymentSpec);
    console.log(`Deployment created: ${res.body.metadata.name}`);
  } catch (error) {
    console.error('Error creating deployment:', error.response.body);
  }
}

// 处理配置并部署镜像
async function deployImages() {
    const usedPorts = await getUsedPorts();  // 获取已使用的端口
    const { config, portMap } = await replacePlaceholders(config, usedPorts); // 替换占位符
  
    for (const imageConfig of config.images) {
    const deploymentSpec = createDeploymentSpec(imageConfig);
    console.log(`Deployment spec for image: ${JSON.stringify(deploymentSpec, null, 2)}`);
    // console.log(`Creating deployment for image: ${deploymentSpec}`);
    //await createDeployment(deploymentSpec);
  }
}

// 执行部署
deployImages();
