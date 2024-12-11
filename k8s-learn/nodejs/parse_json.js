// 导入依赖
const fs = require('fs');

// 模拟从配置文件读取JSON
const configJson = fs.readFileSync('image-deployment-config-template.json', 'utf8');
const config = JSON.parse(configJson);

// 生成随机端口的函数
function getRandomPort() {
  return Math.floor(Math.random() * (32767 - 30000)) + 30000;  // 随机生成1024到65535之间的端口
}
// k8s nodeport 端口范围是30000-32767
// 替换占位符的函数
// 替换占位符的函数
function replacePlaceholders(config) {
    const randomPorts = {};
  
    // 遍历镜像配置，替换端口占位符
    config.images.forEach(image => {
      if (image.ports) {
        // 替换端口占位符
        const portMatches = image.ports.match(/\$\{([a-zA-Z0-9_]+)\}/g) || [];
        portMatches.forEach(match => {
          const placeholder = match.slice(2, -1);  // 去掉 ${ 和 }，提取占位符名称
  
          if (!randomPorts[placeholder]) {
            // 如果该占位符没有被处理过，生成一个随机端口
            randomPorts[placeholder] = getRandomPort();
          }
  
          // 将占位符替换为随机端口
          image.ports = image.ports.replace(match, randomPorts[placeholder]);
          image.env = image.env.replace(match, randomPorts[placeholder]);
        });
      }
  
      // 处理depends_on的端口替换
      if (image.env) {
        Object.keys(randomPorts).forEach(placeholder => {
          const placeholderMatch = new RegExp(`\\$\\{${placeholder}\\}`, 'g');
          image.env = image.env.replace(placeholderMatch, randomPorts[placeholder]);
        });
      }
    });
  
    return config;
}
 

// 替换占位符并输出结果
const updatedConfig = replacePlaceholders(config);

// 将更新后的配置写回文件
fs.writeFileSync('image-deployment-config.json', JSON.stringify(updatedConfig, null, 2), 'utf8');

// 打印最终结果
console.log(JSON.stringify(updatedConfig, null, 2));
