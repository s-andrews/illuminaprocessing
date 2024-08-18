#!/bin/bash

# Usage check_file_sizes.sh [run folder] [lane]
# e.g. check_file_sizes.sh 221110_NB501547_0639_AHJLTLBGXL 1
# To execute from the run_folder on scratch 
# /bi/scratch/scripts/check_file_sizes.sh `basename "$PWD"` 1

if [ "$#" -lt 2 ]; then
    echo "Please supply 2 arguments - the first must be the run folder name, the 2nd must be the lane number for Sierra (usually 1)."
    exit 1
fi

RUN_FOLDER=$1
no=$2
SCRATCH_FOLDER="/bi/scratch/run_processing/${RUN_FOLDER}"
NEXT_LEVEL_SCRATCH_FOLDER="/bi/scratch/run_processing/${RUN_FOLDER}/*"
SEQFAC_BASE="/bi/seqfac/seqfac/${RUN_FOLDER}"
SEQFAC_ALIGNED="${SEQFAC_BASE}/Aligned/*/Sample_lane${no}"
SEQFAC_UNALIGNED="${SEQFAC_BASE}/Unaligned/*/Sample_lane${no}"
UNEQUAL_SIZES=0
OUTFILE="${SCRATCH_FOLDER}/file_sizes_L00${no}.log"

echo -e "\nChecking file sizes in $RUN_FOLDER\nWriting summary to ${OUTFILE}\n"
echo -e "\n========================== folder locations ===========================\n" > $OUTFILE

total_size () {
	du --apparent-size --block-size=1 -c $1 | tail -n 1 | cut -f 1 
}

write_out () {
	echo -e $1 >> $OUTFILE
}

h_size () {
	numfmt --to=iec $1
}

write_out "Run folder:\t\t${RUN_FOLDER}"
write_out "scratch location:\t${SCRATCH_FOLDER}"
write_out "seqfac location:\t${SEQFAC_BASE}"
write_out "\n\n===================   Checking total file sizes   ========================\n"

#shopt -s nullglob

BAM_FILES=(${SCRATCH_FOLDER}/*bam)
if [ -f ${BAM_FILES[0]} ]; then
	bam1=$(total_size "$SCRATCH_FOLDER/*L00${no}*bam")
	bam2=$(total_size "$SEQFAC_ALIGNED/*bam")
	
	if [ $bam1 == $bam2 ]; then
		write_out "Woohoo, total bam file size matches\n" 
	else
		((UNEQUAL_SIZES+=1))
		write_out "Aargh, total bam file size doesn't match\n"
	fi
else 
	# This was added to deal with the trael processing where there are sub folders within the run folder.
	write_out "No bam files found in ${SCRATCH_FOLDER}, checking subfolders..."
	
	BAM_FILES_NESTED=(${NEXT_LEVEL_SCRATCH_FOLDER}/*bam)
	if [ -f ${BAM_FILES_NESTED[0]} ]; then
		
		bam1=$(total_size "$NEXT_LEVEL_SCRATCH_FOLDER/*L00${no}*bam")
		bam2=$(total_size "$SEQFAC_ALIGNED/*bam")
		
		if [ $bam1 == $bam2 ]; then
			write_out "Woohoo, total bam file size matches\n"
		else
			((UNEQUAL_SIZES+=1))
			write_out "Aargh, total bam file size doesn't match\n"
		fi
	else
		echo "No bam files found at all."
		write_out "No bam files found in ${NEXT_LEVEL_SCRATCH_FOLDER}, should there be some somewhere?...\n"
		bam1=0
		bam2=0
	fi	
fi


FASTQ_FILES=(${SCRATCH_FOLDER}/*fastq.gz)
FASTQ_FILES2=(${SEQFAC_UNALIGNED}/*fq.gz)

if [ -L ${FASTQ_FILES[0]} ]; then
	echo "seem to have found a symlink..."
	write_out "First fastq file found is a symlink, assuming all others are too. \n File sizes will be included in the details below.\n"
	fastq1=$(total_size "$SCRATCH_FOLDER/*L00${no}*fastq.gz")
	fastq2=$(total_size "$SEQFAC_UNALIGNED/*fastq.gz")
elif [ -f ${FASTQ_FILES[0]} ]; then
	# First fastq file found is not a symlink so checking file sizes	
	fastq1=$(total_size "$SCRATCH_FOLDER/*L00${no}*fastq.gz")
	fastq2=$(total_size "$SEQFAC_UNALIGNED/*fastq.gz")
	
	if [ $fastq1 == $fastq2 ]; then
		write_out "Woohoo, total fastq file size matches\n"
	else
		((UNEQUAL_SIZES+=1))
		write_out "Aargh, total fastq file size doesn't match\n"
	fi
else
	write_out "No fastq.gz files found in ${SCRATCH_FOLDER}, checking subfolders..."
	
	FASTQ_FILES_NESTED=(${NEXT_LEVEL_SCRATCH_FOLDER}/*fastq.gz)
	if [ -L ${FASTQ_FILES_NESTED[0]} ]; then
		write_out "First fastq file found in nested folder is a symlink, assuming all others are too. \n File sizes will be included in the details below.\n"
		fastq1=$(total_size "$NEXT_LEVEL_SCRATCH_FOLDER/*L00${no}*fastq.gz")
		fastq2=$(total_size "$SEQFAC_UNALIGNED/*fastq.gz")
	elif [ -f ${FASTQ_FILES_NESTED[0]} ]; then
	# First fastq file found is not a symlink so checking file sizes	
		fastq1=$(total_size "$NEXT_LEVEL_SCRATCH_FOLDER/*L00${no}*fastq.gz")
		fastq2=$(total_size "$SEQFAC_UNALIGNED/*fastq.gz")
		
		if [ $fastq1 == $fastq2 ]; then
			write_out "Woohoo, total fastq file size matches\n"
		else
			((UNEQUAL_SIZES+=1))
			write_out "Aargh, total fastq file size doesn't match\n"
		fi
	else
		write_out "No fastq.gz files found in ${NEXT_LEVEL_SCRATCH_FOLDER}, should there be some somewhere?...\n"
		fastq1=0
		# check for fastq in seqfac, they may be .fq.gz in scratch 
		if [ -f ${FASTQ_FILES2[0]} ]; then
			write_out "Found fastq files in ${SEQFAC_UNALIGNED}\n"
			fastq2=$(total_size "$SEQFAC_UNALIGNED/*fastq.gz")
		else 
			fastq2=0
		fi
	fi
fi


FQ_FILES1=(${SCRATCH_FOLDER}/*fq.gz)
FQ_FILES2=(${SEQFAC_UNALIGNED}/*fq.gz)

if [ -f ${FQ_FILES1[0]} ]; then 
	#echo "fq.gz files found - will check sizes"
	fq1=$(total_size "$SCRATCH_FOLDER/*L00${no}*fq.gz")
	
	if [ $fq1 == 0 ]; then
		write_out "No fq files found containing L00${no}, searching more generically\n"
		fq1=$(total_size "$SCRATCH_FOLDER/*fq.gz")
	fi
	
	if [ -f ${FQ_FILES2[0]} ]; then 
		fq2=$(total_size "$SEQFAC_UNALIGNED/*fq.gz")
	else
		fq2=0
	fi

	if [ $fq1 == $fq2 ]; then
		write_out "Woohoo, total fq file size matches\n" 
	else
		((UNEQUAL_SIZES+=1))
		write_out "Aargh, total fq file size doesn't match\n" 
	fi	
else
	# This was added to deal with the trael processing where there are sub folders within the run folder.
	write_out "No fq.gz files found in ${SCRATCH_FOLDER}, checking subfolders..."
	
	FQ_FILES_NESTED=(${NEXT_LEVEL_SCRATCH_FOLDER}/*L00${no}*fq.gz)
	if [ -f ${FQ_FILES_NESTED[0]} ]; then
		write_out "Found some fq.gz files in scratch subfolders, this is the first one:"
		write_out "${FQ_FILES_NESTED[0]}"
		fq1=$(total_size "$NEXT_LEVEL_SCRATCH_FOLDER/*L00${no}*fq.gz")
		if [ -f ${FQ_FILES2[0]} ]; then 
			fq2=$(total_size "$SEQFAC_UNALIGNED/*fq.gz")
		else
			write_out "No fq.gz files found in $SEQFAC_UNALIGNED" 
			fq2=0
		fi
		
		if [ $fq1 == $fq2 ]; then
			write_out "Woohoo, total fq.gz file size matches\n"
		else
			((UNEQUAL_SIZES+=1))
			write_out "Aargh, total fq.gz file size doesn't match\n"
		fi
	else
		echo "No fq.gz files found at all."
		write_out "No fq.gz files found in ${NEXT_LEVEL_SCRATCH_FOLDER}\n"
		fq1=0
		fq2=0
	fi
fi

write_out "\n\n-------------------- details --------------------\n"
write_out "The size check was in bytes, these numbers have been rounded.\n"
write_out "\n---- bam ----"
write_out "$(h_size "$bam1")\tscratch"
write_out "$(h_size "$bam2")\tseqfac"

write_out "\n---- fastq ---"
write_out "$(h_size "$fastq1")\tscratch"
write_out "$(h_size "$fastq2")\tseqfac"

write_out "\n---- fq -----"
write_out "$(h_size "$fq1")\tscratch"
write_out "$(h_size "$fq2")\tseqfac\n"

# need to deal with multi-runs which have multiple multiqc reports
num_multiqc_reports=$(find $SEQFAC_UNALIGNED/ -name '*multiqc*html' | wc -l)

if [ "$num_multiqc_reports" -gt 1 ]; then
	write_out "$num_multiqc_reports multiqc reports found in $SEQFAC_UNALIGNED\n"
elif [ "$num_multiqc_reports" == 1 ]; then
	write_out "multiqc report found in $SEQFAC_UNALIGNED\n"
else	
	write_out "No multiqc report found in $SEQFAC_UNALIGNED\n"
fi	

if [ -f $SCRATCH_FOLDER/raw_data*tar.gz ]; then
	write_out "gzipped raw_data file found in scratch folder"
	raw1=$(total_size "$SCRATCH_FOLDER/raw_data*tar.gz")
	
	if [ -f $SEQFAC_UNALIGNED/raw_data*tar.gz ]; then
		write_out "gzipped raw_data file found in seqfac folder"
		raw2=$(total_size "$SEQFAC_UNALIGNED/raw_data*tar.gz")
		write_out "$(h_size "$raw1")\tscratch"
		write_out "$(h_size "$raw2")\tseqfac"
	else
		write_out "No raw_data file in seqfac folder"
		write_out "$(h_size "$raw1")\tscratch"
	fi
fi

write_out "\nTo check file sizes further, use a combination of these commands:\n"	
write_out "du --apparent-size -ch"
write_out "$SCRATCH_FOLDER/"
write_out "$SEQFAC_UNALIGNED/"
write_out "$SEQFAC_ALIGNED/\n"

