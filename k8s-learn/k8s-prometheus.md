###

```
docker run  -d \
  -p 9090:9090 \
  -v /d/works/prometheus/prometheus1.yml:/etc/prometheus/prometheus.yml \
  -v /d/works/prometheus/data:/prometheus \
  prom/prometheus

```

```
docker run -d --name consul -p 8500:8500 -v /d/works/consul/conf/:/consul/conf/ -v /d/works/consul/data/:/consul/data/ hashicorp/consul:1.17

```
## 注册服务
```curl -X PUT -d '{
  "id": "iotree3d-sys-info",
  "name": "sys-info",
  "address": "io-metric-sys-service",
  "port": 9100,
  "tags": ["sys-info"],
  "meta": {
    "job": "iotree3d-sys-info-sys-info",
    "instance": "iotree3d服务器"
  },
  "checks": [{
    "http": "http://io-metric-sys-service:9100/metrics",
    "interval": "10s"
  }]
}' http://localhost:8500/v1/agent/service/register

```
curl -X PUT -d '{
  "id": "iotree3d-gpu-info",
  "name": "gpu-info",
  "address": "nvidia-dcgm-exporter.gpu-operator",
  "port": 9400,
  "tags": ["gpu-info"],
  "meta": {
    "job": "gpu",
    "instance": "iotree3d服务器"
  },
  "checks": [{
    "http": "http://nvidia-dcgm-exporter.gpu-operator:9400/metrics",
    "interval": "10s"
  }]
}' http://localhost:8500/v1/agent/service/register


```

### 删除服务 
```
curl --request PUT http://127.0.0.1:8500/v1/agent/service/deregister/http1
```