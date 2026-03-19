# project_api_client_demo

这是一个“读项目结构”示例，不追求业务完整，重点是你能看懂：

1. `src/http/client.js`：axios 实例和拦截器。
2. `src/services/userService.js`：业务接口函数封装。

## 建议阅读顺序

1. 先读 `client.js` 里的 `create` 和两个拦截器。
2. 再读 `userService.js` 看每个函数如何调用 client。
3. 然后尝试自己新增一个 `getPosts` 函数。

