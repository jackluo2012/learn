
```yml
version: "3.9"

services:

  # 存储服务-主服务器
  io-fs-master:
    build:
      context: io-fs-master
    image: io-fs-master
    container_name: io-fs-master
    restart: unless-stopped
    volumes:
      - /io3d/fs/master:/data
    ports:
      - "9333:9333"
      - "19333:19333"

  # 存储服务-存储服务器
  io-fs-volume:
    build:
      context: io-fs-volume
    image: io-fs-volume
    container_name: io-fs-volume
    restart: unless-stopped
    volumes:
      - /io3d/fs/volume1:/data
    ports:
      - "9301:9301"
      - "18080:18080"
    depends_on:
      - io-fs-master

  # 存储服务-文件管理服务器
  io-fs-filer:
    build:
      context: io-fs-filer
    image: io-fs-filer
    container_name: io-fs-filer
    restart: unless-stopped
    tty: true
    volumes:
      - /io3d/fs/filer:/data
    ports:
      - "8888:8888"
      - "18888:18888"
    depends_on:
      - io-fs-master
      - io-fs-volume

  # 存储服务-文件访问服务器
  io-fs-s3:
    build:
      context: io-fs-s3
    image: io-fs-s3
    container_name: io-fs-s3
    restart: unless-stopped
    volumes:
      - /io3d/fs/s3:/data
    ports:
      - "8333:8333"
    depends_on:
      - io-fs-master
      - io-fs-volume
      - io-fs-filer

  # 公共服务-缓存
  io-common-cache:
    build:
      context: io-common-cache
    image: io-common-cache
    container_name: io-common-cache
    restart: unless-stopped
    volumes:
      - ./io-common-cache/redis.conf:/etc/redis/redis.conf
    ports:
      - "6379:6379"

  # 公共服务-数据库pg
  io-common-db:
    build:
      context: io-common-db
    image: io-common-db
    container_name: io-common-db
    restart: unless-stopped
    volumes:
      - /io3d/common/db:/data
    ports:
      - "5432:5432"

  # 公共服务-TURN
  io-common-turn:
    build:
      context: io-common-turn
      args:
        TURN_VERSION: 4.5.2
    image: io-common-turn
    container_name: io-common-turn
    restart: unless-stopped
    network_mode: host
    volumes:
      - ./io-common-turn/turnserver.conf:/etc/turnserver.conf

  # 监控服务-GUI服务
  io-monitor-gui:
    build:
      context: io-monitor-gui
      args:
        GRAFANA_VERSION: 11.0.0
    image: io-monitor-gui
    container_name: io-monitor-gui
    #environment:
      #GF_INSTALL_PLUGINS: "grafana-clock-panel,grafana-simple-json-datasource"
    restart: unless-stopped
    volumes:
      - /io3d/monitor/gui:/var/lib/grafana
    ports:
      - "3200:3200"

  # 监控服务-时序数据库服务
  io-monitor-db:
    build:
      context: io-monitor-db
      args:
        PROMETHEUS_VERSION: latest
    image: io-monitor-db
    container_name: io-monitor-db
    restart: unless-stopped
    user: root
    volumes:
      - /io3d/monitor/db:/prometheus/data
    #command:
      # - "--web.enable-lifecycle"
      # - "--web.read-timeout=5m"
      # - "--storage.tsdb.retention=30d"
      # - "--web.max-connections=512"
      # - "--query.timeout=2m"
      # - "--query.max-concurrency=20"
      # - "--web.console.libraries=/usr/share/prometheus/console_libraries"
      # - "--web.console.templates=/usr/share/prometheus/consoles"
      # - '--storage.tsdb.retention.time=7d'
      # - "--config.file=/etc/prometheus/prometheus.yml"
    ports:
      - "3100:9090"

  # 监控服务-节点池服务
  io-monitor-pool:
    build:
      context: io-monitor-pool
      args:
        CONSUL_VERSION: 1.17.0
    image: io-monitor-pool
    container_name: io-monitor-pool
    environment:
      CONSUL_LOCAL_CONFIG: '{
          "http_config": {"response_headers" : { "Access-Control-Allow-Origin": "*", "Access-Control-Allow-Methods": "GET, OPTIONS, POST, PUT"}}
          }'
    restart: unless-stopped
    volumes:
      - /io3d/monitor/pool:/consul/data
    ports:
      - "8500:8500"

  # 三维数据库后端服务，将运行所需的文件放至io-server/build目录
  io-server:
    build:
      context: io-server
    image: io-server
    container_name: io-server
    restart: unless-stopped
    volumes:
      - ./io-server/build:/app
    tty: true
    ports:
      - "8100:8100"

  # 三维数据库文档服务，将编译的文件放至io-server-doc/dist目录
  io-server-doc:
    build:
      context: io-server-doc
    image: io-server-doc
    container_name: io-server-doc
    restart: unless-stopped
    volumes:
      - ./io-server-doc/dist:/app
    tty: true
    ports:
      - "8188:80"

  # 三维数据库GUI服务，将编译的文件放至io-server-gui/dist目录
  io-server-gui:
    build:
      context: io-server-gui
    image: io-server-gui
    container_name: io-server-gui
    restart: unless-stopped
    volumes:
      - ./io-server-gui/dist:/app
    tty: true
    ports:
      - "8000:80"

  # 三维模型库后端服务-数据库pg
  gw-mxk-db:
    build:
      context: gw-mxk-db
    image: gw-mxk-db
    container_name: gw-mxk-db
    restart: unless-stopped
    volumes:
      - /io3d/mxk/db:/data
    ports:
      - "5433:5432"

  # 三维模型库后端服务，将运行所需的文件放至gw-mxk-server/build目录
  gw-mxk-server:
    build:
      context: gw-mxk-server
    image: gw-mxk-server
    container_name: gw-mxk-server
    restart: unless-stopped
    volumes:
      - ./gw-mxk-server/build:/app
    tty: true
    ports:
      - "8200:8200"

  # 三维模型库GUI服务，将编译的文件放至gw-mxk-gui/dist目录
  gw-mxk-gui:
    build:
      context: gw-mxk-gui
    image: gw-mxk-gui
    container_name: gw-mxk-gui
    restart: unless-stopped
    volumes:
      - ./gw-mxk-gui/dist:/app
    tty: true
    ports:
      - "8080:80"

networks:
  default:
    external: true
    name: io3d
```