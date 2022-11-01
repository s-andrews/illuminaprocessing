#!/bin/bash
# adds sample names to file names using contents.csv file
# usage: rename_samples.sh [contents file] [lane no] [extra text to remove (optional)]
# usage: ./rename_samples.sh SLX-20900.HL2JTDSX3.s_3.contents.csv 1
if [ "$#" -lt 2 ]; then
    echo "Please supply 2 or 3 arguments - the first must be the contents.csv file, the 2nd must be the lane number for Sierra. Then a string to remove can also be appended to the arguments."
    exit 1
fi

FILE=$1
LANE=$2
TO_REMOVE=$3

if ! [[ $LANE =~ ^[0-8]{1}$ ]]; then 
    echo "A lane number between 1 and 8 must be supplied as the second argument. The first must be the contents.csv file."
    exit 1
fi


#echo $TO_REMOVE

while read -r LINE; do
    LINEARRAY=(${LINE//,/ })
	SLX=${LINEARRAY[0]}
    BARCODE=${LINEARRAY[1]}
    NAME=${LINEARRAY[3]}
    #echo "renaming $BARCODE to ${BARCODE}_${NAME} for all files"
    rename .$BARCODE. _${BARCODE}_${NAME}_ ${SLX}*fq.gz
    
done < $FILE

# rename s/i/r and add lane number
rename .s_ _S ${SLX}*fq.gz
rename .i_ _L00${LANE}_I ${SLX}*fq.gz
rename .r_ _L00${LANE}_R ${SLX}*fq.gz

# remove '-' from SLX-xxxxx
SLX2=$(echo $SLX | tr -d -)
rename ${SLX} ${SLX2} *fq.gz

# cellranger wants .fastq.gz not fq.gz - we might need the 001 for cellranger, I'm not 100% sure. 
# TODO: add a --cellranger flag to add the 001 in 
#rename .fq.gz _001.fastq.gz *
rename .fq.gz .fastq.gz ${SLX2}*fq.gz

if [[ ! -z "$TO_REMOVE" ]]
then 
    echo "also removing string $TO_REMOVE"
    rename "_"${TO_REMOVE} "" *fastq.gz    
fi
