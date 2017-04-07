#!/bin/bash

trap "exit" SIGINT SIGTERM

a=$1

echo "Turns $a"

while [ $a != 0 ]
do
    beep
    ./circle.py 0 0 $2 1 0.002 10 in
    a=$(expr $a - 1)
done

