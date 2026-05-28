import sys

with open(r'c:\Users\User\capstone-frontend\antutor-repository\front\src\App.js', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if 'isEndSuggested' in line or 'IsEndSuggested' in line:
        print(f"Line {i+1}: {line.strip()}")
