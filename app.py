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
        page = requests.get(url)
        soup = BeautifulSoup(page.text, "html.parser")

        # 1. Tìm trong các thẻ <a>
        for link in soup.find_all("a"):
            if keyword.lower() in link.get_text().lower():
                article_url = link.get("href")
                if article_url and not article_url.startswith("http"):
                    article_url = requests.compat.urljoin(url, article_url)
                return summarize_article(article_url)

        # 2. Tìm trong tiêu đề <h1>–<h6> rồi kiểm tra thẻ cha là <a>
        for tag_name in ["h1", "h2", "h3", "h4", "h5", "h6"]:
            for tag in soup.find_all(tag_name):
                if keyword.lower() in tag.get_text().lower():
                    parent = tag.find_parent("a")
                    if parent and parent.get("href"):
                        article_url = requests.compat.urljoin(url, parent["href"])
                        return summarize_article(article_url)

        return "Không tìm thấy bài viết với từ khóa đó."
    except Exception as e:
        return f"Lỗi: {str(e)}"

def summarize_article(article_url):
    try:
        article_page = requests.get(article_url)
        article_soup = BeautifulSoup(article_page.text, "html.parser")

        # Lấy toàn bộ text trong trang
        content = article_soup.get_text(separator="\n")

        # Gửi đến Gemini để tóm tắt
        response = model.generate_content(
            f"Tóm tắt nội dung sau bằng tiếng Việt:\n\n{content}"
        )
        return response.text
    except Exception as e:
        return f"Lỗi khi tóm tắt bài viết: {str(e)}"

# Chạy app khi local hoặc Render
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
