from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

analyzer = SentimentIntensityAnalyzer()


def analyze(text):
    try:
        vs = analyzer.polarity_scores(text)
    except Exception as e:
        print(f"Error analyzing review sentiment: {e}")
        vs = {"compound": 0}

    if vs["compound"] >= 0.05:
        sentiment = "Positive"
    elif vs["compound"] <= -0.05:
        sentiment = "Negative"
    else:
        sentiment = "Neutral"

    return vs["compound"], sentiment
