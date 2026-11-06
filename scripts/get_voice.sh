#!/usr/bin/env bash
# Downloads the free Piper "Ryan" voice (about 120 MB) into voices/.
set -e
cd "$(dirname "$0")/../voices"
curl -sSL -o ryan.tgz https://github.com/rhasspy/piper/releases/download/v0.0.2/voice-en-us-ryan-high.tar.gz
tar xzf ryan.tgz && rm ryan.tgz
