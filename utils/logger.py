def log(message):
    from datetime import datetime
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")