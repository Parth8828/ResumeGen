from pypdf import PdfReader
import json

reader = PdfReader('sample.pdf')
full_text = ''
for page in reader.pages:
    full_text += page.extract_text() + '\n'

# Save to file for analysis
with open('sample_extracted.txt', 'w', encoding='utf-8') as f:
    f.write(full_text)

print(full_text)
