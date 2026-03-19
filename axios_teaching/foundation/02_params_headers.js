/**
 * 第一层：基础语法 - params / headers / timeout
 *
 * 目标：
 * 1) 看懂“请求配置对象”结构
 * 2) 理解项目里 headers 和 timeout 的常见写法
 */

const axios = require("axios");

async function runConfigExample() {
  const response = await axios({
    method: "get",
    url: "https://jsonplaceholder.typicode.com/comments",
    params: {
      postId: 1,
      _limit: 3,
    },
    headers: {
      // 在真实项目中这里常放 token、语言、trace id。
      "X-Client-Name": "axios-teaching",
    },
    timeout: 5000,
  });

  console.log("状态码:", response.status);
  console.log("第一条评论邮箱:", response.data[0]?.email);
}

runConfigExample().catch((error) => {
  console.error("请求失败:", error.message);
});

