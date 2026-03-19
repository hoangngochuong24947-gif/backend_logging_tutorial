/**
 * 第一层：基础语法 - 基本 GET / POST
 *
 * 目标：
 * 1) 看懂项目里最常见的 axios 调用
 * 2) 区分 params 和 data
 * 3) 看懂 response 对象结构
 */

const axios = require("axios");

async function runBasicExamples() {
  // GET 示例：请求参数放在 params 里，axios 会自动拼接到 URL 查询串。
  const getResponse = await axios.get("https://jsonplaceholder.typicode.com/posts", {
    params: {
      _limit: 2,
    },
  });

  console.log("GET 状态码:", getResponse.status);
  console.log("GET 返回条数:", getResponse.data.length);

  // POST 示例：请求体放在 data 里（这里直接作为第二个参数传入）。
  const postResponse = await axios.post("https://jsonplaceholder.typicode.com/posts", {
    title: "learn axios",
    body: "focus on reading project code",
    userId: 1,
  });

  console.log("POST 状态码:", postResponse.status);
  console.log("POST 返回数据:", postResponse.data);
}

runBasicExamples().catch((error) => {
  // 统一兜底：保证学习时能看到错误信息，而不是直接崩掉。
  console.error("运行失败:", error.message);
});

