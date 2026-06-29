# QQ 群管机器人

这是一个面向零基础用户的 QQ 群管理机器人控制台。用户只需要打开网页、填写信息、点开关；不需要安装开发环境，也不需要打开命令窗口。

## 用户使用流程

1. 打开 CloudStudio 控制台网址。
2. 填写 Railway 后端接口、控制台密钥和机器人 QQ 号。
3. 点“保存账号”，再点“开始托管”。
4. 如果网页显示二维码、滑块、设备锁或验证码提示，由本人完成 QQ 官方验证。
5. 把机器人 QQ 拉进群，控制台显示在线后即可使用。

## 群内能力

- @机器人 你好：AI 聊天
- @机器人 看看这张图：识图
- @机器人 画个内容：AI 生图
- @机器人 生成视频内容：AI 生视频
- 入群欢迎、关键词回复、违禁词处理都可以在网页里开关和编辑。

## 安全约定

- 敏感登录信息不写入代码，不打印到日志。
- Agnes API 密钥只放在 Railway 后端变量里，静态网页不包含完整密钥。
- 日志接口会自动遮挡 API key、token、authorization、password 等敏感内容。
- Lagrange 登录以扫码/快速登录为主；遇到验证码、滑块或设备锁时暂停等待本人处理。

## 部署组件

- Railway：运行 Lagrange.OneBot、NoneBot2 和 FastAPI 后端。
- CloudStudio：托管单页控制台 `index.html`。
- GitHub：作为 Railway 和 CloudStudio 的网页部署来源。

## 后端接口

- `GET /health`：后端健康状态。
- `GET /status`：机器人登录、托管、群数量和消息统计状态。
- `POST /bot/account`：保存机器人 QQ 号并生成 Lagrange 配置。
- `POST /bot/hosting/start`：开始托管。
- `POST /bot/hosting/stop`：停止托管。
- `GET /config` 和 `POST /config`：读取和保存功能开关、欢迎语、违禁词、回复规则。
- `GET /logs`：读取脱敏日志。
- `GET /api-status`：读取后端 API 配置状态。

## 本地旧版

仓库里保留了早期本地 NapCat 控制台文件，作为旧版备用入口。正式交付和零基础使用以 Railway + CloudStudio 网页控制台为准。
