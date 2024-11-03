import sys
import subprocess
import os
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout, QLabel, QMessageBox, QShortcut
from PyQt5.QtGui import QColor, QPalette, QKeySequence
from PyQt5.QtCore import Qt, QThread

class GameThread(QThread):
    def __init__(self, status_label):
        super().__init__()
        self.status_label = status_label
        self.process = None

    def run(self):
        try:
            # Get the current directory
            current_dir = os.path.dirname(os.path.abspath(__file__))
            game_path = os.path.join(current_dir, "P5.py")
            
            # Update status
            self.status_label.setText("Mencoba memulai permainan...")
            
            # Run the game
            self.process = subprocess.Popen(
                [sys.executable, game_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=os.environ.copy()
            )
            
            stdout, stderr = self.process.communicate()
            
            if self.process.returncode != 0:
                error_message = stderr.decode("utf-8") if stderr else "Gagal menjalankan permainan tanpa pesan error."
                self.status_label.setText(f"Error saat menjalankan permainan: {error_message}")
                print(f"Error output: {error_message}")  # For debugging
            else:
                self.status_label.setText("Permainan berhasil dijalankan!")
                print("Game started successfully")  # For debugging
                
        except Exception as e:
            self.status_label.setText(f"Error saat memulai permainan: {e}")
            print(f"Exception occurred: {e}")  # For debugging

    def stop(self):
        if self.process:
            self.process.terminate()
            self.process = None

class GameMenu(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Menu Permainan")
        self.setStyleSheet("background-color: #FFDDC1;")
        self.showFullScreen()
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)

        title_label = QLabel("Selamat Datang di Permainan Menembak!", self)
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("font-size: 42px; font-weight: bold; color: #333;")
        layout.addWidget(title_label)

        self.status_label = QLabel("", self)
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("font-size: 18px; color: #333;")
        layout.addWidget(self.status_label)

        self.start_button = QPushButton("Mulai Permainan")
        self.style_button(self.start_button, "#66CDAA", "#4CAF50")
        self.start_button.clicked.connect(self.start_game)
        layout.addWidget(self.start_button)

        self.credits_button = QPushButton("Credits")
        self.style_button(self.credits_button, "#87CEEB", "#4682B4")
        self.credits_button.clicked.connect(self.show_credits)
        layout.addWidget(self.credits_button)

        self.quit_button = QPushButton("Keluar Permainan")
        self.style_button(self.quit_button, "#FFA07A", "#CD5C5C")
        self.quit_button.clicked.connect(self.quit_game)
        layout.addWidget(self.quit_button)

        quit_shortcut = QShortcut(QKeySequence("Q"), self)
        quit_shortcut.activated.connect(self.quit_game)

        self.setLayout(layout)

    def style_button(self, button, color, hover_color):
        button.setStyleSheet(f"""
            QPushButton {{
                background-color: {color};
                font-size: 28px;
                font-weight: bold;
                color: #FFF;
                border-radius: 20px;
                padding: 20px 40px;
            }}
            QPushButton:hover {{
                background-color: {hover_color};
            }}
        """)
        button.setMinimumHeight(80)
        button.setMinimumWidth(500)

    def start_game(self):
        try:
            self.game_thread = GameThread(self.status_label)
            self.game_thread.start()
            self.status_label.setText("Permainan sedang dimulai...")
            print("Mencoba memulai permainan...")  # Debug output
            self.hide()  # Hide instead of close to maintain the thread
        except Exception as e:
            print(f"Error starting game: {e}")
            self.status_label.setText(f"Error: {str(e)}")

    def show_credits(self):
        credits = "Dibuat oleh Zwingli\n© Zwingli Savanarola Lubis"
        QMessageBox.information(self, "Credits", credits, QMessageBox.Ok)

    def quit_game(self):
        self.close()

if __name__ == "__main__":
    app = QApplication(sys.argv)

    palette = QPalette()
    palette.setColor(QPalette.Window, QColor("#FFDDC1"))
    app.setPalette(palette)

    menu = GameMenu()
    menu.show()
    sys.exit(app.exec_())