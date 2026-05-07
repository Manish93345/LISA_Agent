"""
LISA -- WhatsApp Web Automation (Selenium + Edge)
===================================================
Edge browser + dedicated profile = your main browser stays untouched.
WhatsApp Web pe message/file bhejta hai -- Desktop 3 pe, invisible.

Usage:
    from actions.whatsapp_actions import whatsapp_send_message, whatsapp_send_file
    success, msg = whatsapp_send_message(contact="aniket", message="meeting join kar")
    success, msg = whatsapp_send_file(contact="aniket", folder="free fire", file="divya")
"""

import os
import time
import random
import threading
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.edge.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException, NoSuchElementException,
    WebDriverException, StaleElementReferenceException,
)

from config.settings import (
    WHATSAPP_PROFILE_DIR, WHATSAPP_URL,
    WHATSAPP_LOAD_TIMEOUT, WHATSAPP_ACTION_DELAY,
    WHATSAPP_CONFIRM_SEND,
)


# ── Singleton Driver ──────────────────────────────────────────────────

_driver = None
_driver_lock = threading.Lock()


def _human_delay():
    """Random delay to mimic human behavior."""
    lo, hi = WHATSAPP_ACTION_DELAY
    time.sleep(random.uniform(lo, hi))


def _get_driver() -> webdriver.Edge:
    """
    Lazy-init singleton Edge driver with dedicated WhatsApp profile.
    Reuses existing driver if still alive.
    Selenium 4.6+ has built-in SeleniumManager -- no webdriver-manager needed.
    """
    global _driver

    with _driver_lock:
        # Check if existing driver is still alive
        if _driver is not None:
            try:
                _driver.title  # simple check -- throws if dead
                return _driver
            except Exception:
                _driver = None

        print("  [WhatsApp] Edge browser start ho rha hai...")

        # Ensure profile dir exists
        os.makedirs(WHATSAPP_PROFILE_DIR, exist_ok=True)

        options = Options()
        options.add_argument(f"user-data-dir={WHATSAPP_PROFILE_DIR}")
        options.add_argument("--start-minimized")
        # Suppress automation detection banners
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)

        try:
            # Selenium 4.6+ auto-manages driver download via SeleniumManager
            _driver = webdriver.Edge(options=options)
        except Exception as e:
            print(f"  [WhatsApp] Edge start nahi hua: {e}")
            return None

        # Navigate to WhatsApp Web
        _driver.get(WHATSAPP_URL)
        print("  [WhatsApp] WhatsApp Web load ho rha hai...")

        # Wait for WhatsApp to fully load (QR scan if first time)
        # Edge stays VISIBLE on main screen so user can scan QR if needed
        loaded = _wait_for_load()

        if not loaded:
            print("  [WhatsApp] WhatsApp load nahi hua -- QR scan zaruri ho sakta hai")
            print("  [WhatsApp] QR scan karo, phir ye apne aap detect kar lega...")

            # Keep checking for up to 120 seconds (QR scan time)
            for attempt in range(12):
                time.sleep(10)
                if _wait_for_load(timeout=5):
                    loaded = True
                    print("  [WhatsApp] QR scan successful! WhatsApp ready!")
                    break

            if not loaded:
                print("  [WhatsApp] 2 minute wait kiya, WhatsApp load nahi hua")
                return _driver  # still return -- user can try manually

        if loaded:
            print("  [WhatsApp] WhatsApp ready!")
            # NOW move to Desktop 3 (after WhatsApp is loaded)
            _move_selenium_window_to_desktop3()

        return _driver


def _move_selenium_window_to_desktop3():
    """
    Move ONLY the Selenium-controlled Edge window to Desktop 3.
    Uses Selenium's window handle to identify the correct window.
    Does NOT touch any other Edge windows.
    """
    try:
        from actions.desktop_manager import _load_dll, LISA_DESKTOP
        import win32gui

        dll = _load_dll()
        if dll is None:
            return

        if _driver is None:
            return

        # Get the window title from Selenium
        selenium_title = _driver.title

        # Find the window with matching title
        found_hwnds = []
        def _cb(hwnd, _):
            try:
                if win32gui.IsWindowVisible(hwnd):
                    title = win32gui.GetWindowText(hwnd)
                    # Match by Selenium's current page title
                    if selenium_title and selenium_title in title:
                        found_hwnds.append(hwnd)
                    # Also match WhatsApp-specific titles
                    elif "WhatsApp" in title:
                        found_hwnds.append(hwnd)
            except Exception:
                pass
            return True

        win32gui.EnumWindows(_cb, None)

        for hwnd in found_hwnds:
            try:
                result = dll.MoveWindowToDesktopNumber(hwnd, LISA_DESKTOP)
                if result != -1:
                    title = win32gui.GetWindowText(hwnd)
                    print(f"  [WhatsApp] Desktop 3 pe move kiya: {title}")
            except Exception:
                pass

        if not found_hwnds:
            print("  [WhatsApp] Window nahi mili Desktop 3 move ke liye")

    except Exception as e:
        print(f"  [WhatsApp] Desktop 3 move skip: {e}")


def _wait_for_load(timeout: int = None) -> bool:
    """
    Wait for WhatsApp Web to fully load.
    Checks for the search/chat list to appear.
    """
    if _driver is None:
        return False

    wait_time = timeout if timeout else WHATSAPP_LOAD_TIMEOUT

    try:
        # Wait for the side panel (search area) to load
        # This appears after QR scan and login
        WebDriverWait(_driver, wait_time).until(
            EC.presence_of_element_located((
                By.XPATH,
                "//div[@contenteditable='true'][@data-tab='3']"
            ))
        )
        return True
    except TimeoutException:
        return False


def close_driver():
    """Close the Edge browser cleanly."""
    global _driver
    with _driver_lock:
        if _driver is not None:
            try:
                _driver.quit()
            except Exception:
                pass
            _driver = None
            print("  [WhatsApp] Browser band ho gaya")


# ── Contact Search ────────────────────────────────────────────────────

def _search_contact(contact_name: str) -> bool:
    """
    WhatsApp search bar mein contact search karo.
    Returns True if contact found and chat opened.
    """
    driver = _get_driver()
    if driver is None:
        return False

    try:
        # Find and click search box
        search_box = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((
                By.XPATH,
                "//div[@contenteditable='true'][@data-tab='3']"
            ))
        )
        search_box.click()
        _human_delay()

        # Clear any existing text
        search_box.send_keys(Keys.CONTROL + "a")
        search_box.send_keys(Keys.DELETE)
        time.sleep(0.3)

        # Type contact name
        search_box.send_keys(contact_name)
        time.sleep(2.0)  # Wait for search results to populate

        # Try to find the best matching contact from results
        # WhatsApp shows results as span elements with title attribute
        try:
            results = driver.find_elements(
                By.XPATH,
                "//div[@id='pane-side']//span[@title]"
            )

            if not results:
                print(f"  [WhatsApp] '{contact_name}' ka koi result nahi aaya")
                # Press Escape to close search
                search_box.send_keys(Keys.ESCAPE)
                return False

            # Collect visible contact names
            contact_names = []
            contact_elements = []
            for el in results:
                try:
                    title = el.get_attribute("title")
                    if title:
                        contact_names.append(title)
                        contact_elements.append(el)
                except StaleElementReferenceException:
                    continue

            if not contact_names:
                print(f"  [WhatsApp] Search results mein naam nahi mila")
                search_box.send_keys(Keys.ESCAPE)
                return False

            # Fuzzy match the best contact
            best_idx = _fuzzy_match_contact(contact_name, contact_names)

            if best_idx is None:
                # No good match -- just click the first result
                print(f"  [WhatsApp] Fuzzy match nahi mila, pehla result use kar rhe: '{contact_names[0]}'")
                best_idx = 0

            matched_name = contact_names[best_idx]
            print(f"  [WhatsApp] Contact match: '{contact_name}' -> '{matched_name}'")

            # Click on the matched contact
            contact_elements[best_idx].click()
            _human_delay()
            return True

        except Exception as e:
            print(f"  [WhatsApp] Contact search error: {e}")
            # Fallback -- try pressing Enter on first result
            search_box.send_keys(Keys.ENTER)
            _human_delay()
            return True

    except Exception as e:
        print(f"  [WhatsApp] Search box error: {e}")
        return False


def _fuzzy_match_contact(hint: str, contacts: list[str]) -> int | None:
    """
    Fuzzy match contact name from WhatsApp search results.
    Returns index of best match, or None if no good match.
    """
    try:
        from rapidfuzz import fuzz, process

        hint_lower = hint.lower().strip()
        contacts_lower = [c.lower() for c in contacts]

        result = process.extractOne(
            hint_lower,
            contacts_lower,
            scorer=fuzz.WRatio,
            score_cutoff=50  # pretty relaxed -- WA search already filters
        )

        if result is None:
            return None

        _, score, idx = result
        print(f"  [WhatsApp] Fuzzy: '{hint}' -> '{contacts[idx]}' (score: {score:.0f})")
        return idx

    except ImportError:
        # rapidfuzz not available -- just check simple substring
        hint_lower = hint.lower()
        for i, name in enumerate(contacts):
            if hint_lower in name.lower() or name.lower() in hint_lower:
                return i
        return 0  # default to first result


# ── Message Sending ───────────────────────────────────────────────────

def _type_and_send_message(message: str) -> bool:
    """
    Currently open chat mein message type karo aur send karo.
    """
    driver = _get_driver()
    if driver is None:
        return False

    try:
        # Find message input box
        msg_box = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((
                By.XPATH,
                "//div[@contenteditable='true'][@data-tab='10']"
            ))
        )
        msg_box.click()
        _human_delay()

        # Type message (character by character for multi-line support)
        # For simple single-line messages, send_keys works fine
        msg_box.send_keys(message)
        _human_delay()

        # Click send button
        send_btn = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((
                By.XPATH,
                "//span[@data-icon='send']"
            ))
        )
        send_btn.click()
        _human_delay()

        return True

    except Exception as e:
        print(f"  [WhatsApp] Message send error: {e}")
        return False


# ── File Sending ──────────────────────────────────────────────────────

def _send_file_to_chat(file_path: str, caption: str = "") -> bool:
    """
    Currently open chat mein file attach karo aur send karo.
    Uses hidden <input type='file'> element.
    """
    driver = _get_driver()
    if driver is None:
        return False

    if not os.path.exists(file_path):
        print(f"  [WhatsApp] File nahi mili: {file_path}")
        return False

    abs_path = os.path.abspath(file_path)

    try:
        # Click the attach/plus button
        try:
            attach_btn = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((
                    By.XPATH,
                    "//div[@title='Attach']"
                ))
            )
            attach_btn.click()
        except TimeoutException:
            # Try newer WhatsApp UI with plus icon
            try:
                attach_btn = driver.find_element(
                    By.XPATH,
                    "//span[@data-icon='plus']"
                )
                attach_btn.click()
            except NoSuchElementException:
                # Try the clip/paperclip icon
                attach_btn = driver.find_element(
                    By.XPATH,
                    "//span[@data-icon='clip']"
                )
                attach_btn.click()

        _human_delay()

        # Find the file input element and send file path
        # WhatsApp has multiple file inputs -- we want the document one
        file_inputs = driver.find_elements(By.CSS_SELECTOR, "input[type='file']")

        if not file_inputs:
            print("  [WhatsApp] File input nahi mila")
            return False

        # Use the last file input (usually the most general one)
        # or find one that accepts all files
        target_input = None
        for inp in file_inputs:
            accept = inp.get_attribute("accept") or ""
            if not accept or "*" in accept:
                target_input = inp
                break

        if target_input is None:
            # Fallback -- use the first available
            target_input = file_inputs[0]

        target_input.send_keys(abs_path)
        time.sleep(2.0)  # Wait for file to load/preview

        # Add caption if provided
        if caption:
            try:
                caption_box = driver.find_element(
                    By.XPATH,
                    "//div[@contenteditable='true'][@data-tab='10'] | "
                    "//div[contains(@class,'copyable-text') and @contenteditable='true' and @role='textbox']"
                )
                caption_box.click()
                caption_box.send_keys(caption)
                _human_delay()
            except Exception:
                pass  # Caption is optional

        # Click the send button (in file preview)
        try:
            send_btn = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((
                    By.XPATH,
                    "//span[@data-icon='send']"
                ))
            )
            send_btn.click()
        except TimeoutException:
            # Try alternate send button in media preview
            send_btn = driver.find_element(
                By.XPATH,
                "//div[@role='button'][@aria-label='Send']"
            )
            send_btn.click()

        _human_delay()
        time.sleep(2.0)  # Wait for upload to start

        print(f"  [WhatsApp] File sent: {Path(file_path).name}")
        return True

    except Exception as e:
        print(f"  [WhatsApp] File send error: {e}")
        # Press Escape to close any open dialogs
        try:
            driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
        except Exception:
            pass
        return False


# ── Public API — Called by Router ─────────────────────────────────────

def whatsapp_send_message(
    query: str = "",
    contact: str = "",
    message: str = "",
    **kwargs
) -> tuple[bool, str]:
    """
    WhatsApp pe message bhejo.

    Args:
        query   : original user message (fallback/context)
        contact : contact name hint (fuzzy matched)
        message : message content to send

    Returns:
        (success, status_message)
    """
    if not contact:
        return False, "contact naam nahi bataya -- kisko message bhejun?"

    if not message:
        return False, "message kya bhejun? Batao na"

    # Step 1: Open WhatsApp and search contact
    if not _search_contact(contact):
        return False, f"'{contact}' naam ka contact nahi mila WhatsApp pe"

    # Step 2: Check if confirmation is needed
    if WHATSAPP_CONFIRM_SEND:
        return True, f"CONFIRM_WHATSAPP_MSG|{contact}|{message}"

    # Step 3: Send message
    if _type_and_send_message(message):
        return True, f"'{contact}' ko message bhej diya: \"{message}\""
    else:
        return False, f"message send nahi ho paya '{contact}' ko"


def whatsapp_confirm_and_send(action_type: str, contact: str, content: str) -> tuple[bool, str]:
    """
    User ne confirm kiya -- ab bhejo.
    Called after confirmation response.

    Args:
        action_type : "message" or "file"
        contact     : contact name (already searched, chat should be open)
        content     : message text or file path
    """
    if action_type == "message":
        if _type_and_send_message(content):
            return True, f"message bhej diya!"
        return False, "message send nahi ho paya"

    elif action_type == "file":
        if _send_file_to_chat(content):
            return True, f"file bhej di!"
        return False, "file send nahi ho payi"

    return False, "unknown action type"


def whatsapp_send_file(
    query: str = "",
    contact: str = "",
    folder: str = "",
    file: str = "",
    **kwargs
) -> tuple[bool, str]:
    """
    WhatsApp pe file bhejo — pehle file_finder se dhundhega, phir bhejega.

    Args:
        query   : original user message
        contact : contact name hint
        folder  : folder hint for file_finder
        file    : file hint for file_finder

    Returns:
        (success, status_message)
    """
    if not contact:
        return False, "contact naam nahi bataya -- kisko file bhejun?"

    if not folder and not file:
        return False, "kaunsi file bhejni hai? Folder ya file naam batao"

    # Step 1: Find the file using existing file_finder
    from actions.file_finder import smart_find

    success, file_path, find_msg = smart_find(folder_hint=folder, file_hint=file)

    if not success or not file_path:
        return False, f"file nahi mili: {find_msg}"

    if os.path.isdir(file_path):
        return False, f"ye toh folder hai ({find_msg}) -- file ka naam bhi batao"

    file_name = Path(file_path).name

    # Step 2: Open WhatsApp and search contact
    if not _search_contact(contact):
        return False, f"'{contact}' naam ka contact nahi mila WhatsApp pe"

    # Step 3: Check if confirmation is needed
    if WHATSAPP_CONFIRM_SEND:
        return True, f"CONFIRM_WHATSAPP_FILE|{contact}|{file_path}|{file_name}"

    # Step 4: Send file
    if _send_file_to_chat(file_path):
        return True, f"'{file_name}' bhej diya '{contact}' ko WhatsApp pe!"
    else:
        return False, f"file send nahi ho payi '{contact}' ko"


# ── Standalone Test ───────────────────────────────────────────────────

if __name__ == "__main__":
    print("\n" + "=" * 55)
    print("   LISA -- WhatsApp Automation Test")
    print("=" * 55)
    print()
    print("  Edge browser khulega with dedicated profile.")
    print("  Pehli baar hai toh QR code dikhega -- scan karo.")
    print("  WhatsApp load hone ke baad automatically detect ho jayega.")
    print()

    driver = _get_driver()

    if driver is None:
        print("  [X] Driver start nahi hua!")
        exit(1)

    # Test: search a contact
    test_contact = input("\n  Test contact name (e.g., 'aniket'): ").strip()
    if test_contact:
        found = _search_contact(test_contact)
        if found:
            print(f"  [OK] Contact found and chat opened: {test_contact}")

            send_test = input("  Test message bhejun? (y/n): ").strip().lower()
            if send_test == "y":
                test_msg = "Hello! Ye Lisa ka test message hai -- ignore karna :)"
                if _type_and_send_message(test_msg):
                    print(f"  [OK] Message sent: {test_msg}")
                else:
                    print("  [X] Message send failed")
        else:
            print(f"  [X] Contact nahi mila: {test_contact}")

    input("\n  ENTER dabao browser band karne ke liye...")
    close_driver()
    print("  Done!")
