/**
 * 第三层：高级功能 - 取消请求（AbortController）
 *
 * 目标：
 * 1) 看懂前端切页或输入搜索时为什么要取消旧请求
 * 2) 识别项目里的 signal 用法
 */

const axios = require("axios");

async function runCancelDemo() {
  const controller = new AbortController();

  const promise = axios.get("https://jsonplaceholder.typicode.com/photos", {
    params: { _limit: 20 },
    signal: controller.signal,
  });

  // 教学模拟：快速触发取消。
  setTimeout(() => {
    controller.abort();
  }, 10);

  try {
    const response = await promise;
    console.log("成功:", response.data.length);
  } catch (error) {
    // axios 对取消请求会抛出专门错误。
    if (error.code === "ERR_CANCELED") {
      console.log("请求已取消（这是预期行为）");
      return;
    }
    console.error("其他错误:", error.message);
  }
}

runCancelDemo();

