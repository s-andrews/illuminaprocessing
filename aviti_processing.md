# AVITI processing

## bases2fastq and copying to /primary

The script `process_aviti.py` is the first step in processing the completed AVITI runs.
It needs to be run from /data/AV240405 on pipeline2.

``` bash
nohup ~/illuminaprocessing/process_aviti.py [run_folder] > xx.log &
```

This runs bases2fastq, creates a directory structure on /primary and copies the fastq files from /data to /primary.   
It also checks the first 100,000 index reads and writes out the most frequently occurring to a text file. This is so that a manual check can be carried out to see if the barcodes look right before running the demultiplexing.

## Demultiplexing

As detailed further down, the existing demultiplexing script needed some modifications to work with the AVITI data. There are currently 3 separate aviti splitting scripts to choose from - we should write a simple wrapper around these.   
For now, we've got:    
- `split_barcodes_aviti_dual_index` - for dual index, paired end
- `split_barcodes_aviti_dual_index_single_end` - for dual index, single end
- `split_barcodes_aviti_single_index` - for single index, paired end
- `split_barcodes_aviti_single_index_single_end` - for single index, single end

As with the previous version of the split_barcodes script, these need to be run from /primary/[run_folder]

```
nohup ~/illuminaprocessing/split_barcodes_aviti_dual_index [run_folder] > barcode_splitting.log &
```

FastQC and multiqc can be run on the pipeline server.
Any further processing can be carried out on the capstone cluster.

More details of the initial processing steps can be found in the sections below - this information shouldn't be required unless changes need to be made to the processing script.

------------------------------------------------------------------------------

# Breakdown of processing commands

The first step in processing an AVITI run is to run `bases2fastq`.

## Create fastq files

``` bash
nohup  ~/bases2fastq -p 16 --run-manifest ~/illuminaprocessing/aviti_run_manifest.csv [run_folder] [output_folder]
```

This uses a custom run manifest that creates index fastq files and does not demultiplex. More details of the run manifest are in the later section [Custom run manifest] (#custom-run-manifest)


## Copy data to /primary

Create directory structure on /primary and copy fastqs over.

When copying an initial run over, I did try using the run folder name (20240306_AV240405_InstallPV-SideA-AV240405-06Mar2024) but Sierra rejected it as too long. Genomics have been creating the run_folder names which seems to be working fine.

``` bash
cd /primary
mkdir [run_folder]
cd [run_folder]
~/illuminaprocessing/create_external_run_folder_structure_1_lane.sh

nohup cp /data/AV240405/[output_folder]/Unaligned/Samples/DefaultProject/DefaultSample/*fastq.gz Unaligned/Project_External/Sample_lane1/ > copy.log &
```

Files need to be renamed so that Sierra and the demultiplexing script can find them.

```
rename DefaultSample lane1_NoIndex_L001 Unaligned/Project_External/Sample_lane1/*fastq.gz
```

Quick one-liner to get the most frequent barcodes for a check before running the demultiplexing

```
zcat lane1_NoIndex_L001_I1.fastq.gz | head -n 400000 | awk 'NR % 4 == 2' | sort | uniq -c | sort -k 1 -n -r | head -n 10
```

## Demultiplexing

The `split_barcodes` script, in its existing format, does not work with the AVITI data (even after renaming files) because...

-   It gets file name and number info from the Illumina file RunInfo.xml which AVITI does not produce.

-   It expects index reads to be named \_R2/\_R3, not I1, I2.

-   If we run `create_external_run_folder_structure.sh`, it creates 8 lanes, and so split_barcodes then looks for 8 lanes of data.

For now, I've hardcoded some options in to the script `split_barcodes_aviti_dual_index` so that it expects R1, R2, I1, I2 files.\
There is also an accompanying script `split_barcodes_aviti_single_index` that doesn't expect I2.

There is also a very simple script `create_external_run_folder_structure_1_lane.sh` to just create one lane.

In the `split_barcodes` script, the files are found using this line of perl code:

``` perl
my @files = <$data_folder/$run_folder/Unaligned/Project*/Sample_lane$lane/lane${lane}_NoIndex_L*_${read_number}.fastq.gz>;
```

Essentially, they need to be named:

lane1_NoIndex_L001_R1.fastq.gz\
lane1_NoIndex_L001_R2.fastq.gz\
lane1_NoIndex_L001_I1.fastq.gz\
lane1_NoIndex_L001_I2.fastq.gz

``` bash
rename DefaultSample lane1_NoIndex_L001 Unaligned/Project_External/Sample_lane1/*fastq.gz
```

Demultiplex using the slightly modified version of the split_barcodes script.

``` bash
nohup ~/illuminaprocessing/split_barcodes_aviti_dual_index 20240306_AV240405_InstallPV-SideA > barcode_splitting.log &
```

Hopefully there are now demultiplexed fastq files ready for downstream processing.

------------------------------------------------------------------------

# More details

## bases2fastq

The basecalling software is called `bases2fastq` and can be downloaded from\
<https://go.elementbiosciences.com/bases2fastq-download>

Usage:

``` bash
bases2fastq --run-manifest [run_manifest.csv] [run_folder] [output_folder]
```

A default run manifest is produced with the sequencing run and this is used by `bases2fastq` to demultiplex and convert to fastq. We don't want to demultiplex at this point - there are too many times when the barcodes provided are not quite correct, so we have to manually correct the sequences and re-run the demultiplexing. We therefore want to create the fastq files first and then demultiplex.

## Custom run manifest

To get fastq files for the indexes we need to set:

```         
I1FastQ True
I2FastQ True
```

By default these are false and no index fastq files are produced.

<https://docs.elembio.io/docs/run-manifest/settings/#umi-index-and-control-settings>

We have created a [run manifest](https://github.com/s-andrews/illuminaprocessing/blob/master/aviti_run_manifest.csv) that produces index fastq files. This is in the illuminaprocessing GitHub repo.

### Contents of aviti_run_manifest.csv

```         
[SETTINGS],,,
SettingName,Value,Lane,
SpikeInAsUnassigned,FALSE,,
R1FastQMask,R1:Y*N,1+2,
R2FastQMask,R2:Y*N,1+2,
,,,
# Index mask is set to index length with FASTQ generated for Index 1 and 2.,,,
I1Mask,I1:Y*,1+2,
I2Mask,I2:Y*,1+2,
I1FastQ,True,,
I2FastQ,True,,
```

## Pipeline server

The /data/AV240405 folder has all the AVITI runs in so far

### Running bases2fastq on the pipeline server

Example command for processing the test run from the AV240405 folder:

``` bash
nohup  ~/bases2fastq -p 16 --run-manifest ~/illuminaprocessing/aviti_run_manifest.csv 20240306_AV240405_InstallPV-SideA-AV240405-06Mar2024 20240306_AV240405_InstallPV-SideA-AV240405-06Mar2024/Unaligned
```

The run folder and output directory will need to be changed each time, but the first part of the command can remain the same (up to `.csv`) - unless we need to change the run manifest.   

I did try using the `--legacy-fastq` option which produced filenames in the format of `DefaultSample_S1_L001_I1_001.fastq.gz`, but it put half in L001 and half in L002. Without that option all R1 went into 1 file. We need to rename the files anyway so it was simpler to have output filenames as DefaultSample_I1.fastq.gz and use a simple rename command to convert to lane1_NoIndex_L001_I1.fastq.gz.


### Output files

fastq files located in `/data/AV240405/[bases2fastq_output_dir]/Samples/DefaultProject/DefaultSample/`

```         
DefaultSample_I1.fastq.gz
DefaultSample_I2.fastq.gz
DefaultSample_R1.fastq.gz
DefaultSample_R2.fastq.gz
```

``` bash
rename DefaultSample lane1_NoIndex_L001 *fastq.gz
```

#### Note - SpikeInAsUnassigned setting

From https://docs.elembio.io/docs/run-manifest/settings/#umi-index-and-control-settings

```         
A Boolean value that specifies whether to categorize PhiX Control Library reads as unassigned: When libraries are absent or each lane contains only one unindexed library, the value defaults to true. You can reset it to false. When indexed libraries are present, the value defaults to false. If you reset it to true, Bases2Fastq displays a warning.
```
