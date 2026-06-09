#!/bin/bash
python3 ../main.py -c
python3 ../main.py -s ../schema.ttl
python3 ../main.py -d ./L1_1.ttl
#python3 ../main.py -a
python3 ../main.py -d ./L1_2.ttl
python3 ../main.py -a
python3 ../main.py -t
python3 ../main.py -d ./L2_1.ttl
python3 ../main.py -a
python3 ../main.py -d ./L2_2.ttl
python3 ../main.py -a
