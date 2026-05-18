#!/usr/bin/env python3
"""
Normalize detector output schema so evaluate_golden.py can score it.

Some LLM responses use alternate field names (start_segment_index, story_id,
nested 'segments'). This rewrites them to the canonical schema in place.

Usage: python scripts/normalize_stories.py <path1> [<path2> ...]
"""
import json, sys
from pathlib import Path


def normalize_story(s):
    # start/end segment aliases
    if 'start_segment' not in s:
        if 'start_segment_index' in s:
            s['start_segment'] = s['start_segment_index']
        elif isinstance(s.get('segments'), list) and s['segments']:
            try:
                idxs = [seg if isinstance(seg, int) else seg.get('index')
                        for seg in s['segments']]
                idxs = [i for i in idxs if isinstance(i, int)]
                if idxs:
                    s['start_segment'] = min(idxs)
                    s['end_segment'] = max(idxs)
            except Exception:
                pass
    if 'end_segment' not in s and 'end_segment_index' in s:
        s['end_segment'] = s['end_segment_index']
    # ensure 'continuation' shape for downstream code
    if 'continuation' not in s and (
        'continues_from_previous_page' in s or 'continues_to_next_page' in s
    ):
        s['continuation'] = {
            'continues_from_previous_page': s.get('continues_from_previous_page', False),
            'continues_to_next_page': s.get('continues_to_next_page', False),
        }
    return s


def normalize_file(path):
    with open(path) as f:
        data = json.load(f)
    fixed = 0
    dropped = 0
    for p in data.get('pages', []):
        kept = []
        for s in p.get('stories', []):
            before = ('start_segment' in s) and ('end_segment' in s)
            normalize_story(s)
            after = ('start_segment' in s) and ('end_segment' in s)
            if after:
                kept.append(s)
                if not before:
                    fixed += 1
            else:
                dropped += 1
        p['stories'] = kept
    with open(path, 'w') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"  {path}: normalized {fixed}, dropped {dropped} unrecoverable")


def main():
    for arg in sys.argv[1:]:
        normalize_file(Path(arg))


if __name__ == '__main__':
    main()
