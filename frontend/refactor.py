import re

def get_main_content(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        html = f.read()
    match = re.search(r'<main[^>]*>(.*?)</main>', html, re.DOTALL | re.IGNORECASE)
    return match.group(1).strip() if match else """"

index_html = open('index.html', 'r', encoding='utf-8').read()
results_content = get_main_content('results.html')
research_content = get_main_content('research.html')
deliv_content = get_main_content('deliverables/index.html')

index_main = get_main_content('index.html')

new_main = []

# --- Header ---
header_match = re.search(r'(<header.*?</header>)', index_main, re.DOTALL)
if header_match:
    header = header_match.group(1)
    header = re.sub(r'</header>', r'''
            <div class="mt-loose" style="margin-top:2rem;">
                <a href="./deliverables/source/Client_Post_Mortem_Investment_Challenge-Team-5-BWC_CH200.pptx" class="cta-btn cta-primary" download style="margin-right:1rem;">Download Complete Presentation</a>
                <a href="./deliverables/source/Final Excel model.xlsx" class="cta-btn cta-secondary" download>Download Excel Model</a>
            </div>
        </header>''', header)
    new_main.append(header)

# --- Telemetry ---
new_main.append('\n<section id="telemetry" class="narrative-section fade-up" style="padding-top: var(--spacing-8);">')
res_metrics = re.search(r'(<section.*</section>)', results_content, re.DOTALL)
if res_metrics:
    clean_res = re.sub(r'<header.*?</header>', '', results_content, flags=re.DOTALL)
    new_main.append(clean_res)
new_main.append('</section>')

# --- Story ---
new_main.append('\n<section id="story" class="narrative-section fade-up" style="padding-top: var(--spacing-8);">')
story_content = re.sub(r'<header.*?</header>', '', index_main, flags=re.DOTALL)
story_content = re.sub(r'<section class="narrative-climax.*?</section>', '', story_content, flags=re.DOTALL)
new_main.append(story_content)
new_main.append('</section>')

# --- Methodology ---
new_main.append('\n<section id="methodology" class="narrative-section fade-up" style="padding-top: var(--spacing-8);">')
clean_meth = re.sub(r'<header.*?</header>', '', research_content, flags=re.DOTALL)
new_main.append(clean_meth)
new_main.append('</section>')

# --- Deliverables ---
new_main.append('\n<section id="deliverables" class="narrative-section fade-up" style="padding-top: var(--spacing-8);">')
clean_deliv = re.sub(r'<header.*?</header>', '', deliv_content, flags=re.DOTALL)
clean_deliv = re.sub(r'<div class="carousel-scaffold">.*?</div>.*?<div class="carousel-controls">.*?</div>', r'''
                  <div class="text-body text-muted mb-tight" style="padding:1rem 0;">
                      <a href="./deliverables/source/Client_Post_Mortem_Investment_Challenge-Team-5-BWC_CH200.pptx" target="_blank" class="cta-btn cta-secondary">OPEN FULL POST-MORTEM DECK</a>
                  </div>
''', clean_deliv, flags=re.DOTALL)

clean_deliv = re.sub(r'<a href="\./source/Trading_Log.*?</a>', '', clean_deliv)
clean_deliv = re.sub(r'<a href="\./source/Final Excel model.*?</a>', '', clean_deliv)
clean_deliv = clean_deliv.replace('./source/', './deliverables/source/')
new_main.append(clean_deliv)
new_main.append('</section>')

full_main = '<main class="l-grid-main narrative-flow">\n' + '\n'.join(new_main) + '\n    </main>'
final_html = re.sub(r'<main[^>]*>.*?</main>', full_main, index_html, flags=re.DOTALL)

new_nav = '''<div class="nav-links" role="menubar">
            <a href="#telemetry" class="nav-link" role="menuitem">Quant Telemetry</a>
            <a href="#story" class="nav-link" role="menuitem">The Story</a>
            <a href="#methodology" class="nav-link" role="menuitem">Methodology</a>
            <a href="#deliverables" class="nav-link" role="menuitem">Deliverables</a>
        </div>'''
final_html = re.sub(r'<div class="nav-links".*?</div>', new_nav, final_html, flags=re.DOTALL)

with open('index.html', 'w', encoding='utf-8') as f:
    f.write(final_html)

print("Done refactoring index.html!")
