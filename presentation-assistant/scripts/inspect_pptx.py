#!/usr/bin/env python3
"""Read-only PPTX text, tables and media inventory; no OCR or visual validation."""
import argparse
import json
from pathlib import Path
import posixpath
import sys
import xml.etree.ElementTree as ET
import zipfile

P = '{http://schemas.openxmlformats.org/presentationml/2006/main}'
A = '{http://schemas.openxmlformats.org/drawingml/2006/main}'
R = '{http://schemas.openxmlformats.org/officeDocument/2006/relationships}'
REL = '{http://schemas.openxmlformats.org/package/2006/relationships}'

def read_xml(z, name):
    info = z.getinfo(name)
    if info.file_size > 20_000_000:
        raise ValueError('XML part too large: ' + name)
    return ET.fromstring(z.read(name))

def paragraphs(node):
    return [''.join(t.text or '' for t in p.iter(A+'t')) for p in node.iter(A+'p')]

def inspect(path):
    with zipfile.ZipFile(path) as z:
        names = z.namelist()
        if len(names) > 100_000:
            raise ValueError('Too many archive entries')
        presentation = read_xml(z, 'ppt/presentation.xml')
        relationships = read_xml(z, 'ppt/_rels/presentation.xml.rels')
        targets = {r.get('Id'): r.get('Target') for r in relationships.findall(REL+'Relationship') if r.get('TargetMode') != 'External'}
        slides = []
        for idx, elem in enumerate(presentation.findall('.//'+P+'sldId'), 1):
            target = targets.get(elem.get(R+'id'))
            if not target:
                raise ValueError('Missing slide relationship for slide ' + str(idx))
            part = posixpath.normpath(posixpath.join('ppt', target.lstrip('/'))) if not target.startswith('/') else target.lstrip('/')
            root = read_xml(z, part)
            texts = []
            for shape in root.iter(P+'sp'):
                vals = [t for t in paragraphs(shape) if t.strip()]
                if vals:
                    texts.append('\n'.join(vals))
            tables = []
            for table in root.iter(A+'tbl'):
                tables.append([[ '\n'.join(t for t in paragraphs(cell) if t.strip()) for cell in row.findall(A+'tc')] for row in table.findall(A+'tr')])
            slides.append({'page': idx, 'text_blocks': texts, 'tables': tables, 'image_count': sum(1 for _ in root.iter(P+'pic'))})
        media = [z.getinfo(n) for n in names if n.startswith('ppt/media/') and not n.endswith('/')]
        return {'file_bytes': path.stat().st_size, 'slide_count': len(slides), 'media_count': len(media),
                'media_uncompressed_bytes': sum(x.file_size for x in media), 'slides': slides,
                'limitations': ['Only slide XML text and tables; no OCR, chart data, notes, background text, visual layout or editability verification.', 'File size is not evidence that compression is safe.']}

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', type=Path)
    parser.add_argument('--output', type=Path, help='New JSON file in a private location; default stdout')
    args = parser.parse_args()
    if not args.input.is_file() or args.input.suffix.lower() != '.pptx':
        parser.error('input must be an existing .pptx file')
    if args.output and (args.output.exists() or args.output.resolve() == args.input.resolve()):
        parser.error('output must be a new file; existing files are not overwritten')
    try:
        report = inspect(args.input)
        payload = json.dumps(report, ensure_ascii=False, indent=2)
        if args.output:
            with args.output.open('x', encoding='utf-8') as f:
                f.write(payload + '\n')
            print('Saved local report:', args.output)
        else:
            print(payload)
        return 0
    except (OSError, KeyError, ValueError, zipfile.BadZipFile, ET.ParseError) as exc:
        print('Unable to inspect PPTX:', exc, file=sys.stderr)
        return 1

if __name__ == '__main__':
    sys.exit(main())

