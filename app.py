from flask import Flask, render_template, request
import requests
from bs4 import BeautifulSoup
import google.generativeai as genai
import os

app = Flask(__name__)

genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))

def get_article_summary(url, keyword):
    try:
        page = requests.get(url)
        soup = BeautifulSoup(page.text, "html.parser")
        links = soup.find_all("a", string=lambda t: t and keyword.lower() in t.lower())

        if not links:
            return "Không tìm thấy bài viết với từ khóa đó."

        article_url = links[0].get("href")
        if not article_url.startswith("http"):
            article_url = url.rstrip("/") + "/" + article_url.lstrip("/")

        article_page = requests.get(article_url)
        article_soup = BeautifulSoup(article_page.text, "html.parser")
        paragraphs = article_soup.find_all("p")
        article_text = "\n".join([p.get_text() for p in paragraphs[:20]])

        model = genai.GenerativeModel("gemini-pro")
        prompt = f"Tóm tắt nội dung sau bằng tiếng Việt, ngắn gọn và dễ hiểu:\n\n{article_text}"
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Lỗi: {str(e)}"

@app.route("/", methods=["GET", "POST"])
def index():
    summary = None
    if request.method == "POST":
        url = request.form["url"]
        keyword = request.form["keyword"]
        summary = get_article_summary(url, keyword)
    return render_template("index.html", summary=summary)

if __name__ == "__main__":
#    app.run(debug=True)
    app.run(host="0.0.0.0", port=10000)
