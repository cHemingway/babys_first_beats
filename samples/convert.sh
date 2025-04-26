#!/usr/bin/bash
find . -type f -name '*.wav' | while IFS= read -r infile; do
  outfile="converted/${infile#./}"
  outdir="$(dirname "$outfile")"
  mkdir -p "$outdir"
  ffmpeg -i "$infile" -ac 1 -ar 22050 "${outfile%.wav}_mono22k.wav"
done

