# 命名规范

## 包名与变量名冲突时的处理

当变量名与导入的包名发生冲突时，**禁止**使用无意义的后缀（如 `url2`、`url_`、`urlStr`）来规避冲突。

必须将变量重命名为**更具语义**的名称，使其在上下文中自解释。

### ❌ 反面示例

```go
import "net/url"

func process(u string) {
    url2, err := url.Parse(u)  // 无意义后缀，降低可读性
    if err != nil {
        return
    }
    _ = url2
}
```

```go
import "net/url"

func process(u string) {
    url_, err := url.Parse(u)  // 下划线后缀是偷懒的做法
    if err != nil {
        return
    }
    _ = url_
}
```

### ✅ 正面示例

```go
import "net/url"

func process(raw string) {
    targetURL, err := url.Parse(raw)  // 语义清晰：这是"目标 URL"
    if err != nil {
        return
    }
    _ = targetURL
}
```

```go
import "net/url"

func buildEndpoint(base string) {
    endpointURL, err := url.Parse(base)  // 语义清晰：这是"端点 URL"
    if err != nil {
        return
    }
    _ = endpointURL
}
```

### 常见冲突场景参考

| 导入包 | 避免使用 | 推荐使用 |
|--------|----------|----------|
| `net/url` | `url2`, `url_`, `u` | `targetURL`, `endpointURL`, `parsedURL` |
| `time` | `time2`, `t` | `now`, `deadline`, `createdAt` |
| `context` | `ctx2`, `c` | `parentCtx`, `reqCtx`, `timeoutCtx` |
| `strings` | `str` | `input`, `payload`, `rawText` |
| `fmt` | `f` | 通常不需要变量，直接调用 `fmt.Printf` |
| `errors` | `err2` | `parseErr`, `validateErr`, `wrapErr` |

### 核心原则

1. **语义优先**：变量名应该回答"这是什么"，而不是"为了避免冲突随便起的"。
2. **上下文相关**：同一个包在不同函数中，变量名可以根据具体场景变化（`targetURL` vs `redirectURL`）。
3. **杜绝数字后缀**：`xxx2`、`xxx3` 是代码坏味道，永远不要用。
