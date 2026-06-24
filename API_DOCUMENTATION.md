# API Documentation

## Base URL
```
http://localhost/blog/api/
```

---

## Posts API

### 1. Get All Posts
- **URL**: `/posts/`
- **Method**: `GET`
- **Query Parameters**:
  - `page`: 分页页码（可选）
  - `search`: 搜索关键词（可选）

**Response (200 OK)**:
```json
{
  "count": 10,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "title": "Django Best Practices",
      "slug": "django-best-practices",
      "author": "admin",
      "body": "Post content...",
      "publish": "2026-06-22T10:00:00Z",
      "created": "2026-06-20T08:00:00Z",
      "status": "PB",
      "tags": ["django", "python"]
    }
  ]
}
```

---

### 2. Create Post
- **URL**: `/posts/`
- **Method**: `POST`
- **Authentication**: Required
- **Content-Type**: `application/json`

**Request Body**:
```json
{
  "title": "New Post",
  "body": "Post content",
  "status": "PB",
  "tags": ["django"]
}
```

**Response (201 Created)**:
```json
{
  "id": 11,
  "title": "New Post",
  "slug": "new-post",
  "author": "admin",
  "body": "Post content",
  "status": "PB",
  "tags": ["django"]
}
```

---

### 3. Get Post Detail
- **URL**: `/posts/{id}/`
- **Method**: `GET`

**Response (200 OK)**:
```json
{
  "id": 1,
  "title": "Django Best Practices",
  "slug": "django-best-practices",
  "author": "admin",
  "body": "Detailed post content...",
  "publish": "2026-06-22T10:00:00Z",
  "created": "2026-06-20T08:00:00Z",
  "updated": "2026-06-22T12:00:00Z",
  "status": "PB",
  "tags": ["django", "python"],
  "comments_count": 5
}
```

---

### 4. Update Post
- **URL**: `/posts/{id}/`
- **Method**: `PUT`
- **Authentication**: Required (author only)

**Request Body**:
```json
{
  "title": "Updated Title",
  "body": "Updated content",
  "status": "PB"
}
```

---

### 5. Delete Post
- **URL**: `/posts/{id}/`
- **Method**: `DELETE`
- **Authentication**: Required (author only)

**Response (204 No Content)**

---

## Comments API

### 1. Get All Comments
- **URL**: `/comments/`
- **Method**: `GET`
- **Query Parameters**:
  - `post`: 文章ID（可选）
  - `page`: 分页（可选）

**Response (200 OK)**:
```json
{
  "count": 20,
  "results": [
    {
      "id": 1,
      "post": 1,
      "name": "John Doe",
      "email": "john@example.com",
      "body": "Great post!",
      "created": "2026-06-22T11:00:00Z",
      "active": true
    }
  ]
}
```

---

### 2. Create Comment
- **URL**: `/comments/`
- **Method**: `POST`

**Request Body**:
```json
{
  "post": 1,
  "name": "Jane Doe",
  "email": "jane@example.com",
  "body": "Nice article!"
}
```

**Response (201 Created)**:
```json
{
  "id": 2,
  "post": 1,
  "name": "Jane Doe",
  "email": "jane@example.com",
  "body": "Nice article!",
  "created": "2026-06-22T12:00:00Z",
  "active": true
}
```

---

### 3. Get Comment Detail
- **URL**: `/comments/{id}/`
- **Method**: `GET`

---

### 4. Update Comment
- **URL**: `/comments/{id}/`
- **Method**: `PUT`
- **Authentication**: Optional (admin only)

---

### 5. Delete Comment
- **URL**: `/comments/{id}/`
- **Method**: `DELETE`
- **Authentication**: Optional (admin only)

---

## Tags API

### 1. Get All Tags
- **URL**: `/tags/`
- **Method**: `GET`

**Response (200 OK)**:
```json
{
  "results": [
    {
      "id": 1,
      "name": "django",
      "slug": "django",
      "posts_count": 5
    },
    {
      "id": 2,
      "name": "python",
      "slug": "python",
      "posts_count": 8
    }
  ]
}
```

---

### 2. Get Tag Detail
- **URL**: `/tags/{slug}/`
- **Method**: `GET`

**Response (200 OK)**:
```json
{
  "id": 1,
  "name": "django",
  "slug": "django",
  "posts": [
    {
      "id": 1,
      "title": "Django Best Practices",
      "slug": "django-best-practices"
    }
  ],
  "posts_count": 5
}
```

---

## Error Responses

### 400 Bad Request
```json
{
  "field_name": ["Error message"]
}
```

### 401 Unauthorized
```json
{
  "detail": "Authentication credentials were not provided."
}
```

### 403 Forbidden
```json
{
  "detail": "You do not have permission to perform this action."
}
```

### 404 Not Found
```json
{
  "detail": "Not found."
}
```

### 500 Internal Server Error
```json
{
  "detail": "Internal server error."
}
```

---

## Authentication

- **Type**: Session-based or Token-based
- **Header**: `Authorization: Bearer {token}`
- **Login**: `/users/login/`
- **Logout**: `/users/logout/`

---

## Pagination

Default page size: 20 items

**Query**: `?page=2`

**Response includes**:
- `count`: 总数
- `next`: 下一页URL
- `previous`: 上一页URL
- `results`: 数据列表

---

## Filtering & Search

### Search Posts
```
GET /posts/?search=django
```

### Filter by Tag
```
GET /posts/?tags=django
```

### Filter Comments by Post
```
GET /comments/?post=1
```

---

## Status Codes

| Code | Meaning |
|------|---------|
| 200 | OK |
| 201 | Created |
| 204 | No Content |
| 400 | Bad Request |
| 401 | Unauthorized |
| 403 | Forbidden |
| 404 | Not Found |
| 500 | Server Error |

---

## Examples

### cURL - Get All Posts
```bash
curl -X GET http://localhost/blog/api/posts/
```

### cURL - Create Post
```bash
curl -X POST http://localhost/blog/api/posts/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{"title":"New Post","body":"Content","status":"PB"}'
```

### Python - Get Posts
```python
import requests

response = requests.get('http://localhost/blog/api/posts/')
posts = response.json()
for post in posts['results']:
    print(post['title'])
```

### JavaScript - Create Comment
```javascript
fetch('http://localhost/blog/api/comments/', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    post: 1,
    name: 'User',
    email: 'user@example.com',
    body: 'Great post!'
  })
})
.then(r => r.json())
.then(data => console.log(data))
```

---

## Rate Limiting

Currently: No rate limiting implemented

*Recommendation: Add Django REST Framework throttling*

---

## Versioning

Current version: v1 (implicit)

*Recommendation: Implement API versioning (v1, v2, etc.)*
