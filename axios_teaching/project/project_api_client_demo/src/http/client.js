const axios = require("axios");

const client = axios.create({
  baseURL: "https://jsonplaceholder.typicode.com",
  timeout: 5000,
});

client.interceptors.request.use((config) => {
  // 在真实项目里这里通常会从 store/localStorage 取 token。
  const token = "demo-token";
  config.headers = config.headers || {};
  config.headers.Authorization = `Bearer ${token}`;
  return config;
});

client.interceptors.response.use(
  (response) => response,
  (error) => {
    // 统一错误出口：页面层只处理统一格式。
    const normalizedError = {
      message: error.message,
      status: error.response?.status || 0,
      data: error.response?.data || null,
    };
    return Promise.reject(normalizedError);
  }
);

module.exports = client;

