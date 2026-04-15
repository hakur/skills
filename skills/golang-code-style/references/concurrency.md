# 锁与并发规范

## 互斥锁：必须使用 deadlock

禁止使用 `sync.Mutex` 和 `sync.RWMutex`，必须使用 `deadlock.Mutex` 和 `deadlock.RWMutex`：

```go
import "github.com/sasha-s/go-deadlock"

// ✅ 正确
type XBuffer struct {
    lock   deadlock.RWMutex
    buffer []byte
}

// ❌ 错误
type XBuffer struct {
    lock   sync.RWMutex    // 禁止！
    buffer []byte
}
```

**理由**：`deadlock` 在死锁时会输出完整的调用栈信息，`sync` 只会静默死锁。

## 加锁范式：公开方法加锁，内部方法不加锁

```go
func (t *XBuffer) Write(p []byte) {
    // 公开方法需要加锁，可能被多线程调用
    t.lock.Lock()
    defer t.lock.Unlock()
    t.write(p)
}

func (t *XBuffer) write(p []byte) {
    // 内部私有方法不加锁
    t.buffer = append(t.buffer, p...)
}

func (t *XBuffer) WriteWithXX(xx []byte) {
    // 公开方法需要加锁
    t.lock.Lock()
    defer t.lock.Unlock()
    t.write(xx)
}
```

## 分布式锁

分布式锁首选 `github.com/go-redsync/redsync`（基于 Redis）。

## 锁字段排列

锁字段必须是结构体的小写字段，且排在最后：

```go
// ✅ 正确：锁字段小写、排最后
type Service struct {
    Opts   *ServiceOpts
    Data   []string
    cache  map[string]string   // 小写私有
    lock   deadlock.RWMutex     // 锁排最后
}

// ❌ 错误：锁字段大写或不在最后
type Service struct {
    Lock   deadlock.RWMutex    // 不应该大写
    Data   []string
    cache  map[string]string
}
```

## 读写锁使用场景

- 只读操作 → `RLock()` / `RUnlock()`
- 写操作 → `Lock()` / `Unlock()`

```go
func (t *Cache) Get(key string) (string, bool) {
    t.lock.RLock()
    defer t.lock.RUnlock()
    val, ok := t.data[key]
    return val, ok
}

func (t *Cache) Set(key string, val string) {
    t.lock.Lock()
    defer t.lock.Unlock()
    t.data[key] = val
}
```