from selenium import webdriver
from selenium.webdriver.edge.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import random

URL = ("https://ai-smart-course-student-pro.zhihuishu.com/"
       "singleCourse/knowledgeStudy/新课程ID/新章节ID"
       "?mapUid=新的mapUid")
#把你的课程链接输在这里(如果不懂py的就按照这个格式填一下吧)

options = Options()
options.add_argument("--start-maximized")

driver = webdriver.Edge(options=options)
wait = WebDriverWait(driver, 60)

processed_fps = set()
video_fail_counts = {}


def get_all_boxes():
    return driver.execute_script("""
        const titles = [...document.querySelectorAll('.resources-detail-title')];
        const startTitle = titles.find(t => t.textContent.includes('必学资源'));
        const endTitle = titles.find(t => t.textContent.includes('选学资源'));
        if (!startTitle) return [];

        const selector = '.icon-box.other, .icon-box.book, .icon-box.video';
        const allBoxes = [...document.querySelectorAll(selector)];
        const result = [];
        const typeCount = {};

        for (const box of allBoxes) {
            if (!(startTitle.compareDocumentPosition(box) & Node.DOCUMENT_POSITION_FOLLOWING)) continue;
            if (endTitle && !(endTitle.compareDocumentPosition(box) & Node.DOCUMENT_POSITION_PRECEDING)) continue;

            const type = box.classList.contains('video') ? 'video' :
                         box.classList.contains('book') ? 'book' : 'other';

            let p = box.parentElement;
            let title = '';
            while (p && p !== document.body) {
                const t = (p.textContent || '').trim();
                if (t.length > 0) { title = t.substring(0, 40); break; }
                p = p.parentElement;
            }

            const key = title + '|' + type;
            typeCount[key] = (typeCount[key] || 0) + 1;

            result.push({
                el: box,
                fp: key + '|' + typeCount[key],
                type: type
            });
        }
        return result;
    """)


def summarize_remaining(boxes):
    remaining = [b for b in boxes if b['fp'] not in processed_fps]
    counts = {}
    for b in remaining:
        counts[b['type']] = counts.get(b['type'], 0) + 1
    summary = ", ".join(f"{k}={v}" for k, v in counts.items()) if counts else "无"
    return remaining, summary


def get_zero_chapters():
    result = []
    try:
        pcts = driver.find_elements(By.CSS_SELECTOR, ".pct-num")
    except Exception:
        return result

    for pct in pcts:
        try:
            style = (pct.get_attribute("style") or "").replace(" ", "")
            if "width:0%" not in style:
                continue

            title = driver.execute_script("""
                let p = arguments[0].parentElement;
                for (let i = 0; i < 8 && p; i++) {
                    const t = p.querySelector ? p.querySelector('.item-title') : null;
                    if (t) return t.getAttribute('title') || (t.textContent || '').trim();
                    p = p.parentElement;
                }
                return '';
            """, pct)
            if not title:
                continue

            click_el = driver.execute_script("""
                let p = arguments[0].parentElement;
                for (let i = 0; i < 8 && p; i++) {
                    if (p.classList && p.classList.contains('item-mask')) return p;
                    p = p.parentElement;
                }
                return arguments[0].parentElement;
            """, pct)
            if click_el is None:
                continue

            result.append((title, click_el))
        except Exception:
            continue
    return result


def get_chapter_by_title(title):
    try:
        pcts = driver.find_elements(By.CSS_SELECTOR, ".pct-num")
    except Exception:
        return None
    for pct in pcts:
        try:
            t = driver.execute_script("""
                let p = arguments[0].parentElement;
                for (let i = 0; i < 8 && p; i++) {
                    const el = p.querySelector ? p.querySelector('.item-title') : null;
                    if (el) return el.getAttribute('title') || (el.textContent || '').trim();
                    p = p.parentElement;
                }
                return '';
            """, pct)
            if t == title:
                return driver.execute_script("""
                    let p = arguments[0].parentElement;
                    for (let i = 0; i < 8 && p; i++) {
                        if (p.classList && p.classList.contains('item-mask')) return p;
                        p = p.parentElement;
                    }
                    return arguments[0].parentElement;
                """, pct)
        except Exception:
            continue
    return None


def wait_for_boxes(timeout=15):
    end = time.time() + timeout
    while time.time() < end:
        boxes = get_all_boxes()
        if boxes:
            return boxes
        time.sleep(1)
    return []


def reenter_chapter(chapter_title):
    print(f"[REENTER] 重新进入并点击章节: {chapter_title}")
    try:
        driver.get(URL)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".pct-num")))
    except Exception as e:
        print(f"[REENTER FAIL] 页面加载失败: {type(e).__name__}: {e}")
        return False
    time.sleep(3)
    el = get_chapter_by_title(chapter_title)
    if el is None:
        print(f"[REENTER FAIL] 未找到章节标题: {chapter_title}")
        try:
            titles = driver.execute_script(
                "return [...document.querySelectorAll('.item-title')]"
                ".map(e => e.getAttribute('title') || (e.textContent || '').trim()).slice(0, 20)"
            )
            print(f"[REENTER DEBUG] 当前页面 title 列表: {titles}")
        except Exception:
            pass
        return False
    try:
        el.click()
    except Exception as e:
        print(f"[REENTER] 普通点击失败，尝试 JS: {type(e).__name__}")
        try:
            driver.execute_script("arguments[0].click();", el)
        except Exception as e2:
            print(f"[REENTER FAIL] JS 点击也失败: {type(e2).__name__}")
            return False
    time.sleep(5)
    return True


def wait_video_paused(timeout_started=120, timeout_paused=7200):
    print("[VIDEO] 等待视频开始播放...")
    start = time.time()
    started = False
    while time.time() - start < timeout_started:
        try:
            for v in driver.find_elements(By.TAG_NAME, "video"):
                try:
                    if v.is_displayed() and driver.execute_script(
                        "return arguments[0].currentTime > 0.5", v
                    ):
                        started = True
                        break
                except Exception:
                    continue
        except Exception:
            pass
        if started:
            break
        time.sleep(0.5)

    if not started:
        print("[VIDEO WARN] 视频未开始播放（点击可能无效）")
        return False
    print("[VIDEO] 视频已开始播放，等待暂停...")

    start = time.time()
    pause_count = 0
    while time.time() - start < timeout_paused:
        try:
            paused_now = None
            for v in driver.find_elements(By.TAG_NAME, "video"):
                try:
                    if not v.is_displayed():
                        continue
                    ct = driver.execute_script("return arguments[0].currentTime", v)
                    if ct is None or ct <= 0.5:
                        continue
                    paused_now = driver.execute_script("return arguments[0].paused", v)
                    break
                except Exception:
                    continue
            if paused_now is True:
                pause_count += 1
                if pause_count >= 3:
                    print("[VIDEO] 视频暂停稳定")
                    return True
            else:
                pause_count = 0
        except Exception:
            pass
        time.sleep(1)

    print("[VIDEO WARN] 等待暂停超时")
    return False


try:
    driver.get(URL)
    print("[OK] 页面已打开")
    input(">>> 如需登录，请先登录，然后按回车继续...")

    tried_titles = set()
    chapter_count = 0
    MAX_CHAPTERS = 100

    while chapter_count < MAX_CHAPTERS:
        driver.get(URL)
        try:
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".pct-num")))
        except Exception:
            print("[WARN] 左列未加载，退出外层")
            break
        time.sleep(3)

        zero_list = get_zero_chapters()
        remaining_titles = [(t, el) for t, el in zero_list if t not in tried_titles]
        print(f"\n[OUTER] 当前 0% 章节 {len(zero_list)} 个，其中未尝试 {len(remaining_titles)} 个")

        if not remaining_titles:
            print("[OK] 所有 0% 章节都已尝试，结束")
            break

        chapter_title, chapter_el = remaining_titles[0]
        chapter_count += 1
        print(f"\n[CHAPTER {chapter_count}/{MAX_CHAPTERS}] 处理: {chapter_title}")

        try:
            chapter_el.click()
        except Exception:
            driver.execute_script("arguments[0].click();", chapter_el)
        time.sleep(5)

        processed_fps.clear()
        video_fail_counts.clear()
        inner_count = 0
        MAX_INNER = 200
        inner_success = False

        while inner_count < MAX_INNER:
            boxes = get_all_boxes()
            remaining, summary = summarize_remaining(boxes)
            print(f"[INNER SCAN] 共 {len(boxes)} 个，未处理 {len(remaining)} 个 ({summary})")

            if not remaining:
                if not boxes:
                    print("[INNER] 无必学资源区，退出内层")
                else:
                    inner_success = True
                    print(f"[INNER OK] 本章节处理完，共 {inner_count} 个")
                break

            t = remaining[0]
            box_fp, box_el, box_type = t['fp'], t['el'], t['type']
            print(f"[INNER] 处理第 {inner_count + 1} 个：{box_type}")

            try:
                box_el.click()
                print(f"[INNER] 已点击 {box_type}")
            except Exception as e:
                print(f"[INNER WARN] 普通点击失败: {type(e).__name__}: {e}")
                try:
                    driver.execute_script("arguments[0].click();", box_el)
                    print("[INNER] JS 点击成功")
                except Exception as e2:
                    print(f"[INNER WARN] JS 点击也失败: {type(e2).__name__}: {e2}")
                    time.sleep(2)
                    continue

            time.sleep(2)

            if box_type == "video":
                video_ok = wait_video_paused()
                if video_ok:
                    processed_fps.add(box_fp)
                    inner_count += 1
                    video_fail_counts.pop(box_fp, None)
                else:
                    n = video_fail_counts.get(box_fp, 0) + 1
                    video_fail_counts[box_fp] = n
                    print(f"[INNER WARN] 视频检测失败第 {n} 次（不标记，资源列表恢复后重试）")
                    if n >= 3:
                        print("[INNER] 同一视频连续失败 3 次，强制标记跳过")
                        processed_fps.add(box_fp)
                        inner_count += 1

                boxes = wait_for_boxes(8)
                if not boxes:
                    print("[INNER] 资源列表消失，尝试重新进入章节")
                    if not reenter_chapter(chapter_title):
                        print("[INNER FAIL] 无法恢复章节，退出内层")
                        break
                    boxes = wait_for_boxes(15)
                    if not boxes:
                        print("[INNER FAIL] 重新进入后仍无资源列表，退出内层")
                        break
                print(f"[INNER] 资源列表可访问，共 {len(boxes)} 个")
                continue

            else:
                before_url = driver.current_url
                wait_sec = random.uniform(5, 15)
                print(f"[INNER] other/book 随机停留 {wait_sec:.1f}s")
                time.sleep(wait_sec)
                if driver.current_url != before_url:
                    print("[INNER] URL 变化，返回")
                    driver.back()
                    time.sleep(3)

                processed_fps.add(box_fp)
                inner_count += 1

        tried_titles.add(chapter_title)
        if inner_success:
            print(f"[CHAPTER OK] 「{chapter_title}」完成")
        else:
            print(f"[CHAPTER WARN] 「{chapter_title}」未完全成功，已标记避免死循环")

    print(f"\n[ALL DONE] 共处理 {chapter_count} 个章节")

except Exception as e:
    print(f"[ERROR] {type(e).__name__}: {e}")

finally:
    driver.quit()
    print("[OK] 浏览器已关闭")
