#!/usr/bin/env python3
"""
Generate HTML files with embedded JSON data for GitHub Pages hosting.
"""

import json
import os

def generate_embedded_validation_ui():
    """Generate validation UI with embedded JSON data."""

    # Read the latest results
    with open('results/v4/ketubot_latest.json', 'r') as f:
        data = json.load(f)

    # Read the template HTML
    with open('validation_ui_v4.html', 'r') as f:
        html = f.read()

    # Replace the load section and add embedded data
    embedded_script = f'''
    <script>
        // Embedded data - auto-generated
        const EMBEDDED_DATA = {json.dumps(data)};
    </script>
'''

    # Insert embedded data before closing </head>
    html = html.replace('</head>', f'{embedded_script}</head>')

    # Modify the script to auto-load embedded data
    auto_load_script = '''
        // Auto-load embedded data if available
        if (typeof EMBEDDED_DATA !== 'undefined') {
            document.addEventListener('DOMContentLoaded', function() {
                data = EMBEDDED_DATA;
                document.getElementById('load-section').classList.add('hidden');
                processData();
            });
        }
'''

    # Insert before the closing </script>
    html = html.replace('// Initialize\n        loadSavedValidations();',
                        f'// Initialize\n        loadSavedValidations();\n{auto_load_script}')

    # Write the embedded version
    with open('docs/validation.html', 'w') as f:
        f.write(html)

    print(f"Generated docs/validation.html with {len(data['pages'])} pages of data")


def generate_embedded_batch_review():
    """Generate batch review with embedded JSON data."""

    # Read the latest results
    with open('results/v4/ketubot_latest.json', 'r') as f:
        data = json.load(f)

    # Read the template HTML
    with open('batch_review.html', 'r') as f:
        html = f.read()

    # Replace the load section and add embedded data
    embedded_script = f'''
    <script>
        // Embedded data - auto-generated
        const EMBEDDED_DATA = {json.dumps(data)};
    </script>
'''

    # Insert embedded data before closing </head>
    html = html.replace('</head>', f'{embedded_script}</head>')

    # Modify the script to auto-load embedded data
    auto_load_script = '''
        // Auto-load embedded data if available
        if (typeof EMBEDDED_DATA !== 'undefined') {
            document.addEventListener('DOMContentLoaded', function() {
                data = EMBEDDED_DATA;
                document.getElementById('load-section').style.display = 'none';
                processData();
            });
        }
'''

    # Insert before closing </script>
    html = html.replace('// Initialize\n        loadSavedValidations();',
                        f'// Initialize\n        loadSavedValidations();\n{auto_load_script}')

    # Write the embedded version
    with open('docs/batch-review.html', 'w') as f:
        f.write(html)

    print(f"Generated docs/batch-review.html with {data['total_stories_found']} stories")


def create_index_page():
    """Create an index page for GitHub Pages."""

    index_html = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Talmud Story Detection - v4</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #1e3a5f 0%, #2563eb 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 2rem;
        }
        .container {
            background: white;
            border-radius: 1rem;
            padding: 3rem;
            max-width: 600px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
        }
        h1 { color: #1e3a5f; margin-bottom: 0.5rem; }
        .subtitle { color: #64748b; margin-bottom: 2rem; }
        .card {
            background: #f8fafc;
            border: 1px solid #e2e8f0;
            border-radius: 0.75rem;
            padding: 1.5rem;
            margin-bottom: 1rem;
            text-decoration: none;
            display: block;
            transition: all 0.2s;
        }
        .card:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
            border-color: #2563eb;
        }
        .card h2 { color: #1e3a5f; font-size: 1.25rem; margin-bottom: 0.5rem; }
        .card p { color: #64748b; font-size: 0.9rem; }
        .badge {
            display: inline-block;
            background: #2563eb;
            color: white;
            padding: 0.25rem 0.75rem;
            border-radius: 1rem;
            font-size: 0.75rem;
            margin-top: 0.5rem;
        }
        .stats {
            display: flex;
            gap: 2rem;
            margin-top: 2rem;
            padding-top: 1.5rem;
            border-top: 1px solid #e2e8f0;
        }
        .stat { text-align: center; }
        .stat-value { font-size: 2rem; font-weight: 700; color: #2563eb; }
        .stat-label { font-size: 0.75rem; color: #64748b; text-transform: uppercase; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Talmud Story Detection</h1>
        <p class="subtitle">AI-powered narrative identification in Tractate Ketubot</p>

        <a href="validation.html" class="card">
            <h2>Full Validation Interface</h2>
            <p>Detailed view with side-by-side Hebrew/English text, segment boundaries, and AI reasoning. Best for thorough review.</p>
            <span class="badge">Recommended for detailed review</span>
        </a>

        <a href="batch-review.html" class="card">
            <h2>Quick Batch Review</h2>
            <p>Streamlined interface for rapid validation. Keyboard shortcuts (Y/N/S) for fast feedback.</p>
            <span class="badge">Best for quick validation</span>
        </a>

        <div class="stats">
            <div class="stat">
                <div class="stat-value">76</div>
                <div class="stat-label">Pages Analyzed</div>
            </div>
            <div class="stat">
                <div class="stat-value">30</div>
                <div class="stat-label">Stories Found</div>
            </div>
            <div class="stat">
                <div class="stat-value">69%</div>
                <div class="stat-label">Avg Confidence</div>
            </div>
        </div>
    </div>
</body>
</html>
'''

    with open('docs/index.html', 'w') as f:
        f.write(index_html)

    print("Generated docs/index.html")


if __name__ == '__main__':
    # Create docs directory if it doesn't exist
    os.makedirs('docs', exist_ok=True)

    generate_embedded_validation_ui()
    generate_embedded_batch_review()
    create_index_page()

    print("\nAll files generated in docs/ directory")
    print("Enable GitHub Pages with source: docs/ to publish")
