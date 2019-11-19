# Call as RScript barcode_graph.r [infile] [outfile]

library(RColorBrewer)

infile <- commandArgs(trailingOnly = TRUE)[1]
outfile <- commandArgs(trailingOnly = TRUE)[2]
read.delim(infile,stringsAsFactors=FALSE) -> data

data[order(data$Freq),] -> data

data$Name[data$Name != ""] -> all.names
if (length(all.names) != length(unique(all.names))) {
   data[order(data$Name),] -> data
}


data$Freq <- data$Freq*100
as.integer(sum(data$Freq)) -> total.explained

colours <- rep("red",nrow(data))
colours[data$Name == ""] <- "grey"

# Colour by group if we have a multi-barcode study
if ((length(all.names) != length(unique(all.names))) & length(unique(all.names))< 9) {
  # We have multibarcode samples, and few enough of them that we can colour
  # them separately using colourbrewer
  
  library(RColorBrewer)
  brewer.colours = brewer.pal(n = 8,"Set1")
  
  unique(all.names) -> unique.names

  brewer.colours[match(data$Name,unique.names)] -> colours
  colours[data$Name == ""] <- "grey"
  
}


png(filename = outfile,width = 600,height=100+(50*nrow(data)))

#data$Name[1] <- "This is a longer name than before"

max(nchar(c(data$Code,data$Name))) -> longest.name

par(mar=c(5.1,4+(longest.name/2.5),4.1,2.1))

barplot(
  data$Freq,
  names.arg=sapply(1:nrow(data),function(x)paste(data$Code[x],data$Name[x],sep="\n")),
  horiz=TRUE,
  las=1,
  col=colours,
  xlab="Percentage of reads",
  main=paste("Barcodes shown explain ",total.explained,"% of the data",sep="")
  )

dev.off()
