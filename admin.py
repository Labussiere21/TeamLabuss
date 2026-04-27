import os
import json
import re
import subprocess
import threading
import webbrowser
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory
from bs4 import BeautifulSoup

app = Flask(__name__)
app.secret_key = 'labussiere-admin-secret-2026'

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ACTUALITES_JSON = os.path.join(BASE_DIR, 'actualites.json')
INDEX_HTML = os.path.join(BASE_DIR, 'index.html')

TARIF_PAGES = [
    ('voiture.html', 'Permis Voiture'),
    ('moto.html', 'Permis Moto'),
    ('remorque.html', 'Remorque / BE'),
    ('bsr.html', 'BSR / AM'),
    ('autre.html', 'Autres formations'),
]

FORMATION_PAGES = [
    ('voiture.html', 'Voiture (B)'),
    ('moto.html', 'Moto'),
    ('bsr.html', 'BSR / AM'),
    ('remorque.html', 'Remorque / BE'),
    ('autre.html', 'Autres formations'),
]

CERTIF_IMAGES = [
    ('logo_ecole_de_conduite_0_0.png', 'Label École Conduite Qualité'),
    ('mediation2.jpg',                 'Logo Médiation'),
    ('mobilians.jpg',                  'Logo Mobilians'),
    ('Picto_datadocke.jpg',            'Logo DataDock'),
]

PDF_MAP = [
    ('TARIF_B.pdf', 'Tarif Permis B classique'),
    ('TARIF_AAC.pdf', 'Tarif AAC (conduite accompagnée)'),
    ('TARIF_B_AUTO.pdf', 'Tarif B Boîte Automatique'),
    ('TARIF_AAC_AUTO.pdf', 'Tarif AAC Boîte Automatique'),
    ('TARIF_PASSERELLE_B78.pdf', 'Tarif Passerelle (78h)'),
    ('TARIF_A1.pdf', 'Tarif Moto A1'),
    ('TARIF_A2.pdf', 'Tarif Moto A2'),
    ('TARIF_PASSERELLE_A2_A.pdf', 'Tarif Passerelle A2 → A'),
    ('TARIF_L5E.pdf', 'Tarif L5E (voiturette)'),
    ('TARIF_BE.pdf', 'Tarif Remorque BE'),
    ('TARIF_B96.pdf', 'Tarif B96'),
    ('TARIF_AM.pdf', 'Tarif AM / BSR'),
    ('reglement_intérieur.pdf', 'Règlement Intérieur'),
    ('conduite_supervisée.pdf', 'Conduite Supervisée'),
    ('tableau_prestations_unitaires_2025.pdf', 'Tableau Prestations 2025'),
    ('enjeux_et_deroulement_permis_B.pdf', 'Enjeux et Déroulement Permis B'),
    ('enjeux_et_deroulement_AAC.pdf', 'Enjeux et Déroulement AAC'),
    ('enjeux_et_deroulement_formation_BE.pdf', 'Enjeux et Déroulement BE'),
]


# ── Actualités ──────────────────────────────────────────────────────────────

def load_actualites():
    if not os.path.exists(ACTUALITES_JSON):
        return []
    with open(ACTUALITES_JSON, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_actualites(data):
    with open(ACTUALITES_JSON, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    regenerer_actualites_html()


def regenerer_actualites_html():
    actualites = load_actualites()
    with open(INDEX_HTML, 'r', encoding='utf-8') as f:
        content = f.read()

    if not actualites:
        section = '<!-- ACTUALITES_START -->\n  <!-- ACTUALITES_END -->'
    else:
        cards = '\n'.join(
            f'      <div class="actu-card">\n'
            f'        <span class="actu-date">{a["date"]}</span>\n'
            f'        <h3>{a["titre"]}</h3>\n'
            f'        <p>{a["texte"]}</p>\n'
            f'      </div>'
            for a in actualites
        )
        section = (
            '<!-- ACTUALITES_START -->\n'
            '  <section class="actualites-section">\n'
            '    <h2>Actualités</h2>\n'
            '    <div class="actualites-grid">\n'
            f'{cards}\n'
            '    </div>\n'
            '  </section>\n'
            '  <!-- ACTUALITES_END -->'
        )

    new_content = re.sub(
        r'<!-- ACTUALITES_START -->.*?<!-- ACTUALITES_END -->',
        section,
        content,
        flags=re.DOTALL,
    )
    with open(INDEX_HTML, 'w', encoding='utf-8') as f:
        f.write(new_content)


# ── Tarifs ───────────────────────────────────────────────────────────────────

# ── Formations (contenu) ─────────────────────────────────────────────────────

def get_sections(filename):
    filepath = os.path.join(BASE_DIR, filename)
    if not os.path.exists(filepath):
        return []
    with open(filepath, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f.read(), 'html.parser')
    sections = []
    for i, sec in enumerate(soup.select('.content-section')):
        h2 = sec.find('h2')
        sections.append({
            'index': i,
            'title': h2.get_text(strip=True) if h2 else f'Section {i+1}',
            'h2_html': h2.decode_contents() if h2 else '',
            'paragraphs': [
                {'index': j, 'html': p.decode_contents()}
                for j, p in enumerate(sec.find_all('p'))
            ],
        })
    return sections


def save_sections(filename, form_data):
    filepath = os.path.join(BASE_DIR, filename)
    with open(filepath, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f.read(), 'html.parser')
    for i, sec in enumerate(soup.select('.content-section')):
        h2 = sec.find('h2')
        if h2:
            val = form_data.get(f's{i}_h2', '').strip()
            if val:
                h2.clear()
                h2.append(BeautifulSoup(val, 'html.parser'))
        for j, p in enumerate(sec.find_all('p')):
            val = form_data.get(f's{i}_p{j}')
            if val is not None:
                p.clear()
                p.append(BeautifulSoup(val, 'html.parser'))
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(str(soup))


@app.route('/formations')
def formations_list():
    return render_template('formations_list.html', pages=FORMATION_PAGES, active='formations')


@app.route('/formations/<page>', methods=['GET', 'POST'])
def formations_edit(page):
    allowed = {fn for fn, _ in FORMATION_PAGES}
    if page not in allowed:
        flash('Page non autorisée.', 'error')
        return redirect(url_for('formations_list'))
    label = next(lb for fn, lb in FORMATION_PAGES if fn == page)
    if request.method == 'POST':
        save_sections(page, request.form)
        flash(f'"{label}" mis à jour !', 'success')
        return redirect(url_for('formations_edit', page=page))
    sections = get_sections(page)
    return render_template('formations_edit.html',
                           page=page, label=label,
                           sections=sections,
                           pages=FORMATION_PAGES,
                           active='formations')


def get_tarifs(filename):
    filepath = os.path.join(BASE_DIR, filename)
    if not os.path.exists(filepath):
        return []
    with open(filepath, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f.read(), 'html.parser')
    cards = []
    for card in soup.select('.tarif-card'):
        h4 = card.find('h4')
        prix_el = card.find(class_='prix')
        desc_el = card.find(class_='description')
        if h4 and prix_el:
            cards.append({
                'titre': h4.get_text(strip=True),
                'prix': prix_el.get_text(strip=True),
                'description': desc_el.get_text(strip=True) if desc_el else '',
            })
    return cards


def save_tarifs(filename, updated):
    filepath = os.path.join(BASE_DIR, filename)
    with open(filepath, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f.read(), 'html.parser')
    for i, card in enumerate(soup.select('.tarif-card')):
        if i >= len(updated):
            break
        prix_el = card.find(class_='prix')
        desc_el = card.find(class_='description')
        if prix_el:
            prix_el.string = updated[i]['prix']
        if desc_el and updated[i].get('description'):
            desc_el.string = updated[i]['description']
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(str(soup))


# ── Routes ───────────────────────────────────────────────────────────────────

@app.route('/')
def index():
    return redirect(url_for('actualites'))


@app.route('/actualites', methods=['GET', 'POST'])
def actualites():
    if request.method == 'POST':
        actu = {
            'id': datetime.now().strftime('%Y%m%d%H%M%S'),
            'date': request.form['date'],
            'titre': request.form['titre'],
            'texte': request.form['texte'],
        }
        data = load_actualites()
        data.insert(0, actu)
        save_actualites(data)
        flash('Actualité ajoutée !', 'success')
        return redirect(url_for('actualites'))
    return render_template('actualites.html', actualites=load_actualites(), active='actualites')


@app.route('/actualites/supprimer/<actu_id>', methods=['POST'])
def supprimer_actu(actu_id):
    data = [a for a in load_actualites() if a['id'] != actu_id]
    save_actualites(data)
    flash('Actualité supprimée.', 'info')
    return redirect(url_for('actualites'))


@app.route('/tarifs', methods=['GET', 'POST'])
def tarifs():
    if request.method == 'POST':
        for filename, _ in TARIF_PAGES:
            prefix = filename.replace('.html', '_')
            existing = get_tarifs(filename)
            updated = [
                {
                    'prix': request.form.get(f'{prefix}{i}_prix', c['prix']),
                    'description': request.form.get(f'{prefix}{i}_desc', c['description']),
                }
                for i, c in enumerate(existing)
            ]
            save_tarifs(filename, updated)
        flash('Tarifs mis à jour !', 'success')
        return redirect(url_for('tarifs'))

    pages = [
        {
            'filename': fn,
            'label': lb,
            'prefix': fn.replace('.html', '_'),
            'cards': get_tarifs(fn),
        }
        for fn, lb in TARIF_PAGES
    ]
    return render_template('tarifs.html', pages=pages, active='tarifs')


@app.route('/documents', methods=['GET', 'POST'])
def documents():
    all_labels = dict(PDF_MAP) | dict(CERTIF_IMAGES)
    image_exts = {'.jpg', '.jpeg', '.png', '.webp', '.gif'}

    if request.method == 'POST':
        file_key = request.form.get('pdf_key')
        file = request.files.get('fichier')
        if file_key and file:
            ext = os.path.splitext(file.filename.lower())[1]
            expected_ext = os.path.splitext(file_key.lower())[1]
            allowed = (ext == '.pdf') or (ext in image_exts and expected_ext in image_exts)
            if allowed:
                file.save(os.path.join(BASE_DIR, file_key))
                flash(f'"{all_labels.get(file_key, file_key)}" mis à jour !', 'success')
            else:
                flash('Erreur : format de fichier incompatible.', 'error')
        else:
            flash('Erreur : sélectionnez un fichier valide.', 'error')
        return redirect(url_for('documents'))

    pdfs = [
        {'filename': fn, 'label': lb, 'exists': os.path.exists(os.path.join(BASE_DIR, fn))}
        for fn, lb in PDF_MAP
    ]
    certifs = [
        {'filename': fn, 'label': lb, 'exists': os.path.exists(os.path.join(BASE_DIR, fn))}
        for fn, lb in CERTIF_IMAGES
    ]
    return render_template('documents.html', pdfs=pdfs, certifs=certifs, active='documents')


@app.route('/preview/<path:filename>')
def preview(filename):
    return send_from_directory(BASE_DIR, filename)


@app.route('/publier', methods=['POST'])
def publier():
    try:
        subprocess.run(['git', 'add', '.'], cwd=BASE_DIR, check=True)
        if subprocess.run(['git', 'diff', '--cached', '--quiet'], cwd=BASE_DIR).returncode == 0:
            flash('Aucun changement à publier.', 'info')
        else:
            msg = f"Mise à jour back office — {datetime.now().strftime('%d/%m/%Y %H:%M')}"
            subprocess.run(['git', 'commit', '-m', msg], cwd=BASE_DIR, check=True)
            subprocess.run(['git', 'push', 'origin', 'main'], cwd=BASE_DIR, check=True)
            flash('Site publié sur GitHub !', 'success')
    except subprocess.CalledProcessError as e:
        flash(f'Erreur publication : {e}', 'error')
    return redirect(request.referrer or url_for('actualites'))


if __name__ == '__main__':
    threading.Timer(1.2, lambda: webbrowser.open('http://localhost:5000')).start()
    print('Back office sur http://localhost:5000  —  Ctrl+C pour arrêter')
    app.run(debug=False, port=5000)
