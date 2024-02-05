#!/bin/bash

while true
do
  free_memory=$(vm_stat | awk '/free:/ {print $3}')
  echo -e "HTTP/1.1 200 OK\n\n Free memory: $free_memory pages" | nc -l 8080 
done