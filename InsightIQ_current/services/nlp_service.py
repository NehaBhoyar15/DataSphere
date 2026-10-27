"""Local, dependency-light NLP adapter.

Deliberately avoids requiring an NLTK data download (per README) by using
small built-in word lists for sentiment and stopword filtering. Good
enough for demo-quality keyword/sentiment analysis on short text fields.
"""
import re
from collections import Counter

import pandas as pd

POSITIVE_WORDS = {
    "great", "good", "excellent", "happy", "love", "loved", "helpful", "quickly",
    "perfect", "perfectly", "best", "value", "satisfied", "polite", "recommend",
    "amazing", "fantastic", "resolved", "works", "worked", "easy",
}
NEGATIVE_WORDS = {
    "bad", "terrible", "late", "damaged", "refund", "not", "slow", "stopped",
    "worst", "poor", "issue", "problem", "expensive", "disappointed", "unhappy",
    "broken", "fail", "failed", "complain", "complaint",
}
STOPWORDS = {
    "the", "a", "an", "and", "or", "but", "is", "are", "was", "were", "to", "of",
    "in", "on", "for", "with", "it", "this", "that", "my", "i", "you", "your",
    "we", "they", "he", "she", "be", "as", "at", "so", "just", "really", "very",
    "not", "no", "had", "have", "has", "will", "would", "can", "could", "did",
    "do", "does", "if", "than", "then", "there", "their", "its", "from", "by",
}

WORD_RE = re.compile(r"[a-zA-Z']+")


class NLPService:
    def analyze(self, frame, column):
        if frame is None or frame.empty:
            raise ValueError("No data is loaded.")
        if not column or column not in frame.columns:
            raise ValueError("Choose a text column before analyzing.")

        texts = frame[column].fillna("").astype(str)

        sentiments = []
        pos_count = neg_count = neu_count = 0
        keyword_counter = Counter()

        for text in texts:
            words = [w.lower() for w in WORD_RE.findall(text)]
            score = sum(1 for w in words if w in POSITIVE_WORDS) - sum(
                1 for w in words if w in NEGATIVE_WORDS
            )
            if score > 0:
                label = "Positive"; pos_count += 1
            elif score < 0:
                label = "Negative"; neg_count += 1
            else:
                label = "Neutral"; neu_count += 1
            sentiments.append(label)
            keyword_counter.update(w for w in words if w not in STOPWORDS and len(w) > 2)

        rows = frame.copy()
        rows["Sentiment"] = sentiments

        keywords = keyword_counter.most_common(25)
        if not keywords:
            keywords = [("no_keywords_found", 0)]

        return {
            "counts": {"Positive": pos_count, "Negative": neg_count, "Neutral": neu_count},
            "keywords": keywords,
            "rows": rows,
        }
