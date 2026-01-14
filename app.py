import streamlit as st
import requests
import json
import anthropic
from typing import List, Dict, Tuple
import time
import re

# ============================================
# CONFIGURATION INITIALE
# ============================================

if hasattr(st, 'secrets') and 'ANTHROPIC_API_KEY' in st.secrets:
    st.session_state['anthropic_key'] = st.secrets['ANTHROPIC_API_KEY']
    st.session_state['serper_key'] = st.secrets['SERPER_API_KEY']
    st.session_state['api_configured'] = True

st.set_page_config(
    page_title="Ootravaux Local Page Builder",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ============================================
# TEMPLATE HTML COMPLET OOTRAVAUX
# ============================================

TEMPLATE_HTML = '''<!DOCTYPE html>
<html lang="fr" dir="ltr">
<head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no" />
    <meta http-equiv="x-ua-compatible" content="ie=edge" />
    <title>{{PAGE_TITLE}}</title>
    
    <style>
        *, ::after, ::before { box-sizing: border-box; }
        html { font-family: sans-serif; line-height: 1.15; -webkit-text-size-adjust: 100%; -webkit-tap-highlight-color: transparent; }
        body { margin: 0; font-family: 'Poppins', Helvetica, Roboto, Arial, sans-serif; font-size: 1rem; font-weight: 400; line-height: 1.5; color: #212529; background-color: #fafbfc; }
        :root { --blue: #B8EEFF; --primary: #004AF3; --secondary: #A8CF45; --orange: #FB793E; --white: #fff; --gray: #6c757d; --dark: #343a40; }
        .container { width: 100%; padding-right: 15px; padding-left: 15px; margin-right: auto; margin-left: auto; max-width: 1200px; }
        @media (max-width: 767px) { .container { padding-right: 20px; padding-left: 20px; } }
        .row { display: flex; flex-wrap: wrap; margin-right: -15px; margin-left: -15px; }
        .col-12 { position: relative; width: 100%; padding-right: 15px; padding-left: 15px; flex: 0 0 100%; max-width: 100%; }
        @media (min-width: 768px) { .container { max-width: 720px; } .col-sm-4 { flex: 0 0 33.33333%; max-width: 33.33333%; } .col-sm-5 { flex: 0 0 41.66667%; max-width: 41.66667%; } .col-sm-7 { flex: 0 0 58.33333%; max-width: 58.33333%; } }
        @media (min-width: 992px) { .container { max-width: 960px; } .col-md-3 { flex: 0 0 25%; max-width: 25%; } .col-md-4 { flex: 0 0 33.33333%; max-width: 33.33333%; } .col-md-8 { flex: 0 0 66.66667%; max-width: 66.66667%; } }
        @media (min-width: 1200px) { .container { max-width: 1140px; } .col-lg-4 { flex: 0 0 33.33333%; max-width: 33.33333%; } .col-lg-8 { flex: 0 0 66.66667%; max-width: 66.66667%; } }
        .btn { font-size: 1.8rem; line-height: 2.3rem; font-weight: 700; transition: all .3s ease 0s; border: none; outline: 0; box-shadow: none; min-height: 5rem; background: #004af3; color: #fff; border-radius: 3rem; padding: 1.3rem 2rem; position: relative; overflow: hidden; display: inline-block; text-align: center; text-decoration: none; }
        @media (min-width: 768px) { .btn { padding: 1.1rem 2rem; min-height: 4.5rem; } }
        .btn:hover { color: #fff; transform: scale(.98); }
        .btn.btn-primary { background: #004af3; color: #fff; }
        .btn.btn-primary:hover { background: #022a86; }
        .simple-page { font-size: 16px; line-height: 1.7; color: #212529; margin-bottom: 8rem; }
        .simple-page h1 { color: #000; font-family: 'Poppins', Helvetica, Roboto, Arial, sans-serif; font-size: 2.2em; font-weight: 700; line-height: 1.14; margin: 0 0 12px 0; }
        .simple-page h2 { color: #212529; font-family: 'Poppins', Helvetica, Roboto, Arial, sans-serif; font-size: 28px; margin: 40px 0 24px 0; font-weight: 700; line-height: 1.2; }
        .simple-page h3 { color: #212529; font-family: 'Poppins', Helvetica, Roboto, Arial, sans-serif; font-size: 22px; margin: 30px 0 16px 0; font-weight: 600; line-height: 1.3; }
        @media (min-width: 768px) { .simple-page h1 { font-size: 34px; } .simple-page h2 { font-size: 30px; } .simple-page h3 { font-size: 26px; } }
        .simple-page p { margin: 0 0 16px 0; }
        .simple-page ul { padding-left: 4rem; margin: 1.6rem 0; }
        .simple-page a:not(.btn):not(.carousel-link):not(.cta-b2b-pros-btn) { color: #004AF3; text-decoration: none; transition: color 0.15s, text-decoration 0.15s; }
        .simple-page a:not(.btn):not(.carousel-link):not(.cta-b2b-pros-btn):hover { color: #022a86; text-decoration: underline; }
        .article-heading { margin-bottom: 3rem; }
        .article-img .img-w-border { position: relative; z-index: 1; }
        .article-img .img-w-border:before { content: ''; width: 100%; height: 100%; display: block; position: absolute; border: .6rem solid #fb793e; border-radius: 1rem; z-index: -1; }
        .article-img .img-w-border img { border-radius: 1rem; width: 100%; height: auto; }
        .intro-top-couvreur { font-size: 16px; color: #000; margin-bottom: 1px; font-weight: normal; text-align: left; }
        .chiffres-cle-container { background: #FEDDCF; border: 2.5px solid #FB793E; border-radius: 22px; margin: 0 0 64px 0; padding: 20px 25px 16px 25px; color: #222222; display: flex; justify-content: center; align-items: center; gap: 0; box-shadow: 0 6px 20px rgba(3, 3, 28, 0.22); text-align: center; }
        .chiffre-cle-bloc { flex: 1 1 0; text-align: center; padding: 0 14px 0 14px; border-right: 1px solid #FB793E; min-width: 220px; display: flex; flex-direction: column; align-items: center; justify-content: center; }
        .chiffre-cle-bloc:last-child { border-right: none; }
        .chiffre-cle-valeur { font-size: 2rem; font-weight: bold; display: flex; align-items: center; justify-content: center; gap: 10px; color: #222222; }
        .chiffre-cle-etoiles { color: #222222; font-size: 1.4rem; font-weight: bold; letter-spacing: 2px; }
        .chiffre-cle-label { font-size: 16px; margin-bottom: 4px; margin-top: 4px; font-weight: 500; color: #222222; }
        @media (max-width: 1070px) { .chiffres-cle-container { flex-direction: column; gap: 18px; } .chiffre-cle-bloc { border-right: none; border-bottom: 1px solid #FB793E; } .chiffre-cle-bloc:last-child { border-bottom: none; } }
        .avis-section { display: flex; gap: 24px; margin: 40px 0 20px 0; overflow-x: auto; position: relative; scroll-behavior: smooth; user-select: none; scroll-snap-type: x mandatory; padding-bottom: 18px; }
        .avis-section::-webkit-scrollbar { height: 8px; }
        .avis-section::-webkit-scrollbar-track { background: #f1f1f1; border-radius: 10px; }
        .avis-section::-webkit-scrollbar-thumb { background: #ff6600; border-radius: 10px; }
        .avis-card { background: #fff; border-radius: 18px; box-shadow: 0 4px 12px rgba(60,72,88,0.12); padding: 28px 28px 30px 28px; width: 280px; min-width: 280px; flex: 0 0 auto; display: flex; flex-direction: column; align-items: flex-start; scroll-snap-align: start; margin-bottom: 10px; }
        .avis-card .stars { margin: 10px 0 12px 0; color: #FFA120; font-size: 22px; letter-spacing: 1.5px; }
        .avis-card .avis-txt { font-size: 14px; color: #232323; margin-bottom: 24px; line-height: 1.65; min-height: 62px; }
        .avis-card .avis-user { display: flex; align-items: center; gap: 15px; margin-top: auto; }
        .avis-card .user-name { font-weight: 600; font-size: 1rem; color: #2D3540; }
        .articles-carousel-container { position: relative; overflow-x: hidden; scroll-behavior: smooth; padding-bottom: 20px; }
        .articles-vignettes-container { display: flex; gap: 28px; margin: 36px 0 16px 0; flex-wrap: nowrap; overflow-x: auto; scroll-snap-type: x mandatory; padding-bottom: 18px; }
        .articles-vignettes-container::-webkit-scrollbar { height: 8px; }
        .articles-vignettes-container::-webkit-scrollbar-track { background: #f1f1f1; border-radius: 10px; }
        .articles-vignettes-container::-webkit-scrollbar-thumb { background: #ff6600; border-radius: 10px; }
        .articles-vignette { flex: 0 0 320px; min-width: 320px; scroll-snap-align: start; box-shadow: 0 2px 8px rgba(0,0,0,0.1); border-radius: 10px; background: #fff; padding: 10px 10px 30px 10px; display: flex; flex-direction: column; height: 100%; }
        .articles-vignette-img-wrap { border-radius: 10px; overflow: hidden; position: relative; margin: 0; }
        .articles-vignette-img { width: 100%; height: 122px; object-fit: cover; border-radius: 10px; }
        .articles-vignette-meta { margin: 16px 10px 0 10px; font-size: 14px; color: #888; text-align: left; }
        .articles-vignette-date { color: #ff6600; font-size: 14px; margin: 3px 10px 7px 10px; text-align: left; }
        .articles-vignette-title { font-size: 14px; color: #000; font-weight: bold; margin: 0 10px 25px 10px; text-align: left; min-height: 42px; line-height: 21px; }
        .articles-vignette-title a { color: #000; font-weight: bold; text-decoration: none; }
        .articles-vignette-title a:hover { text-decoration: underline; }
        .articles-vignette-link { display: block; margin: 5px 10px 0 10px; color: #ff6600; font-weight: bold; text-decoration: none; font-size: 14px; margin-top: auto; }
        .articles-vignette-link:hover { color: #c24900; text-decoration: underline; }
        .faq-section { margin: 40px 0; }
        .faq-item { border-radius: 10px; overflow: hidden; border: 2px solid #454868; margin-bottom: 10px; background: #E6EDFE; }
        .faq-question { padding: 16px 24px; font-size: 16px; font-weight: bold; color: #23253a; border-bottom: 1px solid #b9bfcf; }
        .faq-answer { padding: 18px 24px 20px 24px; color: #23253a; line-height: 1.65; }
        .faq-answer a:not(.btn) { color: #004AF3; text-decoration: none; }
        .faq-answer a:not(.btn):hover { color: #022a86; text-decoration: underline; }
        .table { width: 100%; margin-top: 24px; margin-bottom: 24px; border-collapse: collapse; }
        .table th, .table td { border: 1px solid #fb793e; padding: 8px 12px; text-align: left; }
        .table th { background: #f8f9fa; font-weight: bold; }
        .table-striped tbody tr:nth-child(odd) { background: rgba(248, 249, 250, 0.5); }
        .cta-article.article-trouvez { color: #000; text-align: center; border: none; box-shadow: none; padding: 0; margin: 30px 0; background: none; border-radius: 0; }
        .cta-article.article-trouvez .btn { padding: 15px 30px; border-radius: 25px; margin: 0 auto; font-weight: 700; box-shadow: 0 3px 15px 0 rgba(0,52,255,0.20); transition: all 0.3s ease; font-size: 18px; }
        .cta-article.article-trouvez .btn:hover { background: #022a86; box-shadow: 0 8px 30px 0 rgba(2,42,134,0.25); text-decoration: none; transform: translateY(-2px); }
        .cta-article.article-trouvez.first-cta { padding: 0; margin-top: 20px; margin-bottom: 25px; text-align: left; background: none; border: none; }
        .cta-article.article-trouvez.first-cta .btn { margin: 0; }
        @media (max-width: 767px) { .cta-article.article-trouvez.first-cta { text-align: center; } .cta-article.article-trouvez.first-cta .btn { margin: 0 auto; display: inline-block; } }
        .cta-b2b-pros-container { max-width: 100%; margin: 40px 0 0 0; border-radius: 22px; background: #FEDDCF; display: flex; align-items: center; gap: 20px; padding: 24px; box-shadow: 0 8px 30px rgba(3, 3, 28, 0.11); position: relative; overflow: hidden; }
        .cta-b2b-pros-illustration { max-width: 135px; min-width: 86px; width: 17vw; border-radius: 12px; background: #FEDDCF; object-fit: contain; display: block; }
        .cta-b2b-pros-content { flex: 1; display: flex; flex-direction: column; gap: 9px; position: relative; z-index: 2; }
        .cta-b2b-pros-title { font-size: 22px; font-weight: bold; color: #232323; margin: 0 0 3px 0; line-height: 1.18; }
        .cta-b2b-pros-desc { font-size: 16px; color: #212529; margin-bottom: 4px; max-width: 530px; line-height: 1.55; }
        .cta-b2b-pros-btn { background: #004AF3; color: white !important; text-decoration: none; border-radius: 20px; display: inline-block; font-size: 16px; font-weight: bold; padding: 7px 14px; box-shadow: 0 2px 12px 0 rgba(0,52,255,0.10); border: none; transition: background 0.18s; }
        .cta-b2b-pros-btn:hover { background: #022a86; color: white !important; text-decoration: none; }
        .cta-b2b-pros-livres { position: absolute; left: 20px; right: 20px; bottom: 10px; opacity: 0.5; height: 28px; z-index: 1; pointer-events: none; background: url('https://www.ootravaux.fr/sites/ootravaux/files/2025-09/livres-bandeau.svg') repeat-x bottom; background-size: auto 28px; }
        @media (max-width: 1024px) { .cta-b2b-pros-container { flex-direction: column; align-items: flex-start; gap: 12px; padding: 12px 6vw 22px 6vw; } .cta-b2b-pros-illustration { max-width: 80px; } }
        @media (max-width: 767px) { .cta-b2b-pros-container { flex-direction: column; align-items: stretch; padding: 12px 7vw 27px 7vw; border-radius: 12px; gap: 7px; } .cta-b2b-pros-illustration { margin-left: auto; margin-right: auto; } .cta-b2b-pros-title { font-size: 22px; } .cta-b2b-pros-action { width: 100%; text-align: center; } .cta-b2b-pros-btn { display: block; margin: 0 auto; text-align: center; } }
        .article-sidebar { padding: 20px 0; }
        .position-sticky { position: sticky; top: 20px; }
        .article-sidebar .cta-article.article-trouvez { padding: 25px; border: none; border-radius: 15px; background-color: #FEDDCF; }
        .article-sidebar .cta-article.article-trouvez .h4, .article-sidebar .cta-article.article-trouvez ul { text-align: left; }
        .article-sidebar .h4 { font-size: 22px; font-weight: bold; margin-bottom: 15px; }
        .article-sidebar ul { padding-left: 0; list-style: none; margin: 15px 0; }
        .article-sidebar li { padding: 5px 0; position: relative; padding-left: 20px; font-size: 16px; }
        .article-sidebar li:before { content: '✓'; position: absolute; left: 0; color: #212529; font-weight: bold; }
        .article-sidebar .btn.full { width: 100%; display: block; text-align: center; }
        .ootravaux-breadcrumb { font-family: Poppins, Arial, sans-serif; margin: 0 0 24px 0; padding: 0; font-size: 14px; line-height: 1.4; color: #212529; background: transparent; }
        .ootravaux-breadcrumb a { color: #212529 !important; text-decoration: none !important; }
        .ootravaux-breadcrumb a:hover { color: #212529 !important; text-decoration: underline !important; }
        .ootravaux-breadcrumb .breadcrumb-separator { display: inline-block; margin: 0 10px; color: #f28a4b; font-size: 18px; line-height: 1; }
        @media (max-width: 767px) { .ootravaux-breadcrumb { display: none; } }
    </style>
</head>
<body>
    <div class="dialog-off-canvas-main-canvas">
        <main role="main">
            <section class="container simple-page">
                <div class="article-heading">
                    <nav aria-label="Fil d'Ariane" class="ootravaux-breadcrumb breadcrumb">
                        {{BREADCRUMB}}
                    </nav>
                    <div class="row">
                        <div class="article-img col-12 col-sm-5 col-lg-4">
                            <div class="img-w-border">
                                <img alt="{{IMAGE_ALT}}" src="{{IMAGE_URL}}">
                            </div>
                        </div>
                        <div class="article-info col-12 col-sm-7 col-lg-8">
                            <h1>{{H1}}</h1>
                            <p class="intro-top-couvreur">{{INTRO}}</p>
                            <div class="cta-article article-trouvez first-cta">
                                <a class="btn btn-primary" href="{{URL_CTA}}" rel="nofollow" target="_blank">Recevez jusqu'à 4 devis</a>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div style="max-width:960px;margin:0 auto;">
                    <div class="chiffres-cle-container">
                        <div class="chiffre-cle-bloc">
                            <div class="chiffre-cle-valeur"><span class="chiffre-cle-etoiles">★ ★ ★ ★ ☆</span> <span>4,3/5</span></div>
                            <div class="chiffre-cle-label">note sur <a href="https://www.google.fr/search?q=ootravaux&amp;hl=fr" rel="noopener" target="_blank">Google</a></div>
                        </div>
                        <div class="chiffre-cle-bloc">
                            <div class="chiffre-cle-valeur"><span>Devis 100% gratuit</span></div>
                            <div class="chiffre-cle-label">sans engagement</div>
                        </div>
                        <div class="chiffre-cle-bloc">
                            <div class="chiffre-cle-valeur"><span>21 000 artisans</span></div>
                            <div class="chiffre-cle-label">répartis sur toute la France</div>
                        </div>
                    </div>
                </div>
                
                <div class="row">
                    <div class="col-12 col-md-8">
                        <section class="article-body">
                            {{FIRST_H2_SECTION}}
                            
                            <h2>Ils sont passés par Ootravaux</h2>
                            <div class="avis-section">
                                {{TEMOIGNAGES}}
                            </div>
                            
                            {{MAIN_CONTENT}}
                            
                            <div class="cta-article article-trouvez">
                                <a class="btn btn-primary" href="{{URL_CTA}}" rel="nofollow" target="_blank">Trouvez un artisan près de chez vous</a>
                            </div>
                            
                            {{REMAINING_CONTENT}}
                            
                            <div class="cta-article article-trouvez">
                                <a class="btn btn-primary" href="{{URL_CTA}}" rel="nofollow" target="_blank">Comparez les devis gratuitement</a>
                            </div>
                            
                            <h2>Articles liés qui pourraient vous intéresser</h2>
                            <div class="articles-carousel-container">
                                <div class="articles-vignettes-container">
                                    {{CARROUSEL}}
                                </div>
                            </div>
                            
                            {{POURQUOI_OOTRAVAUX}}
                            
                            <h2>FAQ : les questions que vous vous posez</h2>
                            <div class="faq-section">
                                {{FAQ}}
                            </div>
                            
                            <div class="cta-b2b-pros-container">
                                <img src="https://www.ootravaux.fr/sites/ootravaux/storage/files/2025-09/no-hits--response-list.png" alt="Professionnels" class="cta-b2b-pros-illustration">
                                <div class="cta-b2b-pros-content">
                                    <div class="cta-b2b-pros-title">Vous êtes artisan ? Trouvez rapidement de nouveaux chantiers et boostez votre activité !</div>
                                    <p class="cta-b2b-pros-desc">Recevez des contacts de particuliers motivés pour leurs travaux, sélectionnés dans votre secteur et selon vos spécialités. Simple, flexible et sans engagement !</p>
                                    <div class="cta-b2b-pros-action">
                                        <a href="https://www.ootravaux.fr/trouver-des-chantiers" class="cta-b2b-pros-btn" target="_blank">Trouvez des chantiers maintenant</a>
                                    </div>
                                </div>
                                <div class="cta-b2b-pros-livres"></div>
                            </div>
                        </section>
                    </div>
                    
                    <aside class="col-12 col-md-4 article-sidebar">
                        <div class="position-sticky">
                            <div class="cta-article article-trouvez">
                                <h4 class="h4">Besoin d'un professionnel ?</h4>
                                <ul>
                                    <li>Recevez jusqu'à 4 devis</li>
                                    <li>Comparez les offres sans engagement</li>
                                    <li>Trouvez un artisan près de chez vous</li>
                                </ul>
                                <a class="btn btn-primary full" href="{{URL_CTA}}" rel="nofollow" target="_blank">Demandez un devis</a>
                            </div>
                        </div>
                    </aside>
                </div>
            </section>
        </main>
    </div>
</body>
</html>'''


# ============================================
# DONNÉES FIXES (Témoignages et Carrousel)
# ============================================

TEMOIGNAGES_DEFAULT = []


def parse_temoignages_input(temoignages_str: str) -> List[Dict]:
    """Parse les témoignages au format Prénom|texte|date|étoiles;..."""
    if not temoignages_str.strip():
        return TEMOIGNAGES_DEFAULT
    
    temoignages = []
    entries = temoignages_str.strip().split(";")
    
    for entry in entries:
        parts = entry.strip().split("|")
        if len(parts) >= 4:
            etoiles_num = parts[3].strip()
            if etoiles_num == "5":
                etoiles = "★★★★★"
            elif etoiles_num == "4":
                etoiles = "★★★★☆"
            else:
                etoiles = "★★★★★"
            
            temoignages.append({
                "prenom": parts[0].strip(),
                "texte": parts[1].strip(),
                "date": parts[2].strip(),
                "etoiles": etoiles
            })
    
    return temoignages

ARTICLES_CARROUSEL_DEFAULT = []


def parse_carrousel_input(carrousel_str: str) -> List[Dict]:
    """Parse le carrousel au format URL|titre|date|categorie|url_image;..."""
    if not carrousel_str.strip():
        return ARTICLES_CARROUSEL_DEFAULT
    
    articles = []
    entries = carrousel_str.strip().split(";")
    
    for entry in entries:
        parts = entry.strip().split("|")
        if len(parts) >= 5:
            articles.append({
                "url": parts[0].strip(),
                "titre": parts[1].strip(),
                "date": parts[2].strip(),
                "categorie": parts[3].strip(),
                "image": parts[4].strip()
            })
        elif len(parts) == 4:
            # Fallback sans image
            articles.append({
                "url": parts[0].strip(),
                "titre": parts[1].strip(),
                "date": parts[2].strip(),
                "categorie": parts[3].strip(),
                "image": ""
            })
    
    return articles


# ============================================
# CUSTOM CSS STREAMLIT
# ============================================

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&display=swap');
    .stApp { background: linear-gradient(135deg, #fafafa 0%, #f0f4f8 100%); font-family: 'Poppins', sans-serif; }
    #MainMenu, footer, header { visibility: hidden; }
    .main .block-container { max-width: 1200px; padding-top: 2rem; padding-bottom: 2rem; }
    .app-header { text-align: center; padding: 2rem 0 3rem 0; }
    .app-header h1 { font-size: 2.5rem; font-weight: 700; background: linear-gradient(135deg, #FB793E 0%, #004AF3 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; margin-bottom: 0.5rem; }
    .app-header p { color: #64748b; font-size: 1.1rem; }
    .card { background: white; border-radius: 20px; padding: 2rem; box-shadow: 0 4px 20px rgba(0, 0, 0, 0.05); margin-bottom: 1.5rem; border: 1px solid rgba(0, 0, 0, 0.05); }
    .card-title { font-size: 0.85rem; font-weight: 600; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 1rem; }
    .stTextInput > div > div > input, .stTextArea > div > div > textarea { border-radius: 12px !important; border: 2px solid #e2e8f0 !important; font-family: 'Poppins', sans-serif !important; }
    .stTextInput > div > div > input:focus, .stTextArea > div > div > textarea:focus { border-color: #FB793E !important; box-shadow: 0 0 0 3px rgba(251, 121, 62, 0.1) !important; }
    .stButton > button { width: 100%; background: linear-gradient(135deg, #FB793E 0%, #e55a1f 100%); color: white; border: none; border-radius: 12px; padding: 0.875rem 2rem; font-size: 1rem; font-weight: 600; font-family: 'Poppins', sans-serif; transition: all 0.3s ease; box-shadow: 0 4px 15px rgba(251, 121, 62, 0.3); }
    .stButton > button:hover { transform: translateY(-2px); box-shadow: 0 6px 20px rgba(251, 121, 62, 0.4); }
    .step-indicator { display: flex; align-items: center; gap: 0.75rem; padding: 1rem; background: #FEF3EE; border-radius: 12px; margin-bottom: 0.75rem; border-left: 4px solid #FB793E; }
    .step-dot { width: 8px; height: 8px; border-radius: 50%; background: #FB793E; animation: pulse 1.5s infinite; }
    @keyframes pulse { 0%, 100% { opacity: 1; transform: scale(1); } 50% { opacity: 0.5; transform: scale(0.8); } }
    .step-text { color: #475569; font-size: 0.95rem; font-weight: 500; }
</style>
""", unsafe_allow_html=True)


# ============================================
# FONCTIONS UTILITAIRES
# ============================================

def search_serper(query: str, api_key: str, num_results: int = 10) -> Tuple[List[Dict], List[str]]:
    """Recherche SERP via Serper.dev + récupère PAA"""
    url = "https://google.serper.dev/search"
    headers = {"X-API-KEY": api_key, "Content-Type": "application/json"}
    payload = {"q": query, "gl": "fr", "hl": "fr", "num": num_results}
    
    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()
    data = response.json()
    
    results = []
    for item in data.get("organic", [])[:num_results]:
        results.append({
            "title": item.get("title", ""),
            "url": item.get("link", ""),
            "snippet": item.get("snippet", "")
        })
    
    paa = [item.get("question", "") for item in data.get("peopleAlsoAsk", [])[:5]]
    return results, paa


def fetch_content_jina(url: str) -> str:
    """Récupère le contenu via Jina Reader"""
    try:
        response = requests.get(f"https://r.jina.ai/{url}", headers={"Accept": "text/plain"}, timeout=30)
        response.raise_for_status()
        return response.text[:15000]
    except Exception as e:
        return f"Erreur: {str(e)}"


def generate_temoignages_html(temoignages: List[Dict]) -> str:
    """Génère le HTML des témoignages"""
    html = ""
    for t in temoignages:
        html += f'''
                                <div class="avis-card">
                                    <div class="stars">{t['etoiles']}</div>
                                    <p class="avis-txt">{t['texte']}</p>
                                    <div class="avis-user">
                                        <div class="user-info">
                                            <div class="user-name">{t['prenom']}, {t['date']}, sur Ootravaux</div>
                                        </div>
                                    </div>
                                </div>'''
    return html


def generate_carrousel_html(articles: List[Dict]) -> str:
    """Génère le HTML du carrousel d'articles"""
    html = ""
    for a in articles:
        html += f'''
                                    <div class="articles-vignette">
                                        <div class="articles-vignette-img-wrap">
                                            <a class="carousel-link" href="{a['url']}" target="_blank">
                                                <img src="{a['image']}" alt="{a['titre']}" class="articles-vignette-img">
                                            </a>
                                        </div>
                                        <div class="articles-vignette-meta">{a['categorie']}</div>
                                        <div class="articles-vignette-date">{a['date']}</div>
                                        <div class="articles-vignette-title">
                                            <a class="carousel-link" href="{a['url']}" target="_blank">{a['titre']}</a>
                                        </div>
                                        <a href="{a['url']}" class="articles-vignette-link carousel-link" target="_blank">Lire la suite <span class="arrow">›</span></a>
                                    </div>'''
    return html


def detect_breadcrumb_category(keyword: str) -> dict:
    """Détecte la catégorie pour le breadcrumb basé sur le mot-clé"""
    keyword_lower = keyword.lower()
    
    categories = {
        "façad": {"cat": "Façade", "cat_url": "/prestation/ravalement-de-facades", "parent": "Trouver votre artisan", "parent_url": "/prestation"},
        "ravalement": {"cat": "Ravalement de façade", "cat_url": "/prestation/ravalement-de-facades", "parent": "Trouver votre artisan", "parent_url": "/prestation"},
        "plomb": {"cat": "Plombier chauffagiste", "cat_url": "/prestation/plombier-chauffagiste", "parent": "Trouver votre artisan", "parent_url": "/prestation"},
        "chauffag": {"cat": "Plombier chauffagiste", "cat_url": "/prestation/plombier-chauffagiste", "parent": "Trouver votre artisan", "parent_url": "/prestation"},
        "couv": {"cat": "Couvreur", "cat_url": "/prestation/entreprises-de-couverture", "parent": "Trouver votre artisan", "parent_url": "/prestation"},
        "toitur": {"cat": "Toiture", "cat_url": "/toiture-couverture", "parent": "Toiture", "parent_url": "/toiture-couverture"},
        "électric": {"cat": "Électricien", "cat_url": "/prestation/electricien", "parent": "Trouver votre artisan", "parent_url": "/prestation"},
        "peintr": {"cat": "Peintre en bâtiment", "cat_url": "/prestation/peintre-batiment", "parent": "Trouver votre artisan", "parent_url": "/prestation"},
        "maçon": {"cat": "Maçonnerie", "cat_url": "/prestation/entreprise-maconnerie", "parent": "Trouver votre artisan", "parent_url": "/prestation"},
        "isol": {"cat": "Isolation", "cat_url": "/isolation", "parent": "Isolation", "parent_url": "/isolation"},
        "pompe à chaleur": {"cat": "Pompe à chaleur", "cat_url": "/prestation/pompes-a-chaleur", "parent": "Trouver votre artisan", "parent_url": "/prestation"},
    }
    
    for key, data in categories.items():
        if key in keyword_lower:
            return data
    
    return {"cat": "Trouver votre artisan", "cat_url": "/prestation", "parent": "Trouver votre artisan", "parent_url": "/prestation"}


# ============================================
# AGENT 1 : GÉNÉRATION DU CONTENU SEO
# ============================================

def agent1_generate_content(
    client: anthropic.Anthropic,
    keyword: str,
    ytg_keywords: str,
    persona: str,
    sources: List[Dict],
    contents: List[str],
    paa_questions: List[str],
    blocklist: str = "",
    mots_interdits: str = ""
) -> dict:
    """Agent 1 : Génère le contenu SEO structuré"""
    
    sources_context = ""
    for i, (source, content) in enumerate(zip(sources, contents), 1):
        sources_context += f"\n--- SOURCE {i} ---\nTitre: {source['title']}\nURL: {source['url']}\nContenu:\n{content[:6000]}\n"
    
    paa_str = "\n".join([f"- {q}" for q in paa_questions]) if paa_questions else "Aucune"
    
    # Construire la liste des mots interdits
    mots_interdits_list = ""
    if mots_interdits.strip():
        mots_interdits_list = "\n".join([f"❌ \"{mot.strip()}\"" for mot in mots_interdits.strip().split("\n") if mot.strip()])
    
    system_prompt = f"""Tu es un rédacteur SEO expert pour Ootravaux, plateforme de mise en relation avec des artisans (21 000 pros, service gratuit, jusqu'à 4 devis).

## ⛔⛔⛔ MOTS ET EXPRESSIONS STRICTEMENT INTERDITS ⛔⛔⛔
## CONTRAINTE LÉGALE ABSOLUE - NE JAMAIS UTILISER CES TERMES ##

{mots_interdits_list if mots_interdits_list else "Aucun mot interdit spécifié"}

ÉGALEMENT INTERDITS PAR DÉFAUT :
❌ "artisan de confiance", "artisans qualifiés", "meilleurs artisans"
❌ "devis gratuits" → utiliser "devis gratuit" ou "devis sans engagement"
❌ "obtenez des devis" → utiliser "demandez" ou "recevez"
❌ Toute mention de sélection/vérification/certification par Ootravaux
❌ "nos conseillers", "appel conseiller"
❌ "Il est important de noter", "Dans cet article", "N'hésitez pas"

⚠️ VÉRIFICATION OBLIGATOIRE : Avant de générer, vérifie qu'AUCUN de ces termes n'apparaît dans ta réponse.

## PERSONA / TON
{persona}

## MOTS-CLÉS YTG À INTÉGRER OBLIGATOIREMENT
{ytg_keywords}

RÈGLE CRITIQUE : Intègre TOUS ces mots-clés, chacun plusieurs fois (autant que nécessaire par rapport aux concurrents), répartis naturellement. Fluidité > bourrage.

## QUESTIONS PAA
{paa_str}

## BLOCKLIST
{blocklist if blocklist else "Aucun"}

## STRUCTURE DE SORTIE OBLIGATOIRE (JSON)

Tu dois retourner un JSON valide avec cette structure exacte :
{{
    "h1": "Titre H1 accrocheur avec mot-clé + localisation",
    "intro": "2-3 phrases d'accroche percutantes",
    "first_h2_section": "HTML du premier H2 avec son paragraphe intro et ses H3 (contenu complet)",
    "main_content": "HTML des sections H2/H3 suivantes (milieu de page)",
    "remaining_content": "HTML des sections restantes avant la FAQ",
    "pourquoi_ootravaux": "HTML de la section Pourquoi choisir Ootravaux",
    "faq": [
        {{"question": "Question 1 ?", "answer": "Réponse 1"}},
        {{"question": "Question 2 ?", "answer": "Réponse 2"}},
        {{"question": "Question 3 ?", "answer": "Réponse 3"}}
    ]
}}

## RÈGLES HTML
- Chaque H2 DOIT être suivi d'un paragraphe (2-3 phrases) AVANT tout H3
- Max 3-4 H3 par H2, avec contenu substantiel (3-4 phrases min)
- Les questions en titre DOIVENT finir par "?"
- Tableaux de prix si pertinent : <table class="table table-striped">
- Listes : <ul><li>...</li></ul>
- Pas de balises <h1> dans le contenu (juste H2 et H3)

IMPORTANT : Retourne UNIQUEMENT le JSON, sans texte avant ni après.
RAPPEL FINAL : Vérifie qu'AUCUN mot interdit n'apparaît dans ton contenu."""

    user_prompt = f"""Analyse ces {len(sources)} sources sur "{keyword}" et génère le contenu SEO structuré.

{sources_context}

Génère le JSON avec tout le contenu SEO optimisé pour une page locale Ootravaux."""

    response = client.messages.create(
        model="claude-opus-4-5-20251101",
        max_tokens=8000,
        temperature=0.7,
        messages=[{"role": "user", "content": user_prompt}],
        system=system_prompt
    )
    
    # Parser le JSON
    response_text = response.content[0].text.strip()
    
    # Nettoyer si wrapped dans ```json
    if response_text.startswith("```"):
        response_text = re.sub(r'^```json?\n?', '', response_text)
        response_text = re.sub(r'\n?```$', '', response_text)
    
    try:
        return json.loads(response_text)
    except json.JSONDecodeError:
        # Fallback : retourner le texte brut comme contenu
        return {
            "h1": keyword.title(),
            "intro": "Trouvez rapidement un professionnel qualifié près de chez vous.",
            "first_h2_section": response_text,
            "main_content": "",
            "remaining_content": "",
            "pourquoi_ootravaux": "<h2>Pourquoi choisir Ootravaux ?</h2><p>Ootravaux vous met en relation avec des professionnels de votre région. Service gratuit, jusqu'à 4 devis sans engagement.</p>",
            "faq": []
        }


# ============================================
# AGENT 2 : ASSEMBLAGE FINAL
# ============================================

def agent2_assemble_page(
    client: anthropic.Anthropic,
    content: dict,
    keyword: str,
    url_cta: str,
    url_image: str,
    carrousel_articles: List[Dict],
    temoignages_list: List[Dict]
) -> str:
    """Agent 2 : Assemble le contenu dans le template"""
    
    # Générer les éléments fixes
    temoignages_html = generate_temoignages_html(temoignages_list)
    carrousel_html = generate_carrousel_html(carrousel_articles)
    breadcrumb_data = detect_breadcrumb_category(keyword)
    
    # Construire le breadcrumb HTML
    breadcrumb_html = f'''<a href="/">Ootravaux</a>
                        <span class="breadcrumb-separator">›</span>
                        <a href="{breadcrumb_data['parent_url']}">{breadcrumb_data['parent']}</a>
                        <span class="breadcrumb-separator">›</span>
                        <a href="{breadcrumb_data['cat_url']}">{breadcrumb_data['cat']}</a>
                        <span class="breadcrumb-separator">›</span>
                        <span>{content.get('h1', keyword.title())}</span>'''
    
    # Générer le HTML de la FAQ
    faq_html = ""
    for item in content.get("faq", []):
        if isinstance(item, dict):
            faq_html += f'''
                                <div class="faq-item">
                                    <div class="faq-question">{item.get('question', '')}</div>
                                    <div class="faq-answer">{item.get('answer', '')}</div>
                                </div>'''
    
    # Image par défaut si non fournie
    if not url_image:
        url_image = "https://www.ootravaux.fr/sites/ootravaux/storage/files/2025-09/facade-paris.jpg"
    
    # Remplacer les placeholders dans le template
    final_html = TEMPLATE_HTML
    final_html = final_html.replace("{{PAGE_TITLE}}", content.get("h1", keyword.title()))
    final_html = final_html.replace("{{BREADCRUMB}}", breadcrumb_html)
    final_html = final_html.replace("{{IMAGE_URL}}", url_image)
    final_html = final_html.replace("{{IMAGE_ALT}}", content.get("h1", keyword))
    final_html = final_html.replace("{{H1}}", content.get("h1", keyword.title()))
    final_html = final_html.replace("{{INTRO}}", content.get("intro", ""))
    final_html = final_html.replace("{{URL_CTA}}", url_cta)
    final_html = final_html.replace("{{FIRST_H2_SECTION}}", content.get("first_h2_section", ""))
    final_html = final_html.replace("{{TEMOIGNAGES}}", temoignages_html)
    final_html = final_html.replace("{{MAIN_CONTENT}}", content.get("main_content", ""))
    final_html = final_html.replace("{{REMAINING_CONTENT}}", content.get("remaining_content", ""))
    final_html = final_html.replace("{{CARROUSEL}}", carrousel_html)
    final_html = final_html.replace("{{POURQUOI_OOTRAVAUX}}", content.get("pourquoi_ootravaux", ""))
    final_html = final_html.replace("{{FAQ}}", faq_html)
    
    # Nettoyage final avec Agent 2 pour vérifier/corriger le HTML
    system_prompt = """Tu es un expert HTML. Vérifie et corrige ce HTML si nécessaire :
- Toutes les balises doivent être correctement fermées
- Pas de balises orphelines
- HTML valide et bien formé

Si le HTML est correct, retourne-le tel quel.
Si des corrections sont nécessaires, fais-les et retourne le HTML corrigé.

IMPORTANT : Retourne UNIQUEMENT le HTML, rien d'autre."""

    response = client.messages.create(
        model="claude-opus-4-5-20251101",
        max_tokens=16000,
        temperature=0.2,
        messages=[{"role": "user", "content": f"Vérifie et retourne ce HTML :\n\n{final_html}"}],
        system=system_prompt
    )
    
    return response.content[0].text.strip()


# ============================================
# INTERFACE STREAMLIT
# ============================================

# Header
st.markdown("""
<div class="app-header">
    <h1>🏠 Ootravaux Local Page Builder</h1>
    <p>Génère des pages locales SEO complètes pour Ootravaux</p>
</div>
""", unsafe_allow_html=True)

# Configuration API
with st.expander("⚙️ Configuration API", expanded=not st.session_state.get('api_configured', False)):
    col1, col2 = st.columns(2)
    with col1:
        anthropic_key = st.text_input("Clé API Anthropic", type="password", value=st.session_state.get('anthropic_key', ''))
    with col2:
        serper_key = st.text_input("Clé API Serper", type="password", value=st.session_state.get('serper_key', ''))
    
    if anthropic_key and serper_key:
        st.session_state['anthropic_key'] = anthropic_key
        st.session_state['serper_key'] = serper_key
        st.session_state['api_configured'] = True

# Formulaire principal
col_left, col_right = st.columns([2, 1])

with col_left:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="card-title">📝 Paramètres de la page</div>', unsafe_allow_html=True)
    
    keyword = st.text_input("Mot-clé principal", placeholder="Ex: façadier paris, plombier chauffagiste lille...")
    
    ytg_keywords = st.text_area(
        "Mots-clés YTG",
        placeholder="Un mot-clé par ligne...\nEx:\nfaçadier paris\nprix ravalement façade\nentreprise ravalement paris",
        height=150
    )
    
    persona = st.text_area(
        "Persona / Ton",
        value="Expert travaux accessible et rassurant. Ton professionnel mais pas froid. Vocabulaire précis sans jargon excessif. Focus sur l'aide à la décision et la mise en relation.",
        height=100
    )
    
    mots_interdits = st.text_area(
        "⛔ Mots et expressions INTERDITS",
        placeholder="Un mot ou expression par ligne\n\nExemple :\nartisans qualifiés\nartisan de confiance\nmeilleurs artisans\ndevis gratuits",
        height=120,
        help="IMPORTANT : Ces termes ne doivent JAMAIS apparaître dans le contenu généré (contraintes légales)"
    )
    
    st.markdown('</div>', unsafe_allow_html=True)

with col_right:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="card-title">🔧 Options</div>', unsafe_allow_html=True)
    
    url_cta = st.text_input("URL CTA devis", placeholder="https://www.ootravaux.fr/trouverunartisan-...")
    url_image = st.text_input("URL image principale (optionnel)", placeholder="https://...")
    num_sources = st.slider("Sources à analyser", min_value=3, max_value=10, value=5)
    blocklist = st.text_input("Sites à exclure (optionnel)", placeholder="concurrent1.fr, concurrent2.com")
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="card-title">📚 Carrousel articles liés</div>', unsafe_allow_html=True)
    
    carrousel_input = st.text_area(
        "Articles du carrousel",
        placeholder="Format : URL|titre|date|catégorie|url_image\nSépare chaque article par ;\n\nExemple :\nhttps://site.fr/article1|Mon titre|15 janvier 2025|Catégorie|https://site.fr/image1.jpg;https://site.fr/article2|Autre titre|3 décembre 2024|Catégorie 2|https://site.fr/image2.jpg",
        height=120,
        help="3 articles recommandés pour le carrousel"
    )
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="card-title">💬 Témoignages</div>', unsafe_allow_html=True)
    
    temoignages_input = st.text_area(
        "Témoignages clients",
        placeholder="Format : Prénom|texte|date|étoiles (4 ou 5)\nSépare chaque témoignage par ;\n\nExemple :\nNadia|Très satisfaite du service !|20/10/2025|5;Marc|Rappelé en 10 min|25/11/2025|4",
        height=100,
        help="3 témoignages recommandés"
    )
    
    st.markdown('</div>', unsafe_allow_html=True)

# Bouton génération
generate_button = st.button("🚀 Générer la page complète", use_container_width=True)

# ============================================
# LOGIQUE DE GÉNÉRATION
# ============================================

if generate_button:
    if not st.session_state.get('anthropic_key') or not st.session_state.get('serper_key'):
        st.error("⚠️ Configure d'abord tes clés API")
    elif not keyword:
        st.warning("💡 Entre un mot-clé principal")
    elif not ytg_keywords.strip():
        st.warning("💡 Ajoute des mots-clés YTG")
    elif not url_cta.strip():
        st.warning("💡 Ajoute l'URL du CTA devis")
    else:
        client = anthropic.Anthropic(api_key=st.session_state['anthropic_key'])
        progress = st.container()
        
        # Étape 1 : Recherche SERP
        with progress:
            st.markdown('<div class="step-indicator"><div class="step-dot"></div><span class="step-text">🔍 Recherche SERP + PAA...</span></div>', unsafe_allow_html=True)
            try:
                sources, paa = search_serper(keyword, st.session_state['serper_key'], num_sources)
            except Exception as e:
                st.error(f"Erreur recherche : {e}")
                st.stop()
        
        # Étape 2 : Fetch contenus
        progress.empty()
        with progress:
            st.markdown(f'<div class="step-indicator"><div class="step-dot"></div><span class="step-text">📄 Analyse de {len(sources)} sources...</span></div>', unsafe_allow_html=True)
            bar = st.progress(0)
            contents = []
            for i, src in enumerate(sources):
                contents.append(fetch_content_jina(src['url']))
                bar.progress((i + 1) / len(sources))
        
        # Étape 3 : Agent 1
        progress.empty()
        with progress:
            st.markdown('<div class="step-indicator"><div class="step-dot"></div><span class="step-text">✍️ Agent 1 : Génération contenu SEO (Opus 4.5, temp=0.7)...</span></div>', unsafe_allow_html=True)
            try:
                content = agent1_generate_content(client, keyword, ytg_keywords, persona, sources, contents, paa, blocklist, mots_interdits)
            except Exception as e:
                st.error(f"Erreur Agent 1 : {e}")
                st.stop()
        
        # Étape 4 : Agent 2
        progress.empty()
        with progress:
            st.markdown('<div class="step-indicator"><div class="step-dot"></div><span class="step-text">🎨 Agent 2 : Assemblage template (Opus 4.5, temp=0.2)...</span></div>', unsafe_allow_html=True)
            try:
                carrousel_articles = parse_carrousel_input(carrousel_input)
                temoignages_list = parse_temoignages_input(temoignages_input)
                final_html = agent2_assemble_page(client, content, keyword, url_cta, url_image, carrousel_articles, temoignages_list)
            except Exception as e:
                st.error(f"Erreur Agent 2 : {e}")
                st.stop()
        
        # Résultat
        progress.empty()
        st.markdown('<div style="background:#d4edda;border-radius:12px;padding:1rem;margin-bottom:1rem;border-left:4px solid #28a745;"><span style="font-weight:600;color:#155724;">✅ Page générée avec succès !</span></div>', unsafe_allow_html=True)
        
        tab1, tab2, tab3 = st.tabs(["📄 HTML Final", "📊 Contenu structuré (Agent 1)", "🔍 Sources"])
        
        with tab1:
            st.download_button("⬇️ Télécharger HTML", final_html, f"ootravaux-{keyword.replace(' ', '-')}.html", "text/html")
            st.code(final_html, language="html")
        
        with tab2:
            st.json(content)
        
        with tab3:
            for i, src in enumerate(sources, 1):
                st.markdown(f"{i}. [{src['title']}]({src['url']})")
            if paa:
                st.markdown("**Questions PAA :**")
                for q in paa:
                    st.markdown(f"- {q}")

# Footer
st.markdown('<div style="text-align:center;margin-top:3rem;color:#94a3b8;font-size:0.85rem;">Propulsé par Claude Opus 4.5 & Serper • Made for Ootravaux 🏠</div>', unsafe_allow_html=True)
