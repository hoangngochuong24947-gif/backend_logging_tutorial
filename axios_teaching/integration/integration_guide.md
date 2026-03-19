# Integration Guide（读项目重点）

## 你在真实项目里最常见的三层

1. `http/client.js`：放 axios 实例和拦截器。
2. `services/*.js`：按业务领域封装请求函数。
3. `pages/components`：调用 service，不直接写 axios。

## 为什么这样分层

1. 改 `baseURL`、超时、鉴权时只改一处。
2. 测试和排错更容易（接口问题和页面问题分开）。
3. 代码可读性高：业务代码读起来像“操作”，不是“网络细节”。

## 读代码顺序（超实用）

1. 先看 `axios.create` 在哪里定义。
2. 再看 request/response 拦截器做了哪些统一处理。
3. 然后看 service 文件每个函数对应哪个接口。
4. 最后看页面如何调用 service 并处理 loading/error。

