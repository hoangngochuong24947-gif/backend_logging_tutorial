/**
 * 第二层：模块联合 - 并发请求与串行请求
 *
 * 目标：
 * 1) 看懂 Promise.all 的并发场景
 * 2) 看懂先 A 后 B 的串行场景
 */

const axios = require("axios");

const client = axios.create({
  baseURL: "https://jsonplaceholder.typicode.com",
  timeout: 5000,
});

async function runParallel() {
  const [usersRes, postsRes] = await Promise.all([
    client.get("/users", { params: { _limit: 2 } }),
    client.get("/posts", { params: { _limit: 2 } }),
  ]);

  console.log("并发 users:", usersRes.data.length);
  console.log("并发 posts:", postsRes.data.length);
}

async function runSequential() {
  const userRes = await client.get("/users/1");
  const userId = userRes.data.id;
  const postRes = await client.get("/posts", { params: { userId, _limit: 2 } });

  console.log("串行 user:", userRes.data.name);
  console.log("串行 posts:", postRes.data.length);
}

async function run() {
  await runParallel();
  await runSequential();
}

run().catch((error) => {
  console.error("执行失败:", error.message);
});

