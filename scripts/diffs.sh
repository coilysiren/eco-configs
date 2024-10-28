#!/bin/bash

function show_diff() {
  printf "\n"
  printf "%s" "$1"
  printf "\n"
  jq . "Configs/$1" | sponge "../$1" && jd -set "Configs/$1.template" "../$1"
}

cat scripts/diffs.txt | while read -r diff; do
  show_diff "$diff"
done
