<div align="center">

# ZhiHuiShu · AI 智慧课程助手

**智慧树「AI 智慧课程」的半自动脚本集：一条链路刷视频，一条链路刷题库**

Python + Selenium 驱动真实 Edge 浏览器完成点击，两种链路、五个脚本，按需取一个能跑通的

![Python](https://img.shields.io/badge/Python-3.9-3776AB?logo=python&logoColor=white)
![Selenium](https://img.shields.io/badge/Selenium-4.6%2B-43B02A?logo=selenium&logoColor=white)
![Platform](https://img.shields.io/badge/Platform-Windows-0078D6?logo=windows&logoColor=white)
![Purpose](https://img.shields.io/badge/Purpose-Study%20%26%20Research-orange)

[项目主页](https://github.com/Crazzzwind/ZhiHuiShu-ai-smart-course-Assistant/) · [脚本一览](#脚本一览) · [快速开始](#快速开始) · [逐个脚本用法](#逐个脚本用法) · [排错清单](#排错清单) · [免责声明](#免责声明)

</div>

---

## 目录

- [项目简介](#项目简介)
- [脚本一览](#脚本一览)
- [功能特性](#功能特性)
- [快速开始](#快速开始)
- [逐个脚本用法](#逐个脚本用法)
- [运行顺序建议](#运行顺序建议)
- [AI 后端配置](#ai-后端配置)
- [公共配置](#公共配置)
- [日志速查](#日志速查)
- [排错清单](#排错清单)
- [已知限制](#已知限制)
- [写在最后](#写在最后)
- [免责声明](#免责声明)

---

## 项目简介

这是一套用 Python 写的自动化脚本，靠 **Webdriver 驱动真实浏览器** 去点智慧树「AI 智慧课程」的页面，把学习流程拆成两条互不相干的链路：

> **链路一 · 视频（`videos.py`）**
> 扫出所有进度未满 100% 的章节 → 逐章点开 → 在「必学资源」区逐个点开视频 / 图书 → 视频播完自动切下一个资源、下一个章节。
>
> **链路二 · 答题（四个脚本，选一个）**
> 扫出所有进度低于 95% 的章节 → 两段式「去提升」→ 进入题库 → 答题卡逐题抓题干与选项 → 交给 AI 出答案 → 点选 / 填写 → 提交并校验，被拒就补做。

**为什么是五个脚本？**
因为「播视频」不需要 AI，「答题」才需要答案来源。答案来源有四种——本地模型、本地模型＋联网搜索、免费在线代理、任意 OpenAI 兼容中转——而**抓题、点选、提交的代码完全一样**。与其做一套复杂的插件机制，不如复制四份、各配一个后端，你挑能跑通的那份用。

**先说清楚一件事：这不是「全自动」。**
`URL` 要你填，账号要你手动登录，回车要你按。脚本负责的是登录之后那几百次点击，其余仍然要人盯着起跑。

---

## 脚本一览

| # | 脚本 | 作用 | 答案来源 | 额外准备 | 速度 |
| :-: | :--- | :--- | :--- | :--- | :-: |
| ① | `videos.py` | 视频 / 图书资源自动播放、自动切章 | 无（纯 Webdriver） | 无 | 快（受视频时长限制） |
| ② | `questions-local-ai.py` | 去提升 + 题库自动答题 | 本地 **Ollama**（默认 `deepseek-r1:7b`） | Ollama + 模型 | 中（取决于显卡） |
| ③ | `questions-local-ai-Ollama Web Search.py` | 同上，答题前先联网搜索 | 本地 **Ollama** + **Ollama Web Search** | Ollama + `OLLAMA_API_KEY` | 中偏慢（多一次搜索往返） |
| ④ | `questions-online-ai-Deepseek-FreeDeepseekAPI.py` | 同上，思考模型 | **FreeDeepseekAPI** 本地代理 | Node + 代理项目 | 慢（每题停 10~20s，每 2 章停 500s） |
| ⑤ | `questions-online-ai-API.py` | 同上 | 任意 **OpenAI 兼容中转** | 中转 Key / Base URL / 模型名 | 中（无章节停顿，受中转限流） |

**怎么选一个：**

| 你的情况 | 建议 |
| :--- | :--- |
| 只想先把视频刷完 | ① |
| 有独显、不想把题目发到网上 | ② |
| 题库偏事实性（人名、年份、术语），本地模型老答错 | ③ |
| 电脑配置一般、不装模型，但能跑 Node | ④ |
| 手上已有中转 API（`sk-` 开头那种） | ⑤ |

> ⚠️ **②③④⑤ 只能挑一个跑。** 它们操作同一个课程页面，同时开只会互相抢浏览器窗口，进度还会打架。
>
> ⚠️ **① 与答题脚本必须分两次运行**，跑完一个、确认浏览器已关闭，再跑另一个。

---

## 功能特性

### 链路一 · 视频（`videos.py`）

| 功能 | 说明 |
| :--- | :--- |
| **按章筛未完成** | 读左列 `.pct-num` 的进度文本 / style，**低于 100% 的章节都会处理**（旧版只认 0%） |
| **只点必学资源** | 资源区由「必学资源」「选学资源」两个标题夹定，**选学区不会被点** |
| **自动切资源** | 单个资源处理完 → 回到资源列表 → 处理下一个，直到本章资源耗尽 |
| **指纹去重** | 以 `标题 + 类型 + 同名序号` 生成指纹，本次运行内不重复点同一资源 |
| **断点恢复** | 资源列表消失（页面被跳走）时，重新打开课程 URL 并按标题重进该章节 |
| **两段式视频判定** | 先等 `currentTime > 0.5s` 确认真的在播，再等 `paused` 连续 3 次稳定，才算本节结束 |
| **失败重试** | 同一视频连续 3 次检测失败才强制标记跳过，避免卡死 |
| **图书 / 其他资源** | 随机停留 5~15 秒；页面被跳转则自动 `back()` 返回 |

### 链路二 · 答题（②③④⑤ 共用）

| 功能 | 说明 |
| :--- | :--- |
| **低进度章节扫描** | 读 `.el-progress__text` 内 `span`，**进度 < 95% 即可处理**，`"0"` / `"0%"` / `"72"` 都能正确取数 |
| **两段式「去提升」** | 先点 `.simplified-mastery__action`，再点 `.improve-btn`；任一失败即跳过该章 |
| **全题型作答** | 单选、多选、判断（对→A / 错→B）、填空（按空位数对齐答案） |
| **答题卡遍历** | 依据 `.custom-tree-answer-normal` 上的 `answer` 类跳过已答题目 |
| **干扰节点自适应** | 点进去抓不到题干的节点自动标记为干扰项，后续不再尝试 |
| **投票 + 提前收敛** | 同一题采样 3 次取多数票；**前两次答案完全一致就跳过第 3 次**，省 1/3 调用 |
| **填空投票归一化** | 按 NFKC 归一化去空格、去标点后逐空投票，避免「的 / 地」这类差异分票 |
| **提交与校验** | 提交后监听「还有题目没有完成」弹窗，把 `no-answer` 的题补做，最多 3 轮，无进展即停 |
| **提交三重判定** | 弹窗 / URL 变化 / 提交按钮消失，任一命中即认定提交成功 |
| **可选视觉模式** | 截取题目区域交给多模态模型识别（默认关闭，需 `pillow`） |

### 各后端独有能力

| 能力 | ② 本地 | ③ 搜索 | ④ 免费代理 | ⑤ 中转 |
| :--- | :-: | :-: | :-: | :-: |
| 联网搜索增强 | — | ✅ | — | — |
| 思考模型兜底（`thinking` / `reasoning_content`） | ✅ | ✅ | ✅ | ✅ |
| `response_format` 不支持时自动降级 | — | — | ✅ | ✅ |
| 429 限流退避 | — | — | ✅ | ✅ |
| 投票间隔随机停顿 | — | — | ✅ 10~20s | — |
| 每 N 章强制停顿 | — | — | ✅ 2 章 / 500s | — |
| 每题投票前的提前收敛 | ✅ | ✅ | ✅ | ✅ |

---

## 快速开始

### 环境与依赖

| 项目 | 要求 |
| :--- | :--- |
| 操作系统 | Windows（五个脚本都硬编码 **Edge** WebDriver，可在 `IDLE` 下运行） |
| Python | 3.9（推荐） |
| 浏览器驱动 | 无需手动下载，Selenium 4.6+ 的 **Selenium Manager** 会自动匹配 |

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

> **想换 Chrome：** 把每个脚本里的 `from selenium.webdriver.edge.options import Options` 改成 `chrome.options`，再把 `webdriver.Edge` 换成 `webdriver.Chrome`，其余不用动。

### 三步跑通

```text
第一步：改 URL（五个脚本各自顶部，占位字段换成你自己课程的）
第二步：运行脚本 → 浏览器自动打开 → 手动登录 → 停在「课程目录 / 左侧章节列表」页
第三步：回到 IDLE 或命令行，按 Enter → 之后全程无人值守 → 跑完自动 quit()
```

**每次运行都是这个节奏**，没有别的入口，也没有命令行参数。

### 通用前提：URL / 登录 / 回车

**① 改 URL。** 四个答题脚本顶部是三个占位字段，必须全部替换：

```python
URL = ("https://ai-smart-course-student-pro.zhihuishu.com/"
       "singleCourse/knowledgeStudy/新课程ID/新章节ID"
       "?mapUid=新的mapUid")
```

| 占位字段 | 替换为 |
| :--- | :--- |
| `新课程ID` | 你课程的实际课程 ID |
| `新章节ID` | 你课程的实际章节 ID |
| `新的mapUid` | 链接里的 `mapUid` 参数 |

> ⚠️ **`videos.py` 现在填的是作者自己的示例课程链接**（`2091402990853783552 / 257092`），不是占位符，**必须整个换成你自己的**，否则会在别人的课程里乱点。

> 取 URL 的最省事办法：在浏览器里正常打开你的课程目录页，把地址栏整条复制过来，替换掉脚本里的 `URL`。

**② 手动登录。** 浏览器窗口打开后，自己登录账号，并把页面停在**左侧有章节列表的那一页**。左侧章节树如果是折叠状态，先手动展开——脚本靠元素可见性判断，折叠时读不到章节。

**③ 回车放行。** 回到 IDE / 命令行按 `Enter`。之后不要最小化窗口、不要手动滚动页面，脚本会自己翻页。

---

## 逐个脚本用法

### ① `videos.py`：视频自动播放

**流程**

```text
打开课程 → 回车 → 读左列进度，筛出 <100% 的章节 → 逐章点击
→ 内层扫「必学资源」区 → 逐个点开资源（视频等播完，图书停 5~15s）
→ 本章资源处理完 → 下一章 → 全部结束
```

**跑之前要改的**

| 行号 | 变量 | 改什么 |
| :-: | :--- | :--- |
| 10 | `URL` | **必改**，默认是作者示例课程 |
| 16 | `PROGRESS_THRESHOLD = 100` | 低于该值就处理；改成 `1` 就退回「只刷 0% 章节」 |
| 306 | `MAX_CHAPTERS = 100` | 外层章节上限，章节多可调大 |
| 351 | `MAX_INNER = 200` | 单章资源上限 |
| 242 | `timeout_started=120` | 点开资源后等视频起播的秒数，网慢可调大 |
| 242 | `timeout_paused=7200` | 单个视频最长等待（默认 2 小时） |

**启动**

```bash
python videos.py
```

**运行时大概长这样**

```text
[OK] 页面已打开
>>> 如需登录，请先登录，然后按回车继续...        ← 这里按回车
[OUTER] 进度<100% 章节 12 个（进度元素 12 个），其中未尝试 12 个
[CHAPTER 1/100] 处理: 第一章 xxx (进度=0.0 原文='0')
[INNER SCAN] 共 5 个，未处理 5 个 (video=3, book=1, other=1)
[INNER] 处理第 1 个：video
[VIDEO] 等待视频开始播放...
[VIDEO] 视频已开始播放，等待暂停...
[VIDEO] 视频暂停稳定
[INNER] 资源列表可访问，共 5 个
...
[CHAPTER OK] 「第一章 xxx」完成
[ALL DONE] 共处理 12 个章节
[OK] 浏览器已关闭
```

**注意**

- **按「章」整体重播**：脚本只看章节进度，**不判断单个资源是否已完成**。所以章节进度 60% 时重跑，会把这一章的必学资源从头再点一遍（这是阈值从「只认 0%」放宽到「<100%」的代价）。`PROGRESS_THRESHOLD` 改回 `1` 可以避免。
- 同一章处理过就记进 `tried_titles`，本轮内不会再选它；失败的章会打 `[CHAPTER WARN]` 并跳过，不会死循环。
- 日志一直刷 `[WARN] 左列未加载，退出外层`，说明左侧章节列表折叠了，展开后重跑。
- 视频判定依赖 `video` 标签可见性，**别让窗口最小化**。
- 每处理一个章节都会重新 `driver.get(URL)` 刷新页面，所以中途页面跳动通常能自愈；真跳飞了会走 `[REENTER]` 按标题重进。

---

### ② `questions-local-ai.py`：本地 Ollama 答题

**流程**

```text
筛进度<95% 的章节 → 点章节 → 去提升① → 去提升②
→ 答题卡逐题：抓题干/选项 → 本地模型答（投票）→ 点选/填空
→ 提交并校验 → 有漏题就补做（最多 3 轮）→ 下一章
```

**跑之前要改的**

| 行号 | 变量 | 改什么 |
| :-: | :--- | :--- |
| 22 | `URL` | 三个占位字段，**必改** |
| 30 | `PROGRESS_THRESHOLD = 95` | 调大能覆盖更多章节 |
| 67 | `OLLAMA_MODEL = "deepseek-r1:7b"` | **名字必须与 `ollama list` 一致**；可换 `qwen3.5:4b` 等更小的 |
| 77 | `VOTE_SAMPLES = 3` | 机器慢可改 `1`，直接关掉投票 |

**准备模型**

```bash
ollama serve                     # 装完通常开机自启，托盘有图标可跳过
ollama pull deepseek-r1:7b       # 或 ollama pull qwen3.5:4b
ollama list                      # 确认名字，脚本按子串匹配
```

**启动**

```bash
python questions-local-ai.py
```

**运行时大概长这样**

```text
[OLLAMA] 服务在线，可用模型: ['deepseek-r1:7b', ...]
[OK] 纯文本模式（模型=deepseek-r1:7b），每题投票 3 次
[OK] 页面已打开
>>> 如需登录，请先登录，然后按回车继续...        ← 这里按回车
[START] 第1轮 | 进度<95 总数=12 未尝试=12
[CHAPTER 1/100] 点击: 第一章 xxx (进度=0.0 原文='0')
[ACTION] 已点击
[IMPROVE] 已点击
[BANK] 答题卡节点 20 个，遍历上限 20，初始 answer class 数=0
[BANK 1/20] 作答
[VOTE] 第1/3次 single: ['A']
[VOTE] 第2/3次 single: ['A']
[VOTE OPT] 前两次结果一致，跳过剩余采样，不再调用模型
[VOTE] single 票数=['A']x2 → 取=['A']
[ANSWER] single 点击 1 个，期望 ['A']
[SUBMIT] 普通点击成功
[SUBMIT] 页面已跳转，视为提交成功
[ALL DONE] 共处理 12 个章节
```

**注意**

- 探活失败会打印 `[OLLAMA FAIL] 服务不可达` 或 `[OLLAMA WARN] 未找到模型`，但**脚本仍会跑完**——结果是每道题空手而归，只浪费浏览器时间。
- 首次调用要加载权重（几十秒），`OLLAMA_KEEP_ALIVE = "10m"` 保证 10 分钟内不重复加载，别在中途重启 Ollama。
- **没有章节级防风控停顿**，是四个答题脚本里最快的一个，也最像「机器人」，自己权衡。
- 视觉模式默认关闭（`OLLAMA_VISION = False and _HAS_PIL`），要开得同时改 `True` 并装 `pillow`，且模型本身支持多模态。

---

### ③ `questions-local-ai-Ollama Web Search.py`：本地 AI + 联网搜索

**和 ② 的差别只有一处：投票的第一次采样前，先拿题干去搜一次网页，把标题＋正文片段＋来源拼进 prompt。**

```text
题干 → ollama.web_search(最多 3 条) → 拼进 context
→ 本地模型结合搜索结果作答（第 1 次）
→ 第 2、3 次纯模型，复用同一份判断 → 投票
```

**跑之前要改的**

| 行号 | 变量 | 改什么 |
| :-: | :--- | :--- |
| 23 | `URL` | 三个占位字段，**必改** |
| 66 | `OLLAMA_MODEL = "qwen3.5:4b"` | 与 `ollama list` 一致 |
| 72 | `OLLAMA_API_KEY` | 读环境变量，**必须先在系统里设好** |
| 73 | `WEB_SEARCH_ENABLED = True` | 改 `False` 就退回纯本地 |
| 74 | `WEB_SEARCH_MAX_RESULTS = 3` | 每次搜几条（上限 10） |
| 75 | `WEB_SEARCH_CONTENT_LIMIT = 300` | 每条结果进 prompt 的字符数 |

**设置 Key（三选一）**

```bash
set OLLAMA_API_KEY=你的key                 # cmd，只对当前窗口有效
setx OLLAMA_API_KEY 你的key                # cmd，永久写入，需重开窗口
$env:OLLAMA_API_KEY="你的key"              # PowerShell，只对当前会话有效
```

**启动**

```bash
python "questions-local-ai-Ollama Web Search.py"
```

> 文件名带空格，命令行里**必须加引号**；在 IDLE 里直接打开运行则不受影响。

**运行时大概长这样**

```text
[OK] Web Search 已启用（每次答题前搜索，投票仅首次触发搜索）
[SEARCH] 找到 3 条结果，已注入上下文
[VOTE] 第1/3次 single (带搜索): ['B']
[VOTE] 第2/3次 single (纯模型): ['B']
[VOTE OPT] 前两次结果一致，跳过剩余采样，不再调用模型
[SEARCH] 无结果: xxxxx...
```

**注意**

- 没设 Key 会打 `[SEARCH WARN] OLLAMA_API_KEY 未设置，跳过搜索`，答题照常继续，只是退化成 ②。
- 搜索查询就是题干原文截断到 120 字符，题干很长或全是符号时效果会明显变差。
- 搜索异常自动降级，不会中断主流程——`[SEARCH WARN] 搜索失败，降级为纯模型作答`。
- 比 ② 每题多一次网络往返，整体更慢，但**事实性题目的命中率通常更高**，这就是它存在的唯一理由。

---

### ④ `questions-online-ai-Deepseek-FreeDeepseekAPI.py`：免费 Deepseek 代理

**流程同 ②，答案来自 FreeDeepseekAPI 本地代理（OpenAI 兼容，默认 `http://127.0.0.1:9655/v1`）。特点是节奏极慢、防风控最狠。**

**跑之前要改的**

| 行号 | 变量 | 改什么 |
| :-: | :--- | :--- |
| 23 | `URL` | 三个占位字段，**必改** |
| 65~67 | `FREEDEEPSEEK_API_KEY` / `BASE_URL` / `MODEL` | 一般不用改；改过代理端口要同步 |
| 71 | `AI_TIMEOUT = 120` | 思考模型耗时长，别给太小 |
| 79 | `VOTE_SAMPLES = 3` | 改 `1` 能省掉 2/3 的等待 |
| 80~81 | `VOTE_PAUSE_MIN` / `VOTE_PAUSE_MAX` | 投票间隔 10~20 秒，想加速可以调小 |
| 84~85 | `CHAPTER_PAUSE_EVERY` / `CHAPTER_PAUSE_SECONDS` | 每 2 章停 500 秒 |
| 75 | `AI_VISION` | 视觉模式开关，默认关 |

**准备代理（另开一个命令行窗口，跑完之前别关）**

```bash
# 进入 FreeDeepseekAPI 代理项目目录
npm run auth
npm run dashboard
```

想先确认代理是否在听：

```bash
curl http://127.0.0.1:9655/v1/models
```

**启动**

```bash
python questions-online-ai-Deepseek-FreeDeepseekAPI.py
```

**运行时大概长这样**

```text
[AI] FreeDeepseekAPI 在线，可用模型: [...]
[OK] FreeDeepseekAPI 模式 | 模型=deepseek-v4-flash-thinking | 每题投票 3 次
[ACTION] 已点击
[IMPROVE] 已点击
[VOTE] 第1/3次 single: ['C']
[PAUSE] 防风控等待 14.7s ...                     ← 每次投票之间都会停
[VOTE] 第2/3次 single: ['C']
[PAUSE] 已完成 2 个章节，防风控强制停顿 500 秒 ...   ← 每 2 章停一次
```

**注意**

- 这是**最慢的一个**：每题 3 次采样 ×（思考耗时 + 10~20 秒间隔），再加每 2 章约 8 分钟停顿。整门课通常要跑一夜，**适合睡前挂上**。
- 思考模型的 `content` 常常是空的，脚本会去 `reasoning_content` 里抠 JSON，日志提示 `[AI] content 空，从 reasoning 抠出`。
- 代理不支持 `response_format` 时会打印 `该接口不支持 response_format，去掉重试` 并自动重发。
- 探活失败会提示 `[AI HINT] 请先运行: npm run auth  然后  npm run dashboard`。
- 代理窗口一关，答题环节就全部空转——中途别关，也别让电脑睡死。

---

### ⑤ `questions-online-ai-API.py`：通用 OpenAI 兼容中转

**流程同 ②，答案来自任意 OpenAI 兼容的云端中转。适合手上已经有 `sk-` Key、不想在本地装模型的场景。**

**三个占位必须全改**

| 行号 | 变量 | 改成 |
| :-: | :--- | :--- |
| 22 | `URL` | 三个占位字段，**必改** |
| 65 | `CHATANYWHERE_API_KEY = "sk-key"` | 你的中转 Key，形如 `sk-xxxx` |
| 66 | `CHATANYWHERE_BASE_URL = "https://xxxx.com"` | 中转地址，**一般要带 `/v1`**，如 `https://api.xxx.com/v1` |
| 67 | `CHATANYWHERE_MODEL = "xxxx"` | 该中转支持的模型名，如 `gpt-4o-mini`、`deepseek-chat` |
| 70 | `AI_TIMEOUT = 60` | 网络差或模型慢就调大 |
| 71 | `AI_USE_JSON_FORMAT = True` | 中转不支持会**自动降级**，通常不用手动关 |
| 74 | `AI_VISION` | 视觉模式开关，默认关 |
| 78 | `VOTE_SAMPLES = 3` | `1` = 关掉投票 |

**启动**

```bash
python questions-online-ai-API.py
```

**运行时大概长这样**

```text
[AI] ChatAnywhere 在线，模型数=3，样本=['gpt-4o-mini', ...]
[OK] 云端纯文本模式（模型=gpt-4o-mini），每题投票 3 次
[VOTE] 第1/3次 multiple: ['A','C']
[VOTE] 第2/3次 multiple: ['A','C']
[VOTE OPT] 前两次结果一致，跳过剩余采样，不再调用模型
[VOTE] multiple 票数=['A','C']x2 → 取=['A','C']
```

**注意**

- 探活只拦两种情况：`Key` 为空，或仍以 `sk-你的` 开头。脚本默认是 `sk-key`，**会通过这一步检查，然后在 `models.list()` 上直接失败**，日志是 `[AI FAIL] ChatAnywhere 探活失败`。所以别指望它替你发现没改 Key，自己核对。
- 模型名不在中转返回的列表里只告警不退出——很多中转不返回全量模型。
- 命中 429 会自动退避 `5 × 尝试次数` 秒，连续限流时会有明显停顿。
- **没有章节级停顿**，比 ④ 快得多，但请求更密集，免费中转很容易被限流。
- 想开视觉模式：`AI_VISION` 改 `True`，装 `pip install pillow`，并且确认该中转的模型支持多模态。

---

## 运行顺序建议

1. **先跑 ①**，把视频章节刷到 100%。再跑一遍会提示「所有进度<100% 的章节都已尝试，结束」。
2. **再挑一个答题脚本**（②③④⑤ 之一），处理进度 < 95% 的章节——通常就是「去提升」任务。
3. **补漏就重跑同一个答题脚本**。`tried_titles` 只在单次运行内有效，上次失败的章节会被重新尝试。
4. **换脚本前确认上一个浏览器已关闭**（`[OK] 浏览器已关闭`），否则两个 WebDriver 会抢同一个窗口。

---

## AI 后端配置

### Ollama（②③ 使用）

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
| `OLLAMA_RETRY` | `2` | 单题重试次数（共尝试 3 次） |
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
| `AI_TEMPERATURE` | `None` | 思考模式下该参数被忽略，`None` 就不传 |
| `AI_TIMEOUT` | `120` | 思考模型耗时长，别给太小 |
| `AI_USE_JSON_FORMAT` | `True` | 不支持时自动降级 |

### 通用中转（⑤ 使用）

| 配置项 | 默认 | 说明 |
| :--- | :--- | :--- |
| `CHATANYWHERE_BASE_URL` | `https://xxxx.com` | 中转地址，一般带 `/v1` |
| `CHATANYWHERE_API_KEY` | `sk-key` | 必改；空值或 `sk-你的` 前缀才会被前置拦住 |
| `CHATANYWHERE_MODEL` | `xxxx` | 该中转支持的模型名 |
| `AI_TEMPERATURE` | `0` | 云端版会真正传 temperature |
| `AI_TIMEOUT` | `60` | 秒 |

---

## 公共配置

### ②③④⑤ 共享（改一份要同步四份）

| 配置项 | 默认 | 说明 |
| :--- | :--- | :--- |
| `PROGRESS_THRESHOLD` | `95` | 进度低于该值才处理 |
| `SEL_ACTION_BTN` | `.simplified-mastery__action` | 第一次「去提升」按钮 |
| `SEL_IMPROVE_BTN` | `.improve-btn` | 第二次「去提升」按钮 |
| `VOTE_SAMPLES` | `3` | 每题采样次数，`1` = 关闭投票 |
| `FILL_USE_THINKING` | `False` | 填空题是否启用思考模式（仅 ②③） |
| `SUBMIT_RETRY` | `3` | 提交重试轮数 |
| `MAX_CHAPTERS` | `100` | 外层章节上限 |
| `ANSWER_CARD_OFFSET` | `0` | 答题卡节点截断量，`0` = 靠抓取失败识别干扰节点 |
| `WAIT_AFTER_CLICK` | `5` | 点击章节后等待秒数 |
| `WAIT_AFTER_ACTION` / `WAIT_AFTER_IMPROVE` | `5` | 两次去提升之间的等待 |
| `WAIT_AFTER_ANSWER` | `1.5` | 每题之间的间隔 |
| `TIMEOUT_CHAPTER_LIST` | `60` | 左侧章节列表加载超时 |
| `WAIT_BEFORE_SUBMIT` / `WAIT_AFTER_SUBMIT` | `3` / `8` | 提交前后等待 |
| `SCREENSHOT_QUALITY` | `60` | 视觉模式截图 JPEG 质量 |

> **注意**：`videos.py` 的 `URL`、`PROGRESS_THRESHOLD`、`MAX_CHAPTERS`、`MAX_INNER`、两段 `timeout_*` 是**独立的一套**，和上面这组无关。

---

## 日志速查

| 标签 | 含义 |
| :-: | :--- |
| `[OK]` | 初始化或关键步骤成功 |
| `[DEBUG]` | 进度文本样本，用来确认选择器真的取到了值 |
| `[OUTER]` / `[CHAPTER]` | 外层章节扫描与当前章节 |
| `[INNER]` / `[INNER SCAN]` | 内层资源扫描与逐个处理（①） |
| `[VIDEO]` | 视频起播判定与暂停判定（①） |
| `[REENTER]` | 资源列表丢失后按标题重进章节（①） |
| `[ACTION]` / `[IMPROVE]` | 两段式去提升的点击结果 |
| `[BANK]` | 答题卡遍历进度、干扰节点、提交轮次 |
| `[VOTE]` / `[VOTE OPT]` | 多次采样、票数、提前收敛 |
| `[ANSWER]` / `[FILL WARN]` | 最终答案、填空补位与截断 |
| `[SUBMIT]` | 提交结果与弹窗内容 |
| `[SEARCH]` / `[SEARCH WARN]` | 联网搜索命中与降级（③） |
| `[PAUSE]` | 防风控停顿（④） |
| `[OLLAMA]` / `[AI]` | 后端探活与推理日志（②③ / ④⑤） |
| `[STATS]` | 结束时逐章统计汇总 |
| `[WARN]` / `[FAIL]` | 单步失败，通常降级或跳过，不影响全局 |

---

## 排错清单

| 现象 | 大概率原因 | 怎么办 |
| :--- | :--- | :--- |
| `[WARN] 左列未加载，退出外层` | 左侧章节树折叠 / 页面还没加载完 | 手动展开章节树后重跑；确认 URL 是课程目录页 |
| `[WARN] 未找到进度元素 .pct-num` | `videos.py` 选择器失效或页面结构变了 | 先 `driver.get` 一次看左列是否渲染；平台改版需更新 `SEL_PROGRESS_NUM` |
| `[REENTER FAIL] 未找到章节标题` | 章节标题为空，或页面跳到了别的地方 | 日志里的 `[REENTER DEBUG]` 会打印当前 title 列表，对照调整 `MAX_INNER` |
| `[VIDEO WARN] 视频未开始播放` | 点击没生效 / 缓冲慢 / 有弹窗遮挡 | 关掉页面弹窗；把 `timeout_started` 调大到 180~300 |
| `[VIDEO WARN] 等待暂停超时` | 视频挂了 or 播放器行为不同 | 该资源会被记一次失败，3 次后跳过，通常不用管 |
| `[OLLAMA FAIL] 服务不可达` | Ollama 没启动 | `ollama serve`，或确认托盘图标在 |
| `[OLLAMA WARN] 未找到模型 xxx` | 模型名拼错或没拉取 | `ollama list` 对照，改 `OLLAMA_MODEL` 或 `ollama pull` |
| `[SEARCH WARN] OLLAMA_API_KEY 未设置` | 环境变量没生效 | 用 `setx` 写入后**重开命令行/IDE** |
| `[AI FAIL] 本地代理不可达` | FreeDeepseekAPI 没跑 / 端口不对 | `npm run auth` → `npm run dashboard`；`curl` 一下 `/v1/models` |
| `[AI FAIL] ChatAnywhere 探活失败` | Key 或 Base URL 还是占位 | 换真实 Key；Base URL 补 `/v1` |
| `[AI WARN] 该接口不支持 response_format` | 中转不支持 JSON 模式 | 自动降级，忽略即可 |
| `[AI WARN] 第n次触发限流，等 Xs` | 429 限流 | ④ 拉大 `VOTE_PAUSE_*`；⑤ 换中转或减小 `VOTE_SAMPLES` |
| `[BANK WARN] 未检测到答题卡` | 没进题库页 / 去提升没点成功 | 往前看 `[ACTION]` `[IMPROVE]` 有没有 `已点击` |
| `[BANK x/y] 抓取失败 → 标记为干扰节点` | 该节点不是题目 | 单个正常；**大面积出现说明选择器全失效** |
| `[SUBMIT] 弹窗：还有题目没有完成` | 有题没作答（含被当成干扰的节点） | 脚本会自动补做；反复出现就查 `ANSWER_CARD_OFFSET` 与干扰节点 |
| `[SUBMIT FAIL] 多次提交仍未通过` | 补做无进展 | 本章手动处理，或把 `SUBMIT_RETRY` 调大重跑 |
| `[FILL WARN] 用最后一项补齐 / 截断` | 填空空位数与模型答案数不一致 | 属正常兜底；准确率差就开视觉模式 |
| `[STATS]` 里「去提升①=FAIL」 | 该章没有去提升入口 | 章节可能已达标或结构不同，跳过不影响其它章 |

**还想更快定位？** 每个脚本运行时都会打一行 `[DEBUG] 进度文本样本(前20)`——只要这行里的数字跟你眼睛看到的章节进度一致，选择器就是好的；不一致就先改选择器，别怪 AI。

---

## 已知限制

| # | 限制 | 说明 |
| :-: | :--- | :--- |
| 1 | 仅 Windows + Edge | 五个脚本都硬编码 `webdriver.Edge`，换浏览器要改初始化 |
| 2 | 必须分两次运行 | 视频与答题是两套独立脚本，跑完一个再跑另一个 |
| 3 | 答题脚本四选一 | ②③④⑤ 操作同一个课程页，同时跑会抢浏览器 |
| 4 | 视频按「章」整体重播 | 只看章节进度，不看单资源进度；半成品章节重跑会把资源全点一遍 |
| 5 | 全靠前端 class 定位 | 平台一改版，`.pct-num` / `.el-progress__text` / `.custom-tree-answer-normal` 之类就会失效 |
| 6 | 干扰节点靠「抓取失败」识别 | 题库结构变化时可能误判，把正常题目当干扰跳过 |
| 7 | 正确率完全取决于模型 | 投票只能压住随机波动；填空数量不一致时会补齐或截断 |
| 8 | ④ 极慢 | 每题 10~20s × 3 次 + 每 2 章 500s，只适合挂机；②⑤ 无章节停顿 |
| 9 | ⑤ 的 Key 校验很弱 | 默认 `sk-key` 能通过前置检查，然后在探活时失败 |
| 10 | 模型名匹配宽松 | 本地是子串匹配，云端只告警不退出，可能出现「探活通过但作答全空」 |
| 11 | 视觉模式默认关闭 | 需手动改 `True`、装 `pillow`、且模型支持多模态 |
| 12 | 无人值守仍有风险 | 登录态过期、验证码、页面跳动都可能让流程空转，建议隔一段时间瞄一眼 |

---

## 写在最后

前面那版 README 是 AI 写的，这一段我自己写。

**为什么代码看起来这么糙？**
本项目大部分代码由「吃白饭的大肥鱼」完成。我本人不是计算机专业出身，只出思路、做了部分前端工作，望海涵。

项目从最初的「只会播视频」，一路长到「会自动做题」，也就拆成了 5 个脚本、4 套 AI 方案。代码风格确实不优雅：答题脚本之间大段重复，配置散落在文件顶部，改一个常量要同步四份。但至少**每一段都能单独看懂、单独改**，出问题也能只用一份脚本复现。

**几个实测结论，供参考：**

- 本地模型和部分 API **只会推理、不会联网**，事实类题目（人名、年份、术语）答错率不低，这是 ③ 存在的理由。
- 我个人认为**效果最稳的是 FreeDeepSeek 那一版（④）**，但风控也最严重，节奏慢是刻意的。
- 视频链路放宽到「<100%」以后能扫到半成品章节，代价是整章重播——如果你只想刷全新章节，把 `PROGRESS_THRESHOLD` 改回 `1`。

**参考项目：**

- FreeDeepSeek 的部署下载，请看 dekrezz 大神的 [FreeDeepseekAPI](https://github.com/dekrezz/FreeDeepseekAPI)
- 隔壁这个虽然不支持 AI 课程，但确实很强：[Autovisor](https://github.com/CXRunfree/Autovisor/)

希望这个小小的项目能帮到你 QwQ

---

## 免责声明

> **本程序仅可用于学习和研究计算机原理，请于 24 小时内删除所有存档！**
>
> 项目的初衷是练习 Webdriver 的页面定位与流程编排。请勿将其用于任何违反平台服务条款或学术诚信要求的场景——包括但不限于代替本人完成课程考核。使用所产生的后果由使用者自行承担。

<div align="center">

**如果这个项目对你有帮助，欢迎点个 Star**

</div>

> （注：部分内容由豆包 AI 生成）