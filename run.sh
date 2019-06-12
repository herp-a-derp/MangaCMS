#!/bin/bash

while true; do
	python3 mainScrape.py
	killall chrome
	sleep 1
done