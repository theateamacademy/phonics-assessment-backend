"""
PDF Report Generator for ATeam Kids Academy Phonics Assessment.
Extracted from the original main.py Streamlit app for use with the FastAPI backend.
"""

import io
import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle, FancyBboxPatch
from matplotlib.colors import LinearSegmentedColormap
from reportlab.lib.pagesizes import letter
from reportlab.platypus import (
    Paragraph, Spacer, Table, TableStyle, Image, PageBreak
)
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import BaseDocTemplate, PageTemplate, Frame


descriptions = {
    "overall": "How well your child did overall.",
    "pronunciation": "How clearly your child says words.",
    "rhythm": "How smoothly your child's speech flows.",
    "pitch": "How high or low your child's voice sounds.",
    "volume": "How loud your child's voice is.",
    "fluency": "How easily your child speaks without stopping.",
    "speed": "How fast your child talks.",
    "pause_count": "How many times your child pauses unnecessarily.",
    "grammar": "How correctly your child uses grammar.",
    "word_error": "Number of words pronounced incorrectly.",
    "verb_error": "Number of mistakes in verbs.",
    "article_error": "Number of mistakes in articles.",
    "integrity": "How well words match what they're supposed to say."
}


def add_watermark(c, doc):
    c.saveState()
    c.setFont("Helvetica", 40)
    c.setFillColor(colors.lightgrey, alpha=0.5)
    page_width, page_height = letter
    center_x = page_width / 2
    center_y = page_height / 2
    c.translate(center_x, center_y)
    c.rotate(45)
    text = "#ATeamKidsAcademy"
    text_width = c.stringWidth(text, "Helvetica", 40)
    c.drawString(-text_width / 2, -20, text)
    c.restoreState()


class WatermarkedDocTemplate(BaseDocTemplate):
    def __init__(self, *args, **kwargs):
        BaseDocTemplate.__init__(self, *args, **kwargs)
        frame = Frame(
            self.leftMargin, self.bottomMargin,
            self.width, self.height, id='normal'
        )
        self.addPageTemplates([
            PageTemplate(id='AllPages', frames=frame, onPageEnd=add_watermark)
        ])


def sanitize_text(text):
    if not isinstance(text, str):
        text = str(text)
    return text.replace('<', '&lt;').replace('>', '&gt;')


def create_3d_pie_chart(value, filename):
    if value >= 80:
        main_color, shadow_color = '#1A942E', '#0E5F1D'
    elif value >= 60:
        main_color, shadow_color = '#FF9800', '#CC7A00'
    else:
        main_color, shadow_color = '#F44336', '#B1302A'

    sizes = [value, 100 - value]
    fig, ax = plt.subplots(figsize=(3, 3), dpi=200)

    wedges_shadow, _ = ax.pie(
        sizes, colors=[shadow_color, 'lightgrey'], startangle=90,
        explode=[0.1, 0], counterclock=False,
        wedgeprops=dict(edgecolor='white', linewidth=0), radius=1
    )
    for w in wedges_shadow:
        w.set_alpha(0.6)
        w.set_zorder(0)
        w.set_transform(w.get_transform() + plt.matplotlib.transforms.Affine2D().translate(0, -0.05))

    ax.pie(
        sizes, colors=[main_color, 'lightgrey'], startangle=90,
        explode=[0.1, 0], counterclock=False,
        wedgeprops=dict(edgecolor='white', linewidth=1), radius=1
    )

    angle = 90 - (value / 2) * 3.6
    x = 0.7 * np.cos(np.deg2rad(angle)) + 0.1
    y = 0.7 * np.sin(np.deg2rad(angle))
    ax.text(x, y, f"{int(value)}%", ha='center', va='center', fontsize=14, weight='bold')
    ax.axis('equal')
    ax.axis('off')
    plt.savefig(filename, bbox_inches='tight', dpi=200)
    plt.close()


def create_phoneme_line_chart(phoneme_df, filename):
    fig, ax = plt.subplots(figsize=(6, 2), dpi=200)
    chart_colors = ['#34C759' if s > 80 else '#FF9800' if s >= 60 else '#F44336' for s in phoneme_df["Average Score"]]

    for i in range(len(phoneme_df) - 1):
        ax.plot(phoneme_df["Phoneme"].iloc[i:i+2], phoneme_df["Average Score"].iloc[i:i+2],
                linestyle='-', color='#1E2F97', linewidth=1.5)
    ax.scatter(phoneme_df["Phoneme"], phoneme_df["Average Score"], c=chart_colors, s=25, zorder=5)

    for i, (phoneme, score) in enumerate(zip(phoneme_df["Phoneme"], phoneme_df["Average Score"])):
        color = '#34C759' if score > 80 else '#FF9800' if score >= 60 else '#F44336'
        ax.text(i, score + 15, f'{int(score)}', ha='center', va='bottom', fontsize=6, color=color)

    ax.set_title("Average Phoneme Scores", fontsize=10, weight='bold')
    ax.set_xlabel("Phoneme", fontsize=8, weight='bold')
    ax.set_ylabel("Score (%)", fontsize=8, weight='bold')
    ax.set_ylim(0, 130)
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
    thermometer = FancyBboxPatch((0.4, 0), 0.2, max_value, boxstyle="round,pad=0.02",
                                  fill=False, edgecolor='black', lw=2)
    ax.add_patch(thermometer)
    shadow = FancyBboxPatch((0.41, -0.01), 0.2, max_value, boxstyle="round,pad=0.02",
                             fill=True, color='gray', alpha=0.2)
    ax.add_patch(shadow)
    fill_height = min(value, max_value)
    for y_val in np.linspace(0, fill_height, 100):
        ax.add_patch(Rectangle((0.4, y_val), 0.2, fill_height/100,
                                color=gradient_cmap(y_val/fill_height if fill_height > 0 else 0), alpha=0.8))
    ax.add_patch(Circle((0.5, 0), 0.15, fill=True, color=color))
    ax.add_patch(Circle((0.5, 0), 0.18, fill=False, edgecolor=color, lw=2, alpha=0.5))
    font_size = 12 if is_count else 10
    ax.text(0.5, max_value + 28, f"{int(value)}{'' if is_count else '/100'}",
            ha='center', va='center', fontsize=font_size, weight='bold', color=color)
    ax.text(0.5, max_value + 40, metric_name, ha='center', va='center', fontsize=10, weight='bold')
    ax.text(0.5, -20, status, ha='center', va='center', fontsize=8, color=color)
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
    ax.text(0, 0, f"{int(value)}%", ha='center', va='center', fontsize=10, weight='bold', color=color)
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
    for i_val in np.linspace(0, 1, 100):
        ax.fill_between(theta_fill, 0, r_bg[:len(theta_fill)], color=gradient_cmap(i_val), alpha=0.8)
    needle_angle = -np.pi/2 + fill_angle
    ax.plot([needle_angle, needle_angle], [0, 0.9], color='black', lw=2)
    ax.plot([needle_angle], [0], 'ko', markersize=6)
    fig.text(0.5, 0.15, f"{int(value)} wpm", ha='center', va='center', fontsize=6, weight='bold')
    fig.text(0.5, 0.85, "Speed", ha='center', va='center', fontsize=8, weight='bold')
    speed_label = "Excellent" if 100 <= value <= 150 else ("Too Fast" if value > 150 else "Too Slow")
    fig.text(0.5, 0.05, speed_label, ha='center', va='center', fontsize=6, color=color)
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
            ax.bar(i, j, width=0.8, color=gradient_cmap(j/height if height > 0 else 0),
                   edgecolor='black', linewidth=0.2, alpha=0.8)
    ax.text(7.5, 120, "Pitch", ha='center', va='center', fontsize=10, weight='bold')
    ax.text(7.5, 100, f"{int(value)}/100", ha='center', va='center', fontsize=10, weight='bold', color=color)
    pitch_label = "Needs Improvement" if value < 60 else "Good" if value < 80 else "Excellent"
    ax.text(7.5, -10, pitch_label, ha='center', va='center', fontsize=8, color=color)
    plt.savefig(filename, bbox_inches='tight', dpi=200)
    plt.close()


def create_mcq_bar_chart(categories, correct_counts, filename):
    fig, ax = plt.subplots(figsize=(4, 2.8), dpi=200)
    category_labels = {
        "uppercase_lowercase": "Letter Case",
        "syllables": "Syllables",
        "rhyming_words": "Rhyming"
    }
    valid_categories = []
    valid_scores = []
    for cat, count in categories.items():
        if count > 0:
            perc = (correct_counts[cat] / count * 100)
            if not np.isnan(perc):
                valid_categories.append(category_labels.get(cat, cat))
                valid_scores.append(perc)

    if not valid_categories:
        ax.text(0.5, 0.5, "No MCQ Data Available", ha='center', va='center', fontsize=10)
        ax.axis('off')
        plt.savefig(filename, bbox_inches='tight', dpi=200)
        plt.close()
        return

    x = np.arange(len(valid_categories))
    chart_colors = ['#34C759' if s >= 80 else '#FF9800' if s >= 60 else '#F44336' for s in valid_scores]
    bar_width = 0.6
    for i, (score, clr) in enumerate(zip(valid_scores, chart_colors)):
        ax.bar(x[i], score, width=bar_width, color=clr, edgecolor=clr)
    for i, score in enumerate(valid_scores):
        ax.text(x[i], score + 3, f"{int(score)}%", ha='center', va='bottom',
                fontsize=8, weight='bold', color=chart_colors[i])
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


def generate_pdf_report(child_name, age_group, metrics, questions, user_answers, pronunciation_feedbacks, final_feedback, sound_focus=None):
    buffer = io.BytesIO()
    doc = WatermarkedDocTemplate(
        buffer, pagesize=letter,
        topMargin=0.3*inch, bottomMargin=0.3*inch,
        leftMargin=0.3*inch, rightMargin=0.3*inch
    )
    styles = getSampleStyleSheet()
    title_style = styles["Title"]
    heading_style = styles["Heading2"]
    subheading_style = styles["Heading3"]
    normal_style = styles["Normal"]
    normal_style.fontSize = 8.5
    normal_style.leading = 9.5
    heading_style.alignment = 0
    story = []

    from pronunciation_sound_analysis import analyze_sound_focus

    if sound_focus is None:
        sound_focus = analyze_sound_focus(metrics)

    story.append(Paragraph("ATeam Kids Academy Phonics Assessment Report", title_style))
    story.append(Spacer(1, 3))
    story.append(Paragraph(f"Name: {sanitize_text(child_name)}", normal_style))
    story.append(Paragraph(f"Age: {sanitize_text(age_group)}", normal_style))
    story.append(Spacer(1, 6))

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

    sum_pause_count = int(np.sum([m["pause_count"] for m in metrics]))
    pause_status = "No Pauses" if sum_pause_count == 0 else "Needs Improvement" if sum_pause_count in [1, 2] else "Too Many Pauses"
    create_thermometer_chart("Pauses", sum_pause_count, pause_status, "pause_thermometer.png", max_value=5, is_count=True)

    avg_grammar = np.mean([m["grammar"] for m in metrics])
    grammar_status = "Needs Improvement" if avg_grammar < 60 else "Good" if avg_grammar < 80 else "Excellent"
    create_thermometer_chart("Grammar", avg_grammar, grammar_status, "grammar_thermometer.png")

    avg_integrity = np.mean([m["integrity"] for m in metrics])
    integrity_status = "Needs Improvement" if avg_integrity < 60 else "Good" if avg_integrity < 80 else "Excellent"
    create_thermometer_chart("Integrity", avg_integrity, integrity_status, "integrity_thermometer.png")

    sum_word_error = sum(len([err for err in m.get("word_error_list", []) if err["score"] <= 80]) for m in metrics)
    sum_verb_error = sum(len([err for err in m.get("verb_error_list", []) if err["score"] <= 80]) for m in metrics)
    sum_article_error = sum(len([err for err in m.get("article_error_list", []) if err["score"] <= 80]) for m in metrics)

    create_thermometer_chart("Word Errors", sum_word_error, "None" if sum_word_error == 0 else "Some Errors",
                             "word_error_thermometer.png", max_value=5, is_count=True)
    create_thermometer_chart("Verb Errors", sum_verb_error, "None" if sum_verb_error == 0 else "Some Errors",
                             "verb_error_thermometer.png", max_value=5, is_count=True)
    create_thermometer_chart("Article Errors", sum_article_error, "None" if sum_article_error == 0 else "Some Errors",
                             "article_error_thermometer.png", max_value=5, is_count=True)

    skills = [
        ("Vowel Sounds", np.mean([m["Skill 1 (Vowel sounds)"] for m in metrics])),
        ("Fricatives", np.mean([m["Skill 2 (Fricatives and Affricates)"] for m in metrics])),
        ("Clusters", np.mean([m["Skill 3 (Consonant clusters)"] for m in metrics])),
        ("Intrusion", np.mean([m["Skill 4 (Intrusion and Elision)"] for m in metrics])),
        ("Diphthongs", np.mean([m["Skill 5 (Diphthongs)"] for m in metrics]))
    ]
    for i, (skill_name, value) in enumerate(skills):
        status = "Excellent" if value >= 80 else "Good" if value >= 60 else "Needs Improvement"
        create_radial_chart(value, skill_name, f"skill_radial_{i}.png")

    categories = {"uppercase_lowercase": 0, "syllables": 0, "rhyming_words": 0}
    correct_counts = {"uppercase_lowercase": 0, "syllables": 0, "rhyming_words": 0}
    for i, q in enumerate(questions):
        if q.get("options"):
            user_answer = user_answers.get(f"answer_{i}", "")
            is_correct = str(user_answer).lower() == str(q["answer"]).lower()
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

    table_style = TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('SPACEBEFORE', (0, 0), (-1, -1), 4),
        ('SPACEAFTER', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 2),
        ('RIGHTPADDING', (0, 0), (-1, -1), 2),
    ])

    story.append(Paragraph("Overall", heading_style))
    charts_row1 = [
        Image("overall_pie.png", width=2.5*inch, height=2.5*inch),
        Image("mcq_bar.png", width=3*inch, height=2*inch)
    ]
    story.append(Table([charts_row1], colWidths=[2.5*inch, 3*inch], rowHeights=[2.5*inch], style=table_style))
    story.append(Spacer(1, 6))

    story.append(Paragraph("Phonics skills metrics", heading_style))
    charts_row2 = [
        Image("pronunciation_thermometer.png", width=1.5*inch, height=2*inch),
    ] + [Image(f"skill_radial_{i}.png", width=1.1*inch, height=1.1*inch) for i in range(5)]
    story.append(Table([charts_row2],
                       colWidths=[1.5*inch] + [1.1*inch]*5,
                       rowHeights=[2*inch], style=table_style))
    story.append(Spacer(1, 6))

    story.append(Paragraph("Intonation", heading_style))
    charts_row3 = [
        Image("rhythm_thermometer.png", width=1.5*inch, height=2*inch),
        Image("pitch_bars.png", width=1.5*inch, height=1.3*inch),
        Image("volume_thermometer.png", width=1.5*inch, height=2*inch),
        Image("speed_gauge.png", width=1.3*inch, height=1*inch),
    ]
    story.append(Table([charts_row3], colWidths=[1.5*inch, 1.5*inch, 1.5*inch, 1.3*inch],
                       rowHeights=[2*inch], style=table_style))
    story.append(Spacer(1, 6))
    story.append(PageBreak())

    story.append(Paragraph("Phoneme Scores", heading_style))
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
                story.append(Table([[Image("phoneme_line.png", width=6*inch, height=2*inch)]],
                                   colWidths=[6*inch], rowHeights=[2*inch], style=table_style))
        except Exception:
            story.append(Paragraph("Phoneme chart could not be generated.", normal_style))
    story.append(Spacer(1, 6))

    story.append(Paragraph("Fluency and Grammar", heading_style))
    charts_row4 = [
        Image("fluency_thermometer.png", width=1.5*inch, height=2*inch),
        Image("grammar_thermometer.png", width=1.5*inch, height=2*inch),
        Image("integrity_thermometer.png", width=1.5*inch, height=2*inch),
    ]
    story.append(Table([charts_row4], colWidths=[1.5*inch]*3, rowHeights=[2*inch], style=table_style))
    story.append(Spacer(1, 6))

    story.append(Paragraph("Errors", heading_style))
    charts_row5 = [
        Image("word_error_thermometer.png", width=1.5*inch, height=2*inch),
        Image("article_error_thermometer.png", width=1.5*inch, height=2*inch),
        Image("verb_error_thermometer.png", width=1.5*inch, height=2*inch),
        Image("pause_thermometer.png", width=1.5*inch, height=2*inch),
    ]
    story.append(Table([charts_row5], colWidths=[1.5*inch]*4, rowHeights=[2*inch], style=table_style))
    story.append(PageBreak())

    story.append(Paragraph("Final Feedback from AI", heading_style))
    story.append(Paragraph(f"<b>Phonics Assessment by AI:</b> {sanitize_text(final_feedback)}", normal_style))
    story.append(Spacer(1, 12))

    story.append(Paragraph("Sound practice focus", subheading_style))
    story.append(Paragraph(f"<b>Summary:</b> {sanitize_text(sound_focus.get('summary_line', ''))}", normal_style))
    story.append(Spacer(1, 4))
    story.append(Paragraph(sanitize_text(sound_focus.get("detail_paragraph", "")), normal_style))
    story.append(Spacer(1, 12))

    pronunciation_questions = questions[-4:]
    story.append(Paragraph("Pauses in Pronunciation Sentences", subheading_style))
    if len(pronunciation_questions) == 4 and len(metrics) == 4:
        for i, (q, metric) in enumerate(zip(pronunciation_questions, metrics), 1):
            pause_count = metric.get("pause_count", 0)
            pause_status = "No Pauses" if pause_count == 0 else f"{pause_count} Pause{'s' if pause_count > 1 else ''}"
            story.append(Paragraph(f"Question {i}: {sanitize_text(q.get('answer', ''))}", normal_style))
            story.append(Paragraph(f"Status: {pause_status}", normal_style))
            story.append(Spacer(1, 6))

    story.append(Spacer(1, 12))
    story.append(Paragraph("Specific Errors in Pronunciation Questions", subheading_style))
    if len(pronunciation_questions) == 4 and len(metrics) == 4:
        for i, (q, metric) in enumerate(zip(pronunciation_questions, metrics), 1):
            story.append(Paragraph(f"Question {i}: {sanitize_text(q.get('answer', ''))}", normal_style))
            filtered_word_errors = [f"{err['word']} ({err['score']})" for err in metric.get("word_error_list", []) if err["score"] <= 80]
            filtered_verb_errors = [f"{err['word']} ({err['score']})" for err in metric.get("verb_error_list", []) if err["score"] <= 80]
            filtered_article_errors = [f"{err['word']} ({err['score']})" for err in metric.get("article_error_list", []) if err["score"] <= 80]
            error_found = False
            if filtered_word_errors:
                error_found = True
                story.append(Paragraph(f"<font color='red'>Mispronounced Words: {sanitize_text(', '.join(filtered_word_errors))}</font>", normal_style))
            if filtered_verb_errors:
                error_found = True
                story.append(Paragraph(f"<font color='red'>Incorrect Verbs: {sanitize_text(', '.join(filtered_verb_errors))}</font>", normal_style))
            if filtered_article_errors:
                error_found = True
                story.append(Paragraph(f"<font color='red'>Incorrect/Missing Articles: {sanitize_text(', '.join(filtered_article_errors))}</font>", normal_style))
            if not error_found:
                story.append(Paragraph("<font color='green'>No errors detected.</font>", normal_style))
            story.append(Spacer(1, 6))

    story.append(Spacer(1, 12))
    story.append(Paragraph("Descriptions", heading_style))
    story.append(Paragraph("Phonics Skills", subheading_style))
    story.append(Paragraph(f"- Vowel Sounds: {descriptions['pronunciation']}", normal_style))
    story.append(Paragraph("- Fricatives & Affricates: Ability to pronounce sounds like 'f', 'v', 'th', 's', 'z', 'sh', 'ch', and 'j'", normal_style))
    story.append(Paragraph("- Consonant Clusters: Ability to pronounce groups of consonants together (like 'str', 'spl', 'nt')", normal_style))
    story.append(Paragraph("- Intrusion & Elision: Inserting or dropping sounds for smoother speech", normal_style))
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

    doc.build(story)

    image_files = [
        "overall_pie.png", "pronunciation_thermometer.png", "rhythm_thermometer.png",
        "pitch_bars.png", "volume_thermometer.png", "fluency_thermometer.png",
        "speed_gauge.png", "pause_thermometer.png", "grammar_thermometer.png",
        "integrity_thermometer.png", "word_error_thermometer.png",
        "verb_error_thermometer.png", "article_error_thermometer.png", "mcq_bar.png",
        "phoneme_line.png"
    ] + [f"skill_radial_{i}.png" for i in range(5)]
    for fname in image_files:
        if os.path.exists(fname):
            os.remove(fname)

    buffer.seek(0)
    return buffer.getvalue()
