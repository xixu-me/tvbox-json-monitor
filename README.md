# TVBox JSON Monitor

[![Monitor TVBox JSON](https://github.com/xixu-me/tvbox-json-monitor/actions/workflows/tvbox-json-monitor.yml/badge.svg)](https://github.com/xixu-me/tvbox-json-monitor/actions/workflows/tvbox-json-monitor.yml)

TVBox JSON Monitor 定时抓取一个 TVBox 兼容端点，从 JPEG-like 响应里提取附加的配置载荷，解码为严格 JSON，并在内容变化时自动提交更新。

> [!IMPORTANT]
> 本仓库只保存从配置端点解码得到的 JSON 文件，不托管视频内容，不代理媒体流，也不提供播放服务。

## 输出文件

| 文件 | 说明 |
| --- | --- |
| [`data/tvbox.json`](data/tvbox.json) | 解码并格式化后的 TVBox 配置，保持为标准 JSON。 |
| [`data/tvbox.meta.json`](data/tvbox.meta.json) | 最近一次抓取与解码的元数据，包括哈希、大小、响应头和源地址。 |

推荐使用 [Xget](https://github.com/xixu-me/xget) 加速地址读取最新 JSON：

```text
https://xget.xi-xu.me/gh/xixu-me/tvbox-json-monitor/raw/refs/heads/main/data/tvbox.json
```

也可以直接使用 GitHub raw 地址：

```text
https://raw.githubusercontent.com/xixu-me/tvbox-json-monitor/main/data/tvbox.json
```

## 工作方式

上游端点返回给 TVBox 客户端的是一个 JPEG-like payload，真实配置追加在 JPEG EOI 标记 `FF D9` 之后。脚本会按以下步骤处理：

1. 使用 TVBox 风格的 `User-Agent` 请求配置端点。
2. 定位 JPEG EOI 标记 `FF D9`。
3. 读取 EOI 之后的附加载荷。
4. 在附加载荷中查找 `**` 分隔符。
5. 对分隔符之后的内容进行 Base64 解码。
6. 移除上游配置中的 JSONC 风格整行注释。
7. 解析并重新序列化为 2 空格缩进的严格 JSON。

## 自动更新

GitHub Actions 每 5 分钟检查一次上游配置，也支持在 Actions 页面手动触发。

当 `data/tvbox.json` 或 `data/tvbox.meta.json` 有变化时，工作流会提交类似下面的 commit：

```text
chore(tvbox): update decoded JSON 2026-05-13T16:00:00Z
```

如果上游端点临时不可用、返回格式异常或解码失败，本次更新会被跳过，已有数据保持不变，工作流不会因为这类上游问题失败。脚本使用退出码 `75` 标记这类上游问题；仓库变量缺失、脚本错误或文件写入失败等非上游问题仍会使工作流失败。

## 依赖更新

Dependabot 每周检查 GitHub Actions 依赖并创建更新 PR。仓库通过 `CI` workflow 校验 PR；当 Dependabot PR 关联的所有 checks 都为绿色时，`Dependabot auto-merge` workflow 会自动 squash-merge 该 PR 并删除更新分支。

自动合并 workflow 不 checkout PR 代码，也不执行 PR 分支中的脚本；它只读取 PR 元数据和 check 状态，并且只处理作者为 `dependabot[bot]`、目标分支为默认分支的同仓库 PR。

## 仓库配置

工作流依赖一个 GitHub Actions repository variable：

```text
Name: TVBOX_URL
Value: https://www.xn--sss604efuw.com/tv/
```

配置路径：

```text
Repository -> Settings -> Secrets and variables -> Actions -> Variables
```

由于工作流需要把生成文件提交回仓库，请确保 Actions 具备写入权限：

```text
Repository -> Settings -> Actions -> General -> Workflow permissions -> Read and write permissions
```

## 本地运行

项目只依赖 Python 标准库，可直接运行：

```bash
export TVBOX_URL="https://www.xn--sss604efuw.com/tv/"
export TVBOX_UA="okhttp/3.15"
export OUT_JSON="data/tvbox.json"
export OUT_META="data/tvbox.meta.json"

python3 scripts/extract_tvbox.py
```

运行成功后，脚本会更新 `data/tvbox.json` 和 `data/tvbox.meta.json`，并在终端输出本次解码元数据。
