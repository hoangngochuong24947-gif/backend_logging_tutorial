/**
 * 第三层：高级功能 - 401 刷新 token 模式（教学版）
 *
 * 说明：
 * 这份代码重点是“读懂流程”，不是可直接接入生产。
 */

const axios = require("axios");

const client = axios.create({
  baseURL: "https://jsonplaceholder.typicode.com",
  timeout: 5000,
});

let accessToken = "expired-token";

function setAuthHeader(config) {
  config.headers = config.headers || {};
  config.headers.Authorization = `Bearer ${accessToken}`;
  return config;
}

async function fakeRefreshToken() {
  // 教学模拟：真实项目会请求 /auth/refresh 拿新 token。
  await new Promise((resolve) => setTimeout(resolve, 200));
  accessToken = "new-token";
  return accessToken;
}

client.interceptors.request.use((config) => setAuthHeader(config));

client.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    // 教学点：_retry 防止无限循环重试。
    if (error.response?.status === 401 && !originalRequest?._retry) {
      originalRequest._retry = true;
      await fakeRefreshToken();
      setAuthHeader(originalRequest);
      return client(originalRequest);
    }

    return Promise.reject(error);
  }
);

async function run() {
  // jsonplaceholder 不会真的返回 401，这里只演示结构。
  const res = await client.get("/users/1");
  console.log("请求成功:", res.data.name);
}

run().catch((error) => {
  console.error("失败:", error.message);
});

