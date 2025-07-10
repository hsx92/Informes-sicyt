import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

path = os.path.join(BASE_DIR, 'templates/ref')
print(f"Path to templates: {path}")
