#!/usr/bin/env python3

import argparse
import ass
import io
import os
import re
import sys

parser = argparse.ArgumentParser()
parser.add_argument('--exclude', type=str, help='Exclude subtitle events which styles match the given regular expression. Regex is full-match.')
parser.add_argument('file', type=str, help='.ass files.', nargs='+')
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

docs = list(map(tryOpen, args.file))

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
	for doc in docs:
		excludeAss(doc)

def isolateAss(doc, prefix):
	"""Isolate style names by prefixing them with the given prefix.

	This makes the document suitable for merging without name conflicts, if the prefix is unique.
	"""
	for s in doc.styles:
		s.name = '%s.%s' % (prefix, s.name)
	for e in doc.events:
		e.style = '%s.%s' % (prefix, e.style)

for i, doc in enumerate(docs):
	isolateAss(doc, str(i))

# Rescale subtitles from different video sizes
largestY = None
correspondingX = None
for doc in docs:
	if not doc.play_res_x or not doc.play_res_y:
		continue
	currentY = float(doc.play_res_y)
	if largestY is None or currentY > largestY:
		largestY = currentY
		correspondingX = doc.play_res_x
if largestY is not None:
	for doc in docs:
		if not doc.play_res_x or not doc.play_res_y or float(doc.play_res_y) == largestY:
			continue
		scale = largestY / float(doc.play_res_y)
		for s in doc.styles:
			s.scale_x *= scale
			s.scale_y *= scale
		doc.play_res_x = correspondingX
		doc.play_res_y = largestY

# Merge styles and events
mainDoc = docs[0]
for doc in docs[1:]:
	mainDoc.styles.extend(doc.styles)
	mainDoc.events.extend(doc.events)

# Resort
mainDoc.events.sort(key=lambda e: e.start)

output = io.StringIO()
mainDoc.dump_file(output)
print(output.getvalue())
