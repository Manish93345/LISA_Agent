"""
LISA — System Actions (with background desktop support)
=========================================================
Browser/app actions Desktop 3 pe hoti hain — screen disturb nahi hoti.
"""

import subprocess
import webbrowser
import os
import urllib.parse
import threading
from pathlib import Path

# Chrome ka path — tumhare PC pe check karo
CHROME_PATHS = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
]


def _get_chrome() -> str | None:
    for p in CHROME_PATHS:
        if os.path.exists(p):
            return p
    return None


def _launch_chrome_on_lisa_desktop(url: str) -> tuple[bool, str]:
    """
    Chrome ko Lisa ke desktop pe launch karo — screen disturb nahi hogi.
    """
    from actions.desktop_manager import launch_on_lisa_desktop, get_status

    status = get_status()
    chrome = _get_chrome()

    if not chrome:
        # Chrome nahi mila — default browser use karo (visible hoga)
        webbrowser.open(url)
        return True, "browser mein khola (background setup ke liye Chrome install karo)"

    if not status["ready"]:
        # Desktop manager ready nahi — normal browser
        webbrowser.open(url)
        return True, "browser mein khola!"

    # Chrome new window Lisa ke desktop pe
    process = launch_on_lisa_desktop(
        [chrome, "--new-window", "--start-minimized", url],
        wait=2.5
    )

    if process:
        return True, "background mein khola!"
    else:
        webbrowser.open(url)
        return True, "browser mein khola!"


# ── YouTube ───────────────────────────────────────────────────────────

def play_youtube(query: str) -> tuple[bool, str]:
    """YouTube pe gaana — Chrome Lisa ke desktop pe, screen disturb nahi."""
    encoded = urllib.parse.quote(f"{query} official video")
    url     = f"https://www.youtube.com/results?search_query={encoded}"

    # yt-dlp available ho toh direct video ID se play karo
    try:
        result = subprocess.run(
            ["yt-dlp", f"ytsearch1:{query} official video",
             "--get-id", "--no-playlist", "--quiet"],
            capture_output=True, text=True, timeout=15
        )
        if result.returncode == 0 and result.stdout.strip():
            video_id = result.stdout.strip().split('\n')[0]
            url = f"https://www.youtube.com/watch?v={video_id}"
    except Exception:
        pass

    success, msg = _launch_chrome_on_lisa_desktop(url)
    return success, f'"{query}" {msg}'


def search_youtube(query: str) -> tuple[bool, str]:
    encoded = urllib.parse.quote(query)
    url     = f"https://www.youtube.com/results?search_query={encoded}"
    success, msg = _launch_chrome_on_lisa_desktop(url)
    return success, f'YouTube pe "{query}" {msg}'


# ── Website ───────────────────────────────────────────────────────────

def open_website(query: str) -> tuple[bool, str]:
    url = query if query.startswith("http") else f"https://{query}"
    success, msg = _launch_chrome_on_lisa_desktop(url)
    name = query.replace("https://","").replace("http://","").replace("www.","").split("/")[0]
    return success, f"{name} {msg}"


# ── Spotify ──────────────────────────────────────────────────────────

def search_spotify(query: str) -> tuple[bool, str]:
    try:
        encoded = urllib.parse.quote(query)
        try:
            os.startfile(f"spotify:search:{encoded}")
            return True, f'Spotify pe "{query}" laga diya!'
        except Exception:
            success, msg = _launch_chrome_on_lisa_desktop(
                f"https://open.spotify.com/search/{encoded}"
            )
            return success, f'Spotify pe "{query}" {msg}'
    except Exception:
        return False, "Spotify nahi khula"


# ── Google search ─────────────────────────────────────────────────────

def search_google(query: str) -> tuple[bool, str]:
    url     = f"https://www.google.com/search?q={urllib.parse.quote(query)}"
    success, msg = _launch_chrome_on_lisa_desktop(url)
    return success, f'"{query}" search kar diya {msg}'


# ── App open ──────────────────────────────────────────────────────────

APP_MAP = {
    "vs code": "code", "vscode": "code", "visual studio code": "code",
    "notepad": "notepad", "notepad++": "notepad++",
    "chrome": "chrome", "google chrome": "chrome",
    "firefox": "firefox", "edge": "msedge", "brave": "brave",
    "calculator": "calc", "calc": "calc",
    "paint": "mspaint", "task manager": "taskmgr",
    "file explorer": "explorer", "explorer": "explorer",
    "cmd": "cmd", "terminal": "cmd", "powershell": "powershell",
    "whatsapp": "whatsapp", "telegram": "telegram",
    "discord": "discord", "zoom": "zoom", "vlc": "vlc",
}


def open_app(query: str) -> tuple[bool, str]:
    q   = query.lower().strip()
    cmd = APP_MAP.get(q, q)
    try:
        subprocess.Popen(cmd, shell=True)
        return True, f"{query} khol diya!"
    except Exception:
        return False, f"{query} nahi mila"


# ── Folder open ──────────────────────────────────────────────────────

def open_folder(query: str) -> tuple[bool, str]:
    folder_map = {
        "desktop":   str(Path.home() / "Desktop"),
        "downloads": str(Path.home() / "Downloads"),
        "documents": str(Path.home() / "Documents"),
        "d": "D:\\", "d drive": "D:\\",
        "c": "C:\\", "c drive": "C:\\",
    }
    path = folder_map.get(query.lower().strip(), query)
    try:
        os.startfile(path)
        return True, f"lo khol diya {query}!"
    except Exception:
        return False, f"{query} nahi mila"


# ── File open ─────────────────────────────────────────────────────────

def open_file(query: str) -> tuple[bool, str]:
    try:
        if os.path.exists(query):
            os.startfile(query)
            return True, "file khol di!"
        return False, f"file nahi mili: {query}"
    except Exception:
        return False, "file nahi khuli"


# ── System commands ───────────────────────────────────────────────────

def system_command(query: str) -> tuple[bool, str]:
    q = query.lower()

    if "screenshot" in q:
        try:
            import datetime
            fname   = f"screenshot_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            desktop = str(Path.home() / "Desktop" / fname)
            subprocess.run([
                "powershell", "-command",
                f"Add-Type -AssemblyName System.Windows.Forms,System.Drawing; "
                f"$b=New-Object System.Drawing.Bitmap("
                f"[System.Windows.Forms.Screen]::PrimaryScreen.Bounds.Width,"
                f"[System.Windows.Forms.Screen]::PrimaryScreen.Bounds.Height); "
                f"$g=[System.Drawing.Graphics]::FromImage($b); "
                f"$g.CopyFromScreen(0,0,0,0,$b.Size); $b.Save('{desktop}')"
            ], shell=True)
            return True, "screenshot le liya!"
        except Exception:
            return False, "screenshot nahi le payi"

    elif any(x in q for x in ["volume up","volume badhao"]):
        subprocess.run(["powershell","-c","$wsh=New-Object -ComObject WScript.Shell;$wsh.SendKeys([char]175)"],shell=True)
        return True, "volume badha diya!"

    elif any(x in q for x in ["volume down","volume kam","volume ghata"]):
        subprocess.run(["powershell","-c","$wsh=New-Object -ComObject WScript.Shell;$wsh.SendKeys([char]174)"],shell=True)
        return True, "volume ghata diya!"

    elif "mute" in q:
        subprocess.run(["powershell","-c","$wsh=New-Object -ComObject WScript.Shell;$wsh.SendKeys([char]173)"],shell=True)
        return True, "mute kar diya!"

    return False, f"ye command samajh nahi aayi: {query}"


# ── Smart File Finder + Open ─────────────────────────────────────────

def smart_find_and_open(query: str, folder: str = "", file: str = "", on_main_screen: bool = False) -> tuple[bool, str]:
    """
    Smart fuzzy file/folder finder — dhundhega aur Desktop 3 pe kholega.
    Agar user explicitly bole "main screen pe" toh main desktop pe kholega.

    Args:
        query          : original user message (fallback)
        folder         : folder hint from intent detector
        file           : file hint from intent detector
        on_main_screen : True = main desktop, False = Desktop 3 (default)

    Returns:
        (success, message)
    """
    from actions.file_finder import smart_find

    success, path, message = smart_find(folder_hint=folder, file_hint=file)

    if not success or not path:
        return False, message

    # ── Open on main screen (user explicitly asked) ──────────────────
    if on_main_screen:
        try:
            os.startfile(path)
            return True, f"{message}, khol diya tumhare screen pe!"
        except Exception as e:
            return False, f"file khulne mein error: {e}"

    # ── Open on Desktop 3 (default — background mein) ────────────────
    from actions.desktop_manager import get_status, open_file_on_lisa_desktop

    status = get_status()
    if not status["ready"]:
        # Desktop 3 nahi hai — fallback to main screen
        os.startfile(path)
        return True, f"{message}, khol diya! (Desktop 3 ready nahi tha)"

    # Window-snapshot approach: works for BOTH files and folders
    # (PID-based approach fails for explorer.exe because it reuses instances)
    import threading

    def _open_in_background():
        moved = open_file_on_lisa_desktop(path, wait=3.0)
        if not moved:
            print(f"  [Desktop] Desktop 3 pe move nahi hua, main screen pe khula hoga")

    thread = threading.Thread(target=_open_in_background, daemon=True)
    thread.start()

    item_type = "folder" if os.path.isdir(path) else os.path.basename(path)
    return True, f"{message}, background mein khol rhi hoon!"