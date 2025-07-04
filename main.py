"""
PROGRAM ANALISIS ARTIKEL SEO UNTUK MULTI-KEYWORD

Struktur Program:
1. Konfigurasi - Pengaturan dasar program
2. Fungsi Pencarian - Mencari artikel di Google
3. Fungsi Ekstraksi - Mengambil konten dari artikel
4. Fungsi Analisis - Menganalisis konten untuk SEO
5. Fungsi Utilitas - Bantuan untuk pemrosesan teks
6. Fungsi Output - Menyimpan hasil analisis
"""

from newspaper import Article
import requests
from bs4 import BeautifulSoup
from readability import Document
from urllib.parse import urlparse, urljoin
import re
import json
from datetime import datetime
import os
from dotenv import load_dotenv

# ========================
# 1. KONFIGURASI PROGRAM
# ========================
# Memuat file .env
load_dotenv()

# Mengambil data dari .env
api_key = os.getenv("API_KEY")
api_url = os.getenv("API_URL")

# USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'

# ========================
# 2. FUNGSI PENCARIAN
# ========================

def cari_artikel_di_google(keyword):
    """
    Mencari artikel di Google berdasarkan keyword.
    Mengembalikan daftar hasil dan pesan error (jika ada).
    """
    try:
        # headers = {'User-Agent': USER_AGENT}
        params = {
            'q': keyword,
            'location': "Indonesia",
            'hl': "id",
            'api_key': api_key,
            'engine': 'google',
            'num': 6  # Ambil 2 hasil untuk cadangan
        }
        
        response = requests.get(api_url, params=params, timeout=15)
        response.raise_for_status()
        return response.json().get('organic_results', []), None
    except Exception as e:
        return None, f"Error saat mencari artikel: {str(e)}"

# ========================
# 3. FUNGSI EKSTRAKSI KONTEN
# ========================

def ekstrak_gambar_konten(url):
    """Mengambil gambar dari konten artikel, tidak termasuk logo/iklan"""
    try:
        response = requests.get(url, timeout=20)
        doc = Document(response.text)
        clean_html = doc.summary()
        
        soup = BeautifulSoup(clean_html, 'html.parser')
        return [
            img['src'] for img in soup.find_all('img')
            if 'src' in img.attrs
            and not any(x in img.get('class', []) for x in ['logo', 'icon', 'ad'])
            and not any(x in img['src'].lower() for x in ['logo', 'icon', 'spacer'])
        ]
    except Exception as e:
        print(f"Error mengambil gambar: {str(e)}")
        return []

def ekstrak_heading_artikel(url):
    """Mengambil heading (h2 dan h3) dari artikel"""
    try:
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Cari bagian dengan paragraf terbanyak (asumsi ini konten utama)
        konten_utama = max(
            soup.find_all(), 
            key=lambda x: len(x.find_all('p', recursive=False))
        )
        
        h2_list = [h2.get_text(strip=True) for h2 in konten_utama.find_all('h2')]
        h3_list = [h3.get_text(strip=True) for h3 in konten_utama.find_all('h3')]
        
        return {
            'h2': h2_list,
            'h3': h3_list,
            'jumlah_h2': len(h2_list),
            'jumlah_h3': len(h3_list)
        }
    except Exception as e:
        print(f"Error mengambil heading: {str(e)}")
        return {
            'h2': [],
            'h3': [],
            'jumlah_h2': 0,
            'jumlah_h3': 0
        }

def ekstrak_meta_description(soup):
    """Mengambil meta description dari HTML"""
    meta = soup.find('meta', attrs={'name': 'description'})
    return meta.get('content', '') if meta else ''

# ========================
# 4. FUNGSI ANALISIS SEO
# ========================

def analisis_referensi(text):
    """Menghitung jumlah referensi/buku yang disebutkan dalam artikel"""
    # pola_referensi = [r'referensi', r'sumber:', r'bibliografi', r'daftar pustaka', r'literatur', r'buku']
    pola_referensi = [r"\b(mengutip(?: dari)?|dikutip(?: dari)?|dilansir(?: dari)?|lansir|menurut|dihimpun dari|berdasarkan data dari)\s+(situs resmi|buku|jurnal)?\b"]
    kalimat = re.split(r'[\.\n]', text)
    
    hasil_referensi = []
    for k in kalimat:
        if any(re.search(p, k.lower()) for p in pola_referensi):
            hasil_referensi.append(k.strip())
    
    return {
        'jumlah': len(hasil_referensi),
        'daftar_kalimat': hasil_referensi
    }

def hitung_kepadatan_keyword(teks_bersih, keyword_bersih):
    """
    Menghitung seberapa sering keyword muncul dalam teks (dalam persen).
    Contoh: keyword muncul 5 kali dari 1000 kata = 0.5%
    """
    if not teks_bersih or not keyword_bersih:
        return 0.0

    semua_kata = teks_bersih.split()
    total_kata = len(semua_kata)

    kata_keyword = keyword_bersih.split()
    jumlah_kemunculan = 0

    for i in range(len(semua_kata) - len(kata_keyword) + 1):
        if semua_kata[i:i+len(kata_keyword)] == kata_keyword:
            jumlah_kemunculan += 1

    return round((jumlah_kemunculan / total_kata) * 100, 2) if total_kata > 0 else 0.0

# ========================
# 5. FUNGSI UTILITAS
# ========================

def bersihkan_teks(text):
    """Mengubah teks menjadi huruf kecil dan menghilangkan tanda baca"""
    text = text.lower()
    text = re.sub(r'[^\w\s]', '', text)  # Hapus tanda baca
    text = re.sub(r'\s+', ' ', text).strip()  # Hapus spasi berlebih
    return text

def cari_urutan_keyword(teks_bersih, keyword_bersih):
    """
    Mencari posisi pertama keyword dalam teks.
    Hasilnya urutan kata keberapa (dimulai dari 1).
    """
    kata = teks_bersih.split()
    kata_keyword = keyword_bersih.split()
    
    for i in range(len(kata) - len(kata_keyword) + 1):
        if kata[i:i+len(kata_keyword)] == kata_keyword:
            return i + 1  # +1 karena index dimulai dari 1
    return -1

# ========================
# 6. FUNGSI ANALISIS UTAMA
# ========================

def analisis_artikel_seo(url, keyword):
    """
    Fungsi utama untuk menganalisis artikel dari segi SEO.
    Mengembalikan semua data yang relevan untuk analisis SEO.
    """
    hasil = {
        'url': url,
        'keyword': keyword,
        'error': None,
        'judul': '',
        'jumlah_kata_judul': 0,
        'posisi_keyword_di_judul': -1,
        'meta_description': '',
        'jumlah_kata_meta': 0,
        'teks': '',
        'jumlah_kata_teks': 0,
        'kepadatan_keyword': 0,
        'posisi_keyword_pertama': -1,
        'link_internal': [],
        'jumlah_link_internal': 0,
        'heading_h2': [],
        'heading_h3': [],
        'jumlah_h2': 0,
        'jumlah_h3': 0,
        'gambar': [],
        'jumlah_gambar': 0,
        'jumlah_referensi': 0,
        'penulis': [],
        'tanggal_publikasi': None,
        'gambar_utama': None
    }
    
    try:
        # Persiapan artikel
        artikel = Article(url, language='id')
        artikel.download()
        artikel.parse()
        
        # Data dasar artikel
        hasil['judul'] = artikel.title
        hasil['jumlah_kata_judul'] = len(artikel.title.split()) if artikel.title else 0
        hasil['penulis'] = artikel.authors
        hasil['tanggal_publikasi'] = str(artikel.publish_date) if artikel.publish_date else None
        hasil['teks'] = artikel.text
        hasil['jumlah_kata_teks'] = len(artikel.text.split())
        hasil['gambar_utama'] = artikel.top_image
        
        # Analisis keyword dalam judul
        judul_bersih = bersihkan_teks(artikel.title) if artikel.title else ""
        keyword_bersih = bersihkan_teks(keyword)
        
        if judul_bersih and keyword_bersih in judul_bersih:
            hasil['posisi_keyword_di_judul'] = cari_urutan_keyword(judul_bersih, keyword_bersih)
        
        # Meta description
        soup = BeautifulSoup(artikel.html, 'html.parser')
        hasil['meta_description'] = ekstrak_meta_description(soup)
        hasil['jumlah_kata_meta'] = len(hasil['meta_description'].split())
        
        # Analisis keyword dalam teks
        teks_bersih = bersihkan_teks(artikel.text)
        hasil['kepadatan_keyword'] = hitung_kepadatan_keyword(teks_bersih, keyword_bersih)
        hasil['posisi_keyword_pertama'] = cari_urutan_keyword(teks_bersih, keyword_bersih)
        
        # Link internal
        domain = urlparse(url).netloc
        link_internal = set()
        
        for link in soup.find_all('a', href=True):
            href = link['href']
            if href.startswith(('#', 'javascript:')):
                continue
                
            full_url = urljoin(url, href)
            if urlparse(full_url).netloc == domain:
                link_internal.add(full_url)
        
        hasil['link_internal'] = list(link_internal)
        hasil['jumlah_link_internal'] = len(link_internal)
        
        # Heading artikel
        heading = ekstrak_heading_artikel(url)
        hasil['heading_h2'] = heading['h2']
        hasil['heading_h3'] = heading['h3']
        hasil['jumlah_h2'] = heading['jumlah_h2']
        hasil['jumlah_h3'] = heading['jumlah_h3']
        
        # Gambar konten
        hasil['gambar'] = ekstrak_gambar_konten(url)
        if hasil['gambar_utama'] and hasil['gambar_utama'] not in hasil['gambar']:
            hasil['gambar'].insert(0, hasil['gambar_utama'])
        hasil['jumlah_gambar'] = len(hasil['gambar'])
        
        # Referensi
        hasil_referensi = analisis_referensi(artikel.text)
        hasil['jumlah_referensi'] = hasil_referensi['jumlah']
        
    except Exception as e:
        hasil['error'] = f"Gagal menganalisis artikel: {str(e)}"
    
    return hasil

# ========================
# 7. FUNGSI UTAMA & OUTPUT
# ========================

def jalankan_analisis(keywords):
    """Fungsi utama untuk menjalankan seluruh proses analisis"""
    print("=== PROGRAM ANALISIS ARTIKEL SEO ===")
    
    hasil_akhir = {
        'tanggal_analisis': str(datetime.now()),
        'total_keyword': len(keywords),
        'hasil': []
    }
    
    for keyword in keywords:
        print(f"\nMencari artikel untuk keyword: '{keyword}'...")
        hasil_pencarian, error = cari_artikel_di_google(keyword)
        
        if error or not hasil_pencarian:
            print(error or f"❌ Tidak ditemukan artikel untuk keyword: {keyword}")
            hasil_akhir['hasil'].append({
                'keyword': keyword,
                'status': 'tidak_ditemukan' if not error else 'error',
                'pesan_error': error if error else None
            })
            continue
        
        print(f"Ditemukan {len(hasil_pencarian)} artikel teratas")
        
        hasil_keyword = {
            'keyword': keyword,
            'status': 'sukses',
            'artikel': []
        }
        
        for idx, artikel in enumerate(hasil_pencarian, 1):
            print(f"\Menganalisis artikel #{idx}: {artikel.get('title', 'Tanpa judul')[:50]}...")
            print(f"   URL: {artikel.get('link')}")
            
            data_artikel = analisis_artikel_seo(artikel['link'], keyword)
            
            hasil_keyword['artikel'].append({
                'peringkat_pencarian': idx,
                'judul_pencarian': artikel.get('title'),
                'analisis': data_artikel
            })
            
            if not data_artikel.get('error'):
                print(f"   Judul: {data_artikel.get('judul', 'Tidak ada judul')[:50]}...")
                print(f"   Posisi keyword dalam judul: {data_artikel['posisi_keyword_di_judul']}")
                print(f"   Posisi pertama keyword dalam teks: {data_artikel['posisi_keyword_pertama']}")
                print(f"   Jumlah kata: {data_artikel['jumlah_kata_teks']}")
                print(f"   Kepadatan keyword: {data_artikel['kepadatan_keyword']}%")
                print(f"   Jumlah heading H2: {data_artikel['jumlah_h2']}")
                print(f"   Jumlah heading H3: {data_artikel['jumlah_h3']}")
                print(f"   Jumlah gambar konten: {data_artikel['jumlah_gambar']}")
        
        hasil_akhir['hasil'].append(hasil_keyword)
    
    return hasil_akhir

def simpan_hasil(hasil_analisis, nama_file="hasil_analisis_seo.json"):
    """Menyimpan hasil analisis ke file JSON"""
    with open(nama_file, 'w', encoding='utf-8') as f:
        json.dump(hasil_analisis, f, indent=2, ensure_ascii=False)
    print(f"\n🎉 Hasil analisis disimpan di: {nama_file}")

if __name__ == "__main__":
    # Daftar keyword yang akan dianalisis
    daftar_keyword = keywords = [
        "cara membuat website",
        ]


    
    # Jalankan analisis
    hasil = jalankan_analisis(daftar_keyword)
    
    # Simpan hasil
    simpan_hasil(hasil)
    
    # Tampilkan ringkasan
    print(f"\nRingkasan Analisis:")
    print(f"Total keyword: {len(daftar_keyword)}")
    print(f"Total artikel dianalisis: {sum(len(k['artikel']) for k in hasil['hasil'] if 'artikel' in k)}")