/**
 * 第一层：基础语法 - 错误处理 / 超时 / 简易重试
 *
 * 目标：
 * 1) 看懂 axios 错误对象结构
 * 2) 会写最小重试逻辑
 */

const axios = require("axios");

async function requestWithRetry(url, maxRetry) {
  let lastError;

  for (let attempt = 1; attempt <= maxRetry; attempt += 1) {
    try {
      const response = await axios.get(url, { timeout: 2000 });
      return response.data;
    } catch (error) {
      lastError = error;
      console.log(`第 ${attempt} 次失败:`, error.message);
    }
  }

  throw lastError;
}

async function run() {
  try {
    const data = await requestWithRetry("https://jsonplaceholder.typicode.com/todos/1", 3);
    console.log("请求成功:", data);
  } catch (error) {
    // error.response: 服务端返回了非 2xx
    // error.request: 请求发出去了但没收到响应
    // 其他: 配置或代码异常
    if (error.response) {
      console.error("服务端错误:", error.response.status, error.response.data);
    } else if (error.request) {
      console.error("网络或超时错误，没有收到响应");
    } else {
      console.error("请求配置错误:", error.message);
    }
  }
}

run();

