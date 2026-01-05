# Using Expert Feedback to Improve Story Detection AI

## Overview

This document analyzes how to use expert review feedback (from `review_stories.html`) to systematically improve the AI's ability to identify Talmudic stories.

---

## Three Approaches Analyzed

### Approach 1: Few-Shot Prompt Engineering

**Description:** Directly embed validated examples from expert feedback into the AI prompts as few-shot examples.

**How it works:**
1. Collect expert-validated correct stories and false positives
2. Select 3-5 representative examples of each
3. Add these directly to the system prompt before analysis

**Example:**
```python
prompt = f"""You are analyzing Talmudic text for narrative stories.

Here are CORRECT story identifications from expert review:

EXAMPLE 1 (Correct Story):
Text: "Rabbi Akiva was a shepherd for Ben Kalba Savua..."
Why it's a story: Complete narrative arc with characters, dialogue, temporal progression, and resolution

EXAMPLE 2 (False Positive - NOT a story):
Text: "The law regarding marriage contracts is as follows..."
Why it's NOT a story: Pure legal discussion with no narrative elements

Now analyze this passage: {text}
"""
```

**Strengths:**
- ✅ **Immediate impact** - Works instantly without retraining
- ✅ **Low cost** - No training infrastructure needed
- ✅ **Transparent** - Easy to understand what changed
- ✅ **Flexible** - Can update examples quickly

**Weaknesses:**
- ❌ **Context window limits** - Can only fit 3-5 examples
- ❌ **Manual curation** - Someone must pick representative examples
- ❌ **Doesn't scale** - Same examples used for all tractates
- ❌ **Static** - Examples don't adapt to different text types

---

### Approach 2: Supervised Fine-Tuning

**Description:** Create a custom training dataset from expert feedback and fine-tune the AI model.

**How it works:**
1. Accumulate 500+ expert-reviewed passages
2. Format as training pairs: (text, is_story: true/false, reasoning)
3. Fine-tune Claude (or other model) on this dataset
4. Use fine-tuned model for future analysis

**Example training format:**
```json
[
  {
    "input": "Rabbi Akiva was a shepherd...",
    "output": {
      "is_story": true,
      "confidence": 95,
      "reasoning": "Complete narrative with beginning (shepherd betrothal), middle (12 years study), end (wife honored)",
      "story_type": "full_narrative"
    }
  },
  {
    "input": "The halakha regarding ketubot is...",
    "output": {
      "is_story": false,
      "confidence": 5,
      "reasoning": "Pure legal discussion, no characters or narrative progression",
      "story_type": "not_a_story"
    }
  }
]
```

**Strengths:**
- ✅ **Deep learning** - Model internalizes patterns deeply
- ✅ **Scales well** - Works across all tractates once trained
- ✅ **Consistent** - Same quality everywhere
- ✅ **Handles edge cases** - Learns subtle distinctions

**Weaknesses:**
- ❌ **Expensive** - Fine-tuning costs $500-2000+
- ❌ **Time intensive** - Needs 500-1000+ examples for good results
- ❌ **Black box** - Hard to understand why it changed
- ❌ **Version lock** - Tied to specific model version
- ❌ **Slow iteration** - Each refinement requires retraining

---

### Approach 3: Iterative Prompt Refinement with Pattern Analysis ⭐

**Description:** Analyze expert feedback to identify systematic error patterns, then refine prompts to address those specific weaknesses.

**How it works:**
1. **Collect & Analyze Feedback**
   - Run analysis on tractate
   - Expert reviews results
   - Export feedback JSON

2. **Pattern Recognition**
   - Analyze false positives: What patterns do they share?
   - Analyze false negatives (missed stories): What was overlooked?
   - Identify edge cases

3. **Systematic Prompt Refinement**
   - Add specific guidance for identified error patterns
   - Create category-specific prompts (legal debates vs dialogues)
   - Build dynamic example selection

4. **Validation Loop**
   - Re-run analysis with refined prompts
   - Compare results with previous version
   - Iterate until improvement plateaus

**Example Pattern Analysis:**
```python
# Analyze feedback to find patterns
def analyze_false_positives(feedback_json):
    false_positives = [f for f in feedback_json['feedback']
                      if f['feedback_type'] == 'false_positive']

    patterns = {
        'legal_debates': 0,
        'hypothetical_cases': 0,
        'rabbinic_disputes': 0,
        'short_dialogues': 0
    }

    for fp in false_positives:
        text = fp['text'].lower()
        if 'halakha' in text or 'din' in text:
            patterns['legal_debates'] += 1
        if 'if he' in text or 'suppose' in text:
            patterns['hypothetical_cases'] += 1
        if 'rabbi x says' in text and 'rabbi y says' in text:
            patterns['rabbinic_disputes'] += 1
        if len(text.split()) < 50:
            patterns['short_dialogues'] += 1

    return patterns

# Example output: {'legal_debates': 12, 'hypothetical_cases': 8, ...}
```

**Prompt refinement based on patterns:**
```python
# BEFORE (caused false positives)
prompt = "Identify if this is a story with beginning, middle, end"

# AFTER (addresses legal_debates pattern)
prompt = """Identify if this is a story with beginning, middle, end.

IMPORTANT: Legal debates are NOT stories, even if they have dialogue.
- "Rabbi X says... Rabbi Y says..." = Legal dispute, NOT a story
- "If a man does X, the law is Y" = Hypothetical case, NOT a story
- "The halakha is..." = Legal ruling, NOT a story

Stories have:
- Named characters with actions (not just legal positions)
- Temporal progression (things happen in sequence)
- Resolution (outcome beyond legal conclusion)
"""
```

**Strengths:**
- ✅ **Systematic improvement** - Addresses root causes, not symptoms
- ✅ **Interpretable** - Clear why each change was made
- ✅ **Cost effective** - No training costs, just API usage
- ✅ **Fast iteration** - Test changes in minutes
- ✅ **Scalable** - Patterns apply across tractates
- ✅ **Flexible** - Can mix different strategies per error type
- ✅ **Cumulative** - Each round builds on previous learnings
- ✅ **Context-aware** - Can create tractate-specific refinements

**Weaknesses:**
- ❌ **Requires analysis tools** - Need scripts to identify patterns
- ❌ **Manual interpretation** - Human must understand patterns
- ❌ **May plateau** - Diminishing returns after several iterations
- ❌ **Complexity growth** - Prompts can become unwieldy

---

## Winner: Approach 3 (Iterative Prompt Refinement)

**Why this approach wins:**

1. **Best ROI** - Significant improvement without training costs
2. **Rapid iteration** - Test changes in hours, not weeks
3. **Maintainability** - Easy to understand and adjust
4. **Flexible combination** - Can incorporate few-shot examples where helpful
5. **Real-world fit** - Matches how researchers actually work

---

## Critique & Strengthening of Approach 3

### Critique

**Current weaknesses:**
1. **Manual pattern analysis** - Requires writing analysis scripts
2. **Prompt bloat** - Too many edge cases makes prompts long and unfocused
3. **No memory** - Each analysis starts fresh
4. **Limited feedback loop** - No automated A/B testing

### Strengthening Strategy

#### 1. Automated Pattern Detection

Create a feedback analyzer script that automatically identifies common error patterns:

```python
# analyze_feedback.py
import json
from collections import Counter
import re

def analyze_feedback_patterns(feedback_file):
    """
    Automatically detect patterns in expert feedback.
    Returns actionable insights for prompt refinement.
    """
    with open(feedback_file) as f:
        data = json.load(f)

    feedback = data['feedback']

    # Separate false positives and correct stories
    false_positives = [f for f in feedback if f['feedback_type'] == 'false_positive']
    correct_stories = [f for f in feedback if f['feedback_type'] == 'correct']

    analysis = {
        'false_positive_patterns': analyze_fp_patterns(false_positives),
        'correct_story_patterns': analyze_story_patterns(correct_stories),
        'boundary_issues': analyze_length_adjustments(feedback),
        'confidence_calibration': analyze_confidence(feedback),
        'recommendations': []
    }

    # Generate specific recommendations
    analysis['recommendations'] = generate_recommendations(analysis)

    return analysis

def analyze_fp_patterns(false_positives):
    """Find common characteristics in false positives"""
    patterns = {
        'legal_terminology': count_legal_terms(false_positives),
        'hypothetical_markers': count_hypothetical(false_positives),
        'short_length': count_short(false_positives),
        'dialogue_only': count_dialogue_only(false_positives),
        'rabbi_debates': count_debates(false_positives),
    }
    return patterns

def generate_recommendations(analysis):
    """Generate actionable prompt improvements"""
    recs = []

    fp = analysis['false_positive_patterns']

    if fp['legal_terminology'] > 5:
        recs.append({
            'issue': 'Legal discussions misidentified as stories',
            'count': fp['legal_terminology'],
            'prompt_addition': """
CRITICAL: Distinguish legal discussions from stories:
- Pure halakha analysis is NOT a story, even with dialogue
- Hypothetical cases ("If a man...") are NOT stories
- Rabbi debates on law are NOT stories unless they include narrative context
"""
        })

    if fp['short_length'] > 3:
        recs.append({
            'issue': 'Brief dialogues over-identified as stories',
            'count': fp['short_length'],
            'prompt_addition': """
MINIMUM THRESHOLD: Brief exchanges are usually NOT stories unless they have:
- Clear beginning (setup/context)
- Development (progression of events)
- Resolution (outcome/conclusion)

A 2-line "Rabbi X said to Rabbi Y" is typically NOT sufficient.
"""
        })

    return recs
```

#### 2. Modular Prompt Architecture

Instead of one massive prompt, use a modular system:

```python
class PromptBuilder:
    """Build prompts dynamically based on context and feedback learnings"""

    def __init__(self, feedback_analyzer):
        self.base_prompt = self._load_base_prompt()
        self.refinements = feedback_analyzer.get_refinements()

    def build_prompt(self, text, context=None):
        """Build optimized prompt for specific text"""

        # Start with base
        prompt = self.base_prompt

        # Add relevant refinements based on text characteristics
        if self._has_legal_terminology(text):
            prompt += self.refinements['legal_distinction']

        if self._has_dialogue(text):
            prompt += self.refinements['dialogue_vs_story']

        if len(text.split()) < 100:
            prompt += self.refinements['minimum_threshold']

        # Add tractate-specific guidance if available
        if context and context.get('tractate'):
            prompt += self._get_tractate_guidance(context['tractate'])

        return prompt
```

#### 3. Confidence Calibration

Use feedback to calibrate confidence scores:

```python
def calibrate_confidence(feedback_data):
    """
    Analyze how AI confidence correlates with expert validation.
    Provides adjustment factors.
    """

    results = []
    for item in feedback_data['feedback']:
        ai_confidence = item['story_confidence']
        expert_correct = item['feedback_type'] == 'correct'
        results.append((ai_confidence, expert_correct))

    # Find patterns
    calibration = {}
    for confidence_range in [(90,100), (80,89), (70,79), (60,69)]:
        low, high = confidence_range
        in_range = [(c, correct) for c, correct in results if low <= c <= high]

        if in_range:
            accuracy = sum(correct for _, correct in in_range) / len(in_range)
            calibration[confidence_range] = {
                'count': len(in_range),
                'accuracy': accuracy,
                'recommendation': 'increase_threshold' if accuracy < 0.7 else 'good'
            }

    return calibration
```

#### 4. Feedback-Driven Few-Shot Selection

Combine best of Approach 1 and 3:

```python
def select_dynamic_examples(text, feedback_history):
    """
    Select most relevant few-shot examples based on:
    1. Similarity to current text
    2. Historical error patterns
    3. Expert-validated quality
    """

    # Find similar examples from feedback
    candidates = find_similar_texts(text, feedback_history)

    # Prioritize examples that address known weak areas
    if has_legal_terminology(text):
        examples = [c for c in candidates if c['category'] == 'legal_vs_story']
    elif has_dialogue(text):
        examples = [c for c in candidates if c['category'] == 'dialogue_distinction']
    else:
        examples = candidates[:3]

    return examples
```

#### 5. A/B Testing Framework

Test prompt improvements systematically:

```python
def ab_test_prompts(tractate, sample_size=20):
    """
    Test prompt refinements on subset before full rollout.
    Compare with expert feedback.
    """

    # Get random sample
    refs = get_tractate_structure(tractate)
    sample_refs = random.sample(refs, sample_size)

    results = {
        'original_prompt': [],
        'refined_prompt': []
    }

    for ref in sample_refs:
        text = get_text(ref)

        # Test both prompts
        original_result = analyze_with_prompt(text, ORIGINAL_PROMPT)
        refined_result = analyze_with_prompt(text, REFINED_PROMPT)

        results['original_prompt'].append(original_result)
        results['refined_prompt'].append(refined_result)

    # Compare results
    comparison = {
        'agreement_rate': calculate_agreement(results),
        'confidence_diff': compare_confidence(results),
        'needs_expert_review': sample_refs  # Send to expert for validation
    }

    return comparison
```

---

## Implementation Plan

### Phase 1: Data Collection (Weeks 1-2)
1. Expert reviews Ketubot results using `review_stories.html`
2. Export feedback JSON
3. Analyze patterns using `analyze_feedback.py`

### Phase 2: First Iteration (Week 3)
1. Implement top 3 prompt refinements from pattern analysis
2. Add 2-3 few-shot examples for worst error categories
3. A/B test on 20-page sample from Ketubot
4. Validate changes with expert

### Phase 3: Refinement (Week 4)
1. Apply learnings from A/B test
2. Build modular prompt system
3. Test on new tractate (e.g., Bava Metzia)
4. Collect feedback, iterate

### Phase 4: Scale (Ongoing)
1. Refine prompts based on each new tractate
2. Build library of tractate-specific guidance
3. Continuous improvement loop

---

## Measuring Success

### Metrics to track:

1. **Precision** = Correct Stories / (Correct + False Positives)
   - Target: 85%+ after iteration

2. **Recall** = Correct Stories / (Correct + False Negatives)
   - Need to manually check "missed" stories
   - Target: 80%+

3. **Expert Agreement**
   - % of AI identifications expert agrees with
   - Target: 90%+

4. **Confidence Calibration**
   - Do 90% confidence stories match 90% expert validation?
   - Target: ±10% calibration error

5. **Boundary Accuracy**
   - % of stories with correct start/end points
   - Track "expand" and "shrink" feedback
   - Target: 85%+ correct boundaries

---

## Example Workflow

```bash
# 1. Expert reviews and exports feedback
# (In browser: review_stories.html -> Download Feedback JSON)

# 2. Analyze patterns
python3 analyze_feedback.py ketubot_review_expert_2026-01-05.json

# Output:
# PATTERN ANALYSIS
# ================
# False Positives: 23
#   - Legal debates: 12 (52%)
#   - Hypothetical cases: 6 (26%)
#   - Short dialogues: 5 (22%)
#
# Recommendations:
# 1. Add legal distinction guidance (HIGH PRIORITY)
# 2. Increase minimum length threshold
# 3. Add hypothetical case detection

# 3. Apply refinements
python3 refine_prompts.py --apply-recommendations analysis_output.json

# 4. A/B test
python3 ab_test.py --tractate Ketubot --sample 20

# 5. Deploy if successful
python3 find_talmud_stories.py --use-refined-prompts
```

---

## Conclusion

**Approach 3 (Iterative Prompt Refinement)** provides the best balance of:
- Speed (hours to iterate vs weeks for fine-tuning)
- Cost (API usage only vs $500-2000 training)
- Interpretability (know exactly what changed and why)
- Flexibility (adapt per tractate, error type, context)

The strengthened version includes:
- Automated pattern detection
- Modular prompt architecture
- Confidence calibration
- Dynamic few-shot selection
- A/B testing framework

This creates a **sustainable improvement loop** where each tractate's feedback makes the system better for all future tractates.
