#!/usr/bin/python3
import secrets
import string
import sys

len = int(sys.argv[1])
characters = (secrets.choice(string.ascii_letters + string.digits) for _ in range(len))
print("".join(characters))
