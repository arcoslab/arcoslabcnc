#!/bin/bash
#usage: ./slot3d.sh <x1> <y1> <x2> <y2> <zinit> <zend> <zstep> <speed> <mm/in/m>
trap "exit" SIGINT SIGTERM

a=$1

echo "Turns $a"

while [ $a != 0 ]
do
    beep
    ./move_line.py $2 $3  0.004 in abs
    ./move_line.py $4 $5  0.004 in abs
    a=$(expr $a - 1)
done

