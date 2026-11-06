#!/usr/bin/env python3
"""Compõe a revisão da Sprint 1 em SBC. Requer Pandoc e Tectonic."""
from pathlib import Path
import argparse
import json
import re
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]
REPO = "https://github.com/leonardovbf/correlacoes-tres-neutrinos"


def convert(text, source="markdown", target="latex"):
    return subprocess.run(["pandoc", "-f", source, "-t", target, "--wrap=none"],
                          input=text, text=True, capture_output=True, check=True).stdout.strip()


def key_for(label, entries):
    for item in entries:
        author = item["author"][0]
        surname = author.get("family", author.get("literal", ""))
        year = str(item["issued"]["date-parts"][0][0])
        if label.casefold().startswith(surname.casefold()) and year in label:
            return item["id"]


def citations(text, entries):
    text = re.sub(r"(?<!!)\[([^\]]+)\]\((https?://[^)]+)\)",
                  lambda m: m[1] if key_for(m[1], entries) else m[0], text)
    def parenthetical(m):
        keys = []
        for label in re.findall(r"[A-Z][A-Z ;,.-]+?(?:et al\., )?\d{4}", m[1]):
            key = key_for(label.strip("; "), entries)
            if not key:
                raise ValueError("Citação sem registro: " + label)
            keys.append(key)
        if not keys:
            return m[0]
        suffix = re.sub(r".*\d{4}", "", m[1]).strip("; ")
        return r"\cite{" + ",".join(keys) + "}" + (" (" + suffix + ")" if suffix else "")
    text = re.sub(r"\(([A-Z][A-Z ;,.-]+(?:et al\., )?\d{4}[^()]*)\)", parenthetical, text)
    def narrative(m):
        key = key_for(m[0], entries)
        return r"\citeNarrative{" + key + "}{" + m[1] + "}{" + m[2] + "}" if key else m[0]
    return re.sub(r"\b((?:Mangin-Brinet|Riccio|Illa|Lacroix|Hall|Kiss|Cervia|Janka|Nagakura|Akaho|Baum|Cowan|Duan|Sarmah|Vissani)(?: et al\.|(?:,? (?:Bauge|Lacroix|Balantekin|Savage|and|e))*)) \((\d{4})\)", narrative, text)


def raw(text):
    return "\n\n```{=latex}\n" + text + "\n```\n\n"


def floats(text):
    def figure(m):
        return raw("\\begin{figure}[htbp]\n\\centering\n"
                   + r"\includegraphics[width=\linewidth]{" + m[1] + "}\n"
                   + r"\caption{" + convert(m[3]) + "}\n"
                   + r"\label{fig:" + m[2] + "}\n\\end{figure}")
    text = re.sub(r"!\[[^\]]*\]\(([^)]+)\)\s+\*(?:Figura|Figure) (\d+) - (.*?)\*", figure, text, flags=re.S)
    return text


def bibliography():
    def enrich(m):
        block = m[0]
        doi = re.search(r"\bdoi\s*=\s*\{([^}]+)\}", block)
        url = re.search(r"\burl\s*=\s*\{([^}]+)\}", block)
        link = "https://doi.org/" + doi[1] if doi else (url[1] if url else None)
        if link:
            addition = r"\url{" + link + "}"
            note = re.search(r"\bnote\s*=\s*\{([^}]+)\}", block)
            if note:
                block = block[:note.start()] + "note = {" + note[1] + ". " + addition + "}" + block[note.end():]
            else:
                block = block.rstrip()[:-1] + "  note = {" + addition + "},\n}"
        return block
    return re.sub(r"(?ms)^@.*?^\}", enrich, (ROOT / "referencias.bib").read_text())


def build(lang, entries):
    text = (ROOT / ("ARTIGO.md" if lang == "pt" else "ARTIGO.eng.md")).read_text()
    heading, refs = ("Introdução", "Referências") if lang == "pt" else ("Introduction", "References")
    front, body = text.split("## " + heading, 1)
    body = "## " + heading + body.split("## " + refs)[0]
    body = re.sub(r"(?m)^##", "#", body)
    body = floats(citations(body, entries))
    body = re.sub(r"(?<!!)\[([^\]]+)\]\((?!https?://)([^)]+\.md)\)",
                  lambda m: f"[{m[1]}]({REPO}/blob/docs/att-artigo-feedback-1/{m[2]})", body)
    tex = (ROOT / "artigo/revisao-s1/preambulo.tex").read_text().replace("LANGUAGE", "english,brazil" if lang == "pt" else "brazil,english")
    tex = tex.replace("TITLE", convert(text.splitlines()[0][2:]))
    emails = json.loads((ROOT / "artigo/revisao-s1/emails.json").read_text())
    addresses = [emails[key].strip() for key in ("giovanna", "marco", "leonardo") if emails[key].strip()]
    email_tex = r"\email{" + convert(", ".join(addresses)) + "}" if addresses else ""
    tex = tex.replace("AUTHOR_EMAILS", email_tex)
    tex += "\n\\begin{document}\n\\maketitle\n"
    for heading, environment in (("Abstract", "abstract"), ("Resumo", "resumo")):
        match = re.search(r"## " + heading + r"\s*\n(.*?)(?=\n## |\Z)", front, re.S)
        if match:
            paragraph = re.split(r"\n\n\*\*(?:Keywords|Palavras-chave):", match[1].strip())[0]
            tex += "\\begin{otherlanguage}{" + ("english" if environment == "abstract" else "brazil") + "}\n"
            tex += "\\begin{" + environment + "}\n" + convert(paragraph) + "\n\\end{" + environment + "}\n\\end{otherlanguage}\n"
    content = convert(body)
    for label in ("Declaração de uso de inteligência artificial", "Use of generative artificial intelligence"):
        content = content.replace(r"\section{" + label, r"\section*{" + label)
    tex += content + "\n\\FloatBarrier\n\\bibliographystyle{sbc}\n\\bibliography{referencias}\n\\end{document}\n"
    work = ROOT / "tmp/pdfs/revisao-s1" / lang
    work.mkdir(parents=True, exist_ok=True)
    for file in (ROOT / "artigo/revisao-s1/sbc").iterdir():
        if file.suffix in (".sty", ".bst"):
            shutil.copy2(file, work / file.name)
    (work / "referencias.bib").write_text(bibliography())
    shutil.copytree(ROOT / "figuras", work / "figuras", dirs_exist_ok=True)
    name = "artigo-neutrinos-revisao-s1" + ("-en" if lang == "en" else "")
    (work / (name + ".tex")).write_text(tex)
    subprocess.run(["tectonic", "--keep-logs", "--keep-intermediates", name + ".tex"], cwd=work, check=True)
    output = ROOT / "output/pdf"
    output.mkdir(parents=True, exist_ok=True)
    shutil.copy2(work / (name + ".pdf"), output / (name + ".pdf"))
    print(output / (name + ".pdf"))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--idioma", choices=("pt", "en", "ambos"), default="ambos")
    args = parser.parse_args()
    for tool in ("pandoc", "tectonic"):
        if not shutil.which(tool):
            parser.error("Instale " + tool + " e inclua-o no PATH.")
    entries = json.loads(convert((ROOT / "referencias.bib").read_text(), "bibtex", "csljson"))
    for lang in (("pt", "en") if args.idioma == "ambos" else (args.idioma,)):
        build(lang, entries)


if __name__ == "__main__":
    main()
