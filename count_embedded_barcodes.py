#!/usr/bin/env python3
# This script takes in a fastq file which contains embedded barcodes
# and lists the most frequently observed combinations
#
# Just pass the filename as the first argument to the script

import sys
import gzip

def main():
    filenames = sys.argv[1:]

    seen_barcodes = {}

    for filename in filenames:
        print("Reading",filename, flush=True, file=sys.stderr)
        count = 0
        with gzip.open(filename, "rt", encoding="UTF-8") as fh:
            for line in fh:
                x = fh.readline()
                x = fh.readline()
                x = fh.readline()

                barcodes = line.strip().split(":")[-1]

                if not barcodes in seen_barcodes:
                    seen_barcodes[barcodes] = 0

                seen_barcodes[barcodes] += 1

                count += 1
                if count % 1000000 == 0:
                    print ("Processed",int(count/1000000),"million", flush=True, file=sys.stderr)

                # if count % 10000000 == 0:
                #     break


    sorted_barcodes = sorted(seen_barcodes.keys(), key=lambda x: seen_barcodes[x])
    sorted_barcodes.reverse()
    

    for i,b in enumerate(sorted_barcodes):
        if i==100:
            break

        print(i,b,seen_barcodes[b])



if __name__ == "__main__":
    main()
