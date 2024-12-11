const { KubeConfig, CoreV1Api, AppsV1Api, V1Pod, V1PodSpec, V1Container, V1ContainerPort, V1Service, V1ServiceSpec, V1ServicePort } = require('@kubernetes/client-node');
const fs = require('fs');

// 生成一个随机端口
function getRandomPort() {
  return Math.floor(Math.random() * (32767 - 30000)) + 30000;  // 随机生成30000到32767之间的端口
}

// 读取配置文件
const configJson = fs.readFileSync('image-deployment-config-template.json', 'utf8');
const config = JSON.parse(configJson);

// 初始化 Kubernetes 客户端
const kc = new KubeConfig();
kc.loadFromDefault();
const k8sApi = kc.makeApiClient(CoreV1Api);
const appsApi = kc.makeApiClient(AppsV1Api);

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

    // 替换端口占位符
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
    });

    // 替换 env 中的占位符
    image.env = image.env.split(' ').map(item => {
      const [name, value] = item.split('=');
      const newValue = value ? value.replace(/\$\{([a-zA-Z0-9_]+)\}/g, (match, p1) => {
        // 如果在 env 中找到占位符，替换为对应的端口
        return portMap[p1] || match;
      }) : '';
      return `${name}=${newValue}`;
    }).join(' ');  // 重新组合成一个字符串

  }

  return { config, portMap };
}


// 创建 Kubernetes Service
async function createService(imageConfig, ports) {
  const service = new V1Service();
  service.metadata = { name: imageConfig.name };
  service.spec = new V1ServiceSpec();

  // 为每个端口创建 V1ServicePort
  service.spec.ports = ports.map(port => new V1ServicePort({
    port,           // 服务端口
    targetPort: port, // 容器端口
    protocol: 'TCP',  // 协议
  }));

  service.spec.selector = { app: imageConfig.name };

  // 创建服务
  await k8sApi.createNamespacedService('default', service);
  console.log(`Service created for ${imageConfig.name} with ports: ${ports.join(', ')}`);
}

// 创建 Kubernetes Deployment
async function createDeployment(imageConfig, ports, envVariables) {
  console.log(ports)
  return
  const deploymentSpec = {
    apiVersion: 'apps/v1',
    kind: 'Deployment',
    metadata: { name: imageConfig.name },
    spec: {
      replicas: 1,
      selector: {
        matchLabels: { app: imageConfig.name },
      },
      template: {
        metadata: {
          labels: { app: imageConfig.name },
        },
        spec: {
          containers: [
            {
              name: imageConfig.name,
              image: `${imageConfig.name}:latest`,  // 假设镜像已经准备好
              env: envVariables,
              ...(imageConfig.network === 'host' && { hostNetwork: true }), // 设置host网络模式
            },
          ],
        },
      },
    },
  };

  // 仅当 ports 不为空时，才为容器分配端口
  if (ports.length > 0) {
    const containerPorts = ports.map(port => ({ containerPort: port }));
    deploymentSpec.spec.template.spec.containers[0].ports = containerPorts;  // 为容器配置端口
  }

  // 创建 Deployment
  console.log(`Deployment spec for image: ${JSON.stringify(deploymentSpec, null, 2)}`);
  // await appsApi.createNamespacedDeployment('default', deploymentSpec);
  console.log(`Deployment created for ${imageConfig.name}`);
}

// 等待依赖镜像就绪
async function waitForDependency(dependencyName) {
  let podReady = false;
  while (!podReady) {
    const { body: pods } = await k8sApi.listNamespacedPod('default', undefined, undefined, undefined, undefined, `app=${dependencyName}`);
    podReady = pods.items.some(pod => pod.status.phase === 'Running');
    if (!podReady) {
      console.log(`Waiting for ${dependencyName} to be ready...`);
      await new Promise(resolve => setTimeout(resolve, 5000));  // 每5秒检查一次
    }
  }
}

// 自动部署函数
async function deploy() {
  const usedPorts = await getUsedPorts();  // 获取已使用的端口
  const { config: updatedConfig, portMap } = await replacePlaceholders(config, usedPorts); // 替换占位符并获取端口映射
  // 部署每个镜像
  for (const imageConfig of updatedConfig.images) { 
    const ports = imageConfig.ports.split(',').map(Number);
    const envVariables = imageConfig.env.split(' ').map(item => {
      const [name, value] = item.split('=');
      return { name, value };
    });
    // console.log('ports', ports)
    // // 处理镜像的依赖关系
    // if (imageConfig.depends_on) {
    //   for (const dependency of imageConfig.depends_on) {
    //     await waitForDependency(dependency);  // 等待依赖镜像就绪
    //   }
    // }
    // console.log(ports)
    // 创建服务和部署
    //  await createService(imageConfig, ports); 
    await createDeployment(imageConfig, ports.map(port => ({ containerPort: port })), envVariables);
  }
}

// 执行部署
deploy().catch(error => console.error('Error during deployment:', error));
