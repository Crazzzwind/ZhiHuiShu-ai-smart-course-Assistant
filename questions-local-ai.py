from selenium import webdriver
from selenium.webdriver.edge.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import json
import re
import unicodedata
import ollama

try:
    import io
    from PIL import Image
    _HAS_PIL = True
except Exception:
    _HAS_PIL = False

# ============================================================
# 配置区
# ============================================================
URL = ("https://ai-smart-course-student-pro.zhihuishu.com/"
       "singleCourse/knowledgeStudy/新课程ID/新章节ID"
       "?mapUid=新的mapUid")


# --- 章节进度 ---
SEL_PROGRESS_TEXT   = ".el-progress__text"
SEL_PROGRESS_SPAN   = "span"
PROGRESS_THRESHOLD  = 95      # 进度小于该值就处理（原先是严格等于 "0"）
SEL_ITEM_TITLE      = ".item-title"
SEL_ITEM_MASK       = ".item-mask"
MASK_CLS            = "item-mask"

# --- 两段式「去提升」---
SEL_ACTION_BTN    = ".simplified-mastery__action"
SEL_IMPROVE_BTN   = ".improve-btn"

# --- 题库：答题卡 ---
SEL_ANSWER_CARD      = ".custom-tree-answer-normal"
CLS_CARD_DONE        = "answer"
CLS_CARD_TODO        = "no-answer"

# --- 题库：题目容器 ---
SEL_QUESTION_CONTENT = ".questionContent"
SEL_QUESTION_TYPE    = ".questionTitle .letterSortNum"
SEL_QUESTION_STEM    = ".centent-pre pre.preStyle"

# --- 题库：单选/判断选项 ---
SEL_RADIO_OPTIONS    = "ul.radio-view li"
SEL_RADIO_LABEL      = ".letterSort.fl"
SEL_RADIO_TEXT       = ".preStyle.fl.stem"

# --- 题库：多选选项 ---
SEL_CHECKBOX_OPTIONS = ".el-checkbox-group.checkbox-view label.el-checkbox"
SEL_CHECKBOX_LABEL   = ".letterSort.fl"
SEL_CHECKBOX_TEXT    = ".preStyle.fl"

# --- 题库：填空 ---
SEL_FILL_INPUT       = ".input-view.fillAnswer .el-input__inner"

# --- 题库：提交 ---
SEL_SUBMIT_BTN       = ".reviewDone.ZHIHUISHU_QZMD"
SEL_MESSAGE          = "p.el-message__content"

# --- 本地 Ollama ---
OLLAMA_MODEL        = "deepseek-r1:7b"
OLLAMA_TEMPERATURE  = 0
OLLAMA_KEEP_ALIVE   = "10m"
OLLAMA_RETRY        = 2

# --- 视觉方案开关（pillow 没装时强制关）---
OLLAMA_VISION       = False and _HAS_PIL
SCREENSHOT_QUALITY  = 60

# --- 投票：所有题型都多次采样，1 = 关闭投票 ---
VOTE_SAMPLES        = 3
FILL_USE_THINKING   = False

# --- 超时 / 上限 ---
TIMEOUT_CHAPTER_LIST = 60
TIMEOUT_ACTION       = 30
TIMEOUT_IMPROVE      = 30
TIMEOUT_BANK_LOAD    = 15
MAX_CHAPTERS         = 100
WAIT_AFTER_CLICK     = 5
WAIT_AFTER_ACTION    = 5
WAIT_AFTER_IMPROVE   = 5
WAIT_AFTER_ANSWER    = 1.5
SUBMIT_RETRY         = 3

# --- 提交等待 ---
TIMEOUT_SUBMIT       = 20
WAIT_BEFORE_SUBMIT   = 3
WAIT_AFTER_SUBMIT    = 8

# --- 答题卡节点修正：0 = 不截断，靠抓题失败自适应识别干扰节点 ---
ANSWER_CARD_OFFSET = 0

# ============================================================
# 初始化
# ============================================================
options = Options()
options.add_argument("--start-maximized")

driver = webdriver.Edge(options=options)
wait = WebDriverWait(driver, TIMEOUT_CHAPTER_LIST)


# ============================================================
# 章节：JS 模板
# ============================================================
def _js(template):
    return (template
            .replace("$SEL_PROGRESS", SEL_PROGRESS_TEXT)
            .replace("$SEL_P_SPAN",   SEL_PROGRESS_SPAN)
            .replace("$THRESHOLD",    str(PROGRESS_THRESHOLD))
            .replace("$SEL_ITEM_T",   SEL_ITEM_TITLE)
            .replace("$MASK_CLS",     MASK_CLS))


def _progress_text_js():
    return driver.execute_script(_js("""
        return [...document.querySelectorAll('$SEL_PROGRESS')].map(p => {
            const s = p.querySelector('$SEL_P_SPAN');
            return (s ? s.textContent : p.textContent || '').trim();
        });
    """))


def get_low_progress_chapters():
    """
    从上到下遍历 .el-progress__text 内部 span：
      去掉非数字字符后 parseFloat，若数值 < $THRESHOLD 就收集。
      纯文本 "0"、"0%"、"72"、"72%" 都能正确取数。
    """
    raw = driver.execute_script(_js("""
        const progresses = [...document.querySelectorAll('$SEL_PROGRESS')];
        const out = [];
        for (const p of progresses) {
            const s = p.querySelector('$SEL_P_SPAN');
            const txt = (s ? s.textContent : p.textContent || '').trim();
            const num = parseFloat((txt || '').replace(/[^0-9.]/g, ''));
            if (isNaN(num) || num >= $THRESHOLD) continue;

            let title = '';
            let q = p.parentElement;
            for (let i = 0; i < 10 && q; i++) {
                const t = q.querySelector ? q.querySelector('$SEL_ITEM_T') : null;
                if (t) { title = t.getAttribute('title') || (t.textContent || '').trim(); break; }
                q = q.parentElement;
            }
            if (!title) continue;

            let clickEl = null;
            let q2 = p.parentElement;
            for (let i = 0; i < 10 && q2; i++) {
                if (q2.classList && q2.classList.contains('$MASK_CLS')) { clickEl = q2; break; }
                q2 = q2.parentElement;
            }
            if (!clickEl) clickEl = p.parentElement || p;

            out.push({ title: title, el: clickEl, progress: num, raw: txt });
        }
        return out;
    """))

    result = []
    for item in raw or []:
        try:
            title = item.get('title')
            el = item.get('el')
            if title and el is not None:
                result.append((title, el, item.get('progress'), item.get('raw')))
        except Exception:
            continue
    return result


def click_by_selector(selector, label, timeout):
    try:
        btn = WebDriverWait(driver, timeout).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
        )
    except Exception as e:
        print(f"[{label} WARN] 未等到按钮 {selector}: {type(e).__name__}")
        return False

    try:
        btn.click()
        print(f"[{label}] 已点击")
        return True
    except Exception as e:
        print(f"[{label} WARN] 普通点击失败，尝试 JS: {type(e).__name__}")
        try:
            driver.execute_script("arguments[0].click();", btn)
            print(f"[{label}] JS 点击成功")
            return True
        except Exception as e2:
            print(f"[{label} FAIL] JS 点击也失败: {type(e2).__name__}: {e2}")
            return False


# ============================================================
# Ollama：工具
# ============================================================
def _extract_json_from_text(text):
    if not text:
        return None
    try:
        return json.loads(text.strip())
    except Exception:
        pass
    m = re.findall(r'\{[^{}]*"answers"[^{}]*\}', text, re.S)
    if m:
        try:
            return json.loads(m[-1])
        except Exception:
            pass
    return None


def _ollama_chat_with_fallback(**kwargs):
    try:
        response = ollama.chat(**kwargs)
    except TypeError as e:
        if "think" in str(e):
            kwargs.pop("think", None)
            response = ollama.chat(**kwargs)
        else:
            raise

    msg = response["message"]
    content = (msg.get("content") or "").strip()

    if not content:
        thinking = msg.get("thinking") or ""
        data = _extract_json_from_text(thinking)
        if data:
            print(f"[OLLAMA] content 空，从 thinking 抠出: {json.dumps(data, ensure_ascii=False)[:120]}")
            return data
        return None

    try:
        return json.loads(content)
    except json.JSONDecodeError:
        data = _extract_json_from_text(content)
        if data:
            return data
        print(f"[OLLAMA WARN] JSON 解析失败 | 原始: {content[:200]}")
        return None


def ollama_health():
    try:
        models = ollama.list()
        names = []
        for m in (models.get("models", []) if isinstance(models, dict) else getattr(models, "models", [])):
            name = m.get("name") if isinstance(m, dict) else getattr(m, "model", "")
            if name:
                names.append(name)
        print(f"[OLLAMA] 服务在线，可用模型: {names}")
        if not any(OLLAMA_MODEL in n for n in names):
            print(f"[OLLAMA WARN] 未找到模型 {OLLAMA_MODEL}，请检查 OLLAMA_MODEL 配置")
            return False
        return True
    except Exception as e:
        print(f"[OLLAMA FAIL] 服务不可达: {type(e).__name__}: {e}")
        return False


def _clean_answer(a):
    a = str(a).strip().strip('"').strip("'")
    for prefix in ("答案：", "答案:", "答：", "答:"):
        if a.startswith(prefix):
            a = a[len(prefix):].strip()
    return a


def ask_ollama(question_type, stem, options=None, blank_count=None):
    if question_type == "fill":
        n = blank_count or 1
        system_prompt = (
            f"你是一个答题助手。这是一道填空题，题干中共有 {n} 个空。"
            "严格输出 JSON，格式：{\"answers\": [\"第1空答案\", \"第2空答案\"]}。"
            f"answers 数组必须正好 {n} 个元素，按空在题干中出现的顺序。"
            "每个答案只写答案本身：不要写序号、不要写“答案：”、不要解释、不要加引号。"
            "答案要简洁精确，只填关键术语/人名/数字/公式。"
        )
        user_prompt = f"题干：{stem}"
    else:
        system_prompt = (
            "你是一个答题助手。只根据题目和选项作答，不要解释。"
            "严格输出 JSON，格式：{\"answers\": [\"...\"]}。"
            "单选题 answers 只能有 1 个选项字母（如 A）；"
            "多选题 answers 可以有多个选项字母，按字母顺序（如 [\"A\",\"C\"]）；"
            "判断题 answers 只能是 \"对\" 或 \"错\"。"
        )
        user_parts = [f"题型：{question_type}", f"题干：{stem}"]
        if options:
            user_parts.append("选项：")
            for opt in options:
                user_parts.append(f"{opt['label']}. {opt['text']}")
        user_prompt = "\n".join(user_parts)

    use_think = (question_type == "fill" and FILL_USE_THINKING)

    last_err = None
    for attempt in range(1, OLLAMA_RETRY + 2):
        try:
            data = _ollama_chat_with_fallback(
                model=OLLAMA_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                format="json",
                keep_alive=OLLAMA_KEEP_ALIVE,
                options={"temperature": OLLAMA_TEMPERATURE},
                think=use_think,
            )
            if data:
                answers = data.get("answers", [])
                if not isinstance(answers, list):
                    answers = [answers]
                answers = [_clean_answer(a) for a in answers if str(a).strip()]
                if answers:
                    return {"answers": answers}
            print(f"[OLLAMA WARN] 第{attempt}次未拿到有效 answers")
        except Exception as e:
            print(f"[OLLAMA WARN] 第{attempt}次异常: {type(e).__name__}: {e}")
            last_err = repr(e)

        if attempt <= OLLAMA_RETRY:
            time.sleep(2)

    print(f"[OLLAMA FAIL] 重试结束仍失败（最后: {last_err}）")
    return {"answers": []}


def _norm_fill_answer(s):
    s = unicodedata.normalize('NFKC', str(s)).strip().lower()
    s = re.sub(r'[\s\u3000]+', '', s)
    s = re.sub(r'[，。、；：""''（）()【】\[\]<>《》!?？.,;:"]', '', s)
    return s


def ask_ollama_vote(question_type, stem, options=None, blank_count=None, n_samples=VOTE_SAMPLES):
    runs = []
    for k in range(n_samples):
        if question_type == "fill":
            r = ask_ollama("fill", stem, None, blank_count=blank_count)
        else:
            r = ask_ollama(question_type, stem, options, blank_count=blank_count)
        ans = r.get("answers", [])
        print(f"[VOTE] 第{k+1}/{n_samples}次 {question_type}: {ans}")
        if ans:
            runs.append(ans)

    if not runs:
        return {"answers": []}

    if question_type == "fill":
        n = blank_count or len(runs[0])
        final = []
        for i in range(n):
            candidates = [run[i] for run in runs if i < len(run)]
            if not candidates:
                final.append("")
                continue
            counter = {}
            key_to_orig = {}
            for c in candidates:
                key = _norm_fill_answer(c)
                counter[key] = counter.get(key, 0) + 1
                key_to_orig.setdefault(key, c)
            best_key = max(counter, key=counter.get)
            final.append(key_to_orig[best_key])
            print(f"[VOTE] 填空第{i+1}空候选={candidates} → 取={key_to_orig[best_key]}")
        return {"answers": final}

    counter = {}
    key_to_orig = {}
    for run in runs:
        key = tuple(sorted(str(a).strip().upper() for a in run))
        counter[key] = counter.get(key, 0) + 1
        key_to_orig.setdefault(key, run)
    best_key = max(counter, key=counter.get)
    detail = " | ".join(f"{list(k)}x{v}" for k, v in counter.items())
    print(f"[VOTE] {question_type} 票数={detail} → 取={key_to_orig[best_key]}")
    return {"answers": key_to_orig[best_key]}


def ask_ollama_vision(png_bytes, dom_stem_hint=""):
    system_prompt = (
        "你是一个答题助手。我会给你一张题目截图，请识别题目并作答。"
        "严格输出 JSON，格式："
        "{\"type\":\"single|multiple|judge|fill\","
        "\"stem\":\"题干\","
        "\"options\":[{\"label\":\"A\",\"text\":\"...\"}],"
        "\"answers\":[\"A\"]}"
        "单选题 answers 只能 1 个字母；多选题多个字母按字母顺序；"
        "判断题 answers 只能是 \"对\" 或 \"错\"；填空题按空格顺序返回文本。"
        "不要解释。"
    )
    user_text = "请识别这张题目截图并作答。"
    if dom_stem_hint:
        user_text += f"\n（DOM 题干供参考，可能有误：{dom_stem_hint[:200]}）"

    last_err = None
    for attempt in range(1, OLLAMA_RETRY + 2):
        try:
            data = _ollama_chat_with_fallback(
                model=OLLAMA_MODEL,
                messages=[{
                    "role": "user",
                    "content": user_text,
                    "images": [png_bytes],
                }],
                format="json",
                keep_alive=OLLAMA_KEEP_ALIVE,
                options={"temperature": OLLAMA_TEMPERATURE},
                think=False,
            )
            if not data:
                print(f"[VISION WARN] 第{attempt}次未拿到 JSON")
                if attempt <= OLLAMA_RETRY:
                    time.sleep(2)
                continue

            qtype = (data.get("type") or "").strip().lower()
            if qtype not in ("single", "multiple", "judge", "fill"):
                print(f"[VISION WARN] 未知题型: {qtype}")
                return None

            answers = data.get("answers", [])
            if not isinstance(answers, list):
                answers = [answers]
            answers = [_clean_answer(a) for a in answers if str(a).strip()]
            if not answers:
                print(f"[VISION WARN] answers 为空")
                return None

            return {
                "type": qtype,
                "stem": (data.get("stem") or "").strip(),
                "options": data.get("options") or [],
                "answers": answers,
            }

        except Exception as e:
            print(f"[VISION WARN] 第{attempt}次异常: {type(e).__name__}: {e}")
            last_err = repr(e)

        if attempt <= OLLAMA_RETRY:
            time.sleep(2)

    print(f"[VISION FAIL] 重试结束仍失败（最后: {last_err}）")
    return None


# ============================================================
# 截图
# ============================================================
def screenshot_question():
    driver.execute_script("""
        const blocks = [...document.querySelectorAll(arguments[0])];
        let block = null;
        for (const b of blocks) { if (b.offsetParent !== null) { block = b; break; } }
        if (!block && blocks.length) block = blocks[0];
        if (block) block.scrollIntoView({block: 'center'});
    """, SEL_QUESTION_CONTENT)
    time.sleep(0.5)

    png = driver.get_screenshot_as_png()
    img = Image.open(io.BytesIO(png)).convert("RGB")
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=SCREENSHOT_QUALITY)
    return buf.getvalue()


# ============================================================
# 题库：答题卡
# ============================================================
def get_answer_card_status():
    return driver.execute_script("""
        const items = [...document.querySelectorAll(arguments[0])];
        return items.map((el, i) => [i, el.classList.contains(arguments[1])]);
    """, SEL_ANSWER_CARD, CLS_CARD_DONE)


def click_answer_card(index):
    return driver.execute_script("""
        const items = [...document.querySelectorAll(arguments[0])];
        if (arguments[1] >= items.length) return false;
        const el = items[arguments[1]];
        el.scrollIntoView({block: 'center'});
        el.click();
        return true;
    """, SEL_ANSWER_CARD, index)


# ============================================================
# 题库：抓当前题目
# ============================================================
def get_current_question():
    return driver.execute_script("""
        const blocks = [...document.querySelectorAll(arguments[0])];
        let block = null;
        for (const b of blocks) { if (b.offsetParent !== null) { block = b; break; } }
        if (!block && blocks.length) block = blocks[0];
        if (!block) return null;

        const typeEl = block.querySelector(arguments[1]);
        const typeText = typeEl ? typeEl.textContent.trim() : '';

        let type = '';
        if (typeText.includes('单选')) type = 'single';
        else if (typeText.includes('多选')) type = 'multiple';
        else if (typeText.includes('判断')) type = 'judge';
        else if (typeText.includes('填空')) type = 'fill';

        const stemEl = block.querySelector(arguments[2]);
        const stem = stemEl ? stemEl.textContent.trim() : '';

        let options = [];
        if (type === 'single' || type === 'judge') {
            const lis = block.querySelectorAll(arguments[3]);
            options = [...lis].map(li => {
                const lab = li.querySelector(arguments[4]);
                const txt = li.querySelector(arguments[5]);
                return {
                    label: lab ? lab.textContent.trim().replace(/[.、\\s]/g, '') : '',
                    text: txt ? txt.textContent.trim() : ''
                };
            }).filter(o => o.label);
        } else if (type === 'multiple') {
            const lbs = block.querySelectorAll(arguments[6]);
            options = [...lbs].map(lb => {
                const lab = lb.querySelector(arguments[7]);
                const txt = lb.querySelector(arguments[8]);
                return {
                    label: lab ? lab.textContent.trim().replace(/[.、\\s]/g, '') : '',
                    text: txt ? txt.textContent.trim() : ''
                };
            }).filter(o => o.label);
        }

        const blanks = block.querySelectorAll(arguments[9]);

        return { type, typeText, stem, options, blank_count: blanks.length };
    """, SEL_QUESTION_CONTENT, SEL_QUESTION_TYPE, SEL_QUESTION_STEM,
         SEL_RADIO_OPTIONS, SEL_RADIO_LABEL, SEL_RADIO_TEXT,
         SEL_CHECKBOX_OPTIONS, SEL_CHECKBOX_LABEL, SEL_CHECKBOX_TEXT,
         SEL_FILL_INPUT)


# ============================================================
# 题库：点击 / 填写工具
# ============================================================
def _click_element_with_fallback(el, inner_selector=None):
    try:
        el.click()
        return True
    except Exception:
        pass
    if inner_selector:
        try:
            inner = el.find_element(By.CSS_SELECTOR, inner_selector)
            inner.click()
            return True
        except Exception:
            pass
    try:
        driver.execute_script("arguments[0].click();", el)
        return True
    except Exception:
        pass
    return False


def _set_input_value(inp, text):
    text = str(text)
    ok = False
    try:
        inp.clear()
        inp.send_keys(text)
        ok = True
    except Exception:
        pass

    try:
        driver.execute_script("""
            const el = arguments[0];
            const val = arguments[1];
            el.focus();
            if (el.value !== val) { el.value = val; }
            el.dispatchEvent(new Event('input', {bubbles: true}));
            el.dispatchEvent(new Event('change', {bubbles: true}));
            el.blur();
        """, inp, text)
        ok = True
    except Exception:
        pass

    return ok


def _apply_answer_by_dom(qtype, answers):
    blocks = driver.find_elements(By.CSS_SELECTOR, SEL_QUESTION_CONTENT)
    visible_block = None
    for b in blocks:
        try:
            if b.is_displayed():
                visible_block = b
                break
        except Exception:
            continue
    if visible_block is None and blocks:
        visible_block = blocks[0]
    if visible_block is None:
        return False

    if qtype in ("single", "judge"):
        want = set()
        for a in answers:
            a = str(a).strip().upper()
            if qtype == "judge":
                if a in ("对", "正确", "TRUE", "T", "√", "YES", "Y"):
                    want.add("A")
                elif a in ("错", "错误", "FALSE", "F", "×", "NO", "N"):
                    want.add("B")
                else:
                    want.add(a)
            else:
                want.add(a)

        lis = visible_block.find_elements(By.CSS_SELECTOR, SEL_RADIO_OPTIONS)
        clicked = 0
        for li in lis:
            try:
                lab_el = li.find_element(By.CSS_SELECTOR, SEL_RADIO_LABEL)
                lab = lab_el.text.strip().replace(".", "").strip().upper()
            except Exception:
                continue
            if lab not in want:
                continue
            if _click_element_with_fallback(li, "i.checkIcon"):
                clicked += 1
        time.sleep(0.8)
        print(f"[ANSWER] {qtype} 点击 {clicked} 个，期望 {sorted(want)}")
        return clicked > 0

    if qtype == "multiple":
        want = set(str(a).strip().upper() for a in answers)
        lbs = visible_block.find_elements(By.CSS_SELECTOR, SEL_CHECKBOX_OPTIONS)
        clicked = 0
        for lb in lbs:
            try:
                lab_el = lb.find_element(By.CSS_SELECTOR, SEL_CHECKBOX_LABEL)
                lab = lab_el.text.strip().replace(".", "").strip().upper()
            except Exception:
                continue
            if lab not in want:
                continue
            try:
                inp = lb.find_element(By.CSS_SELECTOR, "input[type=checkbox]")
                if inp.is_selected():
                    continue
            except Exception:
                pass
            if _click_element_with_fallback(lb, "span.el-checkbox__inner"):
                clicked += 1
        time.sleep(0.8)
        print(f"[ANSWER] multiple 点击 {clicked} 个，期望 {sorted(want)}")
        return clicked > 0

    if qtype == "fill":
        inputs = visible_block.find_elements(By.CSS_SELECTOR, SEL_FILL_INPUT)
        n_inputs = len(inputs)
        if n_inputs == 0:
            print("[FILL WARN] 未找到填空输入框")
            return False

        aligned = list(answers)
        if len(aligned) < n_inputs:
            print(f"[FILL WARN] 模型只给 {len(aligned)} 个答案，需 {n_inputs} 个，用最后一项补齐")
            while len(aligned) < n_inputs:
                aligned.append(aligned[-1] if aligned else "")
        elif len(aligned) > n_inputs:
            print(f"[FILL WARN] 模型给 {len(aligned)} 个答案，需 {n_inputs} 个，截断")
            aligned = aligned[:n_inputs]

        filled = 0
        for i, inp in enumerate(inputs):
            if _set_input_value(inp, aligned[i]):
                filled += 1
            else:
                print(f"[FILL WARN] 第{i+1}空填写失败")

        time.sleep(0.5)

        actual = []
        for inp in inputs:
            try:
                actual.append(driver.execute_script("return arguments[0].value;", inp) or "")
            except Exception:
                actual.append("")

        print(f"[ANSWER] fill 填写 {filled}/{n_inputs} 空")
        print(f"[ANSWER] fill 期望={aligned}")
        print(f"[ANSWER] fill 实际={actual}")
        return filled > 0

    return False


def answer_current_question_vision():
    dom_q = get_current_question() or {}
    dom_stem = dom_q.get("stem", "")

    result = None
    if OLLAMA_VISION:
        try:
            png = screenshot_question()
            result = ask_ollama_vision(png, dom_stem_hint=dom_stem)
        except Exception as e:
            print(f"[VISION WARN] 截图/调用失败: {type(e).__name__}: {e}")

    if result is None:
        if not dom_q.get("type") or not dom_q.get("stem"):
            print("[ANSWER SKIP] 视觉失败且 DOM 抓取也为空")
            return False
        print("[ANSWER] 回退到文本模型（投票）")
        text_result = ask_ollama_vote(
            dom_q["type"], dom_q["stem"], dom_q.get("options"),
            blank_count=dom_q.get("blank_count"),
        )
        result = {
            "type": dom_q["type"],
            "stem": dom_q["stem"],
            "options": dom_q.get("options") or [],
            "answers": text_result.get("answers", []),
        }

    if not result or not result["answers"]:
        return False

    qtype = result["type"]
    answers = result["answers"]
    print(f"[ANSWER] 最终: type={qtype} answers={answers}")
    print(f"[ANSWER] 题干: {result['stem'][:150]}")
    return _apply_answer_by_dom(qtype, answers)


# ============================================================
# 题库：提交 & 检查
# ============================================================
def submit_and_check():
    print(f"[SUBMIT] 提交前等待 {WAIT_BEFORE_SUBMIT}s ...")
    time.sleep(WAIT_BEFORE_SUBMIT)

    try:
        btn = WebDriverWait(driver, TIMEOUT_SUBMIT).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, SEL_SUBMIT_BTN))
        )
    except Exception as e:
        print(f"[SUBMIT WARN] 未找到提交按钮: {type(e).__name__}")
        return False

    try:
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", btn)
        time.sleep(0.5)
    except Exception:
        pass

    clicked = False
    try:
        btn = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, SEL_SUBMIT_BTN))
        )
        btn.click()
        clicked = True
        print("[SUBMIT] 普通点击成功")
    except Exception as e:
        print(f"[SUBMIT] 普通点击失败，尝试 JS: {type(e).__name__}")

    if not clicked:
        try:
            driver.execute_script("arguments[0].click();", btn)
            clicked = True
            print("[SUBMIT] JS 点击成功")
        except Exception as e2:
            print(f"[SUBMIT FAIL] JS 点击也失败: {type(e2).__name__}: {e2}")
            return False

    before_url = driver.current_url
    end = time.time() + WAIT_AFTER_SUBMIT
    while time.time() < end:
        try:
            msgs = driver.find_elements(By.CSS_SELECTOR, SEL_MESSAGE)
            for m in msgs:
                txt = (m.text or "").strip()
                if "还有题目没有完成" in txt:
                    print(f"[SUBMIT] 弹窗：{txt}")
                    return False
        except Exception:
            pass

        try:
            if driver.current_url != before_url:
                print("[SUBMIT] 页面已跳转，视为提交成功")
                return True
        except Exception:
            pass

        try:
            if not driver.find_elements(By.CSS_SELECTOR, SEL_SUBMIT_BTN):
                print("[SUBMIT] 提交按钮消失，视为成功")
                return True
        except Exception:
            pass

        time.sleep(0.5)

    print(f"[SUBMIT] {WAIT_AFTER_SUBMIT}s 内未检测到弹窗，视为成功")
    return True


# ============================================================
# 题库：主流程
# ============================================================
def solve_question_bank():
    try:
        WebDriverWait(driver, TIMEOUT_BANK_LOAD).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, SEL_ANSWER_CARD))
        )
    except Exception:
        print("[BANK WARN] 未检测到答题卡，跳过")
        return 0

    status = get_answer_card_status()
    raw_total = len(status)
    total = max(0, raw_total - ANSWER_CARD_OFFSET)
    if total == 0:
        print(f"[BANK WARN] 节点数为 0（原始 {raw_total}）")
        return 0
    print(f"[BANK] 答题卡节点 {raw_total} 个，遍历上限 {total}，"
          f"初始 answer class 数={sum(1 for i, a in status[:total] if a)}")

    solved = 0
    bad_indices = set()

    def try_answer(i):
        nonlocal solved
        if i in bad_indices:
            return False
        click_answer_card(i)
        time.sleep(1.5)
        q = get_current_question()
        if not q or not q.get("stem"):
            print(f"[BANK {i+1}/{total}] 抓取失败 → 标记为干扰节点，后续跳过")
            bad_indices.add(i)
            return False
        print(f"[BANK {i+1}/{total}] 作答")
        if not answer_current_question_vision():
            return False
        solved += 1
        return True

    for i in range(total):
        st = get_answer_card_status()
        if i < len(st) and st[i][1]:
            print(f"[BANK {i+1}/{total}] 已答(answer class)，跳过")
            continue
        if i in bad_indices:
            continue
        try_answer(i)
        time.sleep(WAIT_AFTER_ANSWER)

    print(f"[BANK] 首轮结束 | 作答成功 {solved} 道 | 干扰节点: {sorted(bad_indices)}")

    last_todo_count = None
    for attempt in range(1, SUBMIT_RETRY + 1):
        print(f"[BANK] 第{attempt}轮尝试提交")
        if submit_and_check():
            print("[BANK] 提交成功")
            return solved

        st = get_answer_card_status()
        todo = [i for i, a in st[:total] if not a and i not in bad_indices]
        print(f"[BANK] 提交被拒，答题卡显示 no-answer 的题（排除干扰）: {todo}")

        if not todo:
            print("[BANK] 除干扰节点外均 answer，稍等后重试提交")
            time.sleep(3)
            continue

        if last_todo_count is not None and len(todo) >= last_todo_count:
            print(f"[BANK] 补做无进展（{last_todo_count} → {len(todo)}），停止")
            break
        last_todo_count = len(todo)

        for i in todo:
            try_answer(i)
            time.sleep(WAIT_AFTER_ANSWER)

    print("[SUBMIT FAIL] 多次提交仍未通过")
    return solved


# ============================================================
# 主流程
# ============================================================
try:
    if not ollama_health():
        print("[WARN] Ollama 不可用，答题环节会全部失败，脚本仍会继续跑完流程")
    if OLLAMA_VISION:
        print(f"[OK] 视觉模式已启用（模型={OLLAMA_MODEL}）")
    else:
        print(f"[OK] 纯文本模式（模型={OLLAMA_MODEL}），每题投票 {VOTE_SAMPLES} 次")

    driver.get(URL)
    print("[OK] 页面已打开")
    input(">>> 如需登录，请先登录，然后按回车继续...")

    tried_titles = set()
    chapter_count = 0
    round_no = 0
    stats = []

    while chapter_count < MAX_CHAPTERS:
        driver.get(URL)
        try:
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, SEL_PROGRESS_TEXT)))
        except Exception:
            print("[WARN] 左列未加载，退出外层")
            break
        time.sleep(3)

        try:
            texts = _progress_text_js()
            print(f"[DEBUG] 进度文本样本(前20): {texts[:20]}")
        except Exception:
            pass

        low_list = get_low_progress_chapters()
        # 过滤已尝试的标题（保持原有 (title, el) 兼容，进度信息可忽略）
        remaining = [(t, el, p, raw) for (t, el, p, raw) in low_list if t not in tried_titles]

        round_no += 1
        phase = "START" if round_no == 1 else "AFTER"
        print(f"[{phase}] 第{round_no}轮 | 进度<{PROGRESS_THRESHOLD} 总数={len(low_list)} "
              f"未尝试={len(remaining)}")
        stats.append({
            "phase": phase,
            "round": round_no,
            "zero_total": len(low_list),        # 沿用字段名，含义变为「低进度总数」
            "zero_untried": len(remaining),
            "picked": None,
            "action_ok": None,
            "improve_ok": None,
            "solved": 0,
        })

        if not remaining:
            print(f"[OK] 所有进度<{PROGRESS_THRESHOLD} 的章节都已尝试，结束")
            break

        chapter_title, chapter_el, chapter_progress, chapter_raw = remaining[0]
        chapter_count += 1
        stats[-1]["picked"] = chapter_title
        print(f"[CHAPTER {chapter_count}/{MAX_CHAPTERS}] 点击: {chapter_title} "
              f"(进度={chapter_progress} 原文='{chapter_raw}')")

        try:
            chapter_el.click()
        except Exception:
            driver.execute_script("arguments[0].click();", chapter_el)
        time.sleep(WAIT_AFTER_CLICK)

        action_ok = click_by_selector(SEL_ACTION_BTN, "ACTION", TIMEOUT_ACTION)
        stats[-1]["action_ok"] = action_ok

        if action_ok:
            time.sleep(WAIT_AFTER_ACTION)
            improve_ok = click_by_selector(SEL_IMPROVE_BTN, "IMPROVE", TIMEOUT_IMPROVE)
            stats[-1]["improve_ok"] = improve_ok

            if improve_ok:
                time.sleep(WAIT_AFTER_IMPROVE)
                solved = solve_question_bank()
                stats[-1]["solved"] = solved
            else:
                print(f"[IMPROVE WARN] 「{chapter_title}」第二次去提升未点成功")
        else:
            print(f"[ACTION WARN] 「{chapter_title}」第一次去提升未点成功，跳过后续")
            stats[-1]["improve_ok"] = False

        tried_titles.add(chapter_title)

    print("\n[STATS] 每轮章节统计：")
    for s in stats:
        a1 = "OK" if s["action_ok"] else ("FAIL" if s["action_ok"] is False else "-")
        a2 = "OK" if s["improve_ok"] else ("FAIL" if s["improve_ok"] is False else "-")
        print(f"  [{s['phase']}] 第{s['round']}轮: "
              f"<{PROGRESS_THRESHOLD}总数={s['zero_total']}, 未尝试={s['zero_untried']}, "
              f"点击={s['picked']}, 去提升①={a1}, 去提升②={a2}, 答题={s['solved']}")
    print(f"[ALL DONE] 共处理 {chapter_count} 个章节")

except Exception as e:
    print(f"[ERROR] {type(e).__name__}: {e}")

finally:
    driver.quit()
    print("[OK] 浏览器已关闭")
