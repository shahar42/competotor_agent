#!/usr/bin/env python3
import sys

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "schedule":
        from scheduler.runner import DailyRunner
        runner = DailyRunner()
        runner.start()
    else:
        from bot import main
        main()
