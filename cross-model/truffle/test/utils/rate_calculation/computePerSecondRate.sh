#!/bin/bash
rate=$1;
timeline=$2;
rate=$(bc -l <<< "scale=27; e( l(${rate} / 100 + 1) / $timeline) * 10^27");
rate="${rate%.*}";
echo $rate
