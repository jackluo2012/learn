docker kill k8s-node-upload-docker-server
docker rm k8s-node-upload-docker-server
docker build -t k8s-node-upload-docker-server .
docker run -d --name k8s-node-upload-docker-server -p 3000:3000 k8s-node-upload-docker-server