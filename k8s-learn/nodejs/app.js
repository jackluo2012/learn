const express = require('express');
const k8s = require('@kubernetes/client-node');
const fileUpload = require('express-fileupload');
const { exec } = require('child_process');

const app = express();
const port = 3000;

// 中间件解析 JSON 请求体
app.use(express.json());

// 部署和暴露应用函数
async function deployAndExposeApp(imageName, containerPort) {
    const kc = new k8s.KubeConfig();
    kc.loadFromDefault();

    const k8sApi = kc.makeApiClient(k8s.AppsV1Api);
    const k8sCoreApi = kc.makeApiClient(k8s.CoreV1Api);

    const appName = `app-${Date.now()}`;

    const deployment = {
        apiVersion: 'apps/v1',
        kind: 'Deployment',
        metadata: { name: `${appName}-deployment` },
        spec: {
            replicas: 1,
            selector: { matchLabels: { app: appName } },
            template: {
                metadata: { labels: { app: appName } },
                spec: {
                    containers: [{
                        name: appName,
                        image: imageName,
                        imagePullPolicy: 'Never',
                        ports: [{ containerPort }]
                    }],
                    affinity: {
                        nodeAffinity: {
                            requiredDuringSchedulingIgnoredDuringExecution: {
                                nodeSelectorTerms: [{
                                    matchExpressions: [{
                                        key: 'kubernetes.io/hostname',
                                        operator: 'In',
                                        values: ['docker-desktop']
                                    }]
                                }]
                            }
                        }
                    }
                }
            }
        }
    };

    const service = {
        apiVersion: 'v1',
        kind: 'Service',
        metadata: { name: `${appName}-service` },
        spec: {
            selector: { app: appName },
            ports: [{ protocol: 'TCP', port: containerPort, targetPort: containerPort }],
            type: 'NodePort'
        }
    };

    try {
        await k8sApi.createNamespacedDeployment('default', deployment);
        console.log('Deployment created');

        const serviceResponse = await k8sCoreApi.createNamespacedService('default', service);
        console.log('Service created');

        const nodes = await k8sCoreApi.listNode();
        const nodeIp = nodes.body.items[0].status.addresses.find(addr => addr.type === 'InternalIP').address;

        const servicePort = serviceResponse.body.spec.ports[0].nodePort;

        return {
            deploymentName: deployment.metadata.name,
            serviceName: service.metadata.name,
            servicePort,
            nodeIp,
            message: `Service '${service.metadata.name}' is exposed on node '${nodeIp}:${servicePort}'`
        };
    } catch (err) {
        console.error('Error:', err);
        throw new Error(`Failed to deploy and expose app: ${err.message}`);
    }
}

// API 端点：接收镜像名和端口来部署应用
app.post('/deploy', async (req, res) => {
    const { imageName, containerPort } = req.body;

    if (!imageName || !containerPort) {
        return res.status(400).json({ error: 'Missing required parameters: imageName, containerPort' });
    }

    try {
        const result = await deployAndExposeApp(imageName, containerPort);
        res.status(200).json(result);
    } catch (err) {
        res.status(500).json({ error: err.message });
    }
});

app.use(fileUpload());

app.post('/upload', async (req, res) => {
    if (!req.files || !req.files.image) {
        return res.status(400).send('No file uploaded.');
    }

    const imageFile = req.files.image;

    // 获取文件名的后缀是否为tar
    const fileName = imageFile.name;
    const fileExtension = fileName.split('.').pop();
    if (fileExtension !== 'tar') {
        return res.status(400).send('File is not a Docker image.');
    }

    // 获取去掉后缀的文件名
    const imageName = fileName.split('.').slice(0, -1).join('.');
    const imagePath = `/tmp/${imageFile.name}`;

    // 保存文件
    await imageFile.mv(imagePath);

    const repo = '192.168.110.116:30500'; // 替换为你的仓库地址
    const tag = 'latest';

    exec(`docker load < ${imagePath}`, (err, stdout, stderr) => {
        if (err) return res.status(500).send(`Error loading image: ${stderr}`);

        const loadedImage = stdout.match(/Loaded image: (.+)/)[1];
        const newTag = `${repo}/${imageName}:${tag}`;

        exec(`docker tag ${loadedImage} ${newTag}`, (err, stdout, stderr) => {
            if (err) return res.status(500).send(`Error tagging image: ${stderr}`);

            exec(`docker push ${newTag}`, (err, stdout, stderr) => {
                if (err) return res.status(500).send(`Error pushing image: ${stderr}`);

                res.send(`Image successfully pushed to ${newTag}`);
            });
        });
    });
});

// 启动 Web 服务
app.listen(port, () => {
    console.log(`Server is running on http://localhost:${port}`);
});
