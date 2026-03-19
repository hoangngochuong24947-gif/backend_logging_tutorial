/**
 * 第一层：基础语法 - 实例与拦截器
 *
 * 目标：
 * 1) 看懂 create() 生成的 apiClient
 * 2) 看懂请求拦截器 / 响应拦截器做了什么
 */

const axios = require("axios");

// 项目里非常常见：统一创建 axios 实例，避免每个地方重复写 baseURL、timeout。
const apiClient = axios.create({
  baseURL: "https://jsonplaceholder.typicode.com",
  timeout: 5000,
});

// 请求拦截器：请求发出去前统一改配置（加 token、日志、trace id）。
apiClient.interceptors.request.use((config) => {
  config.headers["X-Trace-Id"] = "demo-trace-id";
  console.log("[request]", config.method?.toUpperCase(), config.url);
  return config;
});

// 响应拦截器：响应回来后统一处理（只返回 data、统一错误格式）。
apiClient.interceptors.response.use(
  (response) => {
    console.log("[response]", response.status, response.config.url);
    return response;
  },
  (error) => {
    console.error("[response error]", error.message);
    return Promise.reject(error);
  }
);

async function run() {
  const response = await apiClient.get("/users", { params: { _limit: 2 } });
  console.log("用户数量:", response.data.length);
}

run().catch((error) => {
  console.error("运行失败:", error.message);
});

