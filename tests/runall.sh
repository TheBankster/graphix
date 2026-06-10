#!/bin/bash
python3 ../main.py -c
python3 ../main.py -s ../schema.ttl
python3 ../main.py -d ./L1_1.ttl
#python3 ../main.py -1
python3 ../main.py -d ./L1_2.ttl
#python3 ../main.py -1
python3 ../main.py -d ./L1_3.ttl
python3 ../main.py -t
python3 ../main.py -d ./L2_1.ttl
python3 ../main.py -2
python3 ../main.py -m
# L3 (as-built): extract from Terraform, reconcile against the L2 model, re-grade.
# On the L2_1 gap state this confirms Encryption-at-Rest and Traffic-Encryption from
# real IaC config and flags the unmodeled (shadow) load balancer.
python3 ../main.py -x ../terraform
python3 ../main.py -r
python3 ../main.py -m
python3 ../main.py -d ./L2_2.ttl
python3 ../main.py -2
python3 ../main.py -m
python3 ../main.py -d ./L2_3.ttl
python3 ../main.py -t
