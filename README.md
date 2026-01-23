# Interview Insights

Pipeline for interview recordings: transcribe audio/video, then extract Q/A insights with an LLM.

---

# English

## What it does
- Transcribes media into `transcriptions/` (via `speech-to-text/`).
- Extracts Q/A pairs into `interview_insider/interview_insights/` as JSON and Markdown.
- Supports CLI and a Streamlit UI for insights.

## Project layout
- `speech-to-text/` - submodule with Whisper transcriber (separate container).
- `transcriptions/` - transcripts (`.txt`).
- `interview_insider/` - extraction code and Streamlit app (insights only).
- `interview_insider/interview_insights/` - QA outputs (`.json` + `.md`).

## Requirements
- Python 3.12+
- FFmpeg (for Whisper, in the ASR container)
- OpenAI API key for extraction (`OPENAI_API_KEY`)

## Install (local)
```bash
git clone --recurse-submodules https://github.com/Irina-Na/interview-insights.git
cd interview-insights

python -m venv .venv
# Windows PowerShell
.venv\Scripts\Activate.ps1
# Linux/macOS
source .venv/bin/activate

pip install -r requirements.txt
```

## CLI usage (QA extraction)
Extract from a transcript file or a folder of `.txt` files.

```bash
python -m interview_insider.qa_extractor \
  --model o4-mini \
  --transcript transcriptions \
  --vacancy "Data Analyst" \
  --resume path/to/resume.pdf \
  --language ru
```

Outputs are saved to `interview_insider/interview_insights/`.

### Models
CLI aliases: `o3`, `5.2`, `4.1`, `o4-mini`.

## Streamlit UI (insights only)

```bash
streamlit run interview_insider/app.py --server.maxUploadSize 2048
```

## Docker
Two-container setup (recommended):

Windows (PowerShell):
```powershell
$env:OPENAI_API_KEY="your_key"
docker compose up --build
```

Linux/macOS:
```bash
export OPENAI_API_KEY="your_key"
docker compose up --build
```

- ASR UI: http://localhost:8502 (writes transcripts into `transcriptions/`)
- Insights UI: http://localhost:8501 (reads from `transcriptions/`, or you can upload files)

Run only the Insights container (from compose):

Windows (PowerShell):
```powershell
$env:OPENAI_API_KEY="your_key"
docker compose up --build insights
```

Linux/macOS:
```bash
export OPENAI_API_KEY="your_key"
docker compose up --build insights
```

## Notes
- Resume formats supported: `.pdf`, `.txt`, `.md`.
- Scanned PDFs without text need OCR (not included).

---

# Русский

## Что делает проект
- Транскрибирует аудио/видео в `transcriptions/` (через `speech-to-text/`).
- Извлекает пары «вопрос–ответ» в `interview_insider/interview_insights/` в форматах JSON и Markdown.
- Поддерживает CLI и Streamlit‑интерфейс для инсайтов.

## Структура проекта
- `speech-to-text/` — сабмодуль с Whisper‑транскрибатором (отдельный контейнер).
- `transcriptions/` — транскрипты (`.txt`).
- `interview_insider/` — код извлечения и Streamlit‑приложение (только инсайты).
- `interview_insider/interview_insights/` — результаты QA (`.json` + `.md`).

## Требования
- Python 3.12+
- FFmpeg (для Whisper, внутри ASR‑контейнера)
- OpenAI API key для извлечения (`OPENAI_API_KEY`)

## Установка (локально)
```bash
git clone --recurse-submodules https://github.com/Irina-Na/interview-insights.git
cd interview-insights

python -m venv .venv
# Windows PowerShell
.venv\Scripts\Activate.ps1
# Linux/macOS
source .venv/bin/activate

pip install -r requirements.txt
```

## CLI (извлечение QA)
Извлечение из одного файла или папки с `.txt`‑транскриптами.

```bash
python -m interview_insider.qa_extractor \
  --model o4-mini \
  --transcript transcriptions \
  --vacancy "Data Analyst" \
  --resume path/to/resume.pdf \
  --language ru
```

Результаты сохраняются в `interview_insider/interview_insights/`.

### Модели
CLI‑алиасы: `o3`, `5.2`, `4.1`, `o4-mini`.

## Streamlit UI (только инсайты)

```bash
streamlit run interview_insider/app.py --server.maxUploadSize 2048
```

## Docker
Два контейнера (рекомендуется):

Windows (PowerShell):
```powershell
$env:OPENAI_API_KEY="your_key"
docker compose up --build
```

Linux/macOS:
```bash
export OPENAI_API_KEY="your_key"
docker compose up --build
```

- ASR UI: http://localhost:8502 (пишет транскрипты в `transcriptions/`)
- Insights UI: http://localhost:8501 (читает из `transcriptions/`, либо можно загрузить файлы)

Запуск только Insights контейнера (из compose):

Windows (PowerShell):
```powershell
$env:OPENAI_API_KEY="your_key"
docker compose up --build insights
```

Linux/macOS:
```bash
export OPENAI_API_KEY="your_key"
docker compose up --build insights
```

## Примечания
- Поддерживаемые форматы резюме: `.pdf`, `.txt`, `.md`.
- Для сканов PDF без текста нужен OCR (не включён).
