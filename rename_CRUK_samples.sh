#!/bin/bash

Help()
{ 
   echo -e "\nSyntax: rename_samples.sh [options: -h|-c(cellranger mode)] [contents file] [lane no] [extra text to remove (optional)]\n"
  
   echo "This script is intended to rename fastq files from CRUK using the accompanying contents.csv file, adding sample names, and a lane number so that they are compatible with the format required by copy_back_files to copy them to Sierra.\n"
   echo "The fastq files must be in the directory where the script is executed from."
   
   echo "options:"   
   echo "h     Print this Help."
   echo "c     cellranger naming - adds a 001 directly before .fastq.gz. Only use this if the files will be processed with cellranger. Do not use if processing with other nextflow pipelines e.g. rnaseq, bismark as they may not recognise when files are paired end as they expect xxxx_R1.fastq.gz and xxxx_R2.fastq.gz."
   echo
}

while getopts "hc" flag; do
   case ${flag} in
      h) Help
         exit 0;;
      c) echo "setting cellranger mode"   
         CELLRANGER="true";;
     \?) echo "Error: Invalid option"
         exit 0;;
   esac
done


if [ "$#" -lt 2 ]; then
    echo -e "\nPlease supply at least 2 unnamed arguments - the first must be the contents.csv file, the 2nd must be the lane number for Sierra." 
    Help
    exit 1
fi

FILE=${@:$OPTIND:1}
LANE=${@:$OPTIND+1:1}
TO_REMOVE=${@:$OPTIND+2:1}

echo "file: $FILE"
echo "lane: $LANE"

if ! [[ $LANE =~ ^[0-8]{1}$ ]]; then 
    echo "A lane number between 1 and 8 must be supplied as the second argument. The first must be the contents.csv file."
    exit 1
fi

while read -r LINE; do
    LINEARRAY=(${LINE//,/ })
	SLX=${LINEARRAY[0]}
    BARCODE=${LINEARRAY[1]}
    NAME=${LINEARRAY[3]}
    rename .$BARCODE. _${BARCODE}_${NAME}_ ${SLX}*fq.gz
    
done < $FILE

# rename s/i/r and add lane number
rename .s_ _S ${SLX}*fq.gz
rename .i_ _L00${LANE}_I ${SLX}*fq.gz
rename .r_ _L00${LANE}_R ${SLX}*fq.gz

# remove '-' from SLX-xxxxx
SLX2=$(echo $SLX | tr -d -)
rename ${SLX} ${SLX2} *fq.gz

if [[ ! -z "$CELLRANGER" ]]
then
    rename .fq.gz _001.fastq.gz ${SLX2}*fq.gz
else 
    rename .fq.gz .fastq.gz ${SLX2}*fq.gz
fi

if [[ ! -z "$TO_REMOVE" ]]
then 
    echo "also removing string $TO_REMOVE"
    rename ${TO_REMOVE} "" *fastq.gz  
    rename "__" "_" *fastq.gz 
fi
