# ==================================================================
# File: logic/markitdown_converter.py
# Description: 
# ==================================================================

import os
from PyQt6.QtCore import QThread, pyqtSignal

class MarkItDownConverterThread(QThread):
    progress = pyqtSignal(int)
    status = pyqtSignal(str)
    finished = pyqtSignal(bool, str)

    def __init__(self, input_file: str, output_file: str, openai_api_key: str = ""):
        super().__init__()
        self.input_file = input_file
        self.output_file = output_file
        self.openai_api_key = openai_api_key

    def run(self):
        try:
            self.status.emit(f"Initializing MarkItDown for {os.path.basename(self.input_file)}...")
            self.progress.emit(10)

            # Lazy import to avoid loading markitdown if not used
            from markitdown import MarkItDown

            if self.openai_api_key:
                from openai import OpenAI
                client = OpenAI(api_key=self.openai_api_key)
                md = MarkItDown(llm_client=client, llm_model="gpt-4o")
                self.status.emit("MarkItDown initialized with AI capabilities (OpenAI)")
            else:
                md = MarkItDown()
                self.status.emit("MarkItDown initialized")

            self.progress.emit(30)
            self.status.emit(f"Converting {os.path.basename(self.input_file)}...")

            result = md.convert(self.input_file)
            
            self.progress.emit(80)
            self.status.emit("Writing markdown to file...")
            
            with open(self.output_file, 'w', encoding='utf-8') as f:
                f.write(result.text_content)
                
            self.progress.emit(100)
            self.finished.emit(True, f"Successfully converted: {self.output_file}")
            
        except Exception as e:
            self.finished.emit(False, str(e))
