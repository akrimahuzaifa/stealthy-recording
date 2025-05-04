import os
import shutil
import sys
import ctypes
import winreg

def is_admin():
    """Check if running as admin (required for modifying PATH)."""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def copy_ffmpeg_to_appdata():
    """Copy extracted FFmpeg folder to %LOCALAPPDATA%\ffmpeg."""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    ffmpeg_source = os.path.join(current_dir, "ffmpeg")  # Assumes extracted folder is named "ffmpeg"
    ffmpeg_dest = os.path.join(os.environ["LOCALAPPDATA"], "ffmpeg")

    # Create destination dir if it doesn't exist
    os.makedirs(ffmpeg_dest, exist_ok=True)

    # Copy files (overwrite if exists)
    try:
        if os.path.exists(ffmpeg_dest):
            shutil.rmtree(ffmpeg_dest)
        shutil.copytree(ffmpeg_source, ffmpeg_dest)
        print(f"[+] FFmpeg copied to: {ffmpeg_dest}")
        return ffmpeg_dest
    except Exception as e:
        print(f"[-] Error copying FFmpeg: {e}")
        sys.exit(1)

def add_ffmpeg_to_path(ffmpeg_path):
    """Add FFmpeg's bin folder to the system PATH."""
    bin_path = os.path.join(ffmpeg_path, "bin")
    
    # Update the PATH in the registry (system-wide)
    try:
        with winreg.OpenKey(
            winreg.HKEY_LOCAL_MACHINE,
            r"SYSTEM\CurrentControlSet\Control\Session Manager\Environment",
            0, winreg.KEY_ALL_ACCESS
        ) as key:
            current_path = winreg.QueryValueEx(key, "Path")[0]
            if bin_path not in current_path:
                new_path = f"{current_path};{bin_path}"
                winreg.SetValueEx(key, "Path", 0, winreg.REG_EXPAND_SZ, new_path)
                print(f"[+] Added to PATH: {bin_path}")

                # Notify other processes of the change
                ctypes.windll.user32.SendMessageTimeoutW(
                    0xFFFF, 0x001A, 0, "Environment", 0, 1000, None
                )
    except Exception as e:
        print(f"[-] Failed to update PATH: {e}")
        sys.exit(1)

def main():
    if not is_admin():
        print("[!] Run as Administrator to modify PATH.")
        sys.exit(1)

    ffmpeg_path = copy_ffmpeg_to_appdata()
    add_ffmpeg_to_path(ffmpeg_path)
    print("[+] FFmpeg deployed successfully!")

if __name__ == "__main__":
    main()