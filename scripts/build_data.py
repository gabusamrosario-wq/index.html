#!/usr/bin/env python3
"""pokedata.js を最新のデータから作り直す。

- 種族値・フォーム・進化：PvPoke の gamemaster.json
- 日本語の種族名：PokeAPI の pokemon_species_names.csv

標準ライブラリだけで動くので、GitHub Actions でもそのまま実行できる。
"""
import csv, io, json, re, sys, urllib.request

GM_URL = "https://raw.githubusercontent.com/pvpoke/pvpoke/master/src/data/gamemaster.json"
NAMES_URL = "https://raw.githubusercontent.com/PokeAPI/pokeapi/master/data/v2/csv/pokemon_species_names.csv"
OUT = sys.argv[1] if len(sys.argv) > 1 else "pokedata.js"

FORM = {
 'Alolan':'アローラ','Galarian':'ガラル','Hisuian':'ヒスイ','Paldean':'パルデア',
 'Incarnate':'けしん','Therian':'れいじゅう','Origin':'オリジン','Altered':'アナザー',
 'Female':'メス','Male':'オス','Plant':'くさきのミノ','Sandy':'すなちのミノ','Trash':'ゴミのミノ',
 'Attack':'アタック','Defense':'ディフェンス','Speed':'スピード','Normal':'ノーマル',
 'Standard':'ノーマル','Zen':'ダルマモード','Galarian Zen':'ガラル・ダルマモード',
 'Average':'ふつうのサイズ','Large':'おおきいサイズ','Small':'ちいさいサイズ','Super':'とくだいサイズ',
 'Hero':'マイティ','Land':'ランド','Sky':'スカイ','Overcast':'ネガ','Sunshine':'ポジ',
 'Rainy':'あまみず','Snowy':'ゆきぐも','Sunny':'たいよう',
 'Fan':'スピン','Frost':'フロスト','Heat':'ヒート','Mow':'カット','Wash':'ウォッシュ',
 'Black':'ブラック','White':'ホワイト','Ordinary':'いつも','Resolute':'かくご',
 'Aria':'ボイス','Pirouette':'ステップ','Burn':'ブレイズ','Chill':'フリーズ','Douse':'アクア','Shock':'イナズマ',
 'Aqua':'ウォーター','Blaze':'ファイヤー','Combat':'ファイティング','Armored':'アーマード',
 'Bug':'むし','Dark':'あく','Dragon':'ドラゴン','Electric':'でんき','Fairy':'フェアリー',
 'Fighting':'かくとう','Fire':'ほのお','Flying':'ひこう','Ghost':'ゴースト','Grass':'くさ',
 'Ground':'じめん','Ice':'こおり','Poison':'どく','Psychic':'エスパー','Rock':'いわ','Steel':'はがね','Water':'みず',
 'Blade':'ブレード','Shield':'シールド','Midday':'まひる','Midnight':'まよなか','Dusk':'たそがれ',
 'School':'むれた','Solo':'たんどく','Baile':'めらめら','Pom-Pom':'ぱちぱち',"Pa'u":'ふらふら','Sensu':'まいまい',
 'Core':'コア','Meteor':'りゅうせい','Busted':'ばれた',
 'Dusk Mane':'たそがれのたてがみ','Dawn Wings':'あかつきのつばさ','Ultra':'ウルトラ',
 'Crowned Sword':'けんのおう','Crowned Shield':'たてのおう',
 'Single Strike':'いちげき','Rapid Strike':'れんげき','Ice Rider':'はくば','Shadow Rider':'こくば',
 'Hangry':'はらぺこ','Full Belly':'まんぷく','Amped':'ハイ','Low Key':'ロー','Noice':'ナイスフェイス',
 'Gulping':'うのみ','Gorging':'まるのみ','10% Forme':'10%','50% Forme':'50%','Complete Forme':'パーフェクト',
 'Unbound':'ときはなたれし','Confined':'いましめられし','Eternamax':'ムゲンダイマックス',
 'Curly':'そったすがた','Droopy':'たれたすがた','Stretchy':'のびたすがた',
 'Jr':'ジュニア','5th Anniversary':'5しゅうねん','Horizons':'ホライゾン','Kariyushi':'かりゆし',
 'Libre':'リブレ','Pop Star':'ポップスター','Rock Star':'ロックスター','Shaymin Scarf':'シェイミスカーフ',
}
SKIP = re.compile(r'\((Shadow|Mega|Mega X|Mega Y|Primal)\)')

def fetch(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'iv-rank-data-builder'})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read()

def main():
    gm = json.loads(fetch(GM_URL))['pokemon']
    ja = {}
    for row in csv.DictReader(io.StringIO(fetch(NAMES_URL).decode('utf-8'))):
        if row['local_language_id'] == '11':
            ja[int(row['pokemon_species_id'])] = row['name']

    rows, seen = [], set()
    for p in gm:
        n = p['speciesName']
        if SKIP.search(n): continue
        base = ja.get(p['dex'])
        if not base: continue
        forms = re.findall(r'\((.*?)\)', n)
        label = base + ('（' + '・'.join(FORM.get(f, f) for f in forms) + '）' if forms else '')
        if label in seen: continue
        seen.add(label)
        b = p['baseStats']
        evo = (p.get('family') or {}).get('evolutions') or []
        rows.append({'label': label, 'dex': p['dex'], 'st': (b['atk'], b['def'], b['hp']),
                     'en': n, 'id': p['speciesId'], 'evo': evo,
                     'released': p.get('released', True)})

    # 実装済みを先に（名前照合で同点のとき優先されるように）
    rows.sort(key=lambda r: (r['dex'], not r['released'], r['label']))
    idx = {r['id']: i for i, r in enumerate(rows)}
    out = [[r['label'], r['dex'], *r['st'], r['en'], 1 if r['evo'] else 0,
            [idx[e] for e in r['evo'] if e in idx]] for r in rows]

    if len(out) < 1000:   # 取得失敗で中身が欠けたときに上書きしない
        sys.exit(f'件数が少なすぎます（{len(out)}件）。更新を中止しました。')
    js = 'const POKE=' + json.dumps(out, ensure_ascii=False, separators=(',', ':')) + ';\n'
    open(OUT, 'w', encoding='utf-8').write(js)
    print(f'{len(out)}件 / 図鑑番号 最大{max(r[1] for r in out)} → {OUT}')

if __name__ == '__main__':
    main()
