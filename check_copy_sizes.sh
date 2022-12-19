#!/bin/sh
# Usage check_copy_sizes.sh [run folder] [lane] 
# e.g. check_copy_sizes.sh 221110_NB501547_0639_AHJLTLBGXL 1 

if [ "$#" -lt 2 ]; then
    echo "Please supply 2 arguments - the first must be the run folder name, the 2nd must be the lane number for Sierra (usually 1)."
    exit 1
fi

run_folder=$1
no=$2

echo -e "\nFile size check for $run_folder" > copy_check.txt
echo -e "Writing summary to copy_check.txt"

scratch_path="/bi/scratch/run_processing/$run_folder"
seqfac_path="/bi/seqfac/seqfac/$run_folder"

bam_total_seqfac=$(du --apparent-size -ch $seqfac_path/Aligned/*/Sample_lane${no}/*bam | grep "total")
bam_total_scratch=$(du --apparent-size -ch $scratch_path/*bam | grep "total")

fastq_total_seqfac=$(du --apparent-size -ch $seqfac_path/*/*/Sample_lane${no}/*fastq.gz | grep "total")
fastq_total_scratch=$(du --apparent-size -ch $scratch_path/*fastq.gz | grep "total")

fq_gz_total_seqfac=$(du --apparent-size -ch $seqfac_path/*/*/Sample_lane${no}/*fq.gz | grep "total")
fq_gz_total_scratch=$(du --apparent-size -ch $scratch_path/*fq.gz | grep "total")

shopt -s extglob
all_gz_total_seqfac=$(du --apparent-size -ch $seqfac_path/*/*/Sample_lane${no}/!(*fastq).gz | grep "total")
all_gz_total_scratch=$(du --apparent-size -ch $scratch_path/!(*fastq).gz | grep "total")

multiqc_total_seqfac=$(du --apparent-size -ch $seqfac_path/*/*/Sample_lane${no}/*multiqc* | grep "total")
multiqc_total_scratch=$(du --apparent-size -ch $scratch_path/*multiqc* | grep "total")

echo -e "================\n\nbam files\n----------------" >> copy_check.txt
echo "seqfac:  $bam_total_seqfac" >> copy_check.txt
echo "scratch: $bam_total_scratch" >> copy_check.txt

echo -e "\n================\n\nfastq.gz files\n----------------" >> copy_check.txt
echo "seqfac:  $fastq_total_seqfac" >> copy_check.txt
echo "scratch: $fastq_total_scratch" >> copy_check.txt
echo "scratch fastq files may be symlinks" >> copy_check.txt

echo -e "\n================\n\nfq.gz files\n----------------" >> copy_check.txt
echo "seqfac:  $fq_gz_total_seqfac" >> copy_check.txt
echo "scratch: $fq_gz_total_scratch" >> copy_check.txt

echo -e "\n================\n\nall .gz files (except fastq.gz)\n----------------" >> copy_check.txt
echo "seqfac:  $all_gz_total_seqfac" >> copy_check.txt
echo "scratch: $all_gz_total_scratch" >> copy_check.txt

echo -e "\n================\n\nmultiqc files\n----------------" >> copy_check.txt
echo "seqfac:  $multiqc_total_seqfac" >> copy_check.txt
echo "scratch: $multiqc_total_scratch" >> copy_check.txt


if test -f $scratch_path/*summary*; then 
	summary_total_seqfac=$(du --apparent-size -ch $seqfac_path/*/*/Sample_lane${no}/*summary* | grep "total")
	summary_total_scratch=$(du --apparent-size -ch $scratch_path/*summary* | grep "total")
	echo -e "\n================\n\nsummary files\n----------------" >> copy_check.txt
	echo "seqfac:  $summary_total_seqfac" >> copy_check.txt
	echo "scratch: $summary_total_scratch" >> copy_check.txt
else
	echo -e "\n================\n\nsummary files\n----------------" >> copy_check.txt
	echo "no *summary* files found in scratch" >> copy_check.txt
fi





