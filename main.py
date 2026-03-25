import streamlit as st
import base64
import pathlib
import mimetypes
import json
import random
import record_and_analyze
import pandas as pd
import os
import io
import llm
import prompts
import time
import numpy as np
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.units import inch
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle, FancyBboxPatch
from matplotlib.colors import LinearSegmentedColormap
import pyttsx3  # For text-to-speech
import matplotlib.pyplot as plt
import numpy as np
import io
from matplotlib.patches import Rectangle, Circle
from PIL import Image as PILImage
import numpy as np
import io
import plotly.express as px

from reportlab.platypus import BaseDocTemplate, PageTemplate, Frame




# Set page config as the first Streamlit command
st.set_page_config(page_title="#theAteam Kids Academy", layout="centered")



class WatermarkedDocTemplate(BaseDocTemplate):
    def __init__(self, *args, **kwargs):
        BaseDocTemplate.__init__(self, *args, **kwargs)
        frame = Frame(
            self.leftMargin, 
            self.bottomMargin,
            self.width,
            self.height,
            id='normal'
        )
        self.addPageTemplates([
            PageTemplate(
                id='AllPages',
                frames=frame,
                onPageEnd=add_watermark  # ← KEY CHANGE: Draw AFTER content
            )
        ])

# Add custom CSS for layout and attractive boxes
st.markdown("""
    <style>
    .stPlotlyChart, .stPyplot {
        margin: auto;
    }
    .frequency-graph {
        height: 150px;
        width: 100%;
        background: #2c3e50;
        border-radius: 8px;
        position: relative;
        overflow: hidden;
        margin: 15px 0;
        padding: 0 5px;
    }
    .frequency-container {
      width: 100%;
      height: 100px;
      background: #2c3e50;
      border-radius: 8px;
      padding: 10px 5px;
      position: relative;
      margin: 15px 0;
      overflow: hidden;
      display: flex;
      align-items: flex-end;
      flex-wrap: nowrap;
    }   
    .frequency-bar {
      display: inline-block;
      width: 2px;
      margin: 0 1px;
      border-radius: 2px 2px 0 0;
      justify-content: center;
      align-items: center;
    }
    .speaker-visual {
        width: 120px;
        height: 133px;
        margin: 0 auto;
        position: relative;
        background: #f0f0f0;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    .speaker-waves {
        position: absolute;
        width: 100%;
        height: 100%;
    }
    .speaker-wave {
        position: absolute;
        border: 2px solid #2196F3;
        border-radius: 50%;
        opacity: 0.3;
        animation: pulse 2s infinite;
    }
    @keyframes pulse {
        0% { transform: scale(0.8); opacity: 0.3; }
        50% { transform: scale(1.2); opacity: 0.1; }
        100% { transform: scale(0.8); opacity: 0.3; }
    }
    .large-metric-box {
        border: 2px solid #4CAF50;
        border-radius: 10px;
        padding: 20px;
        background-color: #f9f9f9;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        text-align: center;
        height: 310px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        margin: 10px 0;
    }
    .small-metric-box {
        border: 2px solid #2196F3;
        border-radius: 8px;
        padding: 10px;
        background-color: #e3f2fd;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        text-align: center;
        height: 250px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        margin: 5px 0;
        line-height: 1.2;
    }
    .small-metric-box-grammar {
        border: 2px solid #2196F3;
        border-radius: 8px;
        padding: 10px;
        background-color: #e3f2fd;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        text-align: center;
        height: 100px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        margin: 5px 0;
        line-height: 1.2;
    }
    .gauge-container {
        position: relative;
        width: 150px;
        height: 75px;
        margin: 20px auto;
        overflow: hidden;
    }
    .gauge {
        width: 150px;
        height: 150px;
        border-radius: 50%;
        position: absolute;
        top: 0;
        transform: rotate(180deg);
        background: conic-gradient({0} 0% {1}%, #e0e0e0 {1}% 100%);
    }
    .metric-box {
        border: 2px solid #2196F3;
        border-radius: 10px;
        padding: 15px;
        background-color: #f9f9f9;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        text-align: left;
        margin: 10px 0;
    }
    .progress-bar {
        width: 100%;
        height: 10px;
        background-color: #e0e0e0;
        border-radius: 10px;
        overflow: hidden;
        margin: 10px 0;
    }
    .progress-fill {
        height: 80%;
        background-color: {0};
        width: {1}%;
        border-radius: 10px;
        transition: width 0.3s ease-in-out;
    }
    </style>
""", unsafe_allow_html=True)

# Metric descriptions for parents (simplified with examples)
descriptions = {
    "overall": "How well your child did overall. Example: Scoring high means they did great in most tasks!",
    "pronunciation": "How clearly your child says words. Example: Saying ‘dog’ clearly, not ‘dawg’.",
    "rhythm": "How smoothly your child’s speech flows. Example: Talking like a storyteller, not robotic.",
    "pitch": "How high or low your child’s voice sounds. Example: Using a high voice for excitement.",
    "volume": "How loud your child’s voice is. Example: Speaking loud enough to be heard clearly.",
    "fluency": "How easily your child speaks without stopping. Example: Talking without many ‘um’s.",
    "speed": "How fast your child talks. Example: Speaking not too fast or too slow, like a newsreader.",
    "pause_count": "How many times your child pauses unnecessarily. Example: Stopping mid-sentence often.",
    "grammar": "How correctly your child uses grammar. Example: Saying ‘I have two cats,’ not ‘I has two cat.’",
    "word_error": "Number of words pronounced incorrectly. Example: Saying ‘cat’ as ‘hat’.",
    "verb_error": "Number of mistakes in verbs. Example: Saying ‘I runned’ instead of ‘I ran’.",
    "article_error": "Number of mistakes in words like ‘a’ or ‘the’. Example: Saying ‘I see cat’ instead of ‘I see a cat’.",
    "integrity": "How well your child’s words match what they’re supposed to say. Example: Reading a sentence exactly as written."
}

# --- Load the JSON data from a file ---
def load_json_data(file_path):
    with open(file_path, 'r') as file:
        return json.load(file)

# --- Load the questions JSON file ---
data = load_json_data(r"phonics_questions_age_5_6.json")

def get_random_questions(age_group, level, context, num_questions=10):
    age_group_data = data.get(age_group, {})
    if not isinstance(age_group_data, dict):
        raise ValueError(f"Expected dictionary for age group '{age_group}'.")

    selected_questions = []

    # Determine if level is 1 or 2
    is_level_1_or_2 = level in ["Level 1", "Level 2"]

    # 1. Uppercase/Lowercase (only for younger groups, exclude for 9-10 and 11-13)
    if age_group not in ["9-10", "11-13"]:
        uc_lc_data = age_group_data.get("uppercase_lowercase", [])
        uc_lc_count = 3 if is_level_1_or_2 else 2
        selected_uc_lc = random.sample(uc_lc_data, min(uc_lc_count, len(uc_lc_data)))
        for q in selected_uc_lc:
            q_copy = q.copy()
            q_copy["options"] = ["Upper-Case", "Lower-Case", "Don't Know"]
            # Normalize answer to match option exactly
            if "upper" in q["answer"].lower():
                q_copy["answer"] = "Upper-Case"
            elif "lower" in q["answer"].lower():
                q_copy["answer"] = "Lower-Case"
            else:
                q_copy["answer"] = "Lower-Case"  # Fallback to avoid errors
            selected_questions.append(q_copy)

    # 2. Syllables (exclude for levels 1-2 in younger age groups)
    should_exclude_syllables = is_level_1_or_2 and age_group in ["3-4", "5-6", "7-8"]
    if not should_exclude_syllables:
        syllable_data = age_group_data.get("syllables", [])
        syllable_count = 2 if age_group not in ["9-10", "11-13"] else 3
        selected_syllables = random.sample(syllable_data, min(syllable_count, len(syllable_data)))
        for q in selected_syllables:
            q_copy = q.copy()
            correct = int(q_copy["answer"])
            options = list(range(1, 6))
            if correct not in options:
                options.append(correct)
            random.shuffle(options)
            q_copy["options"] = [str(opt) for opt in options]
            q_copy["options"].append("Don't Know")
            q_copy["answer"] = str(correct)
            selected_questions.append(q_copy)

    # 3. Rhyming Words
    rhyming_data = age_group_data.get("rhyming_words", [])
    
    # Adjust rhyming word count based on whether syllables are included
    if age_group in ["9-10", "11-13"]:
        # For older groups: 3 rhyming words regardless
        rhyming_count = 3
    elif should_exclude_syllables:
        # For younger groups (3-4, 5-6, 7-8) with levels 1-2: 
        # More rhyming words to compensate for no syllables
        rhyming_count = 3
    else:
        # For younger groups with levels 3+: 2 rhyming words (since syllables are included)
        rhyming_count = 2
    
    selected_rhyming = random.sample(rhyming_data, min(rhyming_count, len(rhyming_data)))
    selected_questions.extend(selected_rhyming)

    # 4. Pronunciation (always 4)
    sentences = []
    for _ in range(4):
        sentences.append(llm.get_response_from_ai(prompts.generate_text(sentences, context), age_group))
    for sentence in sentences:
        selected_questions.append({
            "question": f"Read the below Sentence: \n{sentence}",
            "answer": sentence,
            "options": []
        })

    return selected_questions

# --- Sanitize text for PDF ---
# Chart generation functions (adjusted figure sizes for larger charts)
def create_3d_pie_chart(value, filename):
    # Define base and shadow (darker) colors
    if value >= 80:
        main_color = '#1A942E'      # Darker green
        shadow_color = '#0E5F1D'    # Even darker green for shadow
    elif value >= 60:
        main_color = '#FF9800'      # Orange
        shadow_color = '#CC7A00'    # Darker orange
    else:
        main_color = '#F44336'      # Red
        shadow_color = '#B1302A'    # Darker red

    sizes = [value, 100 - value]
    colors = [main_color, 'lightgrey']
    explode = [0.1, 0]

    fig, ax = plt.subplots(figsize=(3, 3), dpi=200)

    # --- Draw shadow pie (shifted downward for 3D effect) ---
    shadow_sizes = sizes
    shadow_colors = [shadow_color, 'lightgrey']
    shadow_explode = [0.1, 0]

    wedges_shadow, _ = ax.pie(
        shadow_sizes,
        colors=shadow_colors,
        startangle=90,
        explode=shadow_explode,
        counterclock=False,
        wedgeprops=dict(edgecolor='white', linewidth=0),
        radius=1,
    )

    for w in wedges_shadow:
        w.set_alpha(0.6)
        w.set_zorder(0)
        w.set_transform(w.get_transform() + plt.matplotlib.transforms.Affine2D().translate(0, -0.05))

    # --- Draw main pie on top ---
    wedges, texts = ax.pie(
        sizes,
        colors=colors,
        startangle=90,
        explode=explode,
        counterclock=False,
        wedgeprops=dict(edgecolor='white', linewidth=1),
        radius=1,
    )

    # --- Center label for percentage ---
    angle = 90 - (value / 2) * 3.6
    x = 0.7 * np.cos(np.deg2rad(angle)) + 0.1
    y = 0.7 * np.sin(np.deg2rad(angle))

    ax.text(x, y, f"{int(value)}%", ha='center', va='center', fontsize=14, weight='bold', color='black')

    ax.axis('equal')
    ax.axis('off')

    plt.savefig(filename, bbox_inches='tight', dpi=200)
    plt.close()


def shade_color(color, factor=0.7):
    """Return a darker shade of the given hex color."""
    import matplotlib.colors as mc
    import colorsys

    try:
        c = mc.cnames[color]
    except:
        c = color
    c = colorsys.rgb_to_hls(*mc.to_rgb(c))
    # darken by factor
    return colorsys.hls_to_rgb(c[0], max(0, factor * c[1]), c[2])


def create_phoneme_line_chart(phoneme_df, filename):
    fig, ax = plt.subplots(figsize=(6, 2), dpi=200)  # Compact size for PDF
    
    # Color-code points based on score
    colors = ['#34C759' if score > 80 else '#FF9800' if score >= 60 else '#F44336' for score in phoneme_df["Average Score"]]
    
    # Plot line with individual point colors
    for i in range(len(phoneme_df) - 1):
        ax.plot(
            phoneme_df["Phoneme"].iloc[i:i+2],
            phoneme_df["Average Score"].iloc[i:i+2],
            linestyle='-', color='#1E2F97', linewidth=1.5
        )
    ax.scatter(
        phoneme_df["Phoneme"], phoneme_df["Average Score"],
        c=colors, s=25, zorder=5
    )
    
    # Add score labels above points, avoiding overlap
    for i, (phoneme, score) in enumerate(zip(phoneme_df["Phoneme"], phoneme_df["Average Score"])):
        color = '#34C759' if score > 80 else '#FF9800' if score >= 60 else '#F44336'
        offset = 15  # Increased offset to avoid collision
        ax.text(i, score + offset, f'{int(score)}', ha='center', va='bottom', fontsize=6, color=color)
    
    ax.set_title("Average Phoneme Scores", fontsize=10, weight='bold')
    ax.set_xlabel("Phoneme", fontsize=8, weight='bold')
    ax.set_ylabel("Score (%)", fontsize=8, weight='bold')
    ax.set_ylim(0, 130)  # Extend y-axis for labels
    ax.grid(True, linestyle='--', alpha=0.4)
    
    plt.xticks(rotation=45, ha='right', fontsize=6)
    plt.yticks(fontsize=6)
    
    plt.tight_layout(pad=0.5)
    plt.savefig(filename, bbox_inches='tight', dpi=200)
    plt.close()


def create_thermometer_chart(metric_name, value, status, filename, max_value=100, is_count=False):
    fig, ax = plt.subplots(figsize=(1.5, 3), dpi=200)
    ax.set_xlim(0, 1)
    ax.set_ylim(-30, max_value + 50)
    ax.axis('off')
    if is_count:
        color = '#4CAF50' if value == 0 else '#FF9800' if value in [1, 2] else '#F44336'
    else:
        color = '#F44336' if value < 60 else '#FF9800' if value < 80 else '#34C759'
    gradient_cmap = LinearSegmentedColormap.from_list('custom', ['#FFFFFF', color], N=256)
    thermometer = FancyBboxPatch((0.4, 0), 0.2, max_value, boxstyle="round,pad=0.02", fill=False, edgecolor='black', lw=2)
    ax.add_patch(thermometer)
    shadow = FancyBboxPatch((0.41, -0.01), 0.2, max_value, boxstyle="round,pad=0.02", fill=True, color='gray', alpha=0.2)
    ax.add_patch(shadow)
    fill_height = min(value, max_value)
    for y in np.linspace(0, fill_height, 100):
        ax.add_patch(Rectangle((0.4, y), 0.2, fill_height/100, color=gradient_cmap(y/fill_height), alpha=0.8))
    ax.add_patch(Circle((0.5, 0), 0.15, fill=True, color=color))
    ax.add_patch(Circle((0.5, 0), 0.18, fill=False, edgecolor=color, lw=2, alpha=0.5))
    font_size = 12 if is_count else 10
    ax.text(0.5, max_value + 28, f"{int(value)}{'' if is_count else '/100'}", 
            ha='center', va='center', fontsize=font_size, weight='bold', color=color)
    ax.text(0.5, max_value + 40, metric_name, 
            ha='center', va='center', fontsize=10, weight='bold')
    ax.text(0.5, -20, status, 
            ha='center', va='center', fontsize=8, color=color)
    plt.savefig(filename, bbox_inches='tight', dpi=200)
    plt.close()

def create_radial_chart(value, title, filename):
    fig, ax = plt.subplots(figsize=(1.1, 1.1), dpi=200)
    ax.set_xlim(-1.6, 1.6)
    ax.set_ylim(-1.6, 1.6)
    ax.axis('off')
    color = '#F44336' if value < 60 else '#FF9800' if value < 80 else '#34C759'
    light_color = '#EF9A9A' if value < 60 else '#FFCC80' if value < 80 else '#A5D6A7'
    theta = np.linspace(0, 2 * np.pi * (value / 100), 100)
    r = np.linspace(0.8, 1.2, 100)
    T, R = np.meshgrid(theta, r)
    X = R * np.cos(T)
    Y = R * np.sin(T)
    norm = plt.Normalize(-1.6, 1.6)
    cmap = LinearSegmentedColormap.from_list('vertical', [light_color, color])
    ax.contourf(X, Y, Y, 100, cmap=cmap, alpha=0.8, norm=norm)
    ax.add_patch(plt.Circle((0, 0), 0.75, color='white'))
    ax.text(0, 0, f"{int(value)}%", ha='center', va='center', 
           fontsize=10, weight='bold', color=color)
    ax.text(0, -1.7, title, ha='center', va='center', fontsize=8, weight='bold')
    plt.savefig(filename, bbox_inches='tight', dpi=200)
    plt.close()

def create_gauge(value, filename):
    fig, ax = plt.subplots(figsize=(1.3, 1), subplot_kw=dict(projection='polar'), dpi=200)
    ax.set_theta_zero_location('N')
    ax.set_theta_direction(-1)
    ax.set_ylim(0, 1)
    ax.set_xlim(-np.pi/2, np.pi/2)
    ax.axis('off')
    percentage = min((value / 300) * 100, 100)
    color = '#34C759' if 100 <= value <= 150 else '#FF9800' if (80 <= value < 100 or 150 < value <= 170) else '#F44336'
    light_color = '#A5D6A7' if 100 <= value <= 150 else '#FFCC80' if (80 <= value < 100 or 150 < value <= 170) else '#EF9A9A'
    gradient_cmap = LinearSegmentedColormap.from_list('custom', [light_color, color], N=256)
    theta_bg = np.linspace(-np.pi/2, np.pi/2, 100)
    r_bg = np.ones_like(theta_bg)
    ax.fill_between(theta_bg, 0, r_bg, color='#e0e0e0', alpha=0.8)
    fill_angle = np.pi * (percentage / 100)
    theta_fill = np.linspace(-np.pi/2, -np.pi/2 + fill_angle, 100)
    for i in np.linspace(0, 1, 100):
        ax.fill_between(theta_fill, 0, r_bg[:len(theta_fill)], color=gradient_cmap(i), alpha=0.8)
    needle_angle = -np.pi/2 + fill_angle
    ax.plot([needle_angle, needle_angle], [0, 0.9], color='black', lw=2)
    ax.plot([needle_angle], [0], 'ko', markersize=6)
    fig.text(0.5, 0.15, f"{int(value)} wpm", ha='center', va='center', fontsize=6, weight='bold')
    fig.text(0.5, 0.85, "Speed", ha='center', va='center', fontsize=8, weight='bold')
    fig.text(0.5, 0.05, "Excellent" if 100 <= value <= 150 else ("Too Fast" if value > 150 else "Too Slow"), 
             ha='center', va='center', fontsize=6, color=color)
    plt.savefig(filename, bbox_inches='tight', dpi=200)
    plt.close()

def create_frequency_bars(value, filename):
    fig, ax = plt.subplots(figsize=(1.5, 1.3), dpi=200)
    ax.set_xlim(0, 15)
    ax.set_ylim(0, 100)
    ax.axis('off')
    base_height = value * 0.5
    color = '#F44336' if value < 60 else '#FF9800' if value < 80 else '#34C759'
    light_color = '#EF9A9A' if value < 60 else '#FFCC80' if value < 80 else '#A5D6A7'
    gradient_cmap = LinearSegmentedColormap.from_list('custom', [light_color, color], N=256)
    for i in range(15):
        height = base_height * (0.8 + 0.2 * abs(np.sin(i/3)) + np.random.uniform(-2, 2))
        height = max(5, min(45, height))
        for j in np.linspace(0, height, 100):
            ax.bar(
                i, j, width=0.8,
                color=gradient_cmap(j/height),
                edgecolor='black',
                linewidth=0.2,
                alpha=0.8
            )
    ax.text(7.5, 120, "Pitch", ha='center', va='center', fontsize=10, weight='bold', color ='black')
    ax.text(7.5, 100, f"{int(value)}/100", ha='center', va='center', fontsize=10, weight='bold', color=color)
    ax.text(7.5, -10, "Needs Improvement" if value < 60 else "Good" if value < 80 else "Excellent", 
            ha='center', va='center', fontsize=8, color=color)
    plt.savefig(filename, bbox_inches='tight', dpi=200)
    plt.close()

def create_mcq_bar_chart(categories, correct_counts, filename):
    fig, ax = plt.subplots(figsize=(4, 2.8), dpi=200)

    valid_categories = []
    valid_scores = []
    category_labels = {
        "uppercase_lowercase": "Letter Case",
        "syllables": "Syllables",
        "rhyming_words": "Rhyming"
    }

    for cat, count in categories.items():
        if count > 0:
            perc = (correct_counts[cat] / count * 100)
            if not np.isnan(perc):
                valid_categories.append(category_labels[cat])
                valid_scores.append(perc)

    if not valid_categories:
        ax.text(0.5, 0.5, "No MCQ Data Available", ha='center', va='center', fontsize=10)
        ax.axis('off')
        plt.savefig(filename, bbox_inches='tight', dpi=200)
        plt.close()
        return

    x = np.arange(len(valid_categories))
    colors = ['#34C759' if s >= 80 else '#FF9800' if s >= 60 else '#F44336' for s in valid_scores]
    light_colors = ['#A5D6A7' if s >= 80 else '#FFCC80' if s >= 60 else '#EF9A9A' for s in valid_scores]
    bar_width = 0.6

    for i, (score, color, light_color) in enumerate(zip(valid_scores, colors, light_colors)):
        gradient = LinearSegmentedColormap.from_list(f'bar_{i}', [light_color, color], N=100)
        ax.bar(x[i], score, width=bar_width, color=color, edgecolor=color)

    for i, score in enumerate(valid_scores):
        ax.text(x[i], score + 3, f"{int(score)}%", ha='center', va='bottom', fontsize=8, weight='bold', color=colors[i])

    ax.set_xticks(x)
    ax.set_xticklabels(valid_categories, fontsize=9, weight='bold')
    ax.set_yticks([0, 20, 40, 60, 80, 100])
    ax.set_yticklabels(['0', '20', '40', '60', '80', '100'], fontsize=8)
    ax.set_ylim(0, 120)

    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.grid(axis='y', linestyle='--', alpha=0.3)

    plt.tight_layout()
    plt.savefig(filename, bbox_inches='tight', dpi=200)
    plt.close()

def sanitize_text(text):
    if not isinstance(text, str):
        text = str(text)
    return text.replace('<', '<').replace('>', '>')


def add_watermark(c, doc):
    """Add a diagonal watermark centered in the middle of each page."""
    c.saveState()
    
    # Set the watermark properties
    c.setFont("Helvetica", 40)
    c.setFillColor(colors.lightgrey, alpha=0.5)  # Light gray with 50% transparency
    
    # Get page dimensions
    page_width, page_height = letter
    
    # Calculate the center of the page
    center_x = page_width / 2
    center_y = page_height / 2
    
    # Move to the center of the page
    c.translate(center_x, center_y)
    
    # Rotate the canvas 45 degrees for diagonal text
    c.rotate(45)
    
    # Draw the text centered at the origin (which is now the page center)
    text = "#ATeamKidsAcademy"
    text_width = c.stringWidth(text, "Helvetica", 40)
    
    # Draw text centered on the rotated canvas
    c.drawString(-text_width / 2, -20, text)  # -20 to account for font height/2
    
    c.restoreState()

def generate_pdf_report(child_name, age_group, metrics, questions, user_answers, pronunciation_feedbacks, final_feedback):
    buffer = io.BytesIO()
    doc = WatermarkedDocTemplate(
        buffer,
        pagesize=letter,
        topMargin=0.3*inch,
        bottomMargin=0.3*inch,
        leftMargin=0.3*inch,
        rightMargin=0.3*inch
    )
    styles = getSampleStyleSheet()
    title_style = styles["Title"]
    heading_style = styles["Heading2"]
    subheading_style = styles["Heading3"]
    normal_style = styles["Normal"]
    normal_style.fontSize = 8.5
    normal_style.leading = 9.5
    heading_style.alignment = 0  # Left-align headings
    story = []

    # Page 1: Title, Name, Age, and Charts
    story.append(Paragraph("ATeam Kids Academy Phonics Assessment Report", title_style))
    story.append(Spacer(1, 3))
    story.append(Paragraph(f"Name: {sanitize_text(child_name)}", normal_style))
    story.append(Paragraph(f"Age: {sanitize_text(age_group)}", normal_style))
    story.append(Spacer(1, 6))

    # Generate charts
    avg_overall = np.mean([m['overall'] for m in metrics])
    overall_status = "Needs Improvement" if avg_overall < 60 else "Good" if avg_overall < 80 else "Excellent"
    create_3d_pie_chart(avg_overall, "overall_pie.png")
    
    avg_pronunciation = np.mean([m["pronunciation"] for m in metrics])
    pronunciation_status = "Needs Improvement" if avg_pronunciation < 60 else "Good" if avg_pronunciation < 80 else "Excellent"
    create_thermometer_chart("Pronunciation", avg_pronunciation, pronunciation_status, "pronunciation_thermometer.png")
    
    avg_rhythm = np.mean([m["rhythm"] for m in metrics])
    rhythm_status = "Needs Improvement" if avg_rhythm < 60 else "Good" if avg_rhythm < 80 else "Excellent"
    create_thermometer_chart("Rhythm", avg_rhythm, rhythm_status, "rhythm_thermometer.png")
    
    avg_volume = np.mean([m["volume"] for m in metrics])
    volume_status = "Needs Improvement" if avg_volume < 60 else "Good" if avg_volume < 80 else "Excellent"
    create_thermometer_chart("Volume", avg_volume, volume_status, "volume_thermometer.png")
    
    avg_pitch = np.mean([m["pitch"] for m in metrics])
    create_frequency_bars(avg_pitch, "pitch_bars.png")
    
    avg_fluency = np.mean([m["fluency"] for m in metrics])
    fluency_status = "Needs Improvement" if avg_fluency < 60 else "Good" if avg_fluency < 80 else "Excellent"
    create_thermometer_chart("Fluency", avg_fluency, fluency_status, "fluency_thermometer.png")
    
    avg_speed = np.mean([m["speed"] for m in metrics])
    create_gauge(avg_speed, "speed_gauge.png")
    
    sum_pause_count = np.sum([m["pause_count"] for m in metrics])
    pause_status = "No Pauses" if sum_pause_count == 0 else "Needs Improvement" if sum_pause_count in [1, 2] else "Too Many Pauses"
    create_thermometer_chart("Pauses", sum_pause_count, pause_status, "pause_thermometer.png", max_value=5, is_count=True)
    
    avg_grammar = np.mean([m["grammar"] for m in metrics])
    grammar_status = "Needs Improvement" if avg_grammar < 60 else "Good" if avg_grammar < 80 else "Excellent"
    create_thermometer_chart("Grammar", avg_grammar, grammar_status, "grammar_thermometer.png")
    
    avg_integrity = np.mean([m["integrity"] for m in metrics])
    integrity_status = "Needs Improvement" if avg_integrity < 60 else "Good" if avg_integrity < 80 else "Excellent"
    create_thermometer_chart("Integrity", avg_integrity, integrity_status, "integrity_thermometer.png")
    
    # Calculate filtered error counts
    sum_word_error = sum(len([err for err in metric.get("word_error_list", []) if err["score"] <= 80]) for metric in metrics)
    sum_verb_error = sum(len([err for err in metric.get("verb_error_list", []) if err["score"] <= 80]) for metric in metrics)
    sum_article_error = sum(len([err for err in metric.get("article_error_list", []) if err["score"] <= 80]) for metric in metrics)
    
    word_error_status = "None" if sum_word_error == 0 else "Some Errors"
    create_thermometer_chart("Word Errors", sum_word_error, word_error_status, "word_error_thermometer.png", max_value=5, is_count=True)
    
    verb_error_status = "None" if sum_verb_error == 0 else "Some Errors"
    create_thermometer_chart("Verb Errors", sum_verb_error, verb_error_status, "verb_error_thermometer.png", max_value=5, is_count=True)
    
    article_error_status = "None" if sum_article_error == 0 else "Some Errors"
    create_thermometer_chart("Article Errors", sum_article_error, article_error_status, "article_error_thermometer.png", max_value=5, is_count=True)
    
    skills = [
        ("Vowel Sounds", np.mean([m["Skill 1 (Vowel sounds)"] for m in metrics]), "Excellent" if np.mean([m["Skill 1 (Vowel sounds)"] for m in metrics]) >= 80 else "Good" if np.mean([m["Skill 1 (Vowel sounds)"] for m in metrics]) >= 60 else "Needs Improvement"),
        ("Fricatives", np.mean([m["Skill 2 (Fricatives and Affricates)"] for m in metrics]), "Excellent" if np.mean([m["Skill 2 (Fricatives and Affricates)"] for m in metrics]) >= 80 else "Good" if np.mean([m["Skill 2 (Fricatives and Affricates)"] for m in metrics]) >= 60 else "Needs Improvement"),
        ("Clusters", np.mean([m["Skill 3 (Consonant clusters)"] for m in metrics]), "Excellent" if np.mean([m["Skill 3 (Consonant clusters)"] for m in metrics]) >= 80 else "Good" if np.mean([m["Skill 3 (Consonant clusters)"] for m in metrics]) >= 60 else "Needs Improvement"),
        ("Intrusion", np.mean([m["Skill 4 (Intrusion and Elision)"] for m in metrics]), "Excellent" if np.mean([m["Skill 4 (Intrusion and Elision)"] for m in metrics]) >= 80 else "Good" if np.mean([m["Skill 4 (Intrusion and Elision)"] for m in metrics]) >= 60 else "Needs Improvement"),
        ("Diphthongs", np.mean([m["Skill 5 (Diphthongs)"] for m in metrics]), "Excellent" if np.mean([m["Skill 5 (Diphthongs)"] for m in metrics]) >= 80 else "Good" if np.mean([m["Skill 5 (Diphthongs)"] for m in metrics]) >= 60 else "Needs Improvement")
    ]
    for i, (skill_name, value, status) in enumerate(skills):
        create_radial_chart(value, skill_name, f"skill_radial_{i}.png")
    
    categories = {"uppercase_lowercase": 0, "syllables": 0, "rhyming_words": 0}
    correct_counts = {"uppercase_lowercase": 0, "syllables": 0, "rhyming_words": 0}
    for i, q in enumerate(questions):
        if q["options"]:
            user_key = f"answer_{i}"
            user_answer = user_answers.get(user_key, "")
            is_correct = user_answer.lower() == str(q["answer"]).lower()
            if "uppercase" in q["question"].lower() or "lowercase" in q["question"].lower():
                category = "uppercase_lowercase"
            elif "syllable" in q["question"].lower():
                category = "syllables"
            else:
                category = "rhyming_words"
            categories[category] += 1
            if is_correct:
                correct_counts[category] += 1
    create_mcq_bar_chart(categories, correct_counts, "mcq_bar.png")
    
    # Chart layout on page 1
    page_width = letter[0] - 2 * 0.3 * inch
    table_style = TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('SPACEBEFORE', (0, 0), (-1, -1), 4),
        ('SPACEAFTER', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 2),
        ('RIGHTPADDING', (0, 0), (-1, -1), 2),
    ])
    
    # Row 1: Overall (Left-aligned header + Pie chart + MCQ 3D bar)
    story.append(Paragraph("Overall", heading_style))
    charts_row1 = [
        Image("overall_pie.png", width=2.5*inch, height=2.5*inch),
        Image("mcq_bar.png", width=3*inch, height=2*inch)
    ]
    story.append(Table([charts_row1], colWidths=[2.5*inch, 3*inch], rowHeights=[2.5*inch], style=table_style))
    story.append(Spacer(1, 6))
    
    # Row 2: Pronunciation (Header + Pronunciation thermometer + Phonics skills)
    story.append(Paragraph("Phonics skills metrics", heading_style))
    charts_row2 = [
        Image("pronunciation_thermometer.png", width=1.5*inch, height=2*inch),
        Image("skill_radial_0.png", width=1.1*inch, height=1.1*inch),
        Image("skill_radial_1.png", width=1.1*inch, height=1.1*inch),
        Image("skill_radial_2.png", width=1.1*inch, height=1.1*inch),
        Image("skill_radial_3.png", width=1.1*inch, height=1.1*inch),
        Image("skill_radial_4.png", width=1.1*inch, height=1.1*inch),
    ]
    story.append(Table([charts_row2], colWidths=[1.5*inch, 1.1*inch, 1.1*inch, 1.1*inch, 1.1*inch, 1.1*inch], rowHeights=[2*inch], style=table_style))
    story.append(Spacer(1, 6))
    
    # Row 3: Intonation (Header + Intonation thermometer + Pitch + Volume + Speed)
    story.append(Paragraph("Intonation", heading_style))
    charts_row3 = [
        Image("rhythm_thermometer.png", width=1.5*inch, height=2*inch),
        Image("pitch_bars.png", width=1.5*inch, height=1.3*inch),
        Image("volume_thermometer.png", width=1.5*inch, height=2*inch),
        Image("speed_gauge.png", width=1.3*inch, height=1*inch),
    ]
    story.append(Table([charts_row3], colWidths=[1.5*inch, 1.5*inch, 1.5*inch, 1.3*inch], rowHeights=[2*inch], style=table_style))
    story.append(Spacer(1, 6))

    story.append(PageBreak())
    # Row 4: Phoneme Scores (Generate phoneme_line.png with Matplotlib)
    # Row 4: Phoneme Scores (Generate phoneme_line.png with Matplotlib)
    story.append(Paragraph("Phoneme Scores", heading_style))
    
    # Compute phoneme averages efficiently
    phoneme_scores = {}
    for metric in metrics:
        for word in metric.get("phoneme_scores", []):
            for phoneme in word.get("phonemes", []):
                ph = phoneme["phoneme"]
                score = phoneme["score"]
                phoneme_scores.setdefault(ph, []).append(score)
    
    phoneme_avg_scores = {ph: np.mean(scores) for ph, scores in phoneme_scores.items()}
    phoneme_df = pd.DataFrame(list(phoneme_avg_scores.items()), columns=["Phoneme", "Average Score"])
    phoneme_df = phoneme_df.sort_values("Phoneme")
    
    if not phoneme_df.empty:
        try:
            create_phoneme_line_chart(phoneme_df, "phoneme_line.png")
            if os.path.exists("phoneme_line.png"):
                charts_row4 = [
                    Image("phoneme_line.png", width=6*inch, height=2*inch)
                ]
                story.append(Table([charts_row4], colWidths=[6*inch], rowHeights=[2*inch], style=table_style))
            else:
                story.append(Paragraph("Phoneme scores chart could not be generated.", normal_style))
        except Exception as e:
            story.append(Paragraph(f"Failed to generate phoneme chart: {str(e)}", normal_style))
    else:
        story.append(Paragraph("No phoneme data available.", normal_style))
    story.append(Spacer(1, 6))
    

    # Row 4: Fluency and Grammar (Header + Fluency thermometer + Grammar + Integrity)
    
    story.append(Paragraph("Fluency and Grammar", heading_style))
    charts_row4 = [
        Image("fluency_thermometer.png", width=1.5*inch, height=2*inch),
        Image("grammar_thermometer.png", width=1.5*inch, height=2*inch),
        Image("integrity_thermometer.png", width=1.5*inch, height=2*inch),
    ]
    story.append(Table([charts_row4], colWidths=[1.5*inch, 1.5*inch, 1.5*inch], rowHeights=[2*inch], style=table_style))
    story.append(Spacer(1, 6))
    
    # Row 5: Errors (Header + Word + Article + Verb + Pause count)
    story.append(Paragraph("Errors", heading_style))
    charts_row5 = [
        Image("word_error_thermometer.png", width=1.5*inch, height=2*inch),
        Image("article_error_thermometer.png", width=1.5*inch, height=2*inch),
        Image("verb_error_thermometer.png", width=1.5*inch, height=2*inch),
        Image("pause_thermometer.png", width=1.5*inch, height=2*inch),
    ]
    story.append(Table([charts_row5], colWidths=[1.5*inch, 1.5*inch, 1.5*inch, 1.5*inch], rowHeights=[2*inch], style=table_style))
    story.append(PageBreak())

    # Page 2: Feedback, Pronunciation, Errors, and Descriptions
    story.append(Paragraph("Final Feedback from AI", heading_style))
    story.append(Paragraph(f"<b>Phonics Assessment by AI:</b> {sanitize_text(final_feedback)}", normal_style))
    story.append(Spacer(1, 12))
    
    story.append(Paragraph("Pauses in Pronunciation Sentences", subheading_style))
    pronunciation_questions = questions[-4:]
    if len(pronunciation_questions) == 4 and len(metrics) == 4:
        for i, (q, metric) in enumerate(zip(pronunciation_questions, metrics), 1):
            pause_count = metric.get("pause_count", 0)
            pause_status = "No Pauses" if pause_count == 0 else f"{pause_count} Pause{'s' if pause_count > 1 else ''}"
            story.append(Paragraph(f"Question {i}: {sanitize_text(q['answer'])}", normal_style))
            story.append(Paragraph(f"Status: {pause_status}", normal_style))
            story.append(Spacer(1, 6))
    else:
        story.append(Paragraph("Insufficient pronunciation questions or metrics to display pause information.", normal_style))
    story.append(Spacer(1, 12))
    
    story.append(Paragraph("Specific Errors in Pronunciation Questions", subheading_style))
    if len(pronunciation_questions) == 4 and len(metrics) == 4:
        for i, (q, metric) in enumerate(zip(pronunciation_questions, metrics), 1):
            story.append(Paragraph(f"Question {i}: {sanitize_text(q['answer'])}", normal_style))
            # Filter error lists and include scores in the display
            filtered_word_errors = [f"{err['word']} ({err['score']})" for err in metric.get("word_error_list", []) if err["score"] <= 80]
            filtered_verb_errors = [f"{err['word']} ({err['score']})" for err in metric.get("verb_error_list", []) if err["score"] <= 80]
            filtered_article_errors = [f"{err['word']} ({err['score']})" for err in metric.get("article_error_list", []) if err["score"] <= 80]
            error_found = False
            if filtered_word_errors:
                error_found = True
                word_errors_text = ', '.join(filtered_word_errors)
                story.append(Paragraph(f"<font color='red'>Mispronounced Words: {sanitize_text(word_errors_text)}</font>", normal_style))
            if filtered_verb_errors:
                error_found = True
                verb_errors_text = ', '.join(filtered_verb_errors)
                story.append(Paragraph(f"<font color='red'>Incorrect Verbs: {sanitize_text(verb_errors_text)}</font>", normal_style))
            if filtered_article_errors:
                error_found = True
                article_errors_text = ', '.join(filtered_article_errors)
                story.append(Paragraph(f"<font color='red'>Incorrect/Missing Articles: {sanitize_text(article_errors_text)}</font>", normal_style))
            if not error_found:
                story.append(Paragraph("<font color='green'>No errors detected.</font>", normal_style))
            story.append(Spacer(1, 6))
    else:
        story.append(Paragraph("Insufficient pronunciation questions or metrics to display errors.", normal_style))
    story.append(Spacer(1, 12))
    
    story.append(Paragraph("Descriptions", heading_style))
    story.append(Paragraph("Phonics Skills", subheading_style))
    story.append(Paragraph(f"- Vowel Sounds: {descriptions['pronunciation']}", normal_style))
    story.append(Paragraph("- Fricatives & Affricates: Ability to pronounce sounds like 'f', 'v', 'th', 's', 'z', 'sh', 'ch', and 'j'", normal_style))
    story.append(Paragraph("- Consonant Clusters: Ability to pronounce groups of consonants together (like 'str', 'spl', 'nt')", normal_style))
    story.append(Paragraph("- Intrusion & Elision: Inserting or dropping sounds for smoother speech. E.g., 'I saw it' → /ai sc wit/", normal_style))
    story.append(Paragraph("- Diphthongs: Ability to correctly pronounce gliding vowel sounds (like 'oi', 'ow', 'ai')", normal_style))
    story.append(Spacer(1, 12))
    
    story.append(Paragraph("Intonation Metrics", subheading_style))
    story.append(Paragraph(f"- Pitch: {descriptions['pitch']}", normal_style))
    story.append(Paragraph(f"- Intonation: {descriptions['rhythm']}", normal_style))
    story.append(Paragraph(f"- Volume: {descriptions['volume']}", normal_style))
    story.append(Spacer(1, 12))
    
    story.append(Paragraph("Grammar", subheading_style))
    story.append(Paragraph(f"- Grammar: {descriptions['grammar']}", normal_style))
    story.append(Paragraph(f"- Integrity: {descriptions['integrity']}", normal_style))
    story.append(Paragraph(f"- Word Errors: {descriptions['word_error']}", normal_style))
    story.append(Paragraph(f"- Verb Errors: {descriptions['verb_error']}", normal_style))
    story.append(Paragraph(f"- Article Errors: {descriptions['article_error']}", normal_style))
    
    # Build the PDF with the watermark
    doc.build(story)
    
    # Clean up image files
    image_files = [
        "overall_pie.png", "pronunciation_thermometer.png", "rhythm_thermometer.png",
        "pitch_bars.png", "volume_thermometer.png", "fluency_thermometer.png",
        "speed_gauge.png", "pause_thermometer.png", "grammar_thermometer.png",
        "integrity_thermometer.png", "word_error_thermometer.png",
        "verb_error_thermometer.png", "article_error_thermometer.png", "mcq_bar.png"
    ] + [f"skill_radial_{i}.png" for i in range(len(skills))]
    for fname in image_files:
        if os.path.exists(fname):
            os.remove(fname)
    
    buffer.seek(0)
    return buffer.getvalue()

# def generate_tts_audio(text, filename="temp_audio.mp3"):
#     try:
#         engine = pyttsx3.init()
#         engine.setProperty('voice', 'HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Speech\Voices\Tokens\TTS_MS_EN-US_ZIRA_11.0')
#         # voices = engine.getProperty('voices')
#         # for voice in voices:
#         #     print(f"Voice: {voice.name}, ID: {voice.id}")
#         engine.setProperty('rate', 115)  # Speed of speech
#         engine.setProperty('volume', 0.9)  # Volume (0.0 to 1.0)
#         engine.save_to_file(text, filename)
#         engine.runAndWait()
#         return filename if os.path.exists(filename) else None
#     except Exception as e:
#         st.error(f"TTS generation failed: {str(e)}")
#         return None

import requests
import os

def generate_tts_audio(text, filename="temp_audio.mp3", voice="shimmer", model="tts-1"):
    try:
        api_key = os.getenv("OPENAI_API_KEY")  
        if not api_key:
            raise ValueError("OPENAI_API_KEY is not set")

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        json_data = {
            "model": model,
            "input": text,
            "voice": voice
        }

        response = requests.post(
            "https://api.openai.com/v1/audio/speech",
            headers=headers,
            json=json_data
        )

        if response.status_code == 200:
            with open(filename, "wb") as f:
                f.write(response.content)
            return filename
        else:
            print(f"Error: {response.status_code} - {response.text}")
            return None

    except Exception as e:
        print(f"TTS generation failed: {str(e)}")
        return None

# --- Clean up temporary audio files ---
def cleanup_audio_files(*files):
    for file in files:
        if file and os.path.exists(file):
            try:
                os.remove(file)
            except:
                pass

def cleanup_files(*files):
    for file in files:
        if file and os.path.exists(file):
            try:
                os.remove(file)
            except:
                pass

# --- Streamlit UI ---
if "show_results" not in st.session_state:
    st.session_state.show_results = False
if "pronunciation_feedbacks" not in st.session_state:
    st.session_state.pronunciation_feedbacks = []
if "age_group" not in st.session_state:
    st.session_state.age_group = None
if "level" not in st.session_state:
    st.session_state.level = None
if "current_question_index" not in st.session_state:
    st.session_state.current_question_index = 0
if "show_inputs" not in st.session_state:
    st.session_state.show_inputs = True
if "child_name" not in st.session_state:
    st.session_state.child_name = ""
if "audio_files" not in st.session_state:
    st.session_state.audio_files = {}  # Track audio files per question
if "audio_played" not in st.session_state:
    st.session_state.audio_played = {}  # Track initial playback

def get_tts_text(child_name, question_index, total_questions, question_text):
    """
    Generate the text to be spoken for a given question, including a personalized prompt.
    
    Args:
        child_name (str): The child's name.
        question_index (int): The current question index (0-based).
        total_questions (int): Total number of questions.
        question_text (str): The question text to be read.
    
    Returns:
        str: The complete text for TTS, including the prompt and question.
    """
    question_number = question_index + 1
    sanitized_name = child_name.strip() or "there"  # Fallback if name is empty
    
    if question_number == 1:
        prompt = f"Hey {sanitized_name}!!, let's begin with the first question!"
    elif question_number == 3:
        prompt = f"Wow this is awesome {sanitized_name}!!! Let's move on to question {question_number}!"
    elif question_number == 5:
        prompt = f"You are half way there! This is great!! Let's move on to question {question_number}!"
    elif question_number == 6:
        prompt = f"This looks fantastic {sanitized_name}!! Let's move on to question {question_number}!"
    elif question_number == 7:
        prompt = f"Here...... comes the pronunciation round! Let's move on to question {question_number}!"
    elif question_number == 8:
        prompt = f"Great, you are Amazing!!!! Let's move on to question {question_number}!"
    elif question_number == 9:
        prompt = f"We are almost done.... Let's move on to question {question_number}!"
    elif question_number == total_questions:
        prompt = f"Here... comes the final question {sanitized_name}! Let's make it count!"
    else:
        prompt = f"Great job! Let's move on to question {question_number}!"
    
    # Split question text to handle formatting (first line and second line)
    try:
        first, second = question_text.split('\n', 1)
        tts_text = f"{prompt} ... {first} ... {second}"
    except ValueError:
        # If question doesn't have a newline, use the whole text
        tts_text = f"{prompt} ... {question_text}"
    
    return tts_text

# Results page display logic
if st.session_state.show_results:
    st.title("🎯 Final Results")
    
    st.markdown(
        f"**Child’s Name**: {st.session_state.get('username', 'Unknown')} | **Age Group**: {st.session_state.get('age_group', 'Unknown')} | **Level**: {st.session_state.get('level', 'Unknown')}",
        unsafe_allow_html=True
    )
    st.markdown("---")

    st.subheader("📊 Performance Dashboard")

    try:
        with open("user_metrics.json", "r") as f:
            data = json.load(f)
            username = st.session_state.get("username", None)
            if username and username in data:
                metrics = data[username]
                if len(metrics) != 4:
                    st.error("Expected 4 sets of pronunciation metrics.")
                else:
                    metric_keys = ["overall", "rhythm", "pitch", "volume", "pronunciation", "fluency", "integrity", "pause_count", "speed", "grammar", "word_error", "verb_error", "article_error"]
                    tab1, tab2, tab3, tab4, tab5 = st.tabs(["Overall", "Pronunciation", "Intonation", "Fluency", "Grammar"])

                    with tab1:
                        st.header("Overall Performance")
                        categories = {"uppercase_lowercase": 0, "syllables": 0, "rhyming_words": 0}
                        correct_counts = {"uppercase_lowercase": 0, "syllables": 0, "rhyming_words": 0}
                        for i, q in enumerate(st.session_state.questions):
                            if q["options"]:
                                user_key = f"answer_{i}"
                                user_answer = st.session_state.user_answers.get(user_key, "")
                                correct_answer = str(q["answer"]).strip()  # Ensure no extra spaces
                                # Case-insensitive comparison with trimmed strings
                                is_correct = user_answer.strip().lower() == correct_answer.lower()
                                if "uppercase" in q["question"].lower() or "lowercase" in q["question"].lower():
                                    category = "uppercase_lowercase"
                                elif "syllable" in q["question"].lower():
                                    category = "syllables"
                                else:
                                    category = "rhyming_words"
                                categories[category] += 1
                                if is_correct:
                                    correct_counts[category] += 1
                        percentages = {}
                        for cat, count in categories.items():
                            if count > 0:
                                perc = (correct_counts[cat] / count * 100)
                                percentages[cat] = perc
                            else:
                                percentages[cat] = "N/A"
                        mcq_data = {
                            "Category": [],
                            "Correct (%)": [],
                            "Status": []
                        }
                        for cat, perc in percentages.items():
                            mcq_data["Category"].append(cat.replace('_', ' ').title())
                            if perc == "N/A":
                                mcq_data["Correct (%)"].append("N/A")
                                mcq_data["Status"].append("Not Applicable")
                            else:
                                mcq_data["Correct (%)"].append(f"{int(perc)}/100")
                                mcq_data["Status"].append("Perfect" if perc == 100 else "Needs Practice")
                        avg_overall = np.mean([m["overall"] for m in metrics])
                        valid_percentages = [p for p in percentages.values() if p != "N/A"]
                        avg_mcq = np.mean(valid_percentages) if valid_percentages else 0
                        # avg_overall = (avg_mcq + avg_overall) / 2 if valid_percentages else avg_overall
                        color = "red" if avg_overall < 60 else "orange" if avg_overall < 80 else "green"
                        st.metric("Average Overall Score", f"{int(avg_overall)}/100", delta_color="normal")
                        st.markdown(f"<span style='color:{color}'>{'Needs Improvement' if avg_overall < 60 else 'Good' if avg_overall < 80 else 'Excellent'}</span>", unsafe_allow_html=True)
                        
                        st.markdown("---")
                        st.subheader("⭐ Final Feedback from AI")
                        st.markdown(f"**Final Assessment by AI:** {st.session_state.final_feedback}")
                    
                        st.markdown("---")
                        st.subheader("Multiple-Choice Summary")
                        st.table(mcq_data)

                        st.markdown("---")
                        with st.expander("What These Metrics Mean"):
                            st.markdown(f"**Overall**: {descriptions['overall']}", unsafe_allow_html=True)

                        st.markdown("---")
                        pdf_bytes = generate_pdf_report(
                            username,
                            st.session_state.age_group,
                            metrics,
                            st.session_state.questions,
                            st.session_state.user_answers,
                            st.session_state.pronunciation_feedbacks,
                            st.session_state.final_feedback
                        )
                        st.download_button(
                            label="📄 Download Report as PDF",
                            data=pdf_bytes,
                            file_name="phonics_report.pdf",
                            mime="application/pdf"
                        )

                    with tab2:
                        st.header("Pronunciation")
                        # Create two columns for layout
                        col1, col2 = st.columns([1, 2])

                        # Left column: Smaller pronunciation box
                        with col1:
                            avg_pronunciation = np.mean([m["pronunciation"] for m in metrics])
                            color = "red" if avg_pronunciation < 60 else "orange" if avg_pronunciation < 80 else "green"
                            st.markdown(f"""
                                <div style="border: 2px solid #2196F3; border-radius: 8px; padding: 10px; background-color: #e3f2fd;
                                box-shadow: 0 2px 4px rgba(0,0,0,0.1); text-align: center; height: 300px; display: flex; flex-direction: column; justify-content: center; margin: 5px 0; line-height: 1.2;">
                                    <h3>Pronunciation Score</h3>
                                    <p style="font-size: 30px; color: {color};">{int(avg_pronunciation)}/100</p>
                                    <p style="color: {color};">{'Needs Improvement' if avg_pronunciation < 60 else 'Good' if avg_pronunciation < 80 else 'Excellent'}</p>
                                </div>
                            """, unsafe_allow_html=True)

                        with col2:
                            # Radial chart for each skill, using average across four metrics
                            skills = [
                                ("Vowel Sounds", np.mean([m["Skill 1 (Vowel sounds)"] for m in metrics])),
                                ("Fricatives & Affricates", np.mean([m["Skill 2 (Fricatives and Affricates)"] for m in metrics])),
                                ("Consonant Clusters", np.mean([m["Skill 3 (Consonant clusters)"] for m in metrics])),
                                ("Intrusion & Elision", np.mean([m["Skill 4 (Intrusion and Elision)"] for m in metrics])),
                                ("Diphthongs", np.mean([m["Skill 5 (Diphthongs)"] for m in metrics]))
                            ]

                            st.markdown("""
                                <h4 style="margin-top: 0; text-align: left; margin-left: 2cm;">Phonics Skills</h4>
                            """, unsafe_allow_html=True)

                            for skill_name, value in skills:
                                color = "#F44336" if value < 60 else "#FF9800" if value < 80 else "#34C759"
                                percentage = value
                                st.markdown(f"""
                                    <div style="display: flex; align-items: center; margin-bottom: 0.5cm; margin-left: 2cm;">
                                        <div style="width: 32px; height: 32px; position: relative; margin-right: 10px; flex-shrink: 0;">
                                            <div style="width: 100%; height: 100%; border-radius: 50%; 
                                                background: conic-gradient({color} 0% {percentage}%, #e0e0e0 {percentage}% 100%);
                                                transform: rotate(90deg);"></div>
                                            <div style="position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); 
                                                width: 24px; height: 24px; background: white; border-radius: 50%;"></div>
                                            <div style="position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); 
                                                font-size: 10px; font-weight: bold;">{int(value)}%</div>
                                        </div>
                                        <span style="font-size: 13px;">{skill_name}</span>
                                    </div>
                                """, unsafe_allow_html=True)

                        st.markdown("---")
                        # Phoneme Scores Line Graph
                        st.subheader("Phoneme Scores")
                        phoneme_scores = {}
                        for metric in metrics:
                            for word in metric["phoneme_scores"]:
                                for phoneme in word["phonemes"]:
                                    ph = phoneme["phoneme"]
                                    score = phoneme["score"]
                                    if ph not in phoneme_scores:
                                        phoneme_scores[ph] = []
                                    phoneme_scores[ph].append(score)

                        # Calculate average score for each phoneme
                        phoneme_avg_scores = {ph: sum(scores) / len(scores) for ph, scores in phoneme_scores.items()}

                        # Create DataFrame for plotting
                        phoneme_df = pd.DataFrame(list(phoneme_avg_scores.items()), columns=["Phoneme", "Average Score"])
                        phoneme_df = phoneme_df.sort_values("Phoneme")  # Sort phonemes for consistent display

                        fig = px.line(
                            phoneme_df,
                            x="Phoneme",
                            y="Average Score",
                            title="Average Phoneme Scores",
                            markers=True,
                            labels={"Average Score": "Score (%)", "Phoneme": "Phoneme"},
                            text=phoneme_df["Average Score"].astype(int)  # Whole numbers
                        )
                        # Color-code points
                        colors = ['#34C759' if score > 80 else '#FF9800' if score >= 60 else '#F44336' for score in phoneme_df["Average Score"]]
                        fig.update_traces(
                            marker=dict(color=colors, size=8),
                            textposition="top center",
                            textfont=dict(size=8, color=colors),  # Smaller font
                            texttemplate='%{text}',  # No decimals
                            cliponaxis=False,
                            dy=-15  # Offset labels above points
                        )
                        fig.update_layout(
                            xaxis_title="Phoneme",
                            yaxis_title="Average Score (%)",
                            yaxis_range=[0, 130],  # Extend y-axis further
                            showlegend=False,
                            xaxis_tickangle=45
                        )
                        
                        st.plotly_chart(fig, use_container_width=True)



                        with st.expander("Individual Feedback"):
                            pronunciation_questions = st.session_state.questions[-4:]
                            if st.session_state.pronunciation_feedbacks and len(pronunciation_questions) == 4:
                                for i, (q, feedback) in enumerate(zip(pronunciation_questions, st.session_state.pronunciation_feedbacks), 1):
                                    st.markdown(f"**Q{i}:** {q['question']}")
                                    st.write(feedback)
                                    st.markdown("---")
                            else:
                                st.info("No individual pronunciation feedback available or insufficient questions.")

                        with st.expander("What These Metrics Mean"):
                            st.markdown(f"""
                                - **Pronunciation**: {descriptions['pronunciation']}
                                - **Vowel Sounds**: Ability to correctly pronounce vowel sounds (a, e, i, o, u) and their variations
                                - **Fricatives & Affricates**: Ability to pronounce sounds like 'f', 'v', 'th', 's', 'z', 'sh', 'ch', and 'j'
                                - **Consonant Clusters**: Ability to pronounce groups of consonants together (like 'str', 'spl', 'nt')
                                - **Intrusion & Elision**: Inserting or dropping sounds for smoother speech. E.g., "I saw it" → /aɪ sɔː wɪt/
                                - **Diphthongs**: Ability to correctly pronounce gliding vowel sounds (like 'oi', 'ow', 'ai')
                            """, unsafe_allow_html=True)

                        

                    with tab3:  # Intonation
                        st.header("Intonation")
                        avg_rhythm = np.mean([m["rhythm"] for m in metrics])
                        avg_pitch = np.mean([m["pitch"] for m in metrics])
                        avg_volume = np.mean([m["volume"] for m in metrics])

                        rhythm_color = "red" if avg_rhythm < 60 else "orange" if avg_rhythm < 80 else "green"
                        pitch_color = "red" if avg_pitch < 60 else "orange" if avg_pitch < 80 else "green"
                        volume_color = "red" if avg_volume < 60 else "orange" if avg_volume < 80 else "green"

                        rhythm_status = "Needs Improvement" if avg_rhythm < 60 else "Good" if avg_rhythm < 80 else "Excellent"
                        pitch_status = "Needs Improvement" if avg_pitch < 60 else "Good" if avg_pitch < 80 else "Excellent"
                        volume_status = "Needs Improvement" if avg_volume < 60 else "Good" if avg_volume < 80 else "Excellent"

                        # Create a compact layout with 3 columns
                        col1, col2, col3 = st.columns([1, 1, 1])

                        with col1:
                            # Rhythm score in a compact box
                            st.markdown(f"""
                                <div class="small-metric-box">
                                    <h6>Intonation Score</h6>
                                    <p style="font-size: 35px; color: {rhythm_color}; margin: 5px 0;">{int(avg_rhythm)}/100</p>
                                    <p style="color: {rhythm_color}; margin: 0;">{rhythm_status}</p>
                                </div>
                            """, unsafe_allow_html=True)

                        with col2:
                            # Pitch visualization in a compact box
                            base_height = avg_pitch * 0.5
                            bars_html = ""
                            for i in range(15):  # Reduced number of bars for compactness
                                height = base_height * (0.8 + 0.2 * abs(np.sin(i/3)) + random.uniform(-2, 2))
                                bars_html += f'<div class="frequency-bar" style="height: {max(5, min(50, height))}px; background: {pitch_color}; margin-left: 2px;"></div>'

                            st.markdown(f"""
                                <div class="small-metric-box" style="text-align: center;">
                                    <h2 style="margin: 5px 0; font-size: 18px; ">Pitch</h2>
                                    <p style="font-size: 35px; color: {pitch_color}; margin: 5px 0;">{int(avg_pitch)}/100</p>
                                    <p style="color: {pitch_color}; margin: 5px 0; font-size: 12px;">{pitch_status}</p>
                                    <div style="height: 60px; display: flex; align-items: flex-end; justify-content: center;">
                                        {bars_html}
                                    </div>
                                </div>
                            """, unsafe_allow_html=True)

                        with col3:
                            # Volume visualization in a compact box
                            wave_size = min(80, avg_volume * 0.8)  # Limit max size
                            st.markdown(f"""
                                <div class="small-metric-box" style="text-align: center;">
                                    <h2 style="margin: 5px 0; font-size: 18px; justify-content: center;">Volume </h2>
                                    <p style="font-size: 35px; color: {volume_color}; margin: 5px 0;">{int(avg_volume)}/100</p>
                                    <p style="color: {volume_color}; margin: 5px 0; font-size: 12px;">{volume_status}</p>
                                    <div style="width: 80px; height: 80px; margin: 0 auto; position: relative;">
                                        <div style="position: absolute; width: 100%; height: 100%;">
                                            <div style="position: absolute; border: 2px solid #2196F3; border-radius: 50%; opacity: 0.3; 
                                                width: {wave_size}%; height: {wave_size}%; top: {10 + (100-wave_size)/2}%; left: {10 + (100-wave_size)/2}%; 
                                                animation: pulse 2s infinite;"></div>
                                            <div style="position: absolute; border: 2px solid #2196F3; border-radius: 50%; opacity: 0.3; 
                                                width: {wave_size*0.8}%; height: {wave_size*0.8}%; top: {10 + (100-wave_size*0.8)/2}%; left: {10 + (100-wave_size*0.8)/2}%; 
                                                animation: pulse 2s infinite; animation-delay: -0.5s;"></div>
                                            <div style="font-size: 24px; color: #2196F3; position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%);">🔊</div>
                                        </div>
                                    </div>
                                </div>
                            """, unsafe_allow_html=True)
                            
                        st.markdown("---")
                        # Metric descriptions in an expander
                        with st.expander("What These Metrics Mean"):
                            st.markdown(f"""
                                - **Intonation**: {descriptions['rhythm']}
                                - **Pitch**: {descriptions['pitch']}
                                - **Volume**: {descriptions['volume']}
                            """, unsafe_allow_html=True)

                    with tab4:
                        st.header("Fluency")
                        avg_fluency = np.mean([m["fluency"] for m in metrics])
                        avg_speed = np.mean([m["speed"] for m in metrics])
                        sum_pause_count = np.sum([m["pause_count"] for m in metrics])
                        fluency_color = "red" if avg_fluency < 60 else "orange" if avg_fluency < 80 else "green"
                        pause_color = "red" if sum_pause_count > 0 else "green"
                        if 100 <= avg_speed <= 150:
                            speed_color = "#4CAF50"
                        elif (80 <= avg_speed < 100) or (150 < avg_speed <= 170):
                            speed_color = "#FF9800"
                        elif (60 <= avg_speed < 80) or (170 < avg_speed <= 190):
                            speed_color = "#FF9800"
                        else:
                            speed_color = "#F44336"
                        speed_percentage = (avg_speed / 300) * 100
                        gauge_html = """
                            <div class="gauge-container">
                                <div class="gauge" style="background: conic-gradient({0} 0% {1}%, #e0e0e0 {1}% 100%);"></div>
                            </div>
                            <p style="text-align: center; font-size: 18px; font-weight: bold;">{2} wpm</p>
                            <p style="text-align: center; color: {0};">
                                {3}
                            </p>
                            <p style="text-align: center; font-size: 14px;">
                                Correct range: 100-150 wpm
                            </p>
                        """.format(
                            speed_color,
                            speed_percentage,
                            int(avg_speed),
                            'Excellent' if 100 <= avg_speed <= 150 else ('Too Fast' if avg_speed > 150 else 'Too Slow')
                        )
                        col1, col2, col3 = st.columns([2, 2, 2])
                        with col1:
                            st.markdown(f"""
                                <div class="large-metric-box">
                                    <h3>Average Fluency Score</h3>
                                    <p style="font-size: 36px; color: {fluency_color};">{int(avg_fluency)}/100</p>
                                    <p style="color: {fluency_color};">{'Needs Improvement' if avg_fluency < 60 else 'Good' if avg_fluency < 80 else 'Excellent'}</p>
                                </div>
                            """, unsafe_allow_html=True)
                        with col2:
                            st.markdown(gauge_html, unsafe_allow_html=True)
                        with col3:
                            st.markdown(f"""
                                <div class="large-metric-box">
                                    <h3>Pause Count</h3>
                                    <p style="font-size: 36px; color: {pause_color};">{int(sum_pause_count)}</p>
                                    <p style="color: {pause_color};">{'No Pauses' if sum_pause_count == 0 else 'Needs Improvement' if sum_pause_count in [1, 2] else 'Too Many Pauses'}</p>
                                    <p style="font-size: 14px;">Should be 0</p>
                                </div>
                            """, unsafe_allow_html=True)
                    
                        st.markdown("---")
                        st.subheader("Pauses in Pronunciation Sentences")
                        pronunciation_questions = st.session_state.questions[-4:]
                        if len(pronunciation_questions) == 4 and len(metrics) == 4:
                            for i, (q, metric) in enumerate(zip(pronunciation_questions, metrics), 1):
                                pause_count = metric.get("pause_count", 0)
                                pause_status = "No Pauses" if pause_count == 0 else f"{pause_count} Pause{'s' if pause_count > 1 else ''}"
                                pause_color = "#4CAF50" if pause_count == 0 else "#F44336"
                                st.markdown(f"""
                                    <div class="metric-box">
                                        <h4>Question {i}: {q['answer']}</h4>
                                        <p style="color: {pause_color};">{pause_status}</p>
                                    </div>
                                """, unsafe_allow_html=True)
                        else:
                            st.info("Insufficient pronunciation questions or metrics to display pause information.")
                    

                        st.markdown("---")
                        with st.expander("What These Metrics Mean"):
                            st.markdown(f"""
                                - **Fluency**: {descriptions['fluency']}
                                - **Speed**: {descriptions['speed']}
                                - **Pause Count**: {descriptions['pause_count']}
                            """, unsafe_allow_html=True)

                    with tab5:
                        st.header("Grammar")
                        avg_grammar = np.mean([m["grammar"] for m in metrics])
                        avg_integrity = np.mean([m["integrity"] for m in metrics])

                        # Calculate filtered error counts
                        sum_word_error = sum(len([err for err in metric.get("word_error_list", []) if err["score"] <= 80]) for metric in metrics)
                        sum_verb_error = sum(len([err for err in metric.get("verb_error_list", []) if err["score"] <= 80]) for metric in metrics)
                        sum_article_error = sum(len([err for err in metric.get("article_error_list", []) if err["score"] <= 80]) for metric in metrics)

                        grammar_color = "red" if avg_grammar < 60 else "orange" if avg_grammar < 80 else "green"
                        integrity_color = "red" if avg_integrity < 60 else "orange" if avg_integrity < 80 else "green"
                        word_error_color = "red" if sum_word_error > 0 else "green"
                        verb_error_color = "red" if sum_verb_error > 0 else "green"
                        article_error_color = "red" if sum_article_error > 0 else "green"

                        col1, col2, col3 = st.columns([2, 1, 2])
                        with col1:
                            st.markdown(f"""
                                <div class="large-metric-box">
                                    <h3>Grammar Score</h3>
                                    <p style="font-size: 36px; color: {grammar_color};">{int(avg_grammar)}/100</p>
                                    <p style="color: {grammar_color};">{'Needs Improvement' if avg_grammar < 60 else 'Good' if avg_grammar < 80 else 'Excellent'}</p>
                                </div>
                            """, unsafe_allow_html=True)
                        with col2:
                            st.markdown(f"""
                                <div class="small-metric-box-grammar">
                                    <span style="font-size: 15px;">Word Errors</span>
                                    <span style="font-size: 30px; color: {word_error_color};">{int(sum_word_error)}</span>
                                    <span style="font-size: 12px;">Should be 0</span>
                                </div>
                            """, unsafe_allow_html=True)
                            st.markdown(f"""
                                <div class="small-metric-box-grammar">
                                    <span style="font-size: 15px;">Verb Errors</span>
                                    <span style="font-size: 30px; color: {verb_error_color};">{int(sum_verb_error)}</span>
                                    <span style="font-size: 12px;">Should be 0</span>
                                </div>
                            """, unsafe_allow_html=True)
                            st.markdown(f"""
                                <div class="small-metric-box-grammar">
                                    <span style="font-size: 15px;">Article Errors</span>
                                    <span style="font-size: 30px; color: {article_error_color};">{int(sum_article_error)}</span>
                                    <span style="font-size: 12px;">Should be 0</span>
                                </div>
                            """, unsafe_allow_html=True)
                        with col3:
                            st.markdown(f"""
                                <div class="large-metric-box">
                                    <h3>Integrity Score</h3>
                                    <p style="font-size: 36px; color: {integrity_color};">{int(avg_integrity)}/100</p>
                                    <p style="color: {integrity_color};">{'Needs Improvement' if avg_integrity < 60 else 'Good' if avg_integrity < 80 else 'Excellent'}</p>
                                </div>
                            """, unsafe_allow_html=True)

                        st.markdown("---")
                        st.subheader("Specific Errors in Pronunciation Questions")
                        pronunciation_questions = st.session_state.questions[-4:]
                        if len(pronunciation_questions) == 4 and len(metrics) == 4:
                            for i, (q, metric) in enumerate(zip(pronunciation_questions, metrics), 1):
                                sentence = q['answer']
                                # Filter error lists and include scores in the display
                                filtered_word_errors = [f"{err['word']} ({err['score']})" for err in metric.get("word_error_list", []) if err["score"] <= 80]
                                filtered_verb_errors = [f"{err['word']} ({err['score']})" for err in metric.get("verb_error_list", []) if err["score"] <= 80]
                                filtered_article_errors = [f"{err['word']} ({err['score']})" for err in metric.get("article_error_list", []) if err["score"] <= 80]

                                error_html = ""
                                if filtered_word_errors or filtered_verb_errors or filtered_article_errors:
                                    if filtered_word_errors:
                                        error_html += f"<p style='color: #F44336;'>Mispronounced Words: {', '.join(filtered_word_errors)}</p>"
                                    if filtered_verb_errors:
                                        error_html += f"<p style='color: #F44336;'>Incorrect Verbs: {', '.join(filtered_verb_errors)}</p>"
                                    if filtered_article_errors:
                                        error_html += f"<p style='color: #F44336;'>Incorrect/Missing Articles: {', '.join(filtered_article_errors)}</p>"
                                else:
                                    error_html = "<p style='color: #4CAF50;'>No errors detected.</p>"

                                st.markdown(f"""
                                    <div class="metric-box">
                                        <h4>Question {i}: {sentence}</h4>
                                        {error_html}
                                    </div>
                                """, unsafe_allow_html=True)
                        else:
                            st.info("Insufficient pronunciation questions or metrics to display errors.")

                        st.markdown("---")
                        with st.expander("What These Metrics Mean"):
                            st.markdown(f"""
                                - **Grammar**: {descriptions['grammar']}
                                - **Word Errors**: {descriptions['word_error']}
                                - **Verb Errors**: {descriptions['verb_error']}
                                - **Article Errors**: {descriptions['article_error']}
                                - **Integrity**: {descriptions['integrity']}
                            """, unsafe_allow_html=True)

            else:
                st.info("No metrics found for you.")
    except Exception as e:
        st.error(f"Failed to load metrics: {e}")

    if st.button("🔁 Restart Quiz"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.session_state.show_inputs = True
        st.rerun()

    st.stop()


# Function to set background image
def set_bg_image(image_path):
    with open(image_path, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode()
    
    bg_css = f"""
        <style>
        .stApp {{
            background-image: url("data:image/png;base64,{encoded_string}");
            background-size: cover;
            background-position: center;
            background-repeat: no-repeat;
            background-attachment: fixed;
            overflow: hidden !important;
        }}
        /* Hide secondary buttons (faded Start Recording button) */
        button[data-testid="baseButton-secondary"] {{
            display: none !important;
        }}

        /* Semi-transparent dark overlay */
        .stApp::before {{
            content: "";
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background-color: rgba(0, 0, 0, 0.3);
            z-index: -1;
        }}

        /* Make ALL LABELS white */
        label, h1, h2, h3, h4, h5, h6,
        .stMarkdown, .stMarkdown p,
        .stRadio, .stCheckbox,
        .stSelectbox, .stTextInput label,
        .stProgress, .stSubheader {{
            color: black !important;
        }}

        /* Ensure spinner is white */
        .stSpinner, .stSpinner > div {{
            color: white !important;
            border-color: white transparent transparent transparent !important;
        }}
        .stSpinner > div > div {{
            border-color: white transparent transparent transparent !important;
        }}

        /* Your preferred alert box */
        .stAlert {{
            background-color: #FFF3CD !important;
            border-left: 4px solid #FFC107 !important;
            color: #856404 !important;
            padding: 3px !important;
            border-radius: 4px !important;
        }}

        /* Input fields - black text on white background */
        .stTextInput input, 
        .stSelectbox select,
        .stTextArea textarea {{
            background-color: white !important;
            color: black !important;
            border: 1px solid #ddd !important;
        }}

        /* Radio/checkbox options - white text */
        .stRadio [class*="st-"], 
        .stCheckbox [class*="st-"] {{
            color: black !important;
        }}

        /* Clean buttons */
        .stButton > button {{
            background-color: #4CAF50 !important;
            color: white !important;
        }}

        /* Adjust navigation buttons position (move up) */
        div[data-testid="stHorizontalBlock"] {{
            margin-top: -50px !important;
        }}
        </style>
        """
        
    st.markdown(bg_css, unsafe_allow_html=True)

# Set the background image
set_bg_image(r"Ateam Logo.png")

if st.session_state.show_inputs:
    st.title("#theAteam Kids Academy")
    st.subheader("Phonics Initial Assessment")
    # st.markdown("Generate phonics questions for kids based on age group and category.")
    st.session_state.child_name = st.text_input("👦👧 Enter Child's Name", value=st.session_state.child_name)

    if not st.session_state.child_name.strip():
        st.warning("Please enter the child's name to continue.")
        st.stop()

    age_group = st.selectbox("Select Age Group", ["3-4","5-6", "7-8", "9-10", "11-13"])
    st.session_state.age_group = age_group

    context = st.text_input("What do you love", value="", placeholder="What interests you more")
    st.session_state.context = context

    level = st.selectbox("Select Level", ["Level 1", "Level 2", "Level 3", "Level 4", "Level 5", "Level 6", "Don't Know"])
    st.session_state.level = level

    num_questions = 10

    if "questions" not in st.session_state:
        st.session_state.questions = []
    if "user_answers" not in st.session_state:
        st.session_state.user_answers = {}
    if "pronunciation_feedbacks" not in st.session_state:
        st.session_state.pronunciation_feedbacks = []
    
    if st.button("Generate Questions"):
        with st.spinner("Generating Questions..."):
            st.session_state.questions = get_random_questions(age_group, level, context, num_questions)
            st.session_state.user_answers = {}
            st.session_state.pronunciation_feedbacks = []
            st.session_state.current_question_index = 0
            st.session_state.show_inputs = False
            st.session_state.audio_played = {}  # Reset audio tracking
            st.rerun()

# Show questions one at a time if questions exist and inputs are hidden
if st.session_state.questions and not st.session_state.show_inputs:
    # st.subheader(f"Question {st.session_state.current_question_index + 1} of {len(st.session_state.questions)}")
    
    i = st.session_state.current_question_index
    q = st.session_state.questions[i]
    
    # Display the current question
    first, second = q['question'].split('\n', 1)
    st.markdown(f"**Q{i + 1}:** {first}<br><span style='font-size:50px'>{second}</span>", unsafe_allow_html=True)
    
    # Text-to-Speech for Questions
    # Text-to-Speech for Questions
    audio_key = f"audio_{i}"
    audio_file = f"temp_audio_{i}.mp3"
    
    # Generate audio if not already generated
    if audio_key not in st.session_state.audio_files:
        if q["options"]:  # Non-pronunciation question (uppercase/lowercase, syllables, rhyming)
            # Generate personalized TTS text
            tts_text = get_tts_text(
                child_name=st.session_state.child_name,
                question_index=i,
                total_questions=len(st.session_state.questions),
                question_text=q["question"]
            )
            generated_file = generate_tts_audio(tts_text, audio_file)
            st.session_state.audio_files[audio_key] = generated_file
        else:  # Pronunciation question
            # Generate personalized TTS text for pronunciation questions
            tts_text = get_tts_text(
                child_name=st.session_state.child_name,
                question_index=i,
                total_questions=len(st.session_state.questions),
                question_text="Read this sentence."
            )
            generated_file = generate_tts_audio(tts_text, audio_file)
            st.session_state.audio_files[audio_key] = generated_file
    
    # Replay Audio Button - Now the only audio control visible to the user
    if st.button("🔊 Replay Question", key=f"replay_{i}"):
        audio_path = st.session_state.audio_files.get(audio_key)
        if audio_path and os.path.exists(audio_path):
            try:
                # Hide the audio player component by creating a hidden container
                with st.container():
                    # Use style to hide the audio player but still allow it to play
                    st.markdown("""
                    <style>
                    div[data-testid="stAudio"] {
                        display: none;
                    }
                    </style>
                    """, unsafe_allow_html=True)
                    with open(audio_path, "rb") as f:
                        st.audio(f.read(), format="audio/mp3", autoplay=True)
            except Exception as e:
                st.error(f"Failed to play audio: {e}")
        else:
            st.error("Audio file not found. Please try again.")
    
    # Play audio automatically the first time (hidden player)
    if audio_key not in st.session_state.audio_played:
        audio_path = st.session_state.audio_files.get(audio_key)
        if audio_path and os.path.exists(audio_path):
            try:
                # Hide the audio player component
                with st.container():
                    st.markdown("""
                    <style>
                    div[data-testid="stAudio"] {
                        display: none;
                    }
                    </style>
                    """, unsafe_allow_html=True)
                    with open(audio_path, "rb") as f:
                        st.audio(f.read(), format="audio/mp3", autoplay=True)
                st.session_state.audio_played[audio_key] = True
            except Exception as e:
                st.error(f"Failed to play audio: {e}")
                st.session_state.audio_played[audio_key] = True  # Avoid retrying
        else:
            st.error("Failed to generate audio for the question.")
            st.session_state.audio_played[audio_key] = True  # Avoid retrying

    if q["options"]:
        key = f"answer_{i}"
        # Get the previously selected answer, if any
        previous_answer = st.session_state.user_answers.get(key, None)
        # Find the index of the previous answer in the options list, or use None if no previous answer
        default_index = q["options"].index(previous_answer) if previous_answer in q["options"] else None
        user_choice = st.radio("Choose an answer:", options=q["options"], index=default_index, key=key)
        st.session_state.user_answers[key] = user_choice
    else:
        key = f"answer_{i}"
        start_key = f"start_btn_{i}"
        stop_key = f"stop_btn_{i}"
        recording_key = f"is_recording_{i}"
        start_time_key = f"start_time_{i}"
        analyzed_key = f"is_analyzed_{i}"
        timer_placeholder = st.empty()

        playback_key = f"playback_{i}"
        if playback_key not in st.session_state:
            st.session_state[playback_key] = False

        # Init session states
        for k in [recording_key, start_time_key, analyzed_key, playback_key]:
            if k not in st.session_state:
                st.session_state[k] = False if k != start_time_key else None

        # ✅ Already analyzed and completed
        if st.session_state[analyzed_key] and key in st.session_state.user_answers and isinstance(st.session_state.user_answers[key], dict):
            st.success("✅ Completed!")
        else:
            # PLAYBACK MODE - Show audio with submit/retry options
            if st.session_state[playback_key]:
                # Display the audio recording
                try:
                    data = pathlib.Path("AudioFiles/output.wav").read_bytes()
                    st.audio(data, format=mimetypes.guess_type("audio.mp3")[0])

                    # Add a bit of vertical space to avoid overlap
                    st.markdown("###")  # or use st.empty() or st.write("")

                    # Show submit/retry buttons side by side
                    col1, col2 = st.columns([1, 1])  # optional: adjust ratios

                    with col1:
                        if st.button("Submit", key=f"submit_{i}"):
                            with st.spinner("Analyzing..."):
                                metrics, feedback = record_and_analyze.analyze_recording(
                                    q["answer"], st.session_state.child_name, model="sent.eval.promax"
                                )
                                if metrics is not None:
                                    st.session_state.user_answers[key] = metrics
                                    st.session_state.pronunciation_feedbacks.append(feedback)
                                    st.session_state[analyzed_key] = True
                                    st.session_state[playback_key] = False
                                    st.success("✅ Completed!")
                                else:
                                    st.error("Analysis failed. Please try again.")
                                    st.session_state[playback_key] = False
                                    st.session_state[recording_key] = False
                                    st.session_state[analyzed_key] = False
                                    st.session_state[start_time_key] = None
                            st.rerun()

                    with col2:
                        if st.button("Retry", key=f"retry_{i}"):
                            st.session_state[playback_key] = False
                            st.session_state[recording_key] = False
                            st.session_state[analyzed_key] = False
                            st.session_state[start_time_key] = None
                            if key in st.session_state.user_answers:
                                del st.session_state.user_answers[key]
                            st.rerun()

                except Exception as e:
                    st.error(f"Error playing audio: {e}")
                    st.session_state[playback_key] = False
                    st.session_state[recording_key] = False
                    st.session_state[analyzed_key] = False
                    st.session_state[start_time_key] = None
                    if key in st.session_state.user_answers:
                        del st.session_state.user_answers[key]
                    st.rerun()

            # 🟢 START BUTTON - Initial state
            elif not st.session_state[recording_key] and not st.session_state[analyzed_key] and not st.session_state[playback_key]:
                if st.button(f"Start Recording Q{i + 1}", key=start_key):
                    timer_placeholder.markdown("<h1 style='text-align: center; font-family: Roboto, sans-serif;  color: #FF4B4B; font-size: 80px;'>3</h1>", unsafe_allow_html=True)
                    time.sleep(1)
                    timer_placeholder.markdown("<h1 style='text-align: center; font-family: Roboto, sans-serif;  color: #FF4B4B; font-size: 80px;'>2</h1>", unsafe_allow_html=True)
                    time.sleep(1)
                    timer_placeholder.markdown("<h1 style='text-align: center; font-family: Roboto, sans-serif;  color: #FF4B4B; font-size: 80px;'>1</h1>", unsafe_allow_html=True)
                    time.sleep(1)
                    st.session_state[recording_key] = True
                    st.session_state[start_time_key] = time.time()
                    st.rerun()

            # ⛔ STOP BUTTON + TIMER - Recording state
            elif st.session_state[recording_key]:
                timer_placeholder.markdown("<h1 style='text-align: center; font-family: Roboto, sans-serif; color: #00FF00; font-size: 80px;'>Speak!</h1>", unsafe_allow_html=True)
                st.write("<h1 style='text-align: center; font-family: Roboto, sans-serif; color: #00FF00; font-size: 20px;'>The recording will turn off on its own after 15 seconds!</h1>", unsafe_allow_html=True)
                record_and_analyze.start_recording()
                st.session_state[playback_key] = True
                st.rerun()

    st.markdown("---")

    # Navigation buttons
    col1, col2 = st.columns([1, 1])
    
    with col1:
        # Show "Back" button if not on the first question
        if st.session_state.current_question_index > 0:
            if st.button("Back"):
                st.session_state.current_question_index -= 1
                st.rerun()
    
    with col2:
        if st.session_state.current_question_index < len(st.session_state.questions) - 1:
            # Show "Next" button if not on the last question
            if st.button("Next"):
                # Validate the current question before proceeding
                key = f"answer_{st.session_state.current_question_index}"
                if key not in st.session_state.user_answers or st.session_state.user_answers[key] in [None, ""]:
                    st.warning("Please answer the current question before proceeding.")
                else:
                    st.session_state.current_question_index += 1
                    st.rerun()
        else:
            # Show "Submit" button on the last question
            if st.button("Submit Answers"):
                # Validation: Check if all answers are provided
                unanswered = []
                for i, q in enumerate(st.session_state.questions):
                    key = f"answer_{i}"
                    if key not in st.session_state.user_answers or st.session_state.user_answers[key] in [None, ""]:
                        unanswered.append(i + 1)
                
                if unanswered:
                    st.warning(f"You missed answering question(s): {', '.join(map(str, unanswered))}. Please go back and answer all questions before submitting.")
                    st.stop()
                
                score = 0
                total_with_options = 0
                records = []
                feedback = ""
                for i, q in enumerate(st.session_state.questions):
                    if q["options"]:  # Only for multiple-choice questions
                        total_with_options += 1
                        correct = str(q["answer"])
                        user_key = f"answer_{i}"
                        user_answer = st.session_state.user_answers.get(user_key, "")
                        is_correct = user_answer.lower() == correct.lower()
                        if is_correct:
                            score += 1
                
                        records.append({
                            "Child Name": st.session_state.child_name,
                            "Question": q["question"],
                            "Options": ", ".join(q["options"]),
                            "Correct Answer": correct,
                            "User Answer": user_answer,
                            "Result": "Correct" if is_correct else "Incorrect"
                        })
                        status = "Correct" if is_correct else "Incorrect"
                        feedback += str(q["question"]) + f". Answer: {user_answer}. Result: {status}\n"
                    else:
                        user_key = f"answer_{i}"
                        feedback += str(st.session_state.user_answers.get(user_key, "")) + "\n"
                
                # Save pronunciation metrics to JSON if available
                pronunciation_metrics = []
                for i, q in enumerate(st.session_state.questions):
                    key = f"answer_{i}"
                    if not q["options"]:
                        metric = st.session_state.user_answers.get(key)
                        if isinstance(metric, dict):  # Ensure it's metrics
                            pronunciation_metrics.append(metric)
                
                # Save only if all 4 are collected
                if len(pronunciation_metrics) == 4:
                    username = st.session_state.child_name
                    st.session_state["username"] = username
                    record_and_analyze.save_user_metrics(username, pronunciation_metrics)
                
                # Convert to DataFrame
                df = pd.DataFrame(records)
                # Save to Excel
                output_path = "phonics_quiz_results.xlsx"
                if os.path.exists(output_path):
                    existing_df = pd.read_excel(output_path)
                    df = pd.concat([existing_df, df], ignore_index=True)
                df.to_excel(output_path, index=False)
                
                # Save feedback in session state for results page
                st.session_state.final_feedback = llm.get_response_from_ai(
                    prompts.get_final_feedback(st.session_state.child_name),
                    feedback
                )
                
                # Set flag to show results page
                st.session_state.show_results = True
                
                # Rerun app to display results page
                st.rerun()
