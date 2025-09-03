#!/usr/bin/bash

mkdir Aligned
mkdir Aligned/Project_External

mkdir Unaligned
mkdir Unaligned/Project_External

for lane in $(seq 1 $1) 
do
    mkdir Unaligned/Project_External/Sample_lane$lane
    mkdir Aligned/Project_External/Sample_lane$lane
done