import matplotlib.pyplot as plt
from wordcloud import WordCloud

# pip install wordcloud matplotlib numpy pillow

ideias = """
python automacao dados inteligencia artificial mapa de ideias brainstorm
prototipo api web scraping visualizacao automacao dados python
ideias inovacao produtividade automacao python dados scripts
"""

stopwords = {"de", "da", "do", "em", "para", "com", "e", "o", "a", "os", "as"}

nuvem = WordCloud(
    width=800,
    height=400,
    background_color="white",
    stopwords=stopwords,
    colormap="viridis",
).generate(ideias)

plt.figure(figsize=(10, 5))
plt.imshow(nuvem, interpolation="bilinear")
plt.axis("off")
plt.tight_layout()
plt.show()


