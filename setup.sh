#!/usr/bin/env bash
# Installs what the video skills need. Safe to run more than once.
set -e
python3 -m pip install -q faster-whisper
# pre-download the Whisper model so the first caption job doesn't wait for it
HF_HUB_DISABLE_XET=1 python3 -c "from faster_whisper import WhisperModel; WhisperModel('large-v3', device='cpu', compute_type='int8')"
