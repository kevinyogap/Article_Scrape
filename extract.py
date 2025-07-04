import json
import pandas as pd

def json_to_excel(json_file, excel_file):
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    rows = []
    for keyword_data in data.get('hasil', []):
        keyword = keyword_data.get('keyword', '')
        for artikel in keyword_data.get('artikel', []):
            posisi = artikel.get('peringkat_pencarian', '')
            analisis = artikel.get('analisis', {})
            # Skip jika tidak ada analisis atau error
            if not analisis or analisis.get('error'):
                continue
            meta_desc = analisis.get('meta_description', '')
            row = {
                'Keyword': keyword,
                'Position Google': posisi,
                'Url': analisis.get('url', ''),
                'Title': analisis.get('judul', ''),
                'Title Word Count': analisis.get('jumlah_kata_judul', 0),
                'Meta Description': meta_desc,
                'meta_desc_word_count': len(meta_desc.split()),
                'Content Word Count': analisis.get('jumlah_kata_teks', 0),
                'Keyword Density': analisis.get('kepadatan_keyword', 0),
                'Internal Links': analisis.get('jumlah_link_internal', 0),
                'H2 Count': analisis.get('jumlah_h2', 0),
                'H3 Count': analisis.get('jumlah_h3', 0),
                'Image Count': analisis.get('jumlah_gambar', 0),
                'Book Source Count': analisis.get('jumlah_referensi', 0),
                'first_keyword_position': analisis.get('posisi_keyword_pertama', ''),
                'first_keyword_position_on_title': analisis.get('posisi_keyword_di_judul', '')
            }
            rows.append(row)

    columns = [
        'Keyword', 'Position Google', 'Url', 'Title', 'Title Word Count','first_keyword_position_on_title',
        'Meta Description', 'meta_desc_word_count', 'Content Word Count',
        'first_keyword_position','Keyword Density', 'Internal Links', 'H2 Count', 'H3 Count',
        'Image Count', 'Book Source Count'
    ]
    df = pd.DataFrame(rows, columns=columns)
    df = df.sort_values(by=['Keyword', 'Position Google'])
    df.to_excel(excel_file, index=False, engine='openpyxl')

# Jalankan fungsi
json_to_excel('hasil_analisis_seo.json', 'seo_analysis.xlsx')