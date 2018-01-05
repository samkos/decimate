#!/bin/bash
#SBATCH -J yyy123
#SBATCH -p debug
#SBATCH -n 1
#SBATCH -t 0:01:00
 

echo job running on...
hostname
sleep 10

echo job DONE
