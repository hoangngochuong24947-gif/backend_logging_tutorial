/**
 * 第二层：模块联合 - Service Layer 模式
 *
 * 目标：
 * 1) 看懂“http client + service 文件”的项目结构
 * 2) 理解为什么业务代码不直接调用 axios
 */

const axios = require("axios");

const httpClient = axios.create({
  baseURL: "https://jsonplaceholder.typicode.com",
  timeout: 5000,
});

// service 层只暴露业务语义，不暴露 axios 细节。
const userService = {
  async getUserList(limit = 3) {
    const response = await httpClient.get("/users", {
      params: { _limit: limit },
    });
    return response.data;
  },

  async getUserDetail(userId) {
    const response = await httpClient.get(`/users/${userId}`);
    return response.data;
  },
};

async function run() {
  const list = await userService.getUserList();
  console.log("列表首个用户:", list[0].name);

  const detail = await userService.getUserDetail(1);
  console.log("详情邮箱:", detail.email);
}

run().catch((error) => {
  console.error("运行失败:", error.message);
});

