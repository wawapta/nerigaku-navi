# ねりがくナビ

**練馬区の学校・子育て情報を探しやすく**

練馬区小学校PTA連合協議会（小P連）が運営する情報ポータルサイト。

- 公開URL: https://nerigaku.com
- ホスティング: GitHub Pages (wawapta組織)
- リポジトリ: wawapta/nerigaku-navi

---

## 構成

```
nerigaku-navi/
├── index.html          # トップページ
├── soudan/index.html   # 相談先ページ (/soudan/)
├── hinagata/index.html # ひな型集ページ (/hinagata/)
├── news/index.html     # 新着情報ページ (/news/)   ← Ph.6で実装
├── menu/index.html     # 全メニューページ (/menu/) ← Ph.6で実装
├── css/style.css       # メインCSS
├── js/main.js          # メインJS（検索・RSS）
├── data/
│   ├── soudan.json           # 相談先データ（静的）
│   ├── hinagata.json         # ひな型集データ（静的）
│   ├── nerima-news.json      # 練馬区新着RSSキャッシュ（Actions生成）
│   ├── nerima-events.json    # 練馬区イベントRSSキャッシュ（Actions生成）
│   └── kopren-note.json      # 小P連noteRSSキャッシュ（Actions生成）
├── scripts/
│   └── fetch_rss.py    # RSS取得スクリプト
├── .github/workflows/
│   └── rss-fetch.yml   # GitHub Actions定期実行
└── CNAME               # カスタムドメイン設定
```

---

## 初回セットアップ（GitHub → GitHub Pages）

1. `wawapta` 組織に `nerigaku-navi` リポジトリを新規作成
2. このコードをpush
3. Settings → Pages → Source: `main` ブランチ `/（root）`
4. DNS設定: お名前.com で `nerigaku.com` → GitHub Pages
   - Aレコード: `185.199.108.153` / `185.199.109.153` / `185.199.110.153` / `185.199.111.153`
   - CNAMEレコード: `www` → `wawapta.github.io`
5. Settings → Pages → Custom domain: `nerigaku.com` を入力
6. HTTPS強制をON

---

## 実装フェーズ

| フェーズ | 状態 | 内容 |
|---------|------|------|
| Ph.1 | ✅ 完了 | プロジェクト構造・静的データ・CSS設計 |
| Ph.2 | ✅ 完了 | トップページ（index.html）|
| Ph.3 | ✅ 完了 | 相談先ページ（/soudan/）|
| Ph.4 | ✅ 完了 | ひな型集ページ（/hinagata/）|
| Ph.5 | ✅ 完了 | GitHub Actions RSSワークフロー |
| Ph.6 | 🔲 次回 | /newsページ・Fuse.js検索完成・/menuページ |
| Ph.7 | 🔲 次回 | DNS・HTTPS・MVP最終確認 |

---

## ひな型GoogleDriveリンクの設定方法

`data/hinagata.json` の `url` フィールドを実際のGoogle DriveリンクURLに書き換える。

```json
{
  "id": "h1",
  "url": "https://drive.google.com/file/d/XXXX/view?usp=sharing"
}
```

HTMLの修正は不要。JSON更新のみでサイトに反映される。

---

## 運営・更新

- **RSS**: GitHub Actionsが自動更新（1日4回）
- **相談先情報**: `data/soudan.json` を直接編集
- **ひな型**: Google Drive上でファイル差し替え（HTMLは変更不要）
- **ひな型リンク**: `data/hinagata.json` の `url` を更新

---

## MVP完成条件チェックリスト

- [x] スマートフォンで見やすいトップページ
- [x] 「いま確認する」4項目から公式情報へ遷移
- [x] 相談先ページ（/soudan/）4分類アンカー付き
- [ ] 練馬区 子育て・教育RSS表示（Actions設定後）
- [ ] 練馬区 イベントRSS表示（Actions設定後）
- [ ] 小P連 note RSS表示（Actions設定後）
- [x] 小P連ひな型集ページ（/hinagata/）
- [x] 外部リンク・免責表示
- [x] 小P連が運営していることの明記
- [x] 練馬区公式サイトと誤認されないデザイン・表記
- [ ] nerigaku.comでのHTTPSアクセス（DNS設定後）
- [x] RSSエラー時の適切なメッセージ表示
