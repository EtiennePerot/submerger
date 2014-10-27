#!/usr/bin/env python3

import argparse
import ass
import io
import os
import re
import sys

parser = argparse.ArgumentParser()
parser.add_argument('--exclude', type=str, help='Exclude subtitle events which styles match the given regular expression. Regex is full-match.')
parser.add_argument('file1', type=str, help='First .ass file.')
parser.add_argument('file2', type=str, help='Second .ass file.')
args = parser.parse_args()

def tryOpen(f):
	"""Open a .ass file with a bunch of encodings until one works."""
	if not os.path.isfile(f):
		raise Exception('Invalid file: %s' % (f,))
	lastException = None
	for encoding in ('utf-8', 'utf-16', 'utf-16-le'):
		try:
			return ass.parse(open(f, 'r', encoding=encoding))
		except Exception as e:
			lastException = e
	raise Exception('Cannot find suitable encoding for file %s. Last error: %s' % (f, lastException))

doc1 = tryOpen(args.file1)
doc2 = tryOpen(args.file2)

def excludeAss(doc, reg):
	"""Remove all styles and events with the style name matching the given regex."""
	badStyles = frozenset(s.name for s in doc.styles if reg.match(s.name))
	for s in list(doc.styles):
		if s.name in badStyles:
			doc.styles.remove(s)
	for e in list(doc.events):
		if e.style in badStyles:
			doc.events.remove(e)

if args.exclude:
	reg = re.compile(args.exclude, re.IGNORECASE)
	excludeAss(doc1, reg)
	excludeAss(doc2, reg)

def isolateAss(doc, prefix):
	"""Isolate style names by prefixing them with the given prefix.

	This makes the document suitable for merging without name conflicts, if the prefix is unique.
	"""
	for s in doc.styles:
		s.name = '%s.%s' % (prefix, s.name)
	for e in doc.events:
		e.style = '%s.%s' % (prefix, e.style)

isolateAss(doc1, '1')
isolateAss(doc2, '2')

doc1.styles.extend(doc2.styles)
doc1.events.extend(doc2.events)

output = io.StringIO()
doc1.dump_file(output)
print(output.getvalue())
