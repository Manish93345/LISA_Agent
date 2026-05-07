"""
LISA — WhatsApp Automation (v2 Fixed)
========================================
Fixes:
  1. BMP error — send_keys se emoji crash hota tha.
     Ab clipboard (pyperclip) se paste hoga — emoji/Hindi sab kaam karega.
  2. Search slow — unnecessary waits kam kiye.
"""

import time
import random
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.edge.options import Options
from selenium.common.exceptions import (
    TimeoutException, NoSuchElementException, ElementNotInteractableException
)

try:
    import pyperclip
    CLIPBOARD_OK = True
except ImportError:
    CLIPBOARD_OK = False

try:
    from config import settings
except ImportError:
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from config import settings


# ══════════════════════════════════════════════════════════════════════
#  SELECTORS
# ══════════════════════════════════════════════════════════════════════

SEARCH_BOX_SELECTORS = [
    (By.CSS_SELECTOR,  'div[role="searchbox"]'),
    (By.CSS_SELECTOR,  'div[contenteditable="true"][role="searchbox"]'),
    (By.CSS_SELECTOR,  'div[aria-label="Search input textbox"]'),
    (By.XPATH,         '//div[@aria-label="Search input textbox"]'),
    (By.XPATH,         '//div[@role="searchbox"]'),
    (By.CSS_SELECTOR,  'div[data-testid="search-input"]'),
    (By.CSS_SELECTOR,  '[data-testid="chat-list-search"] div[contenteditable="true"]'),
    (By.XPATH,         '//*[@data-testid="chat-list-search"]//div[@contenteditable="true"]'),
    (By.CSS_SELECTOR,  'div[contenteditable="true"][data-tab="3"]'),
    (By.XPATH,         '//div[@contenteditable="true"][@data-tab="3"]'),
    (By.CSS_SELECTOR,  'div[title="Search input textbox"]'),
    (By.XPATH,         '//div[@title="Search input textbox"]'),
    (By.XPATH,         '//div[@contenteditable="true"][contains(@aria-label,"Search")]'),
    (By.CSS_SELECTOR,  'input[type="text"][title*="Search"]'),
    (By.CSS_SELECTOR,  '#side div[contenteditable="true"]'),
    (By.XPATH,         '//div[@id="side"]//div[@contenteditable="true"]'),
]

LOGIN_DETECT_SELECTORS = [
    (By.CSS_SELECTOR, 'div[data-testid="chat-list"]'),
    (By.CSS_SELECTOR, '#side'),
    (By.CSS_SELECTOR, '#pane-side'),
    (By.XPATH,        '//div[@aria-label="Chat list"]'),
]

MSG_BOX_SELECTORS = [
    (By.CSS_SELECTOR,  'div[contenteditable="true"][data-tab="10"]'),
    (By.XPATH,         '//div[@contenteditable="true"][@data-tab="10"]'),
    (By.CSS_SELECTOR,  'div[aria-label="Type a message"]'),
    (By.XPATH,         '//div[@aria-label="Type a message"]'),
    (By.CSS_SELECTOR,  'div[title="Type a message"]'),
    (By.XPATH,         '//div[@role="textbox"][contains(@title,"message")]'),
    (By.XPATH,         '//footer//div[@contenteditable="true"]'),
    (By.XPATH,         '//div[@data-testid="conversation-compose-box-input"]'),
]


# ══════════════════════════════════════════════════════════════════════
#  HELPERS
# ══════════════════════════════════════════════════════════════════════

def _delay(lo=0.3, hi=0.7):
    time.sleep(random.uniform(lo, hi))


def _find_element(driver, selectors, timeout=6):
    for by, val in selectors:
        try:
            el = WebDriverWait(driver, timeout).until(
                EC.element_to_be_clickable((by, val))
            )
            return el
        except (TimeoutException, NoSuchElementException):
            continue
    return None


def _type_via_clipboard(driver, element, text: str):
    """
    THE FIX for BMP error:
    send_keys emoji bhejne ki koshish karta hai byte-by-byte,
    msedgedriver BMP (U+0000 to U+FFFF) se bahar nahi ja sakta.
    Clipboard se paste karo — koi restriction nahi.

    Requires: pip install pyperclip
    """
    if CLIPBOARD_OK:
        pyperclip.copy(text)
        element.send_keys(Keys.CONTROL + "v")
        _delay(0.15, 0.25)
    else:
        # JS execCommand fallback (pyperclip nahi hai toh)
        driver.execute_script(
            "arguments[0].focus();"
            "document.execCommand('insertText', false, arguments[1]);",
            element, text
        )
        _delay(0.15, 0.25)


def _js_find_search_box(driver):
    try:
        return driver.execute_script("""
            let el = document.querySelector('div[role="searchbox"]');
            if (el) return el;
            el = document.querySelector('[aria-label*="Search"][contenteditable="true"]');
            if (el) return el;
            const side = document.querySelector('#side') || document.querySelector('#pane-side');
            if (side) {
                el = side.querySelector('div[contenteditable="true"]');
                if (el) return el;
            }
            el = document.querySelector('div[data-tab="3"]');
            if (el) return el;
            for (const div of document.querySelectorAll('div[contenteditable="true"]')) {
                const label = (div.getAttribute('aria-label') || '').toLowerCase();
                const title = (div.getAttribute('title') || '').toLowerCase();
                if (label.includes('search') || title.includes('search')) return div;
            }
            return null;
        """)
    except Exception as e:
        print(f"  [WhatsApp] JS search box error: {e}")
        return None


def _js_click_contact(driver, name: str):
    name_lower = name.lower()
    try:
        return driver.execute_script(f"""
            const q = "{name_lower}";
            for (const span of document.querySelectorAll('span[title]')) {{
                if (!span.offsetParent) continue;
                if (span.title.toLowerCase().includes(q)) {{
                    let el = span;
                    for (let i = 0; i < 10; i++) {{
                        el = el.parentElement;
                        if (!el) break;
                        const role = el.getAttribute('role');
                        const tab  = el.getAttribute('tabindex');
                        if (role === 'listitem' || role === 'button' || tab === '0' || tab === '-1') {{
                            el.click();
                            return span.title;
                        }}
                    }}
                    span.click();
                    return span.title;
                }}
            }}
            return null;
        """)
    except Exception as e:
        print(f"  [WhatsApp] JS contact click error: {e}")
        return None


# ══════════════════════════════════════════════════════════════════════
#  MAIN CLASS
# ══════════════════════════════════════════════════════════════════════

class WhatsAppDriver:

    def __init__(self):
        self.driver: webdriver.Edge | None = None

    def start(self) -> bool:
        profile_dir = settings.WHATSAPP_PROFILE_DIR
        Path(profile_dir).mkdir(parents=True, exist_ok=True)
        first_run = not any(Path(profile_dir).iterdir())

        print("  [WhatsApp] Edge browser start ho rha hai...")
        opts = Options()
        opts.add_argument(f"--user-data-dir={profile_dir}")
        opts.add_argument("--profile-directory=Default")
        opts.add_argument("--no-sandbox")
        opts.add_argument("--disable-dev-shm-usage")
        opts.add_argument("--log-level=3")
        opts.add_experimental_option("excludeSwitches", ["enable-logging"])
        if settings.WHATSAPP_HEADLESS:
            opts.add_argument("--headless=new")

        try:
            self.driver = webdriver.Edge(options=opts)
        except Exception as e:
            print(f"  [X] Edge driver error: {e}")
            return False

        self.driver.get(settings.WHATSAPP_URL)
        print("  [WhatsApp] WhatsApp Web load ho rha hai...")

        if first_run:
            self.driver.maximize_window()
            print("  [WhatsApp] Pehli baar — QR scan karo Edge mein")
            ok = self._wait_login(timeout=120)
        else:
            ok = self._wait_login(timeout=settings.WHATSAPP_LOAD_TIMEOUT)

        if not ok:
            print("  [X] Login timeout")
            return False

        print("  [WhatsApp] QR scan successful! Session save ho gaya")
        # 8s → 3s
        print("  [WhatsApp] Sidebar load ho rhi hai (3s wait)...")
        time.sleep(3)
        print("  [WhatsApp] Ready!")
        return True

    def _wait_login(self, timeout=60) -> bool:
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.any_of(*[
                    EC.presence_of_element_located((by, val))
                    for by, val in LOGIN_DETECT_SELECTORS
                ])
            )
            return True
        except TimeoutException:
            return False

    def _get_search_box(self, timeout=5):
        el = _find_element(self.driver, SEARCH_BOX_SELECTORS, timeout=timeout)
        return el or _js_find_search_box(self.driver)

    def search_and_open_contact(self, name: str) -> bool:
        print(f"  [WhatsApp] '{name}' dhundh rhi hoon...")

        search_box = self._get_search_box()
        if not search_box:
            print("  [X] Search box nahi mila")
            self._save_debug()
            return False

        try:
            self.driver.execute_script("arguments[0].click();", search_box)
            _delay(0.2, 0.3)
            search_box.send_keys(Keys.CONTROL + "a")
            search_box.send_keys(Keys.DELETE)
            _delay(0.1, 0.15)
            # Contact name = ASCII only, send_keys safe hai
            search_box.send_keys(name)
        except ElementNotInteractableException:
            self.driver.execute_script("arguments[0].focus();", search_box)
            search_box.send_keys(name)

        _delay(1.0, 1.3)   # 2.5s → 1s
        return self._click_first_result(name)

    def _click_first_result(self, name: str) -> bool:
        name_lower = name.lower().strip()
        span_xpath = (
            f'//span[@title and contains('
            f'translate(@title,"ABCDEFGHIJKLMNOPQRSTUVWXYZ","abcdefghijklmnopqrstuvwxyz")'
            f',"{name_lower}")]'
        )
        try:
            spans = WebDriverWait(self.driver, 5).until(
                EC.presence_of_all_elements_located((By.XPATH, span_xpath))
            )

            # ── Word-boundary match — exact name wala contact prefer karo ──
            import re
            pattern = re.compile(r'\b' + re.escape(name_lower) + r'\b')

            # Pass 1: exact word match (e.g. "Om" not inside "kaam" or long string)
            for span in spans:
                if not span.is_displayed():
                    continue
                title = span.get_attribute('title') or ''
                title_lower = title.lower()
                # Short titles preferred (actual contact names are short)
                if len(title) > 60:
                    continue
                if pattern.search(title_lower):
                    if self._click_parent_row(span):
                        _delay(0.4, 0.6)
                        print(f"  [✓] Contact mila: '{title}'")
                        return True

            # Pass 2: startswith match (e.g. "Om Sharma")
            for span in spans:
                if not span.is_displayed():
                    continue
                title = span.get_attribute('title') or ''
                if len(title) > 60:
                    continue
                if title.lower().startswith(name_lower):
                    if self._click_parent_row(span):
                        _delay(0.4, 0.6)
                        print(f"  [✓] Contact mila (startswith): '{title}'")
                        return True

            # Pass 3: any contains match but skip very long titles (group chats/self)
            for span in spans:
                if not span.is_displayed():
                    continue
                title = span.get_attribute('title') or ''
                if len(title) > 60:
                    continue
                if name_lower in title.lower():
                    if self._click_parent_row(span):
                        _delay(0.4, 0.6)
                        print(f"  [✓] Contact mila (contains): '{title}'")
                        return True

        except TimeoutException:
            pass

        for xpath in ['//div[@data-testid="cell-frame-container"]', '//div[@role="listitem"]']:
            try:
                for cell in self.driver.find_elements(By.XPATH, xpath)[:4]:
                    if cell.is_displayed():
                        try:
                            cell.click()
                            _delay(0.4, 0.6)
                            print(f"  [✓] Pehla result click (cell): {name}")
                            return True
                        except Exception:
                            continue
            except Exception:
                continue

        matched = _js_click_contact(self.driver, name)
        if matched:
            _delay(0.4, 0.6)
            print(f"  [✓] JS se contact mila: '{matched}'")
            return True

        print(f"  [X] '{name}' result nahi mila")
        self._save_debug()
        return False

    def _click_parent_row(self, element) -> bool:
        el = element
        try:
            for _ in range(10):
                role = el.get_attribute("role")
                tab  = el.get_attribute("tabindex")
                if role in ("listitem", "button", "gridcell") or tab in ("0", "-1"):
                    el.click()
                    return True
                parent = self.driver.execute_script(
                    "return arguments[0].parentElement;", el)
                if not parent:
                    break
                el = parent
        except Exception:
            pass
        return False

    def send_message(self, message: str) -> bool:
        msg_box = _find_element(self.driver, MSG_BOX_SELECTORS, timeout=8)
        if not msg_box:
            print("  [X] Message box nahi mila")
            return False

        try:
            self.driver.execute_script("arguments[0].click();", msg_box)
            _delay(0.2, 0.3)

            lines = message.split('\n')
            for i, line in enumerate(lines):
                if line:
                    _type_via_clipboard(self.driver, msg_box, line)
                if i < len(lines) - 1:
                    msg_box.send_keys(Keys.SHIFT + Keys.ENTER)

            _delay(0.2, 0.3)

            if settings.WHATSAPP_CONFIRM_SEND:
                print(f"\n  ┌─ Message preview ─────────────────────────")
                for line in message.split('\n'):
                    print(f"  │  {line}")
                print(f"  └───────────────────────────────────────────")
                confirm = input("  Bhejun? (y/n): ").strip().lower()
                if confirm != 'y':
                    msg_box.send_keys(Keys.ESCAPE)
                    print("  [WhatsApp] Cancel")
                    return False

            msg_box.send_keys(Keys.ENTER)
            _delay(0.3, 0.5)
            print("  [✓] Message bhej diya!")
            return True

        except Exception as e:
            print(f"  [X] Send error: {e}")
            return False

    def send_whatsapp_message(self, contact: str, message: str) -> bool:
        if not self.driver:
            if not self.start():
                return False
        if not self.search_and_open_contact(contact):
            return False
        return self.send_message(message)

    def close(self):
        if self.driver:
            try:
                self.driver.quit()
            except Exception:
                pass
            self.driver = None
            print("  [WhatsApp] Browser band ho gaya")

    def _save_debug(self):
        if not self.driver:
            return
        try:
            debug_dir = Path(settings.BASE_DIR) / "data"
            debug_dir.mkdir(parents=True, exist_ok=True)
            self.driver.save_screenshot(str(debug_dir / "wa_debug.png"))
            (debug_dir / "wa_debug.html").write_text(
                self.driver.page_source, encoding="utf-8")
            print("  [WhatsApp] Debug saved → data/wa_debug.png")
            divs = self.driver.execute_script("""
                return Array.from(document.querySelectorAll('div[contenteditable="true"]'))
                    .map(d => ({
                        dataTab: d.getAttribute('data-tab'),
                        role: d.getAttribute('role'),
                        ariaLabel: d.getAttribute('aria-label'),
                        title: d.getAttribute('title'),
                    }));
            """)
            print("  [DEBUG] contenteditable divs:")
            for i, d in enumerate(divs or []):
                print(f"    [{i}] data-tab={d['dataTab']} role={d['role']} "
                      f"aria-label={d['ariaLabel']} title={d['title']}")
        except Exception as e:
            print(f"  Debug save error: {e}")


# ── Singleton ──────────────────────────────────────────────────────────
_wa_driver: WhatsAppDriver | None = None

def get_wa_driver() -> WhatsAppDriver:
    global _wa_driver
    if _wa_driver is None:
        _wa_driver = WhatsAppDriver()
    return _wa_driver


# ══════════════════════════════════════════════════════════════════════
#  PUBLIC API — router.py yahi import karta hai
# ══════════════════════════════════════════════════════════════════════

def whatsapp_send_message(
    contact: str,
    message: str = "",
    query:   str = "",        # router.py 'query' kwarg
    intent:  str = "",
    context=None,             # conversation history — LLM context ke liye
    conversation_context=None,# alias
    draft:   bool = True,
) -> tuple:
    """
    router.py ka entry point — (bool, str) tuple return karta hai.
    context/conversation_context pass karo toh LLM mood/tone samjhega.
    """
    raw  = message or query or intent
    ctx  = context or conversation_context
    if not raw:
        return (False, "Koi message/query/intent nahi mila")

    if draft:
        try:
            from actions.wa_send_action import smart_whatsapp_send
            return smart_whatsapp_send(
                contact=contact,
                intent=raw,
                conversation_context=ctx,
            )
        except Exception as e:
            print(f"  [!] LLM draft failed ({e}) — raw bhej rhi hoon...")

    # Fallback: bina drafting
    wa = get_wa_driver()
    if not wa.driver:
        if not wa.start():
            return (False, "Browser start nahi hua")
    ok = wa.send_whatsapp_message(contact, raw)
    return (True, f"{contact} ko message bhej diya!") if ok else (False, "Send fail")


def whatsapp_send_file(contact: str, file_path: str, caption: str = "") -> bool:
    """
    File/attachment bhejne ke liye — abhi basic implementation.
    Contact open karo, attachment button click karo, file select karo.
    """
    import os
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC

    wa = get_wa_driver()
    if not wa.driver:
        if not wa.start():
            return False

    # Contact open karo
    if not wa.search_and_open_contact(contact):
        return False

    driver = wa.driver

    # File path validate karo
    abs_path = os.path.abspath(file_path)
    if not os.path.exists(abs_path):
        print(f"  [X] File nahi mili: {abs_path}")
        return False

    try:
        # Attachment (clip) button click karo
        attach_selectors = [
            (By.CSS_SELECTOR, 'div[data-testid="attach-btn"]'),
            (By.CSS_SELECTOR, 'button[data-testid="attach-btn"]'),
            (By.XPATH,        '//div[@title="Attach"]'),
            (By.XPATH,        '//span[@data-testid="clip"]'),
            (By.CSS_SELECTOR, '[data-testid="clip"]'),
        ]
        attach_btn = _find_element(driver, attach_selectors, timeout=6)
        if not attach_btn:
            print("  [X] Attachment button nahi mila")
            return False

        attach_btn.click()
        _delay(0.5, 0.8)

        # File input element dhundho
        file_input_selectors = [
            (By.CSS_SELECTOR, 'input[type="file"]'),
            (By.XPATH,        '//input[@type="file"]'),
        ]
        # File inputs hidden hote hain — directly send_keys karo
        file_inputs = driver.find_elements(By.CSS_SELECTOR, 'input[type="file"]')
        if not file_inputs:
            print("  [X] File input nahi mila")
            return False

        # Pehla visible/document input use karo
        file_inputs[0].send_keys(abs_path)
        _delay(1.0, 1.5)

        # Caption add karo agar hai
        if caption:
            caption_selectors = [
                (By.CSS_SELECTOR, 'div[data-testid="media-caption-input"]'),
                (By.XPATH,        '//div[@aria-label="Add a caption"]'),
                (By.CSS_SELECTOR, 'div[aria-label="Add a caption"]'),
            ]
            caption_box = _find_element(driver, caption_selectors, timeout=4)
            if caption_box:
                _type_via_clipboard(driver, caption_box, caption)
                _delay(0.3, 0.5)

        # Send button
        send_selectors = [
            (By.CSS_SELECTOR, 'div[data-testid="send"]'),
            (By.CSS_SELECTOR, 'button[data-testid="send"]'),
            (By.XPATH,        '//div[@aria-label="Send"]'),
            (By.XPATH,        '//span[@data-testid="send"]'),
        ]
        send_btn = _find_element(driver, send_selectors, timeout=5)
        if send_btn:
            send_btn.click()
            _delay(0.5, 1.0)
            print(f"  [✓] File bhej di: {os.path.basename(abs_path)}")
            return True
        else:
            # Enter se bhi send ho sakta hai
            from selenium.webdriver.common.keys import Keys
            driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.ENTER)
            _delay(0.5, 1.0)
            print(f"  [✓] File bhej di (Enter): {os.path.basename(abs_path)}")
            return True

    except Exception as e:
        print(f"  [X] File send error: {e}")
        return False


# ══════════════════════════════════════════════════════════════════════
#  STANDALONE TEST
# ══════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    print("\n" + "=" * 55)
    print("   LISA -- WhatsApp Automation Test (v2 - Fixed)")
    print("=" * 55)

    if not CLIPBOARD_OK:
        print("\n  [!] pyperclip nahi hai — install karo pehle:")
        print("      pip install pyperclip\n")

    wa = WhatsAppDriver()
    if not wa.start():
        input("\n  ENTER to close...")
        exit(1)

    contact = input("\n  Test contact (e.g., 'aniket'): ").strip()
    if not contact:
        wa.close()
        exit(0)

    found = wa.search_and_open_contact(contact)
    if found:
        msg = input("  Message (emoji try kar sakte ho 🙏): ").strip()
        if msg:
            wa.send_message(msg)
    else:
        print(f"  [X] Contact nahi mila: '{contact}'")

    input("\n  ENTER to close...")
    wa.close()