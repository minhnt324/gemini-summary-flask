import os
import requests
from bs4 import BeautifulSoup
from flask import Flask, request, render_template
import google.generativeai as genai

# Cấu hình Gemini
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-pro")

# Flask App
app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def index():
    summary = None
    if request.method == "POST":
        url = request.form["url"]
        keyword = request.form["keyword"]
        summary = get_article_summary(url, keyword)
    return render_template("index.html", summary=summary)

def get_article_summary(url, keyword):
    try:
        print(f"\n🔍 Đang truy cập: {url} - Tìm từ khóa: '{keyword}'")

        page = requests.get(url)
        soup = BeautifulSoup(page.text, "html.parser")

        # DEBUG: in tổng số thẻ <a>
        a_tags = soup.find_all("a")
        print(f"📌 Tìm thấy {len(a_tags)} thẻ <a>")
        for i, link in enumerate(a_tags[:20]):  # chỉ in 20 cái đầu
            print(f"[a {i}] {link.get_text(strip=True)} → {link.get('href')}")

        # 1. Tìm trong các thẻ <a>
        for link in a_tags:
            if keyword.lower() in link.get_text().lower():
                article_url = link.get("href")
                if article_url and not article_url.startswith("http"):
                    article_url = requests.compat.urljoin(url, article_url)
                print(f"✅ Tìm thấy trong <a>: {article_url}")
                return summarize_article(article_url)

        # DEBUG: in các tiêu đề h1-h6
        for tag_name in ["h1", "h2", "h3", "h4", "h5", "h6"]:
            tags = soup.find_all(tag_name)
            print(f"📌 Tìm thấy {len(tags)} thẻ <{tag_name}>")
            for i, tag in enumerate(tags[:5]):  # mỗi loại chỉ in 5 cái đầu
                print(f"[{tag_name} {i}] {tag.get_text(strip=True)}")

        # 2. Tìm trong tiêu đề h1–h6
        for tag_name in ["h1", "h2", "h3", "h4", "h5", "h6"]:
            for tag in soup.find_all(tag_name):
                if keyword.lower() in tag.get_text().lower():
                    parent = tag.find_parent("a")
                    if parent and parent.get("href"):
                        article_url = requests.compat.urljoin(url, parent["href"])
                        print(f"✅ Tìm thấy trong <{tag_name}> → <a>: {article_url}")
                        return summarize_article(article_url)

        print("❌ Không tìm thấy bài viết phù hợp.")
        return "Không tìm thấy bài viết với từ khóa đó."
    except Exception as e:
        print(f"💥 Lỗi khi tìm bài viết: {str(e)}")
        return f"Lỗi: {str(e)}"

def summarize_article(article_url):
    try:
        print(f"\n📄 Đang tóm tắt bài viết: {article_url}")
        article_page = requests.get(article_url)
        article_soup = BeautifulSoup(article_page.text, "html.parser")

        content = article_soup.get_text(separator="\n")
        print(f"✂️ Độ dài nội dung: {len(content)} ký tự")

        response = model.generate_content(
            f"Tóm tắt nội dung sau bằng tiếng Việt:\n\n{content}"
        )
        return response.text
    except Exception as e:
        print(f"💥 Lỗi khi tóm tắt bài viết: {str(e)}")
        return f"Lỗi khi tóm tắt bài viết: {str(e)}"

# Run khi local hoặc deploy
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
