const { KubeConfig, CoreV1Api, AppsV1Api } = require('@kubernetes/client-node');
const fs = require('fs');
const k8s = require('@kubernetes/client-node');

// 生成随机端口
function getRandomPort() {
  return Math.floor(Math.random() * (32767 - 30000)) + 30000;
}

// 获取当前时间戳格式化
function getTimestamp() {
  const now = new Date();
  return now.toISOString().replace(/[-:T.]/g, '-').slice(0, 19);
}

// 读取配置文件
const configJson = fs.readFileSync('image-deployment-config-template.json', 'utf8');
const config = JSON.parse(configJson);

// Kubernetes 客户端初始化
const cluster = { name: 'cluster.local', server: 'http://192.168.110.108:31840' };
const user = { username: 'admin', password: 'Iotree.com123' };
const context = { name: 'cluster.local', user: user.name, cluster: cluster.name };

const kc = new k8s.KubeConfig();
kc.loadFromOptions({
  clusters: [cluster],
  users: [user],
  contexts: [context],
  currentContext: context.name,
});

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

async function replacePlaceholders(config, usedPorts) {
  const portMap = {};
  
  for (let image of config.images) {
    // 处理 ports 占位符替换
    const portMatches = image.ports.match(/\$\{([a-zA-Z0-9_]+)\}/g) || [];
    portMatches.forEach(match => {
      const placeholder = match.slice(2, -1);
      if (!portMap[placeholder]) {
        let port;
        do {
          port = getRandomPort();
        } while (usedPorts.has(port));
        portMap[placeholder] = port;
        usedPorts.add(port);
      }
      image.ports = image.ports.replace(match, portMap[placeholder]);
    });

    if (image.env) {
      // 处理 env 中的占位符替换和前缀替换
      image.env = image.env.split(' ').map(item => {
        let [name, value] = item.split('=');

        // 去掉所有前缀为 "-" 的变量名中的 "-"
        if (name.startsWith('-')) {
          name = name.slice(1);
        }

        return `${name}=${value ? value.replace(/\$\{([a-zA-Z0-9_]+)\}/g, (_, p1) => portMap[p1] || _) : ''}`;
      }).join(' ');
    }

    // 替换 PIXEL_STREAMING_IP
    if (image.env.includes("${PIXEL_STREAMING_IP}")) {
      image.env = image.env.replace("${PIXEL_STREAMING_IP}", "192.168.110.108");
    }
  }

  return { config, portMap };
}


// 异步删除Service
async function deleteService(serviceName) {
  try {
    await k8sApi.deleteNamespacedService(serviceName, 'default');
    console.log(`Service deletion initiated: ${serviceName}`);
  } catch (err) {
    if (err.body?.reason !== 'NotFound') {
      console.log(`Error deleting service ${serviceName}:`, err.body.message);
    }
  }
}

// 异步删除Deployment
async function deleteDeployment(deploymentName) {
  try {
    await appsApi.deleteNamespacedDeployment(deploymentName, 'default');
    console.log(`Deployment deletion initiated: ${deploymentName}`);
  } catch (err) {
    if (err.body?.reason !== 'NotFound') {
      console.log(`Error deleting deployment ${deploymentName}:`, err.body.message);
    }
  }
}

// 等待所有Pods删除
async function waitForPodsDeletion(deploymentNames) {
  let retries = 0;
  const maxRetries = 20;

  while (retries < maxRetries) {
    let allDeleted = true;

    for (const deploymentName of deploymentNames) {
      const { body: pods } = await k8sApi.listNamespacedPod(
        'default',
        undefined,
        undefined,
        undefined,
        undefined,
        `app=${deploymentName}`
      );

      if (pods.items.length > 0) {
        allDeleted = false;
        break;
      }
    }

    if (allDeleted) {
      console.log(`All Pods deleted for deployments: ${deploymentNames.join(', ')}`);
      return;
    }

    retries++;
    console.log(`Waiting for Pods to terminate... (${retries * 5}s elapsed)`);
    await new Promise(resolve => setTimeout(resolve, 5000));
  }

  console.error(`Timed out waiting for Pods deletion of deployments: ${deploymentNames.join(', ')}`);
}

// 等待所有Pods变为Running状态
async function waitForPodsRunning(deploymentNames) {
  let retries = 0;
  const maxRetries = 20;

  while (retries < maxRetries) {
    let allRunning = true;

    for (const deploymentName of deploymentNames) {
      const { body: pods } = await k8sApi.listNamespacedPod(
        'default',
        undefined,
        undefined,
        undefined,
        undefined,
        `app=${deploymentName}`
      );

      if (!pods.items.every(pod => pod.status.phase === 'Running')) {
        allRunning = false;
        break;
      }
    }

    if (allRunning) {
      console.log(`All Pods are running for deployments: ${deploymentNames.join(', ')}`);
      return;
    }

    retries++;
    console.log(`Waiting for Pods to enter Running state... (${retries * 5}s elapsed)`);
    await new Promise(resolve => setTimeout(resolve, 5000));
  }

  console.error(`Timed out waiting for Pods to reach Running state: ${deploymentNames.join(', ')}`);
}

// 创建Service
async function createService(imageConfig, ports) {
  if (ports.length === 0) return null;
  const serviceManifest = {
    apiVersion: 'v1',
    kind: 'Service',
    metadata: { name: imageConfig.name },
    spec: {
      selector: { app: imageConfig.name },
      ports: ports.map(port => ({
        name: `port-${port}`,
        port,
        targetPort: port,
        protocol: 'TCP',
        nodePort: port,
      })),
      type: 'NodePort',
    },
  };

  const result = await k8sApi.createNamespacedService('default', serviceManifest);
  console.log(`Service created for ${imageConfig.name} with ports: ${ports.join(', ')}`);
  return { name: result.body.metadata.name, ports };
}

// 创建Deployment
async function createDeployment(imageConfig, ports, envVariables) {
  const deploymentSpec = {
    apiVersion: 'apps/v1',
    kind: 'Deployment',
    metadata: { name: imageConfig.name },
    spec: {
      replicas: 1,
      selector: { matchLabels: { app: imageConfig.name } },
      template: {
        metadata: { labels: { app: imageConfig.name } },
        spec: {
          ...(imageConfig.network === 'host' && { hostNetwork: true }), // 设置host网络模式
          containers: [{
            name: imageConfig.name,
            image: `192.168.110.108:30000/${imageConfig.name}:latest`,
            env: envVariables,
            ports: ports.map(port => ({ containerPort: port })),
          }],
        },
      },
    },
  };

  await appsApi.createNamespacedDeployment('default', deploymentSpec);
  console.log(`Deployment created for ${imageConfig.name}`);
}

// 自动部署
async function deploy() {
  const usedPorts = await getUsedPorts();
  const { config: updatedConfig } = await replacePlaceholders(config, usedPorts);
  console.log(updatedConfig);
  const deletePromises = [];
  const deploymentNames = updatedConfig.images.map(imageConfig => imageConfig.name);

  for (const imageConfig of updatedConfig.images) {
    deletePromises.push(deleteService(imageConfig.name));
    deletePromises.push(deleteDeployment(imageConfig.name));
  }

  // 异步删除所有资源
  await Promise.all(deletePromises);

  // 同步等待所有资源删除完成
  await waitForPodsDeletion(deploymentNames);

  const createPromises = [];
  for (const imageConfig of updatedConfig.images) {
    const ports = imageConfig.ports.split(',').map(Number).filter(Boolean);
    const envVariables = imageConfig.env?.split(' ').map(item => {
      const [name, value] = item.split('=');
      return { name, value };
    }) || [];

    if (ports.length > 0) {
      createPromises.push(createService(imageConfig, ports));
    }
    createPromises.push(createDeployment(imageConfig, ports, envVariables));
  }

  // 异步创建所有资源
  await Promise.all(createPromises);

  // 同步等待所有 Pods 进入 Running 状态
  await waitForPodsRunning(deploymentNames);
}

// 执行部署
deploy().catch(error => console.error('Error during deployment:', error));
