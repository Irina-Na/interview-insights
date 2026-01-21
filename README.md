# Interview Insights

Pipeline for analyzing interview recordings: ingest audio/video, transcribe with the existing speech-to-text module, and send transcripts to LLM (GPT-5.2) for feedback (errors, better answers, materials).

## Layout
- `speech-to-text/` — git submodule pointing to https://github.com/Irina-Na/speech-to-text
- `src/` — interview analysis code (prompts, analysis, UI entrypoints)

## Getting started
```bash
# clone
git clone --recurse-submodules https://github.com/Irina-Na/interview-insights.git
cd interview-insights

# if already cloned without submodules
git submodule update --init --recursive

# optional: install deps
python -m venv .venv
.venv\Scripts\activate
pip install -e .
```

## Notes
- `speech-to-text` stays isolated, so you can update or replace ASR independently.
- Add your LLM prompts and analysis logic under `src/`.