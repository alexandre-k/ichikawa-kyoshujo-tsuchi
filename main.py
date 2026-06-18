import os
from typing import List
from dotenv import load_dotenv

from check import run_check


def main():
    load_dotenv()  # loads variables from .env into os.environ
    start_url = os.getenv("START_URL")
    username = os.getenv("USERNAME")
    password = os.getenv("PASSWORD")
    ignored_dates: List[str] = [s.strip() for s in os.getenv("IGNORED_DATES", "").split(",") if s.strip()]

    assert start_url is not None
    assert username is not None
    assert password is not None
    run_check(start_url, username, password, ignored_dates)

if __name__ == "__main__":
    main()
