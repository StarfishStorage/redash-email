#!/bin/sh

ip route show default | awk '{ print $(NF-2); exit }'
