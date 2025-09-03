import re, unicodedata, difflib
from math import ceil

def _normalize(text: str) -> str:
    s = unicodedata.normalize("NFKC", text)
    s = re.sub(r"[\s、。．，・_';:…「」『』【】（）()“”\"'\-\–—’‘‛]+", "", s)
    return s

def _edit_distance(a: str, b: str) -> int:
    if a == b: return 0
    if not a:  return len(b)
    if not b:  return len(a)
    prev = list(range(len(b)+1))
    for i, ca in enumerate(a, 1):
        cur0 = i
        for j, cb in enumerate(b, 1):
            ins = prev[j] + 1
            del_ = cur0 + 1
            sub = prev[j-1] + (ca != cb)
            cur0, prev[j-1] = min(ins, del_, sub), cur0
        prev[-1] = cur0
    return prev[-1]

def _jaccard_ngrams(a: str, b: str, n: int = 2) -> float:
    A = {a[i:i+n] for i in range(max(0, len(a)-n+1))} or {a}
    B = {b[i:i+n] for i in range(max(0, len(b)-n+1))} or {b}
    inter = len(A & B)
    union = len(A | B)
    return inter / union if union else 1.0

class SubtitleMemory:
    def __init__(self, ratio_thr=0.90, jaccard_thr=0.75):
        self.last_text_raw = None
        self.last_text_norm = None
        self.ratio_thr = ratio_thr
        self.jaccard_thr = jaccard_thr

    def is_new(self, text: str) -> bool:
        raw = (text or "").strip()
        norm = _normalize(raw)
        if not norm:
            return False
        if self.last_text_norm is None:
            self.last_text_raw, self.last_text_norm = raw, norm
            return True

        ratio = difflib.SequenceMatcher(None, norm, self.last_text_norm).ratio()

        L = max(len(norm), len(self.last_text_norm))
        k = max(1, ceil(L / 10))
        dist = _edit_distance(norm, self.last_text_norm)

        jac = _jaccard_ngrams(norm, self.last_text_norm, n=2)

        is_dup = (ratio >= self.ratio_thr) or (dist <= k) or (jac >= self.jaccard_thr)

        if is_dup:
            return False

        self.last_text_raw, self.last_text_norm = raw, norm
        return True
