import sys
import os

# Adds the project root to Python's path so pytest can find the app module
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))