#!/usr/bin/env python3
"""
Simple example demonstrating usage of Trying.expand_symmetric()
Run: python examples/symmetric_example.py
"""

from envara.trying import Trying

# Example environment mapping and positional args
vars = {"TEST_FOO": "bar"}
args = ["one", "two"]

print("1)", Trying.expand_symmetric("Value %TEST_FOO% end", args=args, vars=vars))
print("2)", Trying.expand_symmetric("Arg %1 and %2", args=args, vars=vars))
print("3)", Trying.expand_symmetric("Literal percent: 100%% sure", args=args, vars=vars))

# Modifier example: extract name and extension from a path
sample = "/home/user/file.txt"
print("4)", Trying.expand_symmetric("%~n1 %~x1", args=[sample], vars=vars))

# Expected output:
# 1) Value bar end
# 2) Arg one and two
# 3) Literal percent: 100% sure
# 4) file .txt
