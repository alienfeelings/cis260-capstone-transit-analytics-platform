import sys
import os

print(sys.executable)
print(sys.prefix)

print("Executable:", sys.executable)
print("Virtual environment:", sys.prefix)
print("Base Python:", sys.base_prefix)
print("Python version:", sys.version)

print("PYTHONHOME:", os.environ.get("PYTHONHOME"))
print("PYTHONPATH:", os.environ.get("PYTHONPATH"))