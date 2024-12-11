const { KubeConfig, CoreV1Api, AppsV1Api, V1Service, V1ServiceSpec, V1ServicePort } = require('@kubernetes/client-node');
const fs = require('fs');
const k8s = require('@kubernetes/client-node');

// 生成一个随机端口
function getRandomPort() {
  return Math.floor(Math.random() * (32767 - 30000)) + 30000;  // 随机生成30000到32767之间的端口
}

// 获取当前时间戳格式化
function getTimestamp() {
  const now = new Date();
  return now.toISOString().replace(/[-:T.]/g, '-').slice(0, 19);  // 格式: 2023-10-01-10-10-10
}

// 读取配置文件
const configJson = fs.readFileSync('image-deployment-config-template.json', 'utf8');
const config = JSON.parse(configJson);

// 初始化 Kubernetes 客户端
// const kc = new KubeConfig();
// kc.loadFromDefault();
// const k8sApi = kc.makeApiClient(CoreV1Api);
// const appsApi = kc.makeApiClient(AppsV1Api);


const cluster = {
  name: 'cluster.local',
  server: 'http://192.168.110.108:31840', // 修改为你的 Kubernetes API 服务器地址和端口
};

const user = {
  username: 'admin',
  password: 'Iotree.com123',
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
const k8sApi = kc.makeApiClient(k8s.CoreV1Api);
const appsApi = kc.makeApiClient(k8s.AppsV1Api);



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

  for (let image of config.images) {
    const portMatches = image.ports.match(/\$\{([a-zA-Z0-9_]+)\}/g) || [];
    
    portMatches.forEach(match => {
      const placeholder = match.slice(2, -1);
      if (!portMap[placeholder]) {
        let port;
        do {
          port = getRandomPort();
        } while (usedPorts.has(port)); // 确保端口未被使用

        portMap[placeholder] = port;
        usedPorts.add(port);
      }
      image.ports = image.ports.replace(match, portMap[placeholder]);
    });

    if (image.env) {
      image.env = image.env.split(' ').map(item => {
        const [name, value] = item.split('=');
        const newValue = value ? value.replace(/\$\{([a-zA-Z0-9_]+)\}/g, (match, p1) => {
          return portMap[p1] || match;
        }) : '';
        return `${name}=${newValue}`;
      }).join(' ');
    }

    if (image.env.includes("${PIXEL_STREAMING_IP}")) {
      image.env = image.env.replace("${PIXEL_STREAMING_IP}", "192.168.110.108");
    }
  }

  return { config, portMap };
}

// 删除 Kubernetes Service，并确保其彻底删除
async function deleteService(serviceName) {
  const res = await k8sApi.listNamespacedService('default');

  console.log('listNamespacedService response:', res.body);

  if (!res.body || !Array.isArray(res.body.items)) {
    console.error('Invalid response format or missing "items" property for Services');
    return;
  }

  const serviceExists = res.body.items.some(service => service.metadata.name === serviceName);

  if (serviceExists) {
    await k8sApi.deleteNamespacedService(serviceName, 'default');
    console.log(`Service deletion started: ${serviceName}`);

    let serviceDeleted = false;
    let retries = 0;
    const maxRetries = 20;

    while (!serviceDeleted && retries < maxRetries) {
      const { body: services } = await k8sApi.listNamespacedService('default');
      // console.log('Checking Service status:', services);

      if (!services.items.some(service => service.metadata.name === serviceName)) {
        serviceDeleted = true;
        console.log(`Service deleted: ${serviceName}`);
        break;
      }

      retries++;
      // console.log(`Waiting for Service to be deleted: ${serviceName}`);
      await new Promise(resolve => setTimeout(resolve, 5000)); // 每5秒检查一次
    }

    if (!serviceDeleted) {
      console.error(`Service deletion timed out after ${retries * 5} seconds.`);
    }
  } else {
    console.log(`Service not found: ${serviceName}`);
  }
}

async function deleteDeployment(deploymentName) {
  const res = await appsApi.listNamespacedDeployment('default');

  console.log('listNamespacedDeployment response:', res.body);

  if (!res.body || !Array.isArray(res.body.items)) {
    console.error('Invalid response format or missing "items" property');
    return;
  }

  const deploymentExists = res.body.items.some(deployment => deployment.metadata.name === deploymentName);

  if (deploymentExists) {
    await appsApi.deleteNamespacedDeployment(deploymentName, 'default');
    console.log(`Deployment deletion started: ${deploymentName}`);

    let deploymentDeleted = false;
    let retries = 0;
    const maxRetries = 20;

    while (!deploymentDeleted && retries < maxRetries) {
      const { body: pods } = await k8sApi.listNamespacedPod(
        'default',
        undefined,
        undefined,
        undefined,
        undefined,
        `app=${deploymentName}`
      );

      // console.log(`Pods associated with ${deploymentName}:`, pods.items.map(pod => pod.metadata.name));

      if (!pods.items.length) {
        deploymentDeleted = true;
        console.log(`All Pods deleted for Deployment: ${deploymentName}`);
        break;
      }

      const podStatus = pods.items.map(pod => ({
        name: pod.metadata.name,
        phase: pod.status.phase,
      }));
      // console.log('Current Pod Status:', podStatus);

      const anyPodActive = pods.items.some(
        pod => pod.status.phase !== 'Terminating'
      );

      if (!anyPodActive) {
        retries++;
        console.log(`Waiting for all Pods to be fully terminated: ${deploymentName}`);
        await new Promise(resolve => setTimeout(resolve, 5000));
      }
    }

    if (!deploymentDeleted) {
      console.error(`Deployment deletion timed out after ${retries * 5} seconds.`);
    }
  } else {
    console.log(`Deployment not found: ${deploymentName}`);
  }
}

// 创建 Kubernetes Service
async function createService(imageConfig, ports) {
  if (ports.length === 0) return null;
  const timestamp = getTimestamp();
  const serviceName = imageConfig.name//`${imageConfig.name}-${timestamp}`;

  const serviceManifest = {
    apiVersion: 'v1',
    kind: 'Service',
    metadata: { name: serviceName },
    spec: {
      selector: { app: imageConfig.name },
      ports: ports.map(port => ({
        name: `port-${port}`,
        port: port,
        targetPort: port,
        protocol: 'TCP',
        nodePort: port,
      })),
      type: 'NodePort',
    },
  };

  const result = await k8sApi.createNamespacedService('default', serviceManifest);
  const service = result.body;
  console.log(`NodePort Service created for ${serviceName} with ports: ${ports.join(', ')}`);
  return { name: service.metadata.name, ports: ports };
}

// 创建 Kubernetes Deployment
async function createDeployment(imageConfig, ports, envVariables) {
  const timestamp = getTimestamp();
  const deploymentName = imageConfig.name//`${imageConfig.name}-${timestamp}`;

  const deploymentSpec = {
    apiVersion: 'apps/v1',
    kind: 'Deployment',
    metadata: { name: deploymentName },
    spec: {
      replicas: 1,
      selector: { matchLabels: { app: imageConfig.name } },
      template: {
        metadata: { labels: { app: imageConfig.name } },
        spec: {
          ...(imageConfig.network === 'host' && { hostNetwork: true }),
          containers: [{
            name: imageConfig.name,
            image: `192.168.110.108:30000/${imageConfig.name}:latest`,
            env: envVariables,
            
          }],
        },
      },
    },
  };

  if (ports.length > 0) {
    deploymentSpec.spec.template.spec.containers[0].ports = ports.map(port => ({ containerPort: port }));
  }

  console.log(`Deployment spec for image: ${JSON.stringify(deploymentSpec, null, 2)}`);
  await appsApi.createNamespacedDeployment('default', deploymentSpec);
  console.log(`Deployment created for ${deploymentName}`);

  return { name: deploymentName, ports: ports };
}

// 自动部署函数
async function deploy() {
  const usedPorts = await getUsedPorts();
  const { config: updatedConfig, portMap } = await replacePlaceholders(config, usedPorts);
  const results = [];

  for (const imageConfig of updatedConfig.images) {
    const ports = imageConfig.ports.split(',').map(p => p.trim()).filter(p => p !== '' && p !== '0').map(Number);
    const envVariables = imageConfig.env ? imageConfig.env.split(' ').map(item => {
      const [name, value] = item.split('=');
      return { name, value };
    }) : [];

    let serviceResult = null;
    if (ports.length > 0) {
      await deleteService(imageConfig.name);  // 删除旧的服务并等待删除完成
      
      serviceResult = await createService(imageConfig, ports);
    }

    // 删除旧的部署并等待删除完成
    await deleteDeployment(imageConfig.name);

    // 创建新的部署
    const deploymentResult = await createDeployment(imageConfig, ports, envVariables);
    results.push({ ...deploymentResult, service: serviceResult });
  }

  return results;
}

// 执行部署
deploy().catch(error => console.error('Error during deployment:', error));
