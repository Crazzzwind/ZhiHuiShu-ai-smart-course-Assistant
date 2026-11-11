<div align="center">

# ZhiHuiShu · AI 智慧课程助手

**一个可无人监督运行的智慧树 AI 智慧课程自动播放工具**

基于 Webdriver 与 Python 实现，通过浏览器模拟用户操作完成课程学习

![Python](https://img.shields.io/badge/Python-3.9-3776AB?logo=python&logoColor=white)
![Selenium](https://img.shields.io/badge/Selenium-4.6%2B-43B02A?logo=selenium&logoColor=white)
![Platform](https://img.shields.io/badge/Platform-Windows-0078D6?logo=windows&logoColor=white)
![Purpose](https://img.shields.io/badge/Purpose-Study%20%26%20Research-orange)

[项目主页](https://github.com/Crazzzwind/ZhiHuiShu-ai-smart-course-Assistant/) · [立即开始](#-快速开始) · [已知问题](#-已知问题) · [免责声明](#-免责声明)

</div>

---

## 目录

- [项目简介](#-项目简介)
- [功能特性](#-功能特性)
- [快速开始](#-快速开始)
  - [环境要求](#环境要求)
  - [运行步骤](#运行步骤)
- [配置说明](#-配置说明)
- [已知问题](#-已知问题)
- [写在最后](#-写在最后)
- [免责声明](#-免责声明)

---

## 项目简介

这是一个**可无人监督**的自动化程序，由 Python 编写，基于 **Webdriver** 驱动浏览器模拟用户操作，从而完成智慧树平台的 AI 智慧课程学习流程。

> 核心原理：用浏览器替代人手，自动播放课程视频并在结束后切换下一节。

---

## 功能特性

| 功能 | 说明 |
| :--- | :--- |
| **自动播放** | 打开课程后自动开始播放视频 |
| **自动切课** | 单节结束后自动切换至下一节 |
| **AI 智慧课程支持** | 适配智慧树 AI 智慧课程页面结构 |
| **全自动运行** | 登录后无需人工干预，等待刷完即可 |

---

## 快速开始

### 环境要求

| 项目 | 要求 |
| :--- | :--- |
| 操作系统 | Windows（可在  `IDLE` 下运行） |
| Python | 3.9（推荐） |
| 依赖库 | `selenium` |

> **关于浏览器驱动：** 若使用 Selenium 4.6 或更高版本，无需手动下载或配置浏览器驱动。内置的 **Selenium Manager** 会自动查找并下载与浏览器版本匹配的驱动，甚至可在未安装浏览器时自动完成下载。

### 运行步骤

**① 安装 Python**

下载并安装 Python，本项目在 **3.9** 版本下测试运行。

**② 安装依赖**

在 `cmd` 中执行：

```bash
pip install selenium
```

**③ 打开 IDLE 并载入脚本**

打开 IDLE，在 IDLE 中打开 `main.py`。

**④ 修改课程网址**

将 `main.py` 中的 `URL` 替换为你自己的课程链接，三个占位字段需全部替换：

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

**⑤ 启动程序**

点击 `Run` 开始运行。

**⑥ 手动登录**

浏览器窗口打开后，**手动登录你的账号**，并进入你所填链接对应的课程界面。

**⑦ 回车确认**

回到 IDLE 中按 `Enter`，程序即开始自动播放。

**⑧ 等待完成**

等待课程自动刷完即可，中途无需操作。

---

## 已知问题

| # | 问题 | 说明 |
| :-: | :--- | :--- |
| 1 | 多视频识别异常 | 同一节存在两个及以上视频时，可能只播放其中一个 |
| 2 | 仅支持 0% 进度 | 只能读取进度条为 0% 的课程（作者暂未修改） |

---

## 写在最后

**为什么这个代码这么差？**

本项目大部分代码由「吃白饭的大肥鱼」负责，作者本人并非计算机专业出身，仅提供思路并负责部分前端工作，望海涵。

希望这个小小的项目能帮到你 QwQ

---

## 免责声明

> **本程序仅可用于学习和研究计算机原理，请于 24 小时内删除所有存档！**
>
> 请勿将本项目用于任何违反平台服务条款或学术诚信要求的场景，使用所产生的后果由使用者自行承担。

<div align="center">

**如果这个项目对你有帮助，欢迎点个 Star**

</div>
