# Global Study Policy Daily Digest

每日早上 **8:30（北京时间）** 自动抓取全球英语系国家及地区的**留学、高校政策、移民签证、毕业后工作权利**相关新闻，生成**中英双语摘要**并推送到 **企业微信群 + 邮件**。

覆盖地区：美国、英国、澳大利亚、加拿大、新西兰、爱尔兰、香港、新加坡、马来西亚、荷兰（英语授课）、挪威、瑞典、丹麦、芬兰。

## 功能

- 政府/移民局官方 RSS
- **各大高校官网**新闻 RSS（可在 `config/sources.yaml` 增删）
- 关键词过滤：高校政策、移民配套政策、毕业后有偿工作权利（PSW / OPT / PGWP 等）
- 中英双语摘要（Gemini 或 Groq 免费 API）
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
| `LLM_PROVIDER` | 否 | `gemini`（默认）或 `groq` |
| `LLM_API_KEY` | 推荐 | Gemini 或 Groq API Key |

\* 企业微信和邮件至少配置一种；按你的需求建议**两种都配**。

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

### 4. 邮件（Gmail 示例）

1. Google 账号开启两步验证
2. 生成[应用专用密码](https://myaccount.google.com/apppasswords)
3. Secrets 示例：
   - `SMTP_HOST` = `smtp.gmail.com`
   - `SMTP_PORT` = `587`
   - `SMTP_USER` = 你的 Gmail
   - `SMTP_PASSWORD` = 应用专用密码
   - `EMAIL_RECIPIENTS` = `you@example.com,advisor1@example.com`

**QQ 邮箱**：`SMTP_HOST=smtp.qq.com`，`SMTP_PASSWORD` 填 QQ 邮箱授权码（非 QQ 密码）。

### 5. 免费 LLM API

**Gemini（推荐）**

1. 打开 [Google AI Studio](https://aistudio.google.com/apikey) 申请 API Key
2. `LLM_PROVIDER` = `gemini`
3. `LLM_API_KEY` = 你的 Key

**Groq**

1. 打开 [Groq Console](https://console.groq.com/) 申请 API Key
2. `LLM_PROVIDER` = `groq`
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
export LLM_API_KEY="your-key"

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
- Gemini / Groq 免费档：小团队日报通常够用
