from textblob.base import BaseTokenizer
from uniseg import wordbreak

# TextBlob compatible tokenizer for Norwegian.
# Simple implementation. Tokenizes according to Unicode Appendix 29 (UAX#29).


class NOTokenizer(BaseTokenizer):
    def tokenize(self, text):
        return list(self.itokenize(text))

    def itokenize(self, text, *args, **kwargs):
        return (token for token in wordbreak.words(text) if token != ' ')
