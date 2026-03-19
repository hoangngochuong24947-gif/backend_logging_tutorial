# Advanced Features（看懂就够）

## 401 刷新 token：你要看懂什么

1. 拦截器里判断 `error.response.status === 401`。
2. 用 `_retry` 防止死循环。
3. 刷新成功后，带新 token 重发原请求。

## 请求取消：你要看懂什么

1. `const controller = new AbortController()`。
2. 请求配置里传 `signal: controller.signal`。
3. 在组件卸载或发起新请求前 `controller.abort()`。

## 面试和项目都常问的坑

1. 并发多个 401 时，可能重复刷新 token。
2. 刷新接口本身失败时，要清理登录态并跳登录页。
3. 取消请求不应当作“报错提示用户”，通常静默处理。

