from bs4 import BeautifulSoup
import re

LOGIN_KEYWORDS = [
    "login", "log in", "sign in", "verify", "verification",
    "authenticate", "password", "reset your password",
    "secure your account"
]

PAYMENT_KEYWORDS = [
    "credit card", "debit card", "payment", "pay now",
    "billing", "invoice", "paypal", "net banking",
    "upi", "card number", "cvv"
]

SUSPICIOUS_EVENTS = [
    "onclick", "onload", "onmouseover", "onmouseout",
    "onfocus", "onblur", "onunload", "onsubmit"
]


def _compute_dom_depth(node, depth=0):
    try:
        children = list(node.children)
    except:
        return depth

    if not children:
        return depth

    return max(_compute_dom_depth(c, depth + 1) for c in children)


def extract_beyondphish_features(html: str):
    """Return a fixed-length numeric vector of BeyondPhish features."""
    
    # If empty HTML → return zeros
    if not html or not isinstance(html, str):
        return [0]*11

    try:
        soup = BeautifulSoup(html, "html.parser")
    except:
        return [0]*11

    # --- DOM STRUCTURE ---
    all_tags = soup.find_all(True)
    total_nodes = len(all_tags)

    # DOM depth
    try:
        dom_depth = _compute_dom_depth(soup, 0)
    except:
        dom_depth = 0

    # Branching factor
    total_children = 0
    for t in all_tags:
        try:
            total_children += len(list(t.children))
        except:
            pass

    branch_factor = total_children / total_nodes if total_nodes > 0 else 0

    # script ratio
    num_scripts = len(soup.find_all('script'))
    script_ratio = num_scripts / total_nodes if total_nodes > 0 else 0

    # input fields
    input_count = len(soup.find_all('input')) + len(soup.find_all('form'))

    # hidden ratio
    hidden_count = 0
    for t in all_tags:
        try:
            style = (t.get("style") or "").replace(" ", "").lower()
            if "display:none" in style or "visibility:hidden" in style or t.has_attr("hidden"):
                hidden_count += 1
        except:
            pass
    hidden_ratio = hidden_count / total_nodes if total_nodes > 0 else 0

    # --- BEHAVIORAL FEATURES ---
    lower_html = html.lower()

    redirect_count = len(re.findall(r"location\.href\s*=", lower_html)) + \
                     len(re.findall(r"window\.location", lower_html)) + \
                     len(re.findall(r"http-equiv=['\"]refresh['\"]", lower_html))

    eval_usage = 1 if "eval(" in lower_html else 0

    suspicious_events = sum(lower_html.count(evt + "=") for evt in SUSPICIOUS_EVENTS)

    # --- TEXT FEATURES ---
    text = soup.get_text(separator=" ").lower()

    login_count = sum(text.count(kw) for kw in LOGIN_KEYWORDS)
    payment_count = sum(text.count(kw) for kw in PAYMENT_KEYWORDS)

    return [
        total_nodes,
        dom_depth,
        branch_factor,
        script_ratio,
        input_count,
        hidden_ratio,
        redirect_count,
        eval_usage,
        suspicious_events,
        login_count,
        payment_count,
    ]
