---
name: github-speedup-skill
description: 加速访问 GitHub 资源，包括 git clone 和文件下载。当用户需要克隆 GitHub 仓库或下载 GitHub 上的文件/发布包时，自动使用加速代理。触发词：git clone、github、wget github、下载 github、克隆 github、github release、github 加速。
---

# GitHub Speedup

加速访问 GitHub 资源，通过代理前缀解决中国大陆访问 GitHub 缓慢的问题。

## 何时使用

当用户需要执行以下操作时，自动触发此 skill：
- `git clone` 克隆 GitHub 仓库
- `wget` / `curl` 下载 GitHub 上的文件或发布包
- 任何涉及 `github.com` 域名的资源获取

## 加速规则

### 规则 1：git clone 加速

在 `https://github.com/` 前面加上代理前缀 `https://gh-proxy.org/`。

**转换格式：**

```
原始: git clone https://github.com/{owner}/{repo}.git
加速: git clone https://gh-proxy.org/https://github.com/{owner}/{repo}.git
```

**示例：**

```
原始: git clone https://github.com/TokisanGames/Terrain3D/
加速: git clone https://gh-proxy.org/https://github.com/TokisanGames/Terrain3D/
```

### 规则 2：文件下载加速

在 `https://github.com/` 前面加上代理前缀 `https://gh-proxy.org/`。

**转换格式：**

```
原始: wget https://github.com/{owner}/{repo}/releases/download/{tag}/{file}
加速: wget https://gh-proxy.org/https://github.com/{owner}/{repo}/releases/download/{tag}/{file}
```

**示例：**

```
原始: wget https://github.com/TokisanGames/Terrain3D/releases/download/v1.0.1/Terrain3D_v1.0.1.zip
加速: wget https://gh-proxy.org/https://github.com/TokisanGames/Terrain3D/releases/download/v1.0.1/Terrain3D_v1.0.1.zip
```

## 使用步骤

1. 识别用户命令中是否包含 `github.com` 的 URL
2. 判断是 git clone 还是文件下载（wget/curl）
3. 在原始 URL 前加上 `https://gh-proxy.org/` 前缀
4. 执行加速后的命令

## 注意事项

- 此代理仅适用于 `github.com` 域名，不要对其他域名使用
- 如果代理不可用，回退到原始 URL 并提醒用户代理可能暂时不可用
- 代理前缀是 `https://gh-proxy.org/`，注意尾部有斜杠，与原始 URL 的 `https://` 部分连续使用，不要省略 `https://`