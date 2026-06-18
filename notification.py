import os
import subprocess


def send_notification(date):
    signal_user_phone_number = os.getenv("SIGNAL_USER_PHONE_NUMBER")
    signal_group_id = os.getenv("SIGNAL_GROUP_ID")
    assert signal_user_phone_number is not None
    assert signal_group_id is not None

    return subprocess.run(
        ["flatpak", "run", "org.asamk.SignalCli", "-u", signal_user_phone_number, "send", "-m", f"ピポピポー!空いてる日を見つけたよん: {date}: 空", "-g", signal_group_id],
        check=True
    )