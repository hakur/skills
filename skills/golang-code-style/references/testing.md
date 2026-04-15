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