# Interview Insights

Pipeline for interview recordings: run transcription, collect transcripts in `transcriptions/`, and write insights/results to `inrewiev_insides/`.

## Flow
1) Place raw interview audio/video where the speech-to-text runner can reach it.
2) Start the transcription job (via the `speech-to-text` module). All generated text lands in `transcriptions/`.
3) Feed transcripts into the analysis step (LLM prompts, scoring, materials). Outputs are saved in `inrewiev_insides/`.
4) Review results in `inrewiev_insides/`; rerun analysis if you adjust prompts or inputs.

## Layout
- `speech-to-text/` - git submodule pointing to https://github.com/Irina-Na/speech-to-text
- `src/` - interview analysis code (prompts, analysis, UI entrypoints)
- `transcriptions/` - collected raw transcripts from each run
- `inrewiev_insides/` - generated insights and final artifacts

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
