"""
LISA — System Actions
"""

import subprocess
import webbrowser
import os
import urllib.parse
from pathlib import Path


def open_website(query: str) -> tuple[bool, str]:
    url = query if query.startswith("http") else f"https://{query}"
    try:
        webbrowser.open(url)
        name = query.replace("https://","").replace("http://","").replace("www.","").split("/")[0]
        return True, f"lo khol diya {name}!"
    except Exception:
        return False, "website nahi khuli"


def search_youtube(query: str) -> tuple[bool, str]:
    """YouTube pe search karo."""
    try:
        encoded = urllib.parse.quote(query)
        webbrowser.open(f"https://www.youtube.com/results?search_query={encoded}")
        return True, f'YouTube pe "{query}" search kar diya!'
    except Exception:
        return False, "YouTube nahi khula"


def play_youtube(query: str) -> tuple[bool, str]:
    """
    yt-dlp se pehla result ka video ID lo, seedha watch URL kholo.
    Browser mein open hoga — autoplay hoga video.
    """
    try:
        # Video ID fetch karo (stream URL nahi — sirf ID)
        result = subprocess.run(
            ["yt-dlp", f"ytsearch1:{query} official video", "--get-id", "--no-playlist"],
            capture_output=True, text=True, timeout=15
        )
        if result.returncode == 0 and result.stdout.strip():
            video_id = result.stdout.strip().split('\n')[0]
            watch_url = f"https://www.youtube.com/watch?v={video_id}"
            webbrowser.open(watch_url)
            return True, f'"{query}" chal raha hai YouTube pe!'
    except FileNotFoundError:
        pass   # yt-dlp nahi hai — fallback to search
    except subprocess.TimeoutExpired:
        pass   # Timeout — fallback to search
    except Exception:
        pass

    # Fallback: search results
    encoded = urllib.parse.quote(query)
    webbrowser.open(f"https://www.youtube.com/results?search_query={encoded}")
    return True, f'YouTube pe "{query}" search kar diya — pehla result play karo!'


def search_spotify(query: str) -> tuple[bool, str]:
    try:
        encoded = urllib.parse.quote(query)
        try:
            os.startfile(f"spotify:search:{encoded}")
            return True, f'Spotify pe "{query}" laga diya!'
        except Exception:
            webbrowser.open(f"https://open.spotify.com/search/{encoded}")
            return True, f'Spotify web pe "{query}" search kar diya!'
    except Exception:
        return False, "Spotify nahi khula"


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
    "discord": "discord", "zoom": "zoom",
    "vlc": "vlc", "spotify": "spotify",
}


def open_app(query: str) -> tuple[bool, str]:
    query_lower = query.lower().strip()
    cmd = APP_MAP.get(query_lower, query_lower)
    if cmd and cmd.startswith("http"):
        webbrowser.open(cmd)
        return True, f"{query} khol diya!"
    try:
        subprocess.Popen(cmd, shell=True)
        return True, f"haan, {query} khol diya!"
    except Exception:
        return False, f"{query} nahi mila"


def search_google(query: str) -> tuple[bool, str]:
    try:
        webbrowser.open(f"https://www.google.com/search?q={urllib.parse.quote(query)}")
        return True, f'Google pe "{query}" search kar diya!'
    except Exception:
        return False, "Google search nahi hua"


def open_folder(query: str) -> tuple[bool, str]:
    folder_map = {
        "desktop":   str(Path.home() / "Desktop"),
        "downloads": str(Path.home() / "Downloads"),
        "documents": str(Path.home() / "Documents"),
        "pictures":  str(Path.home() / "Pictures"),
        "music":     str(Path.home() / "Music"),
        "d": "D:\\", "d drive": "D:\\",
        "c": "C:\\", "c drive": "C:\\",
    }
    path = folder_map.get(query.lower().strip(), query)
    try:
        os.startfile(path)
        return True, f"lo khol diya {query}!"
    except Exception:
        return False, f"{query} nahi mila"


def open_file(query: str) -> tuple[bool, str]:
    try:
        if os.path.exists(query):
            os.startfile(query)
            return True, "file khol di!"
        else:
            return False, f"file nahi mili: {query}"
    except Exception:
        return False, "file nahi khuli"


def system_command(query: str) -> tuple[bool, str]:
    q = query.lower()

    if "screenshot" in q:
        try:
            import datetime
            filename = f"screenshot_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            desktop  = str(Path.home() / "Desktop" / filename)
            subprocess.run([
                "powershell", "-command",
                f"Add-Type -AssemblyName System.Windows.Forms,System.Drawing; "
                f"$b=New-Object System.Drawing.Bitmap([System.Windows.Forms.Screen]::PrimaryScreen.Bounds.Width,[System.Windows.Forms.Screen]::PrimaryScreen.Bounds.Height); "
                f"$g=[System.Drawing.Graphics]::FromImage($b); "
                f"$g.CopyFromScreen(0,0,0,0,$b.Size); "
                f"$b.Save('{desktop}')"
            ], shell=True)
            return True, "screenshot le liya! Desktop pe save ho gaya"
        except Exception:
            return False, "screenshot nahi le payi"

    elif any(x in q for x in ["volume up", "volume badhao", "sound badhao"]):
        subprocess.run(["powershell","-command","$wsh=New-Object -ComObject WScript.Shell;$wsh.SendKeys([char]175)"],shell=True)
        return True, "volume badha diya!"

    elif any(x in q for x in ["volume down", "volume kam", "volume ghata", "sound kam"]):
        subprocess.run(["powershell","-command","$wsh=New-Object -ComObject WScript.Shell;$wsh.SendKeys([char]174)"],shell=True)
        return True, "volume ghata diya!"

    elif "mute" in q:
        subprocess.run(["powershell","-command","$wsh=New-Object -ComObject WScript.Shell;$wsh.SendKeys([char]173)"],shell=True)
        return True, "mute kar diya!"

    else:
        return False, f"ye command samajh nahi aayi: {query}"