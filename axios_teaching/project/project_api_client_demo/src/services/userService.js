const client = require("../http/client");

async function getUserList(limit = 5) {
  const response = await client.get("/users", {
    params: { _limit: limit },
  });
  return response.data;
}

async function getUserDetail(userId) {
  const response = await client.get(`/users/${userId}`);
  return response.data;
}

async function searchUsersByName(keyword) {
  // jsonplaceholder 没有真实搜索，这里教学用前端过滤示意。
  const users = await getUserList(10);
  return users.filter((user) =>
    user.name.toLowerCase().includes(keyword.toLowerCase())
  );
}

module.exports = {
  getUserList,
  getUserDetail,
  searchUsersByName,
};

