<div align="center">

# ZhiHuiShu · AI 智慧课程助手

**一个可无人监督运行的智慧树 AI 智慧课程自动化工具集**

基于 Webdriver 与 Python 实现，包含「视频自动播放」与「去提升 + 题库自动答题」两条链路

![Python](https://img.shields.io/badge/Python-3.9-3776AB?logo=python&logoColor=white)
![Selenium](https://img.shields.io/badge/Selenium-4.6%2B-43B02A?logo=selenium&logoColor=white)
![Platform](https://img.shields.io/badge/Platform-Windows-0078D6?logo=windows&logoColor=white)
![Purpose](https://img.shields.io/badge/Purpose-Study%20%26%20Research-orange)

[项目主页](https://github.com/Crazzzwind/ZhiHuiShu-ai-smart-course-Assistant/) · [脚本一览](#-脚本一览) · [逐个脚本用法](#-逐个脚本用法) · [已知问题](#-已知问题) · [免责声明](#-免责声明)

</div>

---

## 目录

- [项目简介](#-项目简介)
- [脚本一览](#-脚本一览)
- [功能特性](#-功能特性)
- [快速开始](#-快速开始)
  - [环境要求与依赖](#环境要求与依赖)
  - [通用前置：改 URL / 登录 / 回车](#通用前置改-url--登录--回车)
- [逐个脚本用法](#-逐个脚本用法)
  - [① videos.py · 视频自动播放](#-videospy--视频自动播放)
  - [② questions-local-ai.py · 本地 Ollama 答题](#-questions-local-aipy--本地-ollama-答题)
  - [③ questions-local-ai-Ollama Web Search.py · 本地 AI + 联网搜索](#-questions-local-ai-ollama-web-searchpy--本地-ai--联网搜索)
  - [④ questions-online-ai-Deepseek-FreeDeepseekAPI.py · 免费 Deepseek 代理](#-questions-online-ai-deepseek-freedeepseekapipy--免费-deepseek-代理)
  - [⑤ questions-online-ai-API.py · 通用 OpenAI 兼容中转](#-questions-online-ai-apipy--通用-openai-兼容中转)
- [运行顺序建议](#-运行顺序建议)
- [AI 后端配置](#-ai-后端配置)
- [公共配置说明](#-公共配置说明)
- [运行日志速查](#-运行日志速查)
- [已知问题](#-已知问题)
- [写在最后](#-写在最后)
- [免责声明](#-免责声明)

---

## 项目简介

这是一个**可无人监督**的自动化项目，由 Python 编写，基于 **Webdriver** 驱动浏览器模拟用户操作，把智慧树「AI 智慧课程」的学习流程拆成两条链路：

> **链路一（视频）**：扫描进度为 0% 的章节 → 逐个点击 → 播放必学资源区的视频 / 图书资源 → 自动切到下一个资源与下一个章节。
>
> **链路二（答题）**：扫描进度低于 95% 的章节 → 两段式「去提升」→ 进入题库 → 逐题抓取题干与选项 → 交给 AI 作答 → 提交并校验，未通过则补做。

**为什么有 5 个脚本？** 因为「播视频」不需要 AI，而「答题」需要答案来源。答案来源分成 **本地模型**、**本地模型 + 联网搜索**、**免费在线代理**、**任意中转 API** 四种，抓题与提交逻辑完全相同，所以用 4 个几乎一样的脚本各配一套后端，你只需挑一个能跑起来的。

---

## 脚本一览

| # | 脚本 | 作用 | 答案来源 | 需额外预置 | 速度 |
| :-: | :--- | :--- | :--- | :--- | :-: |
| ① | `videos.py` | 视频 / 图书资源自动播放、自动切章 | 无（纯 Webdriver） | 无 | 快（受视频时长限制） |
| ② | `questions-local-ai.py` | 去提升 + 题库自动答题 | 本地 **Ollama**（默认 `deepseek-r1:7b`） | Ollama + 模型 | 中（取决于显卡） |
| ③ | `questions-local-ai-Ollama Web Search.py` | 同上 + 答题前联网搜索 | 本地 **Ollama** + **Ollama Web Search** | Ollama + `OLLAMA_API_KEY` | 中偏慢（多一次搜索往返） |
| ④ | `questions-online-ai-Deepseek-FreeDeepseekAPI.py` | 同上（思考模型） | **FreeDeepseekAPI** 本地代理 | Node + 代理项目 | 慢（每题停 10~20s，每 2 章停 500s） |
| ⑤ | `questions-online-ai-API.py` | 同上 | 任意 **OpenAI 兼容中转** | 中转 Key / Base URL / 模型名 | 中（无章节停顿，但受中转限流） |

**怎么选：**

- 只想先把视频刷完 → ①
- 有显卡、不想联网 → ②
- 题库偏事实性（人名、年份、术语），本地模型容易答错 → ③
- 电脑配置差、不想装模型，但能跑 Node → ④
- 手上已有中转 API（ChatAnywhere、各类 `sk-` 中转站） → ⑤

> ⚠️ **②③④⑤ 只能选一个跑**：它们操作同一个课程页面，同时开会互相抢浏览器，进度也会打架。
>
> ⚠️ `videos.py` 与答题脚本要**分两次运行**，一个跑完再跑另一个。

---

## 功能特性

### 视频链路（① `videos.py`）

| 功能 | 说明 |
| :--- | :--- |
| **自动播放** | 打开课程后点击必学资源区内的资源，自动开始播放 |
| **自动切资源** | 单个资源处理完后自动回到资源列表，处理下一个 |
| **资源指纹去重** | 以 `标题 + 类型 + 同名序号` 生成指纹，避免重复点击同一资源 |
| **断点恢复** | 资源列表消失（页面被跳走）时，重新打开课程 URL 并按标题重进该章节 |
| **视频就绪判定** | 先等 `currentTime > 0.5s` 确认真的在播，再等 `paused` 连续 3 次稳定判定本节结束 |
| **失败重试** | 同一视频连续 3 次检测失败才强制标记跳过，避免卡死 |
| **图书 / 其他资源** | 随机停留 5~15 秒，页面被跳转则自动 `back()` 返回 |

### 答题链路（②③④⑤）

| 功能 | 说明 |
| :--- | :--- |
| **低进度章节扫描** | 读取 `.el-progress__text`，**进度 < 95% 即可处理**（旧版只认 0%） |
| **两段式「去提升」** | 先点 `.simplified-mastery__action`，再点 `.improve-btn`，任一失败即跳过该章 |
| **全题型作答** | 单选、多选、判断、填空（按空位数量对齐答案） |
| **答题卡遍历** | 依据 `.custom-tree-answer-normal` 的 `answer` / `no-answer` 状态跳过已答题目 |
| **干扰节点自适应** | 点进去抓不到题干的节点自动标记为干扰项，后续不再尝试 |
| **投票机制** | 同一题采样 3 次取多数票（填空按 NFKC 归一化后逐空投票） |
| **提交与校验** | 提交后监听「还有题目没有完成」弹窗，最多补做 3 轮 |
| **可选视觉模式** | 截取题目区域交给多模态模型识别（默认关闭，需 `pillow`） |

### 各后端独有能力

| 能力 | ② 本地 | ③ 搜索 | ④ 免费代理 | ⑤ 中转 |
| :--- | :-: | :-: | :-: | :-: |
| 联网搜索增强 | — | ✅ | — | — |
| 思考模型 `reasoning_content` / `thinking` 兜底 | ✅ | ✅ | ✅ | ✅ |
| `response_format` 不支持时自动降级 | — | — | ✅ | ✅ |
| 429 限流退避 | — | — | ✅ | ✅ |
| 投票间隔随机停顿 | — | — | ✅ 10~20s | — |
| 每 N 章强制停顿 | — | — | ✅ 2 章 / 500s | — |

---

## 快速开始

### 环境要求与依赖

| 项目 | 要求 |
| :--- | :--- |
| 操作系统 | Windows（脚本硬编码 **Edge** WebDriver，可在 `IDLE` 下运行） |
| Python | 3.9（推荐） |
| 浏览器驱动 | 无需手动配置，Selenium 4.6+ 的 **Selenium Manager** 会自动下载匹配驱动 |

**依赖矩阵：**

| 脚本 | `selenium` | `ollama` | `openai` | 其它 |
| :--- | :-: | :-: | :-: | :--- |
| ① `videos.py` | ✅ | — | — | — |
| ② `questions-local-ai.py` | ✅ | ✅ | — | Ollama 服务 |
| ③ `questions-local-ai-Ollama Web Search.py` | ✅ | ✅ | — | `OLLAMA_API_KEY` |
| ④ `questions-online-ai-Deepseek-FreeDeepseekAPI.py` | ✅ | — | ✅ | FreeDeepseekAPI 代理 |
| ⑤ `questions-online-ai-API.py` | ✅ | — | ✅ | 中转 Key |

```bash
pip install selenium                      # 全都要
pip install ollama                        # ②③
pip install openai                        # ④⑤
pip install pillow                        # 可选，只有开视觉模式才需要
```

> 想换 Chrome：把每个脚本里的 `from selenium.webdriver.edge.options import Options` 换成 `chrome.options`，并把 `webdriver.Edge` 换成 `webdriver.Chrome`。

### 通用前置：改 URL / 登录 / 回车

**①** 每个脚本顶部都有 `URL`，三个占位字段需全部替换：

```python
URL = ("https://ai-smart-course-student-pro.zhihuishu.com/"
       "singleCourse/knowledgeStudy/新课程ID/新章节ID"
       "?mapUid=新的mapUid")
```

| 占位字段 | 替换为 |
| :--- | :--- |
| `新课程ID` | 你课程的实际课程 ID |
| `新章节ID` | 你课程的实际章节 ID |
| `新的mapUid` | 链接中的实际 `mapUid` 参数 |

> 答题脚本里有的已经填了作者自己的示例链接，**务必换成你自己的**，否则会在别人的课程里乱点。

**②** 浏览器窗口打开后，**手动登录账号**，并把页面停在「课程目录 / 左侧章节列表」那页。

**③** 回到 `IDLE` 或命令行，按 `Enter` 开始。之后全程无需干预，跑完脚本会自动 `quit()` 关闭浏览器。

---

## 逐个脚本用法

### ① videos.py · 视频自动播放

**做什么**

```text
打开课程 → 回车 → 扫出所有进度 0% 的章节 → 逐章点击
→ 内层扫必学资源区 → 逐个点开资源（视频等暂停 / 图书停留 5~15s）
→ 本章资源处理完 → 下一章 → 全部结束
```

**用之前要改的**

| 位置 | 变量 | 改什么 |
| :--- | :--- | :--- |
| 第 9 行 | `URL` | 替换三个占位字段，必改 |
| `try:` 块内 | `MAX_CHAPTERS = 100` | 章节上限，课程章节多可调大 |
| `try:` 块内 | `MAX_INNER = 200` | 单章资源上限 |
| `wait_video_paused` | `timeout_started=120` | 点开后等待视频起播的秒数，网慢可调大 |
| `wait_video_paused` | `timeout_paused=7200` | 单个视频最长等待（默认 2 小时） |

**启动**

```bash
python videos.py
```

**运行中你会看到**

```text
[OK] 页面已打开
>>> 如需登录，请先登录，然后按回车继续...        ← 在这里按回车
[OUTER] 当前 0% 章节 12 个，其中未尝试 12 个
[CHAPTER 1/100] 处理: 第一章 xxx
[INNER SCAN] 共 5 个，未处理 5 个 (video=3, book=1, other=1)
[INNER] 处理第 1 个：video
[VIDEO] 等待视频开始播放...
[VIDEO] 视频已开始播放，等待暂停...
[VIDEO] 视频暂停稳定
[INNER] 资源列表可访问，共 5 个
...
[ALL DONE] 共处理 12 个章节
[OK] 浏览器已关闭
```

**注意**

- 只识别**进度严格为 0%**（`width:0%`）的章节，已有一点点进度的章节会跳过
- 必学资源区由「必学资源」「选学资源」两个标题夹定，**选学区不会被点击**
- 如果日志一直是 `[WARN] 左列未加载，退出外层`，说明左侧章节列表处于折叠状态，先手动展开再回车
- 建议不要让 Edge 窗口最小化，脚本靠元素可见性判断资源与视频状态

---

### ② questions-local-ai.py · 本地 Ollama 答题

**做什么**

```text
扫进度<95% 的章节 → 点击章节 → 去提升① → 去提升②
→ 答题卡逐题：抓题干/选项 → 本地模型答 → 点选/填空
→ 提交并校验 → 有漏题就补做（最多 3 轮）→ 下一章
```

**用之前要改的**

| 位置 | 变量 | 改什么 |
| :--- | :--- | :--- |
| 第 22 行 | `URL` | 三个占位字段，必改 |
| 第 67 行 | `OLLAMA_MODEL` | 默认 `deepseek-r1:7b`；可换 `qwen3.5:4b` 等，**名字必须与 `ollama list` 一致** |
| 第 30 行 | `PROGRESS_THRESHOLD` | 默认 `95`，调大能覆盖更多章节 |
| 第 77 行 | `VOTE_SAMPLES` | 默认 `3`；机器慢可改 `1` 关闭投票 |

**准备模型**

```bash
ollama serve                     # 安装后通常开机自启，托盘有图标即可跳过
ollama pull deepseek-r1:7b       # 或 ollama pull qwen3.5:4b
ollama list                      # 确认名字
```

**启动**

```bash
python questions-local-ai.py
```

**运行中你会看到**

```text
[OLLAMA] 服务在线，可用模型: ['deepseek-r1:7b', ...]
[OK] 纯文本模式（模型=deepseek-r1:7b），每题投票 3 次
[OK] 页面已打开
>>> 如需登录，请先登录，然后按回车继续...        ← 在这里按回车
[START] 第1轮 | 进度<95 总数=12 未尝试=12
[CHAPTER 1/100] 点击: 第一章 xxx (进度=0.0 原文='0')
[ACTION] 已点击
[IMPROVE] 已点击
[BANK] 答题卡节点 20 个，遍历上限 20，初始 answer class 数=0
[BANK 1/20] 作答
[VOTE] 第1/3次 single: ['A']
[VOTE] 第2/3次 single: ['A']
[VOTE] single 票数=['A']x3 → 取=['A']
[ANSWER] single 点击 1 个，期望 ['A']
[SUBMIT] 普通点击成功
[SUBMIT] 页面已跳转，视为提交成功
[STATS] ...
[ALL DONE] 共处理 12 个章节
```

**注意**

- 启动探活失败会打印 `[OLLAMA FAIL] 服务不可达` 或 `未找到模型`，此时**脚本仍会继续跑**，但答题环节会全部空手
- 首次调用模型要加载权重（几十秒），`OLLAMA_KEEP_ALIVE = "10m"` 保证 10 分钟内不重复加载
- **没有章节防风控停顿**，是三个答题脚本里最快的一个
- 若某章处理失败，重跑脚本会重新尝试（`tried_titles` 只在本次运行内有效）

---

### ③ questions-local-ai-Ollama Web Search.py · 本地 AI + 联网搜索

**做什么**

与 ② 完全相同的抓题、作答、提交流程，区别是**每道题作答前先拿题干去搜索**：

```text
题干 → ollama.web_search(最多 3 条) → 标题+正文片段+来源拼进 prompt
→ 本地模型结合搜索结果作答 → 投票（仅第 1 次带搜索，后两次纯模型）
```

**用之前要改的**

| 位置 | 变量 | 改什么 |
| :--- | :--- | :--- |
| 第 23 行 | `URL` | 三个占位字段，必改 |
| 第 72 行 | `OLLAMA_API_KEY` | 读环境变量，**必须先在系统里设置** |
| 第 66 行 | `OLLAMA_MODEL` | 默认 `qwen3.5:4b`，按需换 |
| 第 73 行 | `WEB_SEARCH_ENABLED` | `True` 开启搜索；`False` 退回纯本地 |
| 第 74 行 | `WEB_SEARCH_MAX_RESULTS` | 默认 3 条（上限 10） |
| 第 75 行 | `WEB_SEARCH_CONTENT_LIMIT` | 每条结果进 prompt 的字符数，默认 300 |

**设置 Key（三种方式任选）**

```bash
set OLLAMA_API_KEY=你的key                 # cmd，只对当前窗口有效
setx OLLAMA_API_KEY 你的key                # cmd，永久写入，需重开窗口
$env:OLLAMA_API_KEY="你的key"              # PowerShell，只对当前会话有效
```

**启动**

```bash
python "questions-local-ai-Ollama Web Search.py"
```

> 文件名带空格，**必须加引号**；在 IDLE 里直接打开运行则不受影响。

**运行中你会看到**

```text
[OK] Web Search 已启用（每次答题前搜索，投票仅首次触发搜索）
[SEARCH] 找到 3 条结果，已注入上下文
[VOTE] 第1/3次 single (带搜索): ['B']
[VOTE] 第2/3次 single (纯模型): ['B']
[VOTE] 第3/3次 single (纯模型): ['B']
```

**注意**

- 未设置 Key 时打印 `[WARN] WEB_SEARCH_ENABLED=True 但 OLLAMA_API_KEY 为空，搜索将降级跳过`，答题继续
- 搜索查询用题干原文（截断到 120 字符），题干很长或含大量符号时效果会变差
- 搜索失败自动降级为纯模型作答，不中断主流程
- 比 ② 每题多一次网络往返，整体更慢，但事实性题目的命中率通常更高

---

### ④ questions-online-ai-Deepseek-FreeDeepseekAPI.py · 免费 Deepseek 代理

**做什么**

流程同 ②，答案来自 **FreeDeepseekAPI 本地代理**（OpenAI 兼容，默认 `http://127.0.0.1:9655/v1`）。特点是**节奏极慢、防风控最狠**。

**用之前要改的**

| 位置 | 变量 | 改什么 |
| :--- | :--- | :--- |
| 第 23 行 | `URL` | 三个占位字段，必改 |
| 第 65~67 行 | `FREEDEEPSEEK_API_KEY` / `BASE_URL` / `MODEL` | 一般不用改；改过端口要同步 |
| 第 80~81 行 | `VOTE_PAUSE_MIN` / `VOTE_PAUSE_MAX` | 投票间隔 10~20 秒，想加速可调小 |
| 第 84~85 行 | `CHAPTER_PAUSE_EVERY` / `CHAPTER_PAUSE_SECONDS` | 每 2 章停 500 秒 |
| 第 79 行 | `VOTE_SAMPLES` | 默认 3，改 1 能省掉 2/3 的等待 |

**准备代理（另开一个命令行窗口，不要关）**

```bash
# 进入 FreeDeepseekAPI 代理项目目录
npm run auth
npm run dashboard
```

启动脚本时会自动 `models.list()` 探活；想先手动确认代理是否在听：

```bash
curl http://127.0.0.1:9655/v1/models
```

**启动**

```bash
python questions-online-ai-Deepseek-FreeDeepseekAPI.py
```

**运行中你会看到**

```text
[AI] FreeDeepseekAPI 在线，可用模型: [...]
[OK] FreeDeepseekAPI 模式 | 模型=deepseek-v4-flash-thinking | 每题投票 3 次
[ACTION] 已点击
[IMPROVE] 已点击
[VOTE] 第1/3次 single: ['C']
[PAUSE] 防风控等待 14.7s ...                    ← 每次投票之间都会停
[VOTE] 第2/3次 single: ['C']
...
[PAUSE] 已完成 2 个章节，防风控强制停顿 500 秒 ...  ← 每 2 章停一次
```

**注意**

- 这是**最慢的一个**：每题 3 次采样 ×（思考耗时 + 10~20 秒间隔），每 2 章再加约 8 分钟停顿，整门课通常要跑一夜，适合晚上挂着
- 思考模型的 `content` 可能为空，脚本会从 `reasoning_content` 里抠 JSON，日志提示 `[AI] content 空，从 reasoning_content 抠出`
- 若代理不支持 `response_format`，会打印 `该接口不支持 response_format，去掉重试` 并自动重发
- 探活失败会提示 `请先运行: npm run auth  然后  npm run dashboard`
- 代理窗口关掉后答题环节就全空，中途别关

---

### ⑤ questions-online-ai-API.py · 通用 OpenAI 兼容中转

**做什么**

流程同 ②，答案来自**任意 OpenAI 兼容的云端中转**（脚本注释里叫 ChatAnywhere）。适合手上已有 `sk-` 中转 Key、不想在本地装模型的场景。

**用之前要改的（三个占位必须全改）**

| 位置 | 变量 | 改成 |
| :--- | :--- | :--- |
| 第 66 行 | `CHATANYWHERE_API_KEY` | 你的中转 Key，形如 `sk-xxxx`；**保持默认 `sk-你的Key` 会直接探活失败** |
| 第 67 行 | `CHATANYWHERE_BASE_URL` | 中转的接口地址，**一般要带 `/v1`**，如 `https://api.xxx.com/v1` |
| 第 68 行 | `CHATANYWHERE_MODEL` | 该中转支持的模型名，如 `gpt-4o-mini`、`deepseek-chat`，必须与其文档一致 |
| 第 71 行 | `AI_TIMEOUT` | 默认 60 秒；网络差或模型慢就调大 |
| 第 72 行 | `AI_USE_JSON_FORMAT` | 默认 `True`；中转不支持 `response_format` 会自动降级，无需手动关 |

**启动**

```bash
python questions-online-ai-API.py
```

**运行中你会看到**

```text
[AI] ChatAnywhere 在线，模型数=3，样本=['gpt-4o-mini', ...]
[OK] 云端纯文本模式（模型=gpt-4o-mini），每题投票 3 次
[VOTE] 第1/3次 multiple: ['A','C']
[VOTE] multiple 票数=['A','C']x3 → 取=['A','C']
```

**注意**

- 探活的判断是「Key 为空或仍以 `sk-你的` 开头」——**没改 Key 会直接 `[AI FAIL] CHATANYWHERE_API_KEY 未配置`**
- 模型名不在中转返回的列表里只告警不退出（部分中转不返回全量模型）
- 命中 429 会自动退避 `5 × 尝试次数` 秒，连续限流时会有明显停顿
- **没有章节级停顿**，比 ④ 快得多，但请求更密集，免费中转容易被限流
- 想用视觉模式：把 `AI_VISION = False and _HAS_PIL` 改成 `True`，并装 `pip install pillow`，同时中转要支持多模态

---

## 运行顺序建议

1. **先跑 ①**，把视频章节刷到 100%。刷完后再跑一遍会提示「所有 0% 章节都已尝试」
2. **再选一个答题脚本（②③④⑤ 之一）**，处理进度 <95% 的章节（通常就是「去提升」任务）
3. 想补漏：**重跑同一个答题脚本**。`tried_titles` 只在单次运行内有效，上次失败的章节会被重新尝试
4. 答题脚本跑完会自动关闭浏览器，换脚本前先确认上一个已经退出

---

## AI 后端配置

### Ollama（本地，②③ 使用）

```bash
ollama serve
ollama pull deepseek-r1:7b
ollama list
```

| 配置项 | 默认 | 说明 |
| :--- | :--- | :--- |
| `OLLAMA_MODEL` | `deepseek-r1:7b`（②）/ `qwen3.5:4b`（③） | 必须是 `ollama list` 里出现过的名字 |
| `OLLAMA_TEMPERATURE` | `0` | 答题场景建议保持 0 |
| `OLLAMA_KEEP_ALIVE` | `"10m"` | 模型驻留时长，避免每题重新加载 |
| `OLLAMA_RETRY` | `2` | 单题失败重试次数 |
| `OLLAMA_VISION` | `False` | 需 `pillow` + 多模态模型，默认强制关闭 |

### Ollama Web Search（③ 使用）

| 配置项 | 默认 | 说明 |
| :--- | :--- | :--- |
| `OLLAMA_API_KEY` | 空 | 从环境变量读取，搜索的必需前提 |
| `WEB_SEARCH_ENABLED` | `True` | 总开关 |
| `WEB_SEARCH_MAX_RESULTS` | `3` | 每次搜索返回条数（上限 10） |
| `WEB_SEARCH_CONTENT_LIMIT` | `300` | 每条结果截取字符数 |

### FreeDeepseekAPI（④ 使用）

| 配置项 | 默认 | 说明 |
| :--- | :--- | :--- |
| `FREEDEEPSEEK_BASE_URL` | `http://127.0.0.1:9655/v1` | 本地代理地址 |
| `FREEDEEPSEEK_API_KEY` | `sk-any-text` | 本地代理不校验，随便填 |
| `FREEDEEPSEEK_MODEL` | `deepseek-v4-flash-thinking` | 与代理暴露的模型名一致 |
| `AI_TIMEOUT` | `120` | 思考模型耗时长，别给太小 |
| `AI_USE_JSON_FORMAT` | `True` | 不支持时自动降级 |

### 通用中转（⑤ 使用）

| 配置项 | 默认 | 说明 |
| :--- | :--- | :--- |
| `CHATANYWHERE_BASE_URL` | `https://xxxx.com` | 中转地址，一般带 `/v1` |
| `CHATANYWHERE_API_KEY` | `sk-你的Key` | 必改，否则直接探活失败 |
| `CHATANYWHERE_MODEL` | `xxxx` | 该中转支持的模型名 |
| `AI_TEMPERATURE` | `0` | 云端版会真正传 temperature |
| `AI_TIMEOUT` | `60` | 秒 |

---

## 公共配置说明

### ②③④⑤ 共享（改一份要同步四份）

| 配置项 | 默认 | 说明 |
| :--- | :--- | :--- |
| `PROGRESS_THRESHOLD` | `95` | 进度低于该值才处理 |
| `SEL_ACTION_BTN` | `.simplified-mastery__action` | 第一次「去提升」按钮 |
| `SEL_IMPROVE_BTN` | `.improve-btn` | 第二次「去提升」按钮 |
| `VOTE_SAMPLES` | `3` | 每题采样次数，`1` = 关闭投票 |
| `FILL_USE_THINKING` | `False` | 填空题是否启用思考模式（②③） |
| `SUBMIT_RETRY` | `3` | 提交重试轮数 |
| `MAX_CHAPTERS` | `100` | 外层章节上限 |
| `ANSWER_CARD_OFFSET` | `0` | 答题卡节点截断量，`0` = 靠抓取失败识别干扰节点 |
| `WAIT_AFTER_CLICK` | `5` | 点击章节后等待秒数 |
| `WAIT_AFTER_ACTION` / `WAIT_AFTER_IMPROVE` | `5` | 两次去提升之间的等待 |
| `TIMEOUT_CHAPTER_LIST` | `60` | 左侧章节列表加载超时 |
| `WAIT_BEFORE_SUBMIT` / `WAIT_AFTER_SUBMIT` | `3` / `8` | 提交前后等待 |
| `SCREENSHOT_QUALITY` | `60` | 视觉模式截图 JPEG 质量 |

> **注意**：`videos.py` 的 `URL`、`MAX_CHAPTERS`、`MAX_INNER`、两段 `timeout_*` 是独立的，与上面这组无关。

---

## 运行日志速查

| 标签 | 含义 |
| :-: | :--- |
| `[OK]` | 初始化或关键步骤成功 |
| `[OUTER]` / `[CHAPTER]` | 外层章节扫描与进度 |
| `[INNER]` / `[INNER SCAN]` | 内层资源扫描与逐个处理（①） |
| `[VIDEO]` | 视频起播判定与暂停判定（①） |
| `[REENTER]` | 资源列表丢失后重新进入章节（①） |
| `[ACTION]` / `[IMPROVE]` | 两段式去提升的点击结果 |
| `[BANK]` | 答题卡遍历进度、干扰节点、提交轮次 |
| `[VOTE]` | 每题多次采样与最终票数 |
| `[ANSWER]` / `[FILL WARN]` | 最终答案、填空题补位与截断 |
| `[SUBMIT]` | 提交结果与弹窗内容 |
| `[SEARCH]` / `[SEARCH WARN]` | 联网搜索命中与降级（③） |
| `[PAUSE]` | 防风控停顿（④） |
| `[OLLAMA]` / `[AI]` | 后端探活与推理日志（②③ / ④⑤） |
| `[STATS]` | 结束时的逐章统计汇总 |
| `[WARN]` / `[FAIL]` | 单步失败，通常降级或跳过，不影响全局 |

---

## 已知问题

| # | 问题 | 说明 |
| :-: | :--- | :--- |
| 1 | 仅支持 Windows + Edge | 5 个脚本都硬编码 `webdriver.Edge`，换浏览器需改初始化部分 |
| 2 | 视频链路只认 0% | `videos.py` 按 `width:0%` 筛选章节，已有进度的会跳过；答题脚本已放宽到 95% |
| 3 | 需分两次运行 | 视频与答题是两个独立脚本，跑完一个再跑另一个 |
| 4 | 答题脚本四选一 | ②③④⑤ 逻辑重复，同时跑会抢浏览器与课程页 |
| 5 | 视觉模式默认关闭 | `OLLAMA_VISION` / `AI_VISION` 均为 `False and _HAS_PIL`，需手动开启并装 `pillow` |
| 6 | 干扰节点靠失败识别 | 依赖「抓不到题干」判定，题库结构变化时可能误判并跳过正常题目 |
| 7 | 正确率依赖模型 | 投票只能降低随机波动；填空题答案数量与输入框不一致时会补齐或截断 |
| 8 | ④ 极慢 | 每题间隔 10~20 秒 + 每 2 章停 500 秒，适合挂机；②⑤ 无章节停顿 |
| 9 | ⑤ 的 Key 有占位校验 | 保持 `sk-你的Key` 会直接探活失败，必须换成真实 Key |
| 10 | 模型名匹配较宽松 | 本地版用子串匹配、云端版只告警不退出，可能出现「探活通过但作答全空」 |

---

## 写在最后

**为什么这个代码这么差？**

本项目大部分代码由「吃白饭的大肥鱼」负责，作者本人并非计算机专业出身，仅提供思路并负责部分前端工作，望海涵。

项目从最初的「只会播视频」，一路加到了「会自动做题」，也因此拆成了 5 个脚本、4 套 AI 方案。代码风格上确实不够优雅，答题脚本之间有大量重复，配置项散落在文件顶部，但胜在**每一段都能单独看懂、单独改**。

希望这个小小的项目能帮到你 QwQ

PS：隔壁这个虽然不支持 ai 课程 但是很？！强强？！https://github.com/CXRunfree/Autovisor/

## 免责声明

> **本程序仅可用于学习和研究计算机原理，请于 24 小时内删除所有存档！**
>
> 请勿将本项目用于任何违反平台服务条款或学术诚信要求的场景，使用所产生的后果由使用者自行承担。

<div align="center">

**如果这个项目对你有帮助，欢迎点个 Star**

</div>