# 单元测试与 Mock 测试规范

## 测试库

| 用途 | 库 |
|------|-----|
| 标准库 | `github.com/stretchr/testify` |
| assert | `github.com/stretchr/testify/assert` |
| mock | `github.com/stretchr/testify/mock` |
| MySQL 内存数据库 | `github.com/dolthub/go-mysql-server`（结合 gorm） |
| Redis 内存数据库 | `github.com/alicebob/miniredis/v2` |
| 环境变量加载 | `github.com/joho/godotenv` |

## 测试规范

### 必须遵守

- **禁止嵌套测试**：不要使用 `t.Run` 嵌套，一层套一层很不好看
- **禁止 t.Skip**：不要因为条件不满足就跳过测试，缺少条件应人工补充
- **禁止集成测试文件**：不生成 `xxx_integration_test.go`
- **禁止根目录 test 目录**：不生成 `test/` 或 `test/integration/`
- **一一对应**：`abc.go` → `abc_test.go`，只测试大写名字的函数
- **独立测试函数**：每个被测函数写独立 `TestXxx`，差异大时写 `TestXxxWithAaa`
- **TestMain 初始化**：环境信息和全局变量在 `TestMain` 中通过 `godotenv.Load(".env")` 完成

### Mock 测试

- `abc.go` → `abc_mock_test.go`
- 使用 `testify/mock` 设计 mock
- 只测试 `abc.go` 中大写名字的函数

## 好的示范

```go
import "github.com/joho/godotenv"

func TestMain(m *testing.M) {
    godotenv.Load(".env")
    pool, resource := startTestDB()
    runMigrations(getDBURL(resource))
    code := m.Run()
    if err := pool.Purge(resource); err != nil {
        log.Printf("清理测试数据库失败: %v", err)
    }
    os.Exit(code)
}

func TestTrieTreeInsert(t *testing.T) {
    tree := NewTrieTree()
    var matched []byte
    tree.Insert([]byte("abcdefg"))
    matched = tree.Match([]byte("abcdefg"))
    assert.Equal(t, []byte("abcdefg"), matched)
}

func TestTrieTreeDelete(t *testing.T) {}
```

## 坏的示范

```go
// ❌ t.Run 嵌套测试
func TestCalculator(t *testing.T) {
    t.Run("Advanced", func(t *testing.T) {
        t.Run("Multiplication", func(t *testing.T) {})
        t.Run("Division", func(t *testing.T) {})
    })
}
```

## 代码重复检测

### DRY 原则（Don't Repeat Yourself）

测试代码同样需要遵循 DRY 原则。重复的测试代码会导致：
- 维护困难：一处改动需要修改多处
- 可读性差：测试意图被重复代码淹没
- 容易遗漏：复制粘贴时可能漏改关键部分

### 代码重复检测配置

L2 层代码检查包含 `dupl` 工具检测代码重复：

```bash
# 设置重复阈值（默认 15 行）
export DUPL_THRESHOLD=10

# 运行检查
python <skill-dir>/scripts/verify.py <project-path>
```

### 严重程度分级

| 重复次数 | 严重程度 | 处理要求 |
|---------|---------|---------|
| 2 处 | WARN | 建议提取公共函数或 setup 方法 |
| 3+ 处 | ERROR | 必须重构，提取公共辅助函数 |

### 常见重复场景

**❌ 重复的场景：多处测试使用相同的初始化逻辑**

```go
func TestCreateUser(t *testing.T) {
    db := setupTestDB()
    defer teardownTestDB(db)
    user := &User{Name: "test"}
    err := db.Create(user).Error
    assert.NoError(t, err)
}

func TestUpdateUser(t *testing.T) {
    db := setupTestDB()  // 重复！
    defer teardownTestDB(db)  // 重复！
    user := &User{Name: "test"}
    err := db.Create(user).Error  // 重复！
    assert.NoError(t, err)  // 重复！
}
```

**✅ 好的示范：使用 TestMain 和辅助函数**

```go
var testDB *gorm.DB

func TestMain(m *testing.M) {
    testDB = setupTestDB()
    defer teardownTestDB(testDB)
    code := m.Run()
    os.Exit(code)
}

func createTestUser(t *testing.T, name string) *User {
    user := &User{Name: name}
    err := testDB.Create(user).Error
    assert.NoError(t, err)
    return user
}

func TestCreateUser(t *testing.T) {
    user := createTestUser(t, "test")
    assert.NotZero(t, user.ID)
}

func TestUpdateUser(t *testing.T) {
    user := createTestUser(t, "test")
    user.Name = "updated"
    err := testDB.Save(user).Error
    assert.NoError(t, err)
}
```

### 允许合理重复的情况

以下情况不算违规：
- 测试数据准备（不同测试需要不同数据）
- 断言组合（合理的 assert 组合）
- 简单的 3-5 行重复（低于阈值）

## 内存数据库使用

### MySQL 内存测试（结合 gorm）

```go
func TestMain(m *testing.M) {
    godotenv.Load(".env")
    // 启动 go-mysql-server 内存数据库
    // 连接 gorm
    // 运行迁移
    code := m.Run()
    // 清理
    os.Exit(code)
}
```

### Redis 内存测试

```go
func TestMain(m *testing.M) {
    godotenv.Load(".env")
    // 使用 miniredis 启动内存 Redis
    code := m.Run()
    // 清理
    os.Exit(code)
}
```