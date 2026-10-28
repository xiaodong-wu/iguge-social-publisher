"""Create a product-source topic plan; generated briefs do not establish finished claims."""
import re


def build_content_plan(product):
    source = product['title'].split('|')[0]
    phrase = re.sub(r'\biGuge(?:\s+healthy)?\b', '', source, flags=re.I)
    phrase = re.sub(r'\s+', ' ', phrase).strip(' -|')
    if not 1 <= len(phrase.split()) <= 24:
        raise ValueError('Product has no usable source-backed social topic')
    return {
        'core_keyword': phrase, 'source_text': source,
        'source_url': product['canonical_url'],
        'related_topics': product.get('use_cases', [])[:4],
        'buyer_intent': 'B2B product evaluation, sample specification and sourcing inquiry',
        'instructions': 'Use verified format, ingredients and sourcing facts. The title is a topic, not proof of benefits. Omit health efficacy claims. Preserve optional formula and packaging qualifiers; do not infer dosages, certification, finished ingredients or market eligibility.',
    }
