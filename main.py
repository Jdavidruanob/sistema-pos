import sys
from PySide6.QtWidgets import QApplication
from db.database import init_db
from ui.login_window import LoginWindow


def main():
    init_db()

    app = QApplication(sys.argv)
    window = LoginWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()