import sys
import os

# Add src directory to sys.path so that 'import <module>' works in src/config.py
sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src/envara"))
)
