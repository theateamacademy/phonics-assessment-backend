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

def create_thermometer_chart(metric_name, value, status, filename, max_value=100, is_count=False):
    fig, ax = plt.subplots(figsize=(3, 4))
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
    font_size = 16 if is_count else 14
    ax.text(0.5, max_value + 28, f"{int(value)}{'' if is_count else '/100'}", 
            ha='center', va='center', fontsize=font_size, weight='bold', color=color)
    ax.text(0.5, max_value + 40, metric_name, 
            ha='center', va='center', fontsize=12, weight='bold')
    ax.text(0.5, -20, status, 
            ha='center', va='center', fontsize=10, color=color)
    plt.savefig(filename, bbox_inches='tight', dpi=200)
    plt.close()

def create_radial_chart(value, title, filename):
    fig, ax = plt.subplots(figsize=(2, 2), dpi=200)
    ax.set_xlim(-1.6, 1.6)
    ax.set_ylim(-1.6, 1.6)
    ax.axis('off')
    
    # Color setup
    color = '#F44336' if value < 60 else '#FF9800' if value < 80 else '#34C759'
    light_color = '#EF9A9A' if value < 60 else '#FFCC80' if value < 80 else '#A5D6A7'
    
    # Gradient arc
    theta = np.linspace(0, 2 * np.pi * (value / 100), 100)
    r = np.linspace(0.8, 1.2, 100)
    T, R = np.meshgrid(theta, r)
    X = R * np.cos(T)
    Y = R * np.sin(T)
    
    # Vertical gradient
    norm = plt.Normalize(-1.6, 1.6)
    cmap = LinearSegmentedColormap.from_list('vertical', [light_color, color])
    ax.contourf(X, Y, Y, 100, cmap=cmap, alpha=0.8, norm=norm)
    
    # Inner elements
    ax.add_patch(plt.Circle((0, 0), 0.75, color='white'))
    ax.text(0, 0, f"{int(value)}", ha='center', va='center', 
           fontsize=12, weight='bold', color=color)
    ax.text(0, -1.7, title, ha='center', va='center', fontsize=10)
    
    plt.savefig(filename, bbox_inches='tight', dpi=200)
    plt.close()


def create_gauge(value, filename):
    fig, ax = plt.subplots(figsize=(2, 1.5), subplot_kw=dict(projection='polar'), dpi=200)
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
    fig.text(0.5, 0.15, f"{int(value)} wpm", ha='center', va='center', fontsize=8, weight='bold')
    fig.text(0.5, 0.85, "Speed", ha='center', va='center', fontsize=10, weight='bold')
    fig.text(0.5, 0.05, "Excellent" if 100 <= value <= 150 else ("Too Fast" if value > 150 else "Too Slow"), 
             ha='center', va='center', fontsize=7, color=color)
    plt.savefig(filename, bbox_inches='tight', dpi=200)
    plt.close()

def create_frequency_bars(value, filename):
    fig, ax = plt.subplots(figsize=(3, 3), dpi=200)
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
            ax.bar(i, j, width=0.8, color=gradient_cmap(j/height), alpha=0.8)
    ax.text(7.5, 90, "Pitch", ha='center', va='center', fontsize=12, weight='bold')
    ax.text(7.5, 80, f"{int(value)}/100", ha='center', va='center', fontsize=12, weight='bold', color=color)
    ax.text(7.5, -5, "Needs Improvement" if value < 60 else "Good" if value < 80 else "Excellent", 
            ha='center', va='center', fontsize=10, color=color)
    plt.savefig(filename, bbox_inches='tight', dpi=200)
    plt.close()

def create_mcq_bar_chart(categories, correct_counts, filename):
    fig, ax = plt.subplots(figsize=(4, 3), dpi=200)
    valid_categories = []
    valid_scores = []
    category_labels = {
        "uppercase_lowercase": "Letter Case",
        "syllables": "Syllables",
        "rhyming_words": "Rhyming"
    }
    
    # Data processing
    for cat, count in categories.items():
        if count > 0:
            perc = (correct_counts[cat] / count * 100)
            valid_categories.append(category_labels[cat])
            valid_scores.append(perc)
    
    if not valid_categories:
        plt.close()
        return
    
    # Visual setup
    x = np.arange(len(valid_categories))
    colors = ['#34C759' if s >= 80 else '#FF9800' if s >= 60 else '#F44336' for s in valid_scores]
    light_colors = ['#A5D6A7' if s >= 80 else '#FFCC80' if s >= 60 else '#EF9A9A' for s in valid_scores]
    bar_width = 0.5
    
    # Gradient bars
    for i, (score, color, light_color) in enumerate(zip(valid_scores, colors, light_colors)):
        gradient = LinearSegmentedColormap.from_list(f'bar_{i}', [light_color, color], N=100)
        for y in np.linspace(0, score, 100):
            alpha = 0.6 + 0.4*(y/score)
            ax.bar(x[i], y, width=bar_width, 
                  color=gradient(y/score), 
                  alpha=alpha, 
                  edgecolor=gradient(y/score),
                  zorder=2)
    
    # Annotations
    for i, score in enumerate(valid_scores):
        ax.text(x[i], score + 5, f"{int(score)}", 
                ha='center', va='bottom', 
                fontsize=10, weight='bold', color=colors[i])
    
    # Axis styling
    ax.set_xticks(x)
    ax.set_xticklabels(valid_categories, fontsize=10, weight='bold')
    ax.set_yticks([0, 20, 40, 60, 80, 100])
    ax.set_yticklabels(['0', '20', '40', '60', '80', '100'], fontsize=10)
    ax.set_ylim(0, 120)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.grid(axis='y', linestyle='--', alpha=0.3)
    
    plt.savefig(filename, bbox_inches='tight', dpi=200)
    plt.close()



def sanitize_text(text):
    if not isinstance(text, str):
        text = str(text)
    return text.replace('<', '<').replace('>', '>')

# Sample data (unchanged)
child_name = "Test Child"
age_group = "5-7"
metrics = [
    {
        "overall": 85,
        "pronunciation": 80,
        "rhythm": 75,
        "pitch": 90,
        "volume": 70,
        "fluency": 82,
        "speed": 120,
        "pause_count": 1,
        "grammar": 88,
        "integrity": 85,
        "word_error": 0,
        "verb_error": 1,
        "article_error": 0,
        "Skill 1 (Vowel sounds)": 90,
        "Skill 2 (Fricatives and Affricates)": 85,
        "Skill 3 (Consonant clusters)": 80,
        "Skill 4 (Intrusion and Elision)": 75,
        "Skill 5 (Diphthongs)": 88,
        "word_error_list": [],
        "verb_error_list": ["was"],
        "article_error_list": []
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

def generate_pdf_report(child_name, age_group, metrics, questions, user_answers, pronunciation_feedbacks, final_feedback):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    title_style = styles["Title"]
    heading_style = styles["Heading2"]
    subheading_style = styles["Heading3"]
    normal_style = styles["Normal"]
    story = []

    # Page 1: Name, Age, Levels, Overall Graph, and Description
    story.append(Paragraph("ATeam Kids Academy Phonics Assessment Report", title_style))
    story.append(Spacer(1, 12))
    story.append(Paragraph(f"Name: {sanitize_text(child_name)}", normal_style))
    story.append(Paragraph(f"Age: {sanitize_text(age_group)}", normal_style))
    story.append(Spacer(1, 12))
    story.append(Paragraph("Levels in Phonics:", normal_style))
    story.append(Paragraph("- Level 1: Foundational Sounds", normal_style))
    story.append(Paragraph("- Level 2: Digraphs and Blends", normal_style))
    story.append(Paragraph("- Level 3: Long Vowel Sounds and Silent E", normal_style))
    story.append(Paragraph("- Level 4: Vowel Teams and Diphthongs", normal_style))
    story.append(Paragraph("- Level 5: R-Controlled Vowels and Other Complex Sounds", normal_style))
    story.append(Paragraph("- Level 6 and Beyond: Advanced Phonics and Word Study", normal_style))
    story.append(Spacer(1, 24))
    story.append(Paragraph("Overall Performance", heading_style))
    avg_overall = np.mean([m['overall'] for m in metrics])
    overall_status = "Needs Improvement" if avg_overall < 60 else "Good" if avg_overall < 80 else "Excellent"
    create_thermometer_chart("Overall Score", avg_overall, overall_status, "overall_thermometer.png")
    story.append(Image("overall_thermometer.png", width=3*inch, height=4*inch))
    story.append(Spacer(1, 12))
    story.append(Paragraph(f"Description: {descriptions['overall']}", normal_style))
    story.append(PageBreak())

    # Page 2: Final Feedback and MCQ Bar Chart
    story.append(Paragraph("Final Feedback from AI", heading_style))
    story.append(Paragraph(sanitize_text(final_feedback), normal_style))
    story.append(Spacer(1, 24))
    story.append(Paragraph("Multiple-Choice Summary", heading_style))
    story.append(Spacer(1, 12))
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
    story.append(Image("mcq_bar.png", width=4*inch, height=3*inch))
    story.append(PageBreak())

    # Page 3: Pronunciation and Phonics Skills
    story.append(Paragraph("Pronunciation", heading_style))
    avg_pronunciation = np.mean([m["pronunciation"] for m in metrics])
    pronunciation_status = "Needs Improvement" if avg_pronunciation < 60 else "Good" if avg_pronunciation < 80 else "Excellent"
    create_thermometer_chart("Pronunciation Score", avg_pronunciation, pronunciation_status, "pronunciation_thermometer.png")
    story.append(Image("pronunciation_thermometer.png", width=3*inch, height=4*inch))
    story.append(Spacer(1, 12))
    skills = [
        ("Vowel Sounds", np.mean([m["Skill 1 (Vowel sounds)"] for m in metrics]), "Excellent" if np.mean([m["Skill 1 (Vowel sounds)"] for m in metrics]) >= 80 else "Good" if np.mean([m["Skill 1 (Vowel sounds)"] for m in metrics]) >= 60 else "Needs Improvement"),
        ("Fricatives & Affricates", np.mean([m["Skill 2 (Fricatives and Affricates)"] for m in metrics]), "Excellent" if np.mean([m["Skill 2 (Fricatives and Affricates)"] for m in metrics]) >= 80 else "Good" if np.mean([m["Skill 2 (Fricatives and Affricates)"] for m in metrics]) >= 60 else "Needs Improvement"),
        ("Consonant Clusters", np.mean([m["Skill 3 (Consonant clusters)"] for m in metrics]), "Excellent" if np.mean([m["Skill 3 (Consonant clusters)"] for m in metrics]) >= 80 else "Good" if np.mean([m["Skill 3 (Consonant clusters)"] for m in metrics]) >= 60 else "Needs Improvement"),
        ("Intrusion & Elision", np.mean([m["Skill 4 (Intrusion and Elision)"] for m in metrics]), "Excellent" if np.mean([m["Skill 4 (Intrusion and Elision)"] for m in metrics]) >= 80 else "Good" if np.mean([m["Skill 4 (Intrusion and Elision)"] for m in metrics]) >= 60 else "Needs Improvement"),
        ("Diphthongs", np.mean([m["Skill 5 (Diphthongs)"] for m in metrics]), "Excellent" if np.mean([m["Skill 5 (Diphthongs)"] for m in metrics]) >= 80 else "Good" if np.mean([m["Skill 5 (Diphthongs)"] for m in metrics]) >= 60 else "Needs Improvement")
    ]
    story.append(Paragraph("Phonics Skills", subheading_style))
    skill_table_data = []
    for i, (skill_name, value, status) in enumerate(skills):
        create_radial_chart(value, skill_name, f"skill_radial_{i}.png")
        skill_table_data.append(Image(f"skill_radial_{i}.png", width=1.5*inch, height=1.5*inch))
    story.append(Table([skill_table_data], colWidths=[1.5*inch]*5))
    story.append(Spacer(1, 12))
    story.append(Paragraph(f"Description: {descriptions['pronunciation']}", normal_style))
    story.append(Paragraph("- Vowel Sounds: Ability to correctly pronounce vowel sounds (a, e, i, o, u) and their variations", normal_style))
    story.append(Paragraph("- Fricatives & Affricates: Ability to pronounce sounds like 'f', 'v', 'th', 's', 'z', 'sh', 'ch', and 'j'", normal_style))
    story.append(Paragraph("- Consonant Clusters: Ability to pronounce groups of consonants together (like 'str', 'spl', 'nt')", normal_style))
    story.append(Paragraph("- Intrusion & Elision: Inserting or dropping sounds for smoother speech. E.g., 'I saw it' → /aɪ sɔː wɪt/", normal_style))
    story.append(Paragraph("- Diphthongs: Ability to correctly pronounce gliding vowel sounds (like 'oi', 'ow', 'ai')", normal_style))
    story.append(PageBreak())

    # Page 4: Intonation (Pitch, Rhythm, Volume)
    story.append(Paragraph("Intonation", heading_style))
    avg_rhythm = np.mean([m["rhythm"] for m in metrics])
    avg_pitch = np.mean([m["pitch"] for m in metrics])
    avg_volume = np.mean([m["volume"] for m in metrics])
    rhythm_status = "Needs Improvement" if avg_rhythm < 60 else "Good" if avg_rhythm < 80 else "Excellent"
    pitch_status = "Needs Improvement" if avg_pitch < 60 else "Good" if avg_pitch < 80 else "Excellent"
    volume_status = "Needs Improvement" if avg_volume < 60 else "Good" if avg_volume < 80 else "Excellent"
    create_thermometer_chart("Intonation", avg_rhythm, rhythm_status, "rhythm_thermometer.png")
    create_thermometer_chart("Volume", avg_volume, volume_status, "volume_thermometer.png")
    create_frequency_bars(avg_pitch, "pitch_bars.png")
    pitch_table = Table([
        [Image("pitch_bars.png", width=3*inch, height=3*inch)]
    ], colWidths=[3*inch])
    pitch_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOX', (0, 0), (-1, -1), 2, colors.black),
        ('BACKGROUND', (0, 0), (-1, -1), colors.white),
    ]))
    story.append(pitch_table)
    story.append(Spacer(1, 12))
    intonation_volume_table = Table([
        [Image("rhythm_thermometer.png", width=3*inch, height=3.5*inch), 
         Image("volume_thermometer.png", width=3*inch, height=3.5*inch)]
    ], colWidths=[3*inch, 3*inch])
    intonation_volume_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOX', (0, 0), (-1, -1), 2, colors.black),
        ('BACKGROUND', (0, 0), (-1, -1), colors.white),
    ]))
    story.append(intonation_volume_table)
    story.append(Spacer(1, 12))
    story.append(Paragraph(f"Descriptions:", normal_style))
    story.append(Paragraph(f"- Pitch: {descriptions['pitch']}", normal_style))
    story.append(Paragraph(f"- Intonation: {descriptions['rhythm']}", normal_style))
    story.append(Paragraph(f"- Volume: {descriptions['volume']}", normal_style))
    story.append(PageBreak())

        # Page 5: Fluency and Speed
    story.append(Paragraph("Fluency and Speed", heading_style))
    avg_fluency = np.mean([m["fluency"] for m in metrics])
    avg_speed = np.mean([m["speed"] for m in metrics])
    fluency_status = "Needs Improvement" if avg_fluency < 60 else "Good" if avg_fluency < 80 else "Excellent"
    speed_status = "Excellent" if 100 <= avg_speed <= 150 else ("Too Fast" if avg_speed > 150 else "Too Slow")
    create_thermometer_chart("Fluency", avg_fluency, fluency_status, "fluency_thermometer.png")
    create_gauge(avg_speed, "speed_gauge.png")
    # Fluency chart
    fluency_table = Table([
        [Image("fluency_thermometer.png", width=3*inch, height=4*inch)]
    ], colWidths=[3*inch])
    fluency_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(fluency_table)
    story.append(Spacer(1, 12))
    story.append(Paragraph(f"Description: {descriptions['fluency']}", normal_style))
    story.append(Spacer(1, 12))
    # Speed chart
    speed_table = Table([
        [Image("speed_gauge.png", width=2*inch, height=2*inch)]
    ], colWidths=[2*inch])
    speed_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(speed_table)
    story.append(Spacer(1, 12))
    story.append(Paragraph(f"Description: {descriptions['speed']}", normal_style))
    story.append(PageBreak())

        # Page 6: Pause Count and Pauses in Pronunciation
    story.append(Paragraph("Pause Count", heading_style))
    sum_pause_count = np.sum([m["pause_count"] for m in metrics])
    pause_status = "No Pauses" if sum_pause_count == 0 else "Needs Improvement" if sum_pause_count in [1, 2] else "Too Many Pauses"
    create_thermometer_chart("Pause Count", sum_pause_count, pause_status, "pause_thermometer.png", max_value=5, is_count=True)
    pause_table = Table([
        [Image("pause_thermometer.png", width=2.5*inch, height=3*inch)]
    ], colWidths=[2.5*inch])
    pause_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(pause_table)
    story.append(Spacer(1, 12))
    story.append(Paragraph(f"Description: {descriptions['pause_count']}", normal_style))
    story.append(Spacer(1, 12))
    story.append(Paragraph("Pauses in Pronunciation Sentences", subheading_style))
    pronunciation_questions = questions[-4:]
    if len(pronunciation_questions) == 4 and len(metrics) == 4:
        for i, (q, metric) in enumerate(zip(pronunciation_questions, metrics), 1):
            pause_count = metric.get("pause_count", 0)
            pause_status = "No Pauses" if pause_count == 0 else f"{pause_count} Pause{'s' if pause_count > 1 else ''}"
            story.append(Paragraph(f"Question {i}: {sanitize_text(q['answer'])}", normal_style))
            story.append(Paragraph(f"Status: {pause_status}", normal_style))
            story.append(Spacer(1, 8))
    else:
        story.append(Paragraph("Insufficient pronunciation questions or metrics to display pause information.", normal_style))
    story.append(PageBreak())

    # Page 7: Grammar
    story.append(Paragraph("Grammar", heading_style))
    story.append(Spacer(1, 12))
    avg_grammar = np.mean([m["grammar"] for m in metrics])
    avg_integrity = np.mean([m["integrity"] for m in metrics])
    sum_word_error = np.sum([m["word_error"] for m in metrics])
    sum_verb_error = np.sum([m["verb_error"] for m in metrics])
    sum_article_error = np.sum([m["article_error"] for m in metrics])
    grammar_status = "Needs Improvement" if avg_grammar < 60 else "Good" if avg_grammar < 80 else "Excellent"
    integrity_status = "Needs Improvement" if avg_integrity < 60 else "Good" if avg_integrity < 80 else "Excellent"
    word_error_status = "None" if sum_word_error == 0 else "Some Errors"
    verb_error_status = "None" if sum_verb_error == 0 else "Some Errors"
    article_error_status = "None" if sum_article_error == 0 else "Some Errors"
    create_thermometer_chart("Grammar Score", avg_grammar, grammar_status, "grammar_thermometer.png")
    create_thermometer_chart("Integrity Score", avg_integrity, integrity_status, "integrity_thermometer.png")
    create_thermometer_chart("Word Errors", sum_word_error, word_error_status, "word_error_thermometer.png", max_value=5, is_count=True)
    create_thermometer_chart("Verb Errors", sum_verb_error, verb_error_status, "verb_error_thermometer.png", max_value=5, is_count=True)
    create_thermometer_chart("Article Errors", sum_article_error, article_error_status, "article_error_thermometer.png", max_value=5, is_count=True)
    grammar_integrity_table = Table([
        [Image("grammar_thermometer.png", width=3*inch, height=3.5*inch), 
         Image("integrity_thermometer.png", width=3*inch, height=3.5*inch)]
    ], colWidths=[3*inch, 3*inch])
    grammar_integrity_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOX', (0, 0), (-1, -1), 2, colors.black),
        ('BACKGROUND', (0, 0), (-1, -1), colors.white),
    ]))
    story.append(grammar_integrity_table)
    # story.append(Spacer(1, 12))
    error_table = Table([
        [Image("word_error_thermometer.png", width=2*inch, height=3.5*inch), 
         Image("verb_error_thermometer.png", width=2*inch, height=3.5*inch), 
         Image("article_error_thermometer.png", width=2*inch, height=3.5*inch)]
    ], colWidths=[2*inch, 2*inch, 2*inch])
    error_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOX', (0, 0), (-1, -1), 2, colors.black),
        ('BACKGROUND', (0, 0), (-1, -1), 'white'),
    ]))
    story.append(Spacer(1, 12))
    story.append(error_table)
    story.append(Spacer(1, 12))
    story.append(Paragraph(f"Descriptions:", normal_style))
    # story.append(Paragraph(f"- Grammar: {descriptions['grammar']}", normal_style))
    story.append(Paragraph(f"- Word Errors: {descriptions['word_error']}", normal_style))
    story.append(Paragraph(f"- Verb Errors: {descriptions['verb_error']}", normal_style))
    story.append(Paragraph(f"- Article Errors: {descriptions['article_error']}", normal_style))
    story.append(Paragraph(f"- Integrity: {descriptions['integrity']}", normal_style))
    story.append(PageBreak())

    # Page 8: Specific Errors in Pronunciation Questions
    story.append(Paragraph("Specific Errors in Pronunciation Questions", heading_style))
    pronunciation_questions = questions[-4:]
    if len(pronunciation_questions) == 4 and len(metrics) == 4:
        for i, (q, metric) in enumerate(zip(pronunciation_questions, metrics), 1):
            story.append(Paragraph(f"Question {i}: {sanitize_text(q['answer'])}", normal_style))
            word_errors = metric.get("word_error_list", [])
            verb_errors = metric.get("verb_error_list", [])
            article_errors = metric.get("article_error_list", [])
            error_found = False
            if word_errors:
                error_found = True
                word_errors_text = ', '.join(word_errors)
                story.append(Paragraph(f"<font color='red'>Mispronounced Words: {sanitize_text(word_errors_text)}</font>", normal_style))
            if verb_errors:
                error_found = True
                verb_errors_text = ', '.join(verb_errors)
                story.append(Paragraph(f"<font color='red'>Incorrect Verbs: {sanitize_text(verb_errors_text)}</font>", normal_style))
            if article_errors:
                error_found = True
                article_errors_text = ', '.join(article_errors)
                story.append(Paragraph(f"<font color='red'>Incorrect/Missing Articles: {sanitize_text(article_errors_text)}</font>", normal_style))
            if not error_found:
                story.append(Paragraph("<font color='green'>No errors detected.</font>", normal_style))
            story.append(Spacer(1, 8))
    else:
        story.append(Paragraph("Insufficient pronunciation questions or metrics to display errors.", normal_style))

    doc.build(story)

    image_files = [
        "overall_thermometer.png", "pronunciation_thermometer.png",
        "rhythm_thermometer.png", "pitch_bars.png", "volume_thermometer.png",
        "fluency_thermometer.png", "speed_gauge.png", "pause_thermometer.png",
        "grammar_thermometer.png", "integrity_thermometer.png", 
        "word_error_thermometer.png", "verb_error_thermometer.png", 
        "article_error_thermometer.png", "mcq_bar.png"
    ] + [f"skill_radial_{i}.png" for i in range(len(skills))]
    for fname in image_files:
        if os.path.exists(fname):
            os.remove(fname)

    buffer.seek(0)
    return buffer.getvalue()

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