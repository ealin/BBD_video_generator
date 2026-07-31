---
name: voice2video_skill
description: Automatically batch generate animated character videos from MP3 audio files on pure green screen, mapping TTS voices/speakers to custom Adobe Express character models dynamically using 發音人清單.csv and user input.
---

# Voice to Video Animation Batch Generator Skill (`voice2video_skill`)

Use this skill when you need to batch generate voice-synchronized character animation videos (with a pure green screen background `#27BB36`) from a directory of MP3 audio clips based on a speaker mapping CSV file.

## Prerequisites

1.  **Playwright and dependencies:**
    Ensure `playwright` is installed and Chrome/Chromium binaries are available in the virtual environment.
2.  **Adobe Session State:**
    A valid Adobe Express session JSON file must exist at `config/adobe_session.json`. If missing or expired, run an interactive Chrome session manually, log in to Adobe Express, and save the cookies using `page.context.storage_state(path="config/adobe_session.json")`.

---

## Workflow Steps for the Agent

### Step 1: Locate Inputs and Extract Voices
1.  Verify the input MP3 files directory exists.
2.  Locate `發音人清單.csv`.
3.  Read the CSV file using Python's `csv` module with `encoding="utf-8-sig"` (to correctly strip BOM marks).
4.  Extract all unique values in the `TTS語音` (or `發音人`, `角色名稱`) column.

### Step 2: Query Character Mapping from the User
Output a clear, formatted table to the user listing all unique speaker names found in the CSV. Ask the user to specify which Adobe Express character name (e.g. `Sticky` for stickman, `Aihan`, `Anna`, `Rei`, etc.) should be mapped to each unique speaker voice.

> [!NOTE]
> Do NOT guess the characters; always present the list of unique voices to the user and obtain their preference.

### Step 3: Trigger the Batch Generation Script
Once the user provides the character mappings, construct a JSON string representation of the mappings:
```json
{
  "zh-TW-HsiaoChenNeural": "Aihan",
  "zh-TW-YunJheNeural": "Sticky",
  "zh-CN-YunyangNeural": "Sticky"
}
```

Run the background batch processing command:
```bash
.venv/bin/python -u .agents/skills/voice2video_skill/scripts/batch_generator.py \
  --input-dir "path/to/mp3_dir" \
  --output-dir "path/to/stickman_green" \
  --csv-path "path/to/發音人清單.csv" \
  --char-mapping '{"zh-TW-HsiaoChenNeural": "Aihan", "zh-TW-YunJheNeural": "Sticky", "zh-CN-YunyangNeural": "Sticky"}' \
  --session-path "config/adobe_session.json"
```

### Step 4: Monitor and Report Progress
1.  Monitor the log files in the background.
2.  Verify that correct character choices are printed for each file (e.g. `[1/283] B146_0001.mp3 (配角: Sticky)`).
3.  Check for completed `.mp4` files in the output directory.
4.  Provide periodic status updates to the user.
