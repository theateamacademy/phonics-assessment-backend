import os
import io
import numpy as np
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.units import inch
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle, FancyBboxPatch
from matplotlib.colors import LinearSegmentedColormap
from mpl_toolkits.mplot3d import Axes3D
# With this custom template approach:
from reportlab.platypus import BaseDocTemplate, PageTemplate, Frame

# Descriptions (unchanged)
descriptions = {
    "overall": "Overall performance across all assessed areas.",
    "pronunciation": "Ability to articulate sounds and words correctly.",
    "rhythm": "The pattern and flow of speech, including stress and intonation.",
    "pitch": "The highness or lowness of the voice during speech.",
    "volume": "The loudness or softness of the voice.",
    "fluency": "The smoothness and ease of speech delivery.",
    "speed": "The rate of speech, measured in words per minute (wpm).",
    "pause_count": "Number of pauses in pronunciation sentences.",
    "grammar": "Correctness of sentence structure and word usage.",
    "integrity": "Overall coherence and accuracy of spoken sentences.",
    "word_error": "Number of mispronounced or incorrect words.",
    "verb_error": "Number of incorrect verb forms or usage.",
    "article_error": "Number of incorrect or missing articles (a, an, the)."
}


import plotly.graph_objects as go

import matplotlib.pyplot as plt


import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Circle


from reportlab.platypus import BaseDocTemplate, PageTemplate, Frame

def add_watermark(canvas, doc):
    """Add watermark to every page (drawn last)"""
    canvas.saveState()
    # Watermark settings
    canvas.setFont("Helvetica-Bold", 38)
    canvas.setFillColor(colors.HexColor("#F0F0F0"))  # Light gray
    canvas.setFillAlpha(0.25)  # 25% opacity
    
    # Page dimensions
    page_width, page_height = letter
    
    # Text positioning
    text = "#ATeamKidsAcademy"
    text_width = canvas.stringWidth(text, "Helvetica-Bold", 38)
    
    # Center rotation and positioning
    canvas.translate(page_width/2, page_height/2)
    canvas.rotate(45)
    canvas.drawCentredString(0, -text_width/8, text)  # Adjusted vertical positioning
    
    canvas.restoreState()

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

def create_3d_mcq_bar_chart(categories, correct_counts, filename):
    fig = plt.figure(figsize=(4, 2.8), dpi=200)
    ax = fig.add_subplot(111, projection='3d')
    ax.view_init(elev=3, azim=90)
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
        ax.text(0.2, 0.2, 0.2, "No MCQ Data Available", ha='center', va='center', fontsize=5)
        ax.axis('off')
        plt.savefig(filename, bbox_inches='tight', dpi=200)
        plt.close()
        return
    
    x = np.arange(len(valid_categories))
    y = np.array(valid_scores)
    z = np.zeros(len(valid_categories))
    dx = np.ones(len(valid_categories)) * 0.4
    dy = np.ones(len(valid_categories)) * 0.4
    dz = y
    colors = ['#34C759' if s >= 80 else '#FF9800' if s >= 60 else '#F44336' for s in valid_scores]
    light_colors = ['#A5D6A7' if s >= 80 else '#FFCC80' if s >= 60 else '#EF9A9A' for s in valid_scores]
    
    for i in range(len(valid_categories)):
        gradient = LinearSegmentedColormap.from_list(f'bar_{i}', [light_colors[i], colors[i]], N=100)
        z_vals = np.linspace(0, dz[i], 100)
        for j, z_val in enumerate(z_vals):
            ax.bar3d(x[i], 0, z_val, dx[i], dy[i], z_val/dz[i] if dz[i] > 0 else 1, 
                     color=gradient(z_val/dz[i] if dz[i] > 0 else 1), alpha=0.6 + 0.4 * (z_val/dz[i] if dz[i] > 0 else 1))
    
    ax.set_xticks(x)
    ax.set_xticklabels(valid_categories, fontsize=6, weight='bold')
    ax.set_yticks([])
    ax.set_zticks([0, 20, 40, 60, 80, 100])
    ax.set_zticklabels(['0', '20', '40', '60', '80', '100'], fontsize=8)
    ax.set_zlim(0, 120)
    for i, score in enumerate(valid_scores):
        ax.text(x[i], 0, score + 5, f"{int(score)}", ha='center', va='bottom', fontsize=8, weight='bold', color=colors[i])
    plt.savefig(filename, bbox_inches='tight', dpi=200)
    plt.close()

def sanitize_text(text):
    if not isinstance(text, str):
        text = str(text)
    return text.replace('<', '<').replace('>', '>')



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
    create_3d_mcq_bar_chart(categories, correct_counts, "mcq_bar.png")
    
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
    
    # Row 4: Fluency and Grammar (Header + Fluency thermometer + Grammar + Integrity)
    story.append(PageBreak())
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
    story.append(Paragraph(sanitize_text(final_feedback), normal_style))
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

# Sample data (unchanged)
child_name = "Test Child"
age_group = "5-7"
metrics = [
    {
        "overall": 88,
      "rhythm": 95,
      "pause_count": 0,
      "pronunciation": 85,
      "fluency": 100,
      "integrity": 100,
      "speed": 206,
      "grammar": 89,
      "word_error": 2,
      "word_error_list": [
        {
          "word": "cat",
          "score": 73
        },
        {
          "word": "fluffy.",
          "score": 77
        }
      ],
      "verb_error": 0,
      "verb_error_list": [],
      "article_error": 0,
      "article_error_list": [],
      "pitch": 100.0,
      "volume": 100.0,
      "Skill 1 (Vowel sounds)": 73,
      "Skill 2 (Fricatives and Affricates)": 77,
      "Skill 3 (Consonant clusters)": 35,
      "Skill 4 (Intrusion and Elision)": 100,
      "Skill 5 (Diphthongs)": 78
    }
] * 4
questions = [
    {"question": "What is the uppercase of 'a'?", "options": ["A", "B", "C"], "answer": "A"},
    {"question": "How many syllables in 'cat'?", "options": ["1", "2", "3"], "answer": "1"},
    {"question": "What rhymes with 'hat'?", "options": ["Cat", "Dog", "Pen"], "answer": "Cat"},
    {"question": "Pronounce: The cat runs.", "answer": "The cat runs.", "options": []},
    {"question": "Pronounce: A big dog.", "answer": "A big dog.", "options": []},
    {"question": "Pronounce: She is happy.", "answer": "She is happy.", "options": []},
    {"question": "Pronounce: I see a tree.", "answer": "I see a tree.", "options": []}
]
user_answers = {
    "answer_0": "A",
    "answer_1": "1",
    "answer_2": "Cat",
    "answer_3": "The cat runs.",
    "answer_4": "A big dog.",
    "answer_5": "She is happy.",
    "answer_6": "I see a tree."
}
pronunciation_feedbacks = [
    "Good pronunciation, clear articulation.",
    "Slight pause detected, but clear.",
    "Minor verb error on 'is'.",
    "Excellent, no issues."
]
final_feedback = "Great job overall! Continue practicing verb forms."

# Generate and save PDF
pdf_buffer = generate_pdf_report(
    child_name,
    age_group,
    metrics,
    questions,
    user_answers,
    pronunciation_feedbacks,
    final_feedback
)

with open("phonics_report.pdf", "wb") as f:
    f.write(pdf_buffer)

print("PDF generated and saved as 'phonics_report.pdf'.")