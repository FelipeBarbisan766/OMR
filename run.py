from __future__ import annotations

import threading
import time
import webbrowser

from backend.app import create_app


def main() -> None:
    app = create_app()

    def run_flask() -> None:
        app.run(host="127.0.0.1", port=5000, debug=False, use_reloader=False)

    thread = threading.Thread(target=run_flask, daemon=True)
    thread.start()

    time.sleep(1)
    webbrowser.open("http://127.0.0.1:5000")
    thread.join()


if __name__ == "__main__":
    main()
