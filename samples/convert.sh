#!/bin/bash
# Exit on error
set -e

input_dir="original"

# Count the total number of .wav files
total_files=$(find "$input_dir" -type f -name '*.wav' | wc -l)
current_file=0

find "$input_dir" -type f -name '*.wav' | while IFS= read -r infile; do
  current_file=$((current_file + 1))
  echo "Processing file $current_file of $total_files: $infile"
  

  infile_stripped=${infile#$input_dir}
  outfile="converted/${infile_stripped#./}" # Strip "input_dir/" from the outdir path
  outdir="$(dirname "$outfile")"
  mkdir -p "$outdir"
  ffmpeg -y -i "$infile" -loglevel error -ac 1 -ar 22050 "${outfile%.wav}_mono22k.wav"
done