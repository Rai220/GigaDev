#!/bin/bash
top -l 1 | grep PhysMem
ps aux | sort -nrk 4 | head -n 5
