from pathlib import Path



class StoragePaths:
    BASE_DIR = Path(__file__).parent.parent.parent
    LOG_DIR = BASE_DIR / "logs"
    MARKDOWN_DIR = BASE_DIR / "output" / "markdown"
    AUDIO_DIR = BASE_DIR / "output" / "audio"
    TEMP_DIR = BASE_DIR / "temp"