import sys
import os
import time

from PyQt5.QtWidgets import QDialog
from PyQt5.QtCore import QThread, pyqtSignal, QLibraryInfo
from PyQt5.QtWidgets import (
    QApplication, QWidget, QPushButton, QVBoxLayout,
    QFileDialog, QTextEdit, QListWidget, QListWidgetItem,
    QLabel, QProgressBar
)

# Qt plugin 문제 해결
os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"] = QLibraryInfo.location(QLibraryInfo.PluginsPath)

from core.pipeline import prepare_video, transcribe_selected


# ======================
# Worker Thread
# ======================
class Worker(QThread):
    progress = pyqtSignal(int)
    log = pyqtSignal(str)

    def __init__(self, func):
        super().__init__()
        self.func = func

    def run(self):
        try:
            self.func(self)
        except Exception as e:
            self.log.emit(f"❌ 에러: {str(e)}")


# ======================
# 메인 앱
# ======================
class App(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("🎬 VideoTranscriber")
        self.resize(700, 850)

        self.layout = QVBoxLayout()

        # 상태 표시
        self.status_label = QLabel("대기중...")
        self.layout.addWidget(self.status_label)

        self.label = QLabel("영상 파일을 선택하세요")
        self.layout.addWidget(self.label)

        # 영상 선택
        self.btn_select = QPushButton("📂 영상 불러오기")
        self.btn_select.clicked.connect(self.select_video)
        self.layout.addWidget(self.btn_select)

        # 영상 분석
        self.btn_split = QPushButton("🎞 영상 분석 및 구간 분할")
        self.btn_split.clicked.connect(self.split_video)
        self.layout.addWidget(self.btn_split)

        # chunk 리스트
        self.list_widget = QListWidget()
        self.layout.addWidget(self.list_widget)

        # chunk 클릭 이벤트
        self.list_widget.itemDoubleClicked.connect(self.preview_chunk)

        # 전체 추출
        self.btn_all = QPushButton("📄 전체 영상 대본 생성")
        self.btn_all.clicked.connect(self.run_all)
        self.layout.addWidget(self.btn_all)

        # 선택 추출
        self.btn_selected = QPushButton("✂ 선택한 구간만 대본 생성")
        self.btn_selected.clicked.connect(self.run_selected)
        self.layout.addWidget(self.btn_selected)

        # 전체 미리보기 버튼
        self.btn_preview_full = QPushButton("전체 추출된 대본 미리보기")
        self.btn_preview_full.setEnabled(False)
        self.btn_preview_full.clicked.connect(self.preview_full_text)
        self.layout.addWidget(self.btn_preview_full)

        # 진행률
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.layout.addWidget(self.progress_bar)

        # 미리보기 안내
        self.preview_area = QTextEdit()
        self.preview_area.setReadOnly(True)
        self.preview_area.setPlaceholderText(
            "구간 클릭 시 미리보기가 표시됩니다."
        )
        self.layout.addWidget(self.preview_area)

        # 로그창
        self.text_area = QTextEdit()
        self.text_area.setReadOnly(True)
        self.layout.addWidget(self.text_area)

        self.setLayout(self.layout)

        self.video_path = None
        self.job = None
        self.worker = None
        self.full_txt_path = None

        # 스타일
        self.setStyleSheet("""
            QWidget {
                background-color: #121212;
                color: #f5f5f5;
                font-size: 13px;
            }

            QPushButton {
                background-color: #2f6df6;
                padding: 12px;
                border-radius: 12px;
                font-weight: bold;
            }

            QPushButton:hover {
                background-color: #1d56d8;
            }

            QListWidget {
                background-color: #1a1a1a;
                border-radius: 12px;
                padding: 5px;
            }

            QTextEdit {
                background-color: #0d0d0d;
                border-radius: 12px;
                padding: 10px;
            }

            QProgressBar {
                background-color: #222;
                border-radius: 8px;
                height: 14px;
            }

            QProgressBar::chunk {
                background-color: #00e676;
                border-radius: 8px;
            }

            QLabel {
                font-weight: bold;
            }
        """)

    # ======================
    # 영상 선택
    # ======================
    def select_video(self):
        file, _ = QFileDialog.getOpenFileName(
            self,
            "영상 선택",
            "",
            "Video Files (*.mp4)"
        )

        if file:
            self.video_path = file
            self.label.setText(f"선택됨: {os.path.basename(file)}")

    # ======================
    # 영상 분할
    # ======================
    def split_video(self):
        if not self.video_path:
            self.text_area.setText("❗ 영상 먼저 선택하세요")
            return

        self.progress_bar.setValue(0)

        self.status_label.setText("영상 분석중...")
        self.text_area.append("🎬 영상 분석 시작...")

        self.worker = Worker(self.split_video_thread)

        self.worker.progress.connect(self.update_progress)
        self.worker.log.connect(self.update_log)

        self.worker.start()

    def split_video_thread(self, worker):
        self.job = prepare_video(self.video_path)

        total = len(self.job["chunk_files"])

        self.list_widget.clear()

        for i, path in enumerate(self.job["chunk_files"], 1):

            start_min = (i - 1) * 5
            end_min = i * 5

            time_text = f"[{start_min:02}:00 ~ {end_min:02}:00]"

            item = QListWidgetItem(f"{i}. {time_text}")

            item.setCheckState(0)
            item.setData(1, path)

            self.list_widget.addItem(item)

            percent = int((i / total) * 100)

            worker.progress.emit(percent)
            worker.log.emit(f"chunk 생성 ({i}/{total})")

            time.sleep(0.2)

        worker.log.emit("✔ 분할 완료")

        self.status_label.setText("✔ 분할 완료")

    # ======================
    # 전체 추출
    # ======================
    def run_all(self):
        if not self.job:
            self.text_area.setText("❗ 먼저 영상 분석하세요")
            return

        self.progress_bar.setValue(0)

        self.status_label.setText("전체 영상 분석중...")
        self.text_area.append("📄 전체 대본 생성 시작...")

        self.worker = Worker(self.run_all_thread)

        self.worker.progress.connect(self.update_progress)
        self.worker.log.connect(self.update_log)

        self.worker.start()

    def run_all_thread(self, worker):

        files = self.job["chunk_files"]

        total = len(files)

        txt_path, srt_path = transcribe_selected(
            self.job["base_dir"],
            self.job["srt_dir"],
            files,
            "result"
        )

        for i in range(total):
            percent = int(((i + 1) / total) * 100)

            worker.progress.emit(percent)

            worker.log.emit(f"🎧 처리중 ({i+1}/{total})")

            time.sleep(0.1)

        self.full_txt_path = txt_path

        self.btn_preview_full.setEnabled(True)

        worker.log.emit(f"✔ 완료: {txt_path}")

        self.status_label.setText("✔ 전체 추출 완료")

    # ======================
    # 선택 추출
    # ======================
    def run_selected(self):

        if not self.job:
            self.text_area.setText("❗ 먼저 영상 분석하세요")
            return

        selected = []

        for i in range(self.list_widget.count()):

            item = self.list_widget.item(i)

            if item.checkState():
                selected.append(item.data(1))

        if not selected:
            self.text_area.setText("❗ 처리할 구간 선택하세요")
            return

        self.progress_bar.setValue(0)

        self.status_label.setText("선택 구간 분석중...")
        self.text_area.append("✂ 선택 구간 처리 시작...")

        self.worker = Worker(
            lambda w: self.run_selected_thread(w, selected)
        )

        self.worker.progress.connect(self.update_progress)
        self.worker.log.connect(self.update_log)

        self.worker.start()

    def run_selected_thread(self, worker, selected):

        total = len(selected)

        txt_path, srt_path = transcribe_selected(
            self.job["base_dir"],
            self.job["srt_dir"],
            selected,
            "partial"
        )

        for i in range(total):
            percent = int(((i + 1) / total) * 100)

            worker.progress.emit(percent)

            worker.log.emit(f"🎧 처리중 ({i+1}/{total})")

            time.sleep(0.1)

        worker.progress.emit(100)

        worker.log.emit(f"✔ 완료: {txt_path}")

        self.status_label.setText("✔ 선택 추출 완료")

    # ======================
    # 전체 미리보기
    # ======================
    def preview_full_text(self):

        if not self.full_txt_path:
            return

        if not os.path.exists(self.full_txt_path):
            return

        with open(self.full_txt_path, "r", encoding="utf-8") as f:
            text = f.read()

        dialog = QDialog(self)

        dialog.setWindowTitle("📄 전체 대본 미리보기")

        dialog.resize(900, 700)

        layout = QVBoxLayout()

        text_edit = QTextEdit()

        text_edit.setReadOnly(True)

        text_edit.setText(text)

        layout.addWidget(text_edit)

        dialog.setLayout(layout)

        dialog.exec_()

    # ======================
    # chunk 미리보기
    # ======================
    def preview_chunk(self, item):

        path = item.data(1)

        preview_path = path.replace(".mp3", "_preview.txt")

        if not os.path.exists(preview_path):

            self.preview_area.setText(
                "❌ 아직 추출되지 않은 영상 데이터입니다.\n\n"
                "먼저 대본 생성을 진행하세요."
            )

            return

        with open(preview_path, "r", encoding="utf-8") as f:
            text = f.read()

        dialog = QDialog(self)

        dialog.setWindowTitle("🎬 구간 대본 미리보기")

        dialog.resize(800, 600)

        layout = QVBoxLayout()

        preview_text = QTextEdit()

        preview_text.setReadOnly(True)

        preview_text.setText(text)

        layout.addWidget(preview_text)

        dialog.setLayout(layout)

        dialog.exec_()

    # ======================
    # UI 업데이트
    # ======================
    def update_progress(self, value):
        self.progress_bar.setValue(value)

    def update_log(self, text):
        self.text_area.append(text)


# ======================
# 실행
# ======================
if __name__ == "__main__":
    app = QApplication(sys.argv)

    window = App()

    window.show()

    sys.exit(app.exec_())