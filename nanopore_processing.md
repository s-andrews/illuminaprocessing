# PromethION processing

A folder is created in `/data` on pipeline2. This doesn't yet have a naming convention. The output file types that we get depend on what options have been selected on the machine when the run is initiated.

[Dorado](https://github.com/nanoporetech/dorado) can be used for basecalling, trimming and aligning. This is installed on the capstone cluster.

## Processing on the pipeline server

There is currently very limited processing that occurs on the pipeline server. Depending on the output files produced by the machine, these processes may be required:

-   merging of fastq files

-   merging of bam files (these will be unaligned)

-   tar and gzip of pod5 files

-   tar and gzip of report files

## Backing up the run

### Create run folder and structure on `/primary`

Choose a run folder name - there may or may not be one on Sierra already

``` bash
mkdir PromethION_1_20240716_1132_ab54f415 
cd PromethION_1_20240716_1132_ab54f415 
/home/sbsuser/illuminaprocessing/create_external_run_folder_structure_1_lane.sh
```

### Merging fastq files

If the reads have already been basecalled and demultiplexed on the machine, we should have a set of folders that include:

fastq_fail\
fastq_pass\

We can ignore the fastq_fail folder. Within fastq_pass there should be fastq files in barcode folders e.g.\
barcode01\
barcode02\
barcode03

The fastq files need merging as there are thousands of fastq.gz files that contain 4000 reads each. There is currently a `merge_nanopore_fastqs.sh` script in `~/illumina_processing` on pipeline2.

Run this from the location that we want the merged files to be written to (probably the root run folder name). The only argument to pass in is the folder name i.e. fastq_pass. The script will expect subfolders named barcode01, barcode02 etc plus unclassified.

``` bash
nohup ~/illuminaprocessing/merge_nanopore_fastqs.sh fastq_pass > fastq_pass_merge.log &
```

This should create one fastq.gz file for each barcode.

### Merging bam files

If unaligned bam files are present then these can be merged. These have only been produced for one run so far. The commands used for that run were as follows:

from `/primary/20241119_1616_P2I-00102_SB6139_cDNA_PCR/Unaligned/Project_External/Sample_lane1/unaligned_bam`

```         
for i in {01..12}; do ln -s /data/SB6139_cDNA_PCR_Barcoding_19112024/no_sample_id/20241119_1616_P2I-00102-A_PAW56776_6f11a984/bam_pass/barcode${i} .; done
for i in {01..12}; do samtools merge -o barcode${i}_L001_merged_unaligned.bam barcode${i}/* ; done
```

### Tar up pod5 files and reports

```         
nohup tar -zcvf pod5_pass_L001_all.tar.gz pod5_pass &
nohup tar -zcvf reports_L001_PAU87880.tar.gz *PAU87880*.{csv,txt,md,json} &

rename report_ report_L001_ *html
rename barcode_alignment barcode_alignment_L001 *tsv
```

### Copy fastq, bam, pod5 files and reports

Check they've all got \_*L001*\_ in `_L001_`{=asciidoc}the file name.

From /primary/[RUN_FOLDER]

```         
nohup cp /data/[RUN_FOLDER_ON_/DATA]/*_L001_* Unaligned/Project_External/Sample_lane1/ > copy.log &
```

## Mapping fastqs or unaligned bams

Dorado can be used for trimming and aligning - run it on a node with a GPU on the capstone cluster.

If bams are present, it is preferable to use those. 

### Trimming

Default trimming options seem to work.

Example command:

```         
for i in {01..06}; do ssub_node --node compute-0-1 --mem 20G -o barcode${i}_trimmed.bam -e barcode${i}_trimmed.err dorado trim barcode${i}_L001_merged_unaligned.bam; done
```

### Alignment

For spliced alignment specify `--mm2-opts "-x splice"`

The supplied genome needs to be a single fastq file\
Latest mouse: `/bi/scratch/Genomes/Mouse/GRCm39/Mus_musculus.GRCm39.dna.primary_assembly.fa`\
Latest human: `/bi/scratch/Genomes/Human/GRCh38/Homo_sapiens.GRCh38.mfa`

Example command:

```         
for i in {1..12}; do ssub_node --mem 30G --node compute-0-1 -o barcode${i}_L001_trimmed_splice_aligned.bam -e barcode${i}_L001_trimmed_splice_aligned.err dorado aligner /bi/scratch/Genomes/Human/GRCh38/Homo_sapiens.GRCh38.mfa --emit-summary --mm2-opts "-x splice" --output-dir trimmed_splice_aligned barcode${i}_trimmed.bam; done
```

The `--emit-summary` option only produces some very simple output (I can't remember exactly what).\
To get mapping stats, they recommend running `samtools flagstat`.

The following was from an ssub err file:

```         
tail barcode01_L001_trimmed_splice_aligned.err

[2024-11-26 14:47:29.786] [info] num input files: 1
[2024-11-26 14:47:29.786] [info] > loading index /bi/scratch/Genomes/Human/GRCh38/Homo_sapiens.GRCh38.mfa
[2024-11-26 14:49:45.046] [info] processing barcode01_L001_merged_trimmed.bam -> trimmed_splice_aligned/barcode01_L001_merged_trimmed.bam
[2024-11-26 14:49:45.738] [info] > starting alignment
[2024-11-26 14:53:01.469] [info] > finished alignment
[2024-11-26 14:53:01.469] [info] > merging temporary BAM files
[2024-11-26 14:53:43.595] [info] > Simplex reads basecalled: 727275
[2024-11-26 14:53:43.595] [info] > total/primary/unmapped 847610/94268/633009
[2024-11-26 14:53:44.525] [info] > generating summary file
[2024-11-26 14:54:04.876] [info] > summary file complete.
```

## Basecalling from pod5 files

Sometimes we have pod5_pass and pod5_fail, sometimes just pod5.

In this job, there were only pod5 files (not split into pass and fail) <https://www.bioinformatics.babraham.ac.uk/cgi-bin/helpdeskuser.cgi?action=show_job&public_id=kneelmarty>

We can use dorado basecaller and set a min Q score of 9 (this is the value used by default on the machine when filtering is enabled). Presumably if pod5_pass files are present and being used, they would already have a min Q score.\
To detect the barcodes, use the `kit-name` argument. The barcodes get detected and written into the output bam file. It only produces one output bam file at this stage, but the demultiplexer can then be run subsequently. The basecaller should be run on a gpu.

```         
ssub_node --mem 80G --node compute-0-2 -o outQ9_barcode.log -e outQ9_barcode.err dorado basecaller hac --models-directory /bi/apps/dorado/models_dir/ --min-qscore 9 --output-dir basecalled_Q9_barcoded pod5/ --kit-name SQK-PCB11-24
```

Same command split out below for clarity.

```         
ssub_node 
  --mem 80G 
  --node compute-0-2 
  -o outQ9_barcode.log 
  -e outQ9_barcode.err 
  dorado basecaller hac 
    --models-directory /bi/apps/dorado/models_dir/ 
    --min-qscore 9 
    --output-dir basecalled_Q9_barcoded pod5/ 
    --kit-name SQK-PCB11-24
```

From the docs...

```         
By default, dorado basecaller will attempt to detect any adapter or primer sequences at the beginning and ending of reads, and remove them from the output sequence.
```

We can then run the demultiplexer `dorado demux`. We need to have `--no-classify` in there for it to use the classifications in the bam files from the previous step. If we don't have that and we specify the kit again, it will try and detect the barcodes, which will no longer be there if they've been trimmed in the previous step.

```         
ssub_node --node compute-0-1 --mem 30G -o demux1.out -e demux1.err dorado demux --no-classify --output-dir demux_no_classify calls_2024-11-26_T08-29-02.bam
```

The output can then be aligned as detailed in the section [Mapping fastqs or unaligned bams]

### Extra note

The software demultiplexes into barcode01, barcode02 etc. If the barcodes don't seem to match properly on Sierra, it's not particularly straightforward to check this, as the barcodes get trimmed off during the demultiplexing and we're just left with barcode01, barcode02 etc in the name.\
If you go back to the pod5 files and basecall them with a --no-trim or --trim primer options, then the barcode sequences don't get trimmed off and they can be checked.
