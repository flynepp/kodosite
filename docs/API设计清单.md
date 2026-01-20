# API 设计清单

## 🔐 用户管理（User）

### 前台用户

- `POST /api/user/register` - 用户注册
- `POST /api/user/login` - 用户登录
- `GET /api/user/profile` - 获取用户信息
- `PUT /api/user/profile` - 更新用户信息
- `POST /api/user/logout` - 用户登出

### 管理员

- `POST /api/admin/login` - 管理员登录
- `GET /api/admin/verify` - 验证管理员 token

---

## 🛒 购物车（Cart）

- `GET /api/cart` - 获取购物车列表
- `POST /api/cart` - 添加商品到购物车
- `PUT /api/cart/:id` - 更新购物车商品数量
- `DELETE /api/cart/:id` - 从购物车删除商品
- `DELETE /api/cart` - 清空购物车

---

## 📦 商品管理（Product）

### 前台

- `GET /api/products?page=1&limit=12` - 查询商品列表（分页）
- `GET /api/products/:id` - 获取商品详情
- `GET /api/products?tag=标签名` - 通过标签查询商品
- `GET /api/products?category=分类ID` - 通过分类查询商品
- `GET /api/products/search?q=关键词` - 搜索商品

### 后台（管理员）

- `POST /api/admin/products` - 创建商品
- `PUT /api/admin/products/:id` - 编辑商品
- `DELETE /api/admin/products/:id` - 删除商品
- `PATCH /api/admin/products/:id/status` - 上架/下架商品
- `PATCH /api/admin/products/:id/stock` - 更新库存

---

## 🏷️ 标签管理（Tag）

- `GET /api/tags` - 获取所有标签
- `POST /api/admin/tags` - 创建标签（管理员）
- `PUT /api/admin/tags/:id` - 修改标签（管理员）
- `DELETE /api/admin/tags/:id` - 删除标签（管理员）

---

## 📁 分类管理（Category）

- `GET /api/categories` - 获取所有分类
- `GET /api/categories/:id` - 获取分类详情
- `POST /api/admin/categories` - 创建分类（管理员）
- `PUT /api/admin/categories/:id` - 修改分类（管理员）
- `DELETE /api/admin/categories/:id` - 删除分类（管理员）

---

## 🛍️ 订单管理（Order）**【核心功能】**

### 前台用户

- `POST /api/orders` - 创建订单（下单）
- `GET /api/orders` - 查询我的订单列表
- `GET /api/orders/:id` - 查询订单详情
- `POST /api/orders/:id/payment-proof` - 上传付款凭证

### 后台管理员

- `GET /api/admin/orders?status=pending` - 查询所有订单（可筛选）
- `GET /api/admin/orders/:id` - 查询订单详情
- `PATCH /api/admin/orders/:id/status` - 更新订单状态
- `POST /api/admin/orders/:id/confirm` - 确认收款
- `POST /api/admin/orders/:id/cancel` - 取消订单

---

## 📰 新闻管理（News）

### 前台

- `GET /api/news?page=1&limit=10` - 查询新闻列表（分页）
- `GET /api/news/:id` - 查询新闻详情

### 后台（管理员）

- `GET /api/admin/news` - 查询所有新闻（管理员）
- `POST /api/admin/news` - 创建新闻
- `PUT /api/admin/news/:id` - 编辑新闻
- `DELETE /api/admin/news/:id` - 删除新闻

---

## 📝 博客管理（Blog）

### 前台

- `GET /api/blogs?page=1&limit=10` - 查询博客列表（分页）
- `GET /api/blogs/:id` - 查询博客详情
- `GET /api/blogs?tag=标签名` - 通过标签查询博客

### 后台（管理员）

- `GET /api/admin/blogs` - 查询所有博客（管理员）
- `POST /api/admin/blogs` - 创建博客
- `PUT /api/admin/blogs/:id` - 编辑博客
- `DELETE /api/admin/blogs/:id` - 删除博客

---

## 🔍 搜索（Search）

- `GET /api/search?q=关键词&type=all` - 全站搜索
- `GET /api/search/products?q=关键词` - 搜索商品
- `GET /api/search/news?q=关键词` - 搜索新闻
- `GET /api/search/blogs?q=关键词` - 搜索博客

---

## 📧 邮件通知（Email）

- `POST /api/email/order-created` - 下单成功通知
- `POST /api/email/payment-reminder` - 付款提醒
- `POST /api/email/order-confirmed` - 订单确认通知
- `POST /api/email/order-cancelled` - 订单取消通知

---

## 📊 数据统计（Analytics）**【可选】**

- `GET /api/admin/stats/overview` - 首页概览数据
- `GET /api/admin/stats/orders` - 订单统计
- `GET /api/admin/stats/products` - 商品销售统计

---

## 🖼️ 文件上传（Upload）

- `POST /api/upload/image` - 上传图片（商品图/付款凭证等）
- `POST /api/upload/document` - 上传文件

---

## 📄 静态页面（Page）

- `GET /api/pages/:slug` - 获取静态页面内容（关于我们、联系方式等）
- `PUT /api/admin/pages/:slug` - 编辑静态页面（管理员）

---

## ✅ 优先级建议

### 第一阶段（MVP - 最小可用）

1. ✅ 用户注册/登录
2. ✅ 商品列表/详情
3. ✅ 购物车
4. ✅ 订单创建/查询
5. ✅ 订单状态管理
6. ✅ 管理员登录

### 第二阶段（核心功能）

7. 商品管理（CRUD）
8. 付款凭证上传
9. 订单确认流程
10. 标签/分类管理

### 第三阶段（内容管理）

11. 新闻管理
12. 博客管理
13. 搜索功能

### 第四阶段（增强功能）

14. 邮件通知
15. 数据统计
16. 静态页面管理

---

## 🗄️ 数据库表设计建议

### Users（用户表）

```sql
id, email, password_hash, first_name, last_name, phone,
created_at, updated_at
```

### Admins（管理员表）

```sql
id, username, password_hash, role, created_at
```

### Products（商品表）

```sql
id, title, description, price, compare_price, stock,
status (draft/active/sold), images, category_id,
created_at, updated_at
```

### Categories（分类表）

```sql
id, name, slug, description, parent_id, created_at
```

### Tags（标签表）

```sql
id, name, slug, created_at
```

### ProductTags（商品标签关联）

```sql
product_id, tag_id
```

### Cart（购物车表）

```sql
id, user_id, product_id, quantity, created_at
```

### Orders（订单表）

```sql
id, user_id, order_number, total_amount, status,
payment_proof_url, due_date, created_at, updated_at
```

### OrderItems（订单商品表）

```sql
id, order_id, product_id, quantity, price, created_at
```

### News（新闻表）

```sql
id, title, content, slug, image, published_at, created_at, updated_at
```

### Blogs（博客表）

```sql
id, title, content, slug, image, tags, published_at, created_at, updated_at
```

### Pages（静态页面表）

```sql
id, slug, title, content, seo_title, seo_description, updated_at
```

---

**总计：**

- **前台 API**: 约 25 个
- **后台管理 API**: 约 20 个
- **总计**: 约 45 个 API 端点
