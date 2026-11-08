#!/usr/bin/env python3
"""
Post-Processing Rules for v7 Story Detection

Mechanical rules applied AFTER LLM detection to reduce false positives.
No API calls — operates entirely on existing results.

Rules:
  1. Single-Event Filter: Demote stories with ≤1 event in criteria
  2. Duplicate Reclassification: Demote stories flagged as duplicates
  3. v6 Ensemble: Demote stories where v6 disagrees AND page is heavily legal

Phase 1 of v7 evaluation pipeline.
"""

import copy
import json
from collections import Counter
from pathlib import Path
from typing import Dict, List, Optional, Tuple


def is_story_positive(cls: str) -> bool:
    return cls in ('YES', 'HIGH_CONFIDENCE', 'LOW_CONFIDENCE')


class PostProcessor:
    """Apply mechanical post-processing rules to v7 results."""

    def __init__(self,
                 v6_results_path: Optional[str] = None,
                 triage_results_path: Optional[str] = None,
                 enable_rule1: bool = False,
                 enable_rule2: bool = False,
                 enable_rule3: bool = True):
        self.v6_lookup: Dict[str, str] = {}   # "Ref_start-end" -> classification
        self.triage_events: Dict[str, List[str]] = {}  # "Ref" -> [event_types]
        self.enable_rule1 = enable_rule1
        self.enable_rule2 = enable_rule2
        self.enable_rule3 = enable_rule3

        if v6_results_path:
            self._load_v6(v6_results_path)
        if triage_results_path:
            self._load_triage(triage_results_path)

    def _load_v6(self, path: str):
        with open(path) as f:
            v6_data = json.load(f)
        for page in v6_data.get('pages', []):
            ref = page.get('ref', '')
            for story in page.get('stories', []):
                key = f"{ref}_{story['start_segment']}-{story['end_segment']}"
                self.v6_lookup[key] = story.get('classification', 'UNKNOWN')

    def _load_triage(self, path: str):
        with open(path) as f:
            triage_data = json.load(f)
        self.triage_events = triage_data.get('triage_results', {})

    def apply(self, v7_data: dict) -> Tuple[dict, dict]:
        """
        Apply all post-processing rules to v7 results.

        Returns:
            (modified_data, stats) — modified copy of v7_data and rule application stats
        """
        data = copy.deepcopy(v7_data)
        stats = {
            'rule1_single_event': {'checked': 0, 'demoted': 0, 'details': []},
            'rule2_duplicate': {'checked': 0, 'demoted': 0, 'details': []},
            'rule3_v6_ensemble': {'checked': 0, 'demoted': 0, 'details': []},
            'total_demotions': 0,
        }

        for page in data.get('pages', []):
            ref = page.get('ref', '')
            for story in page.get('stories', []):
                if not is_story_positive(story.get('classification', '')):
                    continue

                original_cls = story['classification']
                key = f"{ref}_{story['start_segment']}-{story['end_segment']}"

                # Rule 1: Single-Event Filter (disabled by default — causes regressions
                # on cross-page stories where LLM reports count=1 for the segment
                # visible on this page but the story continues on the next page)
                if self.enable_rule1:
                    demoted, reason = self._rule1_single_event(story)
                    stats['rule1_single_event']['checked'] += 1
                    if demoted:
                        story['classification'] = 'NOT_A_STORY'
                        story['post_processing'] = {
                            'rule': 'single_event_filter',
                            'original_classification': original_cls,
                            'reason': reason,
                        }
                        stats['rule1_single_event']['demoted'] += 1
                        stats['rule1_single_event']['details'].append(f"{key}: {original_cls} → NOT_A_STORY ({reason})")
                        stats['total_demotions'] += 1
                        continue

                # Rule 2: Duplicate Reclassification (disabled by default —
                # the LLM sometimes flags valid stories as duplicates when they
                # are legitimate continuations on the next page)
                if self.enable_rule2:
                    demoted, reason = self._rule2_duplicate(story)
                    stats['rule2_duplicate']['checked'] += 1
                    if demoted:
                        story['classification'] = 'NOT_A_STORY'
                        story['post_processing'] = {
                            'rule': 'duplicate_reclassification',
                            'original_classification': original_cls,
                            'reason': reason,
                        }
                        stats['rule2_duplicate']['demoted'] += 1
                        stats['rule2_duplicate']['details'].append(f"{key}: {original_cls} → NOT_A_STORY ({reason})")
                        stats['total_demotions'] += 1
                        continue

                # Rule 3: v6 Ensemble (conservative)
                demoted, reason = self._rule3_v6_ensemble(ref, story)
                stats['rule3_v6_ensemble']['checked'] += 1
                if demoted:
                    story['classification'] = 'NOT_A_STORY'
                    story['post_processing'] = {
                        'rule': 'v6_ensemble',
                        'original_classification': original_cls,
                        'reason': reason,
                    }
                    stats['rule3_v6_ensemble']['demoted'] += 1
                    stats['rule3_v6_ensemble']['details'].append(f"{key}: {original_cls} → NOT_A_STORY ({reason})")
                    stats['total_demotions'] += 1

        rules_applied = []
        if self.enable_rule1:
            rules_applied.append('single_event_filter')
        if self.enable_rule2:
            rules_applied.append('duplicate_reclassification')
        if self.enable_rule3:
            rules_applied.append('v6_ensemble')

        data['post_processing'] = {
            'version': 'v7+pp',
            'rules_applied': rules_applied,
            'stats': stats,
        }
        return data, stats

    def _rule1_single_event(self, story: dict) -> Tuple[bool, str]:
        """
        Rule 1: Demote stories with ≤1 multiple_events count.

        Only applies to HIGH_CONFIDENCE or YES classifications.
        Stories with only one event don't meet the narrative threshold.
        """
        cls = story.get('classification', '')
        if cls not in ('HIGH_CONFIDENCE', 'YES'):
            return False, ''

        criteria = story.get('criteria', {})
        me = criteria.get('multiple_events', {})
        count = me.get('count', 99)

        if count <= 1:
            events = me.get('events', [])
            return True, f"only {count} event(s): {events}"
        return False, ''

    def _rule2_duplicate(self, story: dict) -> Tuple[bool, str]:
        """
        Rule 2: Demote stories flagged as possible duplicates.

        If the LLM flagged possible_duplicate_of, demote to NOT_A_STORY.
        """
        dup_of = story.get('possible_duplicate_of')
        if dup_of:
            return True, f"duplicate of {dup_of}"
        return False, ''

    def _rule3_v6_ensemble(self, page_ref: str, story: dict) -> Tuple[bool, str]:
        """
        Rule 3: v6 Ensemble — demote where v6 disagrees AND page is legal-heavy.

        Conservative version: requires BOTH conditions:
        1. v6 did NOT classify this as a story (NOT_A_STORY or not detected)
        2. Page has very few narrative events in triage (≤1 NARRATIVE_EVENT)

        The low narrative event count on the page is a strong signal that the
        page is predominantly legal discussion, making story detection less reliable.
        """
        cls = story.get('classification', '')
        if not is_story_positive(cls):
            return False, ''

        # Check v6 classification
        key = f"{page_ref}_{story['start_segment']}-{story['end_segment']}"
        v6_cls = self.v6_lookup.get(key)

        # v6 must NOT have found this as a story
        if v6_cls is not None and is_story_positive(v6_cls):
            return False, ''

        # Page must have very few narrative events (legal-heavy signal)
        event_types = self.triage_events.get(page_ref, [])
        if not event_types:
            return False, ''

        narrative_count = sum(1 for et in event_types if et == 'NARRATIVE_EVENT')

        if narrative_count <= 1:
            v6_status = f"v6={v6_cls or 'not detected'}"
            return True, f"{v6_status}, page has only {narrative_count} NARRATIVE_EVENT(s) in {len(event_types)} segments"

        return False, ''


def apply_post_processing(v7_path: str,
                          v6_path: Optional[str] = None,
                          triage_path: Optional[str] = None,
                          output_path: Optional[str] = None) -> Tuple[dict, dict]:
    """
    Convenience function to apply post-processing to a v7 results file.

    Args:
        v7_path: Path to v7 results JSON
        v6_path: Path to v6 results JSON (for ensemble rule)
        triage_path: Path to event triage results JSON
        output_path: Optional path to save post-processed results

    Returns:
        (processed_data, stats)
    """
    with open(v7_path) as f:
        v7_data = json.load(f)

    pp = PostProcessor(
        v6_results_path=v6_path,
        triage_results_path=triage_path,
    )
    processed, stats = pp.apply(v7_data)

    if output_path:
        with open(output_path, 'w') as f:
            json.dump(processed, f, indent=2, ensure_ascii=False)
        print(f"Saved post-processed results to {output_path}")

    return processed, stats


def print_stats(stats: dict):
    """Print post-processing stats summary."""
    print(f"\nPost-Processing Summary:")
    print(f"  Total demotions: {stats['total_demotions']}")

    for rule_name in ['rule1_single_event', 'rule2_duplicate', 'rule3_v6_ensemble']:
        rule = stats[rule_name]
        label = rule_name.replace('_', ' ').title()
        print(f"\n  {label}:")
        print(f"    Checked: {rule['checked']}, Demoted: {rule['demoted']}")
        for detail in rule['details']:
            print(f"      {detail}")


if __name__ == '__main__':
    import sys

    project_root = Path(__file__).parent.parent

    v7_path = str(project_root / 'results' / 'v7' / 'ketubot_v7_2-60.json')
    v6_path = str(project_root / 'results' / 'v6' / 'ketubot_v6_2-60.json')
    triage_path = str(project_root / 'results' / 'v7' / 'event_triage_2-60.json')
    output_path = str(project_root / 'results' / 'v7' / 'ketubot_v7_2-60_pp.json')

    processed, stats = apply_post_processing(
        v7_path=v7_path,
        v6_path=v6_path,
        triage_path=triage_path,
        output_path=output_path,
    )
    print_stats(stats)
