# Global Study Policy Daily Digest

每日早上 **8:30（北京时间）** 自动抓取全球英语系国家及地区的**留学、高校政策、移民签证、毕业后工作权利**相关新闻，生成**中英双语摘要**并推送到 **企业微信群 + 邮件**。

覆盖地区：美国、英国、澳大利亚、加拿大、新西兰、爱尔兰、香港、新加坡、马来西亚、荷兰（英语授课）、挪威、瑞典、丹麦、芬兰。

## 功能

- 政府/移民局官方 RSS
- **各大高校官网**新闻 RSS（可在 `config/sources.yaml` 增删）
- 关键词过滤：高校政策、移民配套政策、毕业后有偿工作权利（PSW / OPT / PGWP 等）
- 中英双语摘要（DeepSeek / 通义千问 / 智谱等国内可用 API）
- 企业微信群机器人 + HTML 邮件每日推送
- URL 去重（`data/seen_urls.json`）

## 快速开始

### 1. Fork 本仓库并启用 GitHub Actions

仓库 → **Settings** → **Actions** → **General** → 允许 Actions 运行。

### 2. 配置 Secrets

仓库 → **Settings** → **Secrets and variables** → **Actions** → **New repository secret**

| Secret | 必填 | 说明 |
|--------|------|------|
| `WECHAT_WORK_WEBHOOK_URL` | 是* | 企业微信群机器人 Webhook |
| `SMTP_HOST` | 是* | 如 `smtp.gmail.com` |
| `SMTP_PORT` | 否 | 默认 `587` |
| `SMTP_USER` | 是* | SMTP 用户名 |
| `SMTP_PASSWORD` | 是* | SMTP 密码或应用专用密码 |
| `SMTP_USE_TLS` | 否 | 默认 `true` |
| `EMAIL_FROM` | 否 | 发件人，默认同 `SMTP_USER` |
| `EMAIL_RECIPIENTS` | 是* | 收件人，逗号分隔 |
| `LLM_PROVIDER` | 否 | `deepseek`（默认）、`qwen`、`zhipu`、`groq` |
| `LLM_API_KEY` | 推荐 | DeepSeek 或其他 LLM API Key |

\* 企业微信和邮件至少配置一种；按你的需求建议**两种都配**。

### 推荐组合：企业微信 + Outlook + DeepSeek

下面是一份可直接照填的完整配置指南（**AI 摘要默认使用 DeepSeek，国内可注册使用**）。

#### 一、企业微信群机器人

1. 企业微信 → 打开顾问群 → 右上角 **「…」** → **群机器人** → **添加机器人**
2. 名称：`留学政策日报` → 复制 Webhook
3. GitHub Secret：

| Name | 填什么 |
|------|--------|
| `WECHAT_WORK_WEBHOOK_URL` | `https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=你的key` |

#### 二、Outlook 邮箱

**个人 Outlook（@outlook.com / @hotmail.com / @live.com）**

1. 登录 [Microsoft 账户安全中心](https://account.microsoft.com/security)
2. 开启**两步验证**（若尚未开启）
3. 进入 **高级安全选项** → **应用密码**（或「App passwords」）→ 生成新密码
4. GitHub Secrets：

| Name | 填什么 | 示例 |
|------|--------|------|
| `SMTP_HOST` | `smtp-mail.outlook.com` | 固定值 |
| `SMTP_PORT` | `587` | 固定值 |
| `SMTP_USER` | 你的 Outlook 邮箱 | `you@outlook.com` |
| `SMTP_PASSWORD` | 应用密码（16位，非登录密码） | `abcd efgh ijkl mnop` |
| `EMAIL_FROM` | 发件人（可不填） | 默认同 `SMTP_USER` |
| `EMAIL_RECIPIENTS` | 收件人，英文逗号分隔 | `you@outlook.com,同事@company.com` |

**Microsoft 365 企业邮箱（@company.com）**

| Name | 填什么 |
|------|--------|
| `SMTP_HOST` | `smtp.office365.com` |
| `SMTP_PORT` | `587` |
| `SMTP_USER` | 你的企业邮箱完整地址 |
| `SMTP_PASSWORD` | 邮箱密码或应用密码 |

> 若企业 IT 禁用了 SMTP 基本认证，需联系管理员开启，或改用已开启 SMTP 的邮箱。

#### 三、DeepSeek API（国内可用，推荐）

1. 打开 [DeepSeek 开放平台](https://platform.deepseek.com/)
2. 注册账号 → **API Keys** → 创建 Key
3. 新用户通常有免费额度，小团队日报足够用
4. GitHub Secrets：

| Name | 填什么 |
|------|--------|
| `LLM_API_KEY` | 你的 DeepSeek Key（形如 `sk-...`） |
| `LLM_PROVIDER` | `deepseek`（可不填，默认就是 deepseek） |

**其他国内可选 LLM（二选一）**

| LLM_PROVIDER | 申请地址 | 说明 |
|--------------|----------|------|
| `qwen` | [阿里云百炼 / 通义](https://bailian.console.aliyun.com/) | 填 `DASHSCOPE_API_KEY` 或 `LLM_API_KEY` |
| `zhipu` | [智谱开放平台](https://open.bigmodel.cn/) | 填 `ZHIPU_API_KEY` 或 `LLM_API_KEY` |

#### 四、全部 Secrets 清单（复制对照）

配置完成后，GitHub Actions Secrets 中应有：

```text
WECHAT_WORK_WEBHOOK_URL = https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=xxxx
SMTP_HOST               = smtp-mail.outlook.com
SMTP_PORT               = 587
SMTP_USER               = you@outlook.com
SMTP_PASSWORD           = 你的Outlook应用密码
EMAIL_RECIPIENTS        = you@outlook.com,同事A@outlook.com
LLM_API_KEY             = sk-你的deepseek密钥
LLM_PROVIDER            = deepseek
```

#### 五、测试

1. 合并 PR 到 `main` 分支
2. 仓库 → **Actions** → **Daily Study Policy Digest** → **Run workflow**
3. 约 1～3 分钟后检查：
   - 企业微信群收到 Markdown 日报
   - Outlook 收件箱（及垃圾箱）收到 HTML 邮件

**邮件发不出去？**

- 确认用的是**应用密码**，不是 Outlook 登录密码
- 确认 `SMTP_HOST` 个人邮箱用 `smtp-mail.outlook.com`，企业邮箱用 `smtp.office365.com`
- 查看 Actions 日志中 `SMTP` 相关报错

**中文摘要显示「请参阅原文链接」？**

- 检查 `LLM_API_KEY` 是否正确、账户是否有余额
- 确认 `LLM_PROVIDER` 为 `deepseek` 或未填写

### 3. 企业微信群机器人

1. 在企业微信中创建或打开顾问团队群聊
2. 群聊右上角 **「…」** → **群机器人** → **添加机器人**
3. 给机器人起名，例如：`留学政策日报`
4. 复制 Webhook 地址，形如：

```text
https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
```

5. 在 GitHub Secrets 中添加：
   - Name：`WECHAT_WORK_WEBHOOK_URL`
   - Secret：粘贴上面的完整 Webhook 地址

> 注意：Webhook 地址包含密钥，不要公开分享。若泄露，在企业微信机器人设置里重置。

### 4. 邮件（Outlook / Gmail 示例）

**Outlook 个人邮箱**：见上方「推荐组合」章节。

**Gmail 示例**

1. Google 账号开启两步验证
2. 生成[应用专用密码](https://myaccount.google.com/apppasswords)
3. Secrets 示例：
   - `SMTP_HOST` = `smtp.gmail.com`
   - `SMTP_PORT` = `587`
   - `SMTP_USER` = 你的 Gmail
   - `SMTP_PASSWORD` = 应用专用密码
   - `EMAIL_RECIPIENTS` = `you@example.com,advisor1@example.com`

**QQ 邮箱**：`SMTP_HOST=smtp.qq.com`，`SMTP_PASSWORD` 填 QQ 邮箱授权码（非 QQ 密码）。

### 5. AI 摘要 API（国内可用）

**DeepSeek（默认推荐）**

1. 打开 [DeepSeek 开放平台](https://platform.deepseek.com/) 注册并创建 API Key
2. `LLM_PROVIDER` = `deepseek`（可不填）
3. `LLM_API_KEY` = 你的 Key

**通义千问（阿里云）**

1. 打开 [阿里云百炼](https://bailian.console.aliyun.com/) 开通 DashScope
2. `LLM_PROVIDER` = `qwen`
3. `LLM_API_KEY` = DashScope API Key

**智谱 GLM**

1. 打开 [智谱开放平台](https://open.bigmodel.cn/) 申请 API Key
2. `LLM_PROVIDER` = `zhipu`
3. `LLM_API_KEY` = 你的 Key

未配置 LLM 时仍可运行，但中文摘要会降级为「请参阅原文链接」。

### 6. 手动测试

Actions 页 → **Daily Study Policy Digest** → **Run workflow**。

## 本地运行

```bash
pip install -r requirements.txt

export WECHAT_WORK_WEBHOOK_URL="https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=..."
export SMTP_HOST="smtp.gmail.com"
export SMTP_USER="you@gmail.com"
export SMTP_PASSWORD="your-app-password"
export EMAIL_RECIPIENTS="you@gmail.com"
export LLM_API_KEY="sk-your-deepseek-key"
export LLM_PROVIDER="deepseek"

python -m src.main
```

## 自定义信源

编辑 `config/sources.yaml`。高校与政府机构优先使用 `site:大学官网域名` 的 Google News RSS（免费、稳定），格式示例：

```yaml
- name: Imperial College London
  type: university
  url: "https://news.google.com/rss/search?q=site:imperial.ac.uk+international+student&hl=en-GB&gl=GB&ceid=GB:en"
```

`type` 可选：

- `immigration` — 移民/签证机构
- `education` — 教育主管部门
- `university` — 高校官网

荷兰高校源会自动额外要求 `international student` / `English-taught` 等关键词（见 `config/keywords.yaml`）。

## 推送时间

GitHub Actions cron：`30 0 * * *`（UTC）= **每天北京时间 08:30**。

## 免责声明

本工具聚合公开信息，仅供参考，不构成法律或移民建议。请以各国官方及院校官网为准。

## 费用

- GitHub Actions：公开仓库免费额度内通常 $0
- 企业微信群机器人：免费
- Gmail SMTP：免费
- DeepSeek / 通义 / 智谱：新用户通常有免费额度，小团队日报成本低
