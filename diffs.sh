#!/bin/bash

function show_diff() {
  printf "\n"
  printf "%s" "$1"
  printf "\n"
  jq . "$1" | sponge "$1" && jd -set "$1.template" "$1"
}

cat diffs.txt | while read -r diff; do
  show_diff "$diff"
done
