import os
import re
import json
import time
import base64
import shutil
import asyncio
import logging
import smtplib
import threading
import subprocess
from datetime import datetime
from email.message import EmailMessage
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.request import Request, urlopen


# ==============================================================================
# 0. SERVIDOR HTTP MINIMO PARA RENDER (PYTHON PURO)
# ==============================================================================

class _RenderHealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain; charset=utf-8")
        self.end_headers()
        self.wfile.write(b"OK - SERIE VIVA QUANT ENGINE ativo")

    def do_HEAD(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain; charset=utf-8")
        self.end_headers()

    def log_message(self, format, *args):
        return


def iniciar_porta_render():
    porta = int(os.environ.get("PORT", 10000))
    servidor = HTTPServer(("0.0.0.0", porta), _RenderHealthHandler)
    thread = threading.Thread(target=servidor.serve_forever, daemon=True)
    thread.start()
    return servidor


# ==============================================================================
# 1. CHAVE LIGA/DESLIGA, VALIDACAO (NOME, E-MAIL, TELEFONE) E CONFIGURACOES
# ==============================================================================

CHAVE_ROBO_LIGADA = os.getenv("ROBO_LIGADO", "true").strip().lower() in ("1", "true", "sim", "on")

NOME_USUARIO = (os.getenv("USUARIO_NOME") or "Francisco Cardoso Borges").strip()
EMAIL_PADRAO_USUARIO = "franciscocardosoborges3@gmail.com"
EMAIL_USUARIO = EMAIL_PADRAO_USUARIO
TELEFONE_USUARIO = (os.getenv("USUARIO_TELEFONE") or "86994165193").strip()

NOME_PROJETO = "SERIE VIVA QUANT ENGINE - PRODUCAO E DIRECAO 24/7"
VERSAO_SISTEMA = "2026.11-SERIE-VIVA-QUANT-ENGINE-PYTHON-PURO"

ARQUIVO_SEGREDO_LOCAL = ".env.local.json"
ARQUIVO_MEMORIA_SERIE = os.getenv("MEMORIA_SERIE_ARQUIVO", "memoria_serie_viva_quant.json")
PASTA_SAIDA_MIDIA = os.getenv("PASTA_SAIDA", "output_serie_viva_quant")
ARQUIVO_TRILHA = os.getenv("TRILHA_ARQUIVO", "trilha.mp3")
ARQUIVO_RELATORIO = "relatorio_serie_viva_quant.json"

# Ritmo humano sugerido: 5 a 7 videos por 24h (intervalo padrao 3600s = 1h)
INTERVALO_VARREDURA_SEGUNDOS = max(10, int(os.getenv("CYCLE_SECONDS", "3600")))
RITMO_VIDEOS_24H_MIN = max(1, int(os.getenv("VIDEOS_24H_MIN", "5")))
RITMO_VIDEOS_24H_MAX = max(RITMO_VIDEOS_24H_MIN, int(os.getenv("VIDEOS_24H_MAX", "7")))

# API Unica OpenAI (Roteiro em serie + Voz + Cenas + Video)
CHAVE_OPENAI = os.getenv("OPENAI_API_KEY", "").strip()
MODELO_TEXTO = os.getenv("OPENAI_TEXT_MODEL", "gpt-4o-mini")
MODELO_VOZ = os.getenv("OPENAI_TTS_MODEL", "gpt-4o-mini-tts")
VOZ_NARRADOR = os.getenv("OPENAI_TTS_VOICE", "onyx")
MODELO_IMAGEM = os.getenv("OPENAI_IMAGE_MODEL", "gpt-image-1")
QTD_CENAS_SERIE = max(2, min(6, int(os.getenv("QTD_CENAS", "4"))))

TEMA_SERIE_BASE = os.getenv(
    "TEMA_SERIE_BASE",
    "Serie continua original (PT-BR) com base na origem viva de valores humanos, familia, "
    "entendimento vs. confusao, referencias biblicas e escala do valor das palavras sagradas "
    "(1 a 3 vezes sem habito vs. 4 a 5 dias de dedicacao vs. habito firme e luz), "
    "100% original e sem copia de terceiros"
)

EPISODIOS_ORIGEM_BASE = [
    {
        "episodio": 1,
        "titulo": "O Valor da Biblia e das Palavras Sagradas: Quando a Luz Entra na Vida",
        "origem": "Fato real, valor das palavras sagradas e habito constante vs. confusao do dia a dia",
        "cenario_real": "Supermercado de bairro, concessionaria e casa de familia",
        "referencias_biblicas": [
            "Josue 1:8 (Meditar na Palavra com constancia e fidelidade)",
            "Salmos 119:105 (As palavras sagradas como lampada e luz para o caminho)",
            "Tiago 1:19 (Parar para ouvir com calma e evitar confusao precipitada)",
            "Mateus 24 (Sinais dos tempos, arrependimento e volta de Cristo)",
            "Genesis 6-7 (Noe), Genesis 5:22-24 (Enoque) e 1 Reis 18 (Elias)",
        ],
        "escala_valor_palavras_sagradas": {
            "1_a_3_vezes_sem_habito": "Apenas olhar ou abrir de vez em quando sem constancia nao cria raiz profunda nem transforma o rumo do dia a dia.",
            "4_a_5_dias_com_dedicacao": "Quando a pessoa se dedica de verdade quatro, cinco dias ou mais, a vida comeca a mudar, brigas e desconfiancas perdem forca e a fidelidade abre portas.",
            "habito_firme_e_luz": "Quando as palavras sagradas viram habito firme e constante, iluminam como luz, ensinam a ouvir e dao palavra e firmeza para falar da verdade de Deus.",
        },
        "cenas": [
            {"cena": 1, "pilar": "Curiosidade e Justica", "duracao_seg": 15, "movimento": "No comercio e na concessionaria, pessoas discutem por vaidade e aparencia enquanto alguem simples mantem a calma, abaixa o tom e para para ouvir.", "fala": "Confusao nao compensa: quem aprende a ouvir e valoriza a palavra certa enxerga o que o orgulho esconde."},
            {"cena": 2, "pilar": "Empatia e Nostalgia", "duracao_seg": 20, "movimento": "Na casa da familia, pais, filhos, netos, bisnetos e tataranetos se reunem a mesa, oram e abrem as palavras sagradas com constancia.", "fala": "Abrir a Biblia uma, duas ou tres vezes sem constancia nao firma a raiz; mas de quatro a cinco dias e virando habito, a casa muda e a luz aparece."},
            {"cena": 3, "pilar": "Revelacao Biblica e Chamado", "duracao_seg": 20, "movimento": "Cristo surge com firmeza e compaixao, destacando o valor eterno das Escrituras, a fidelidade que gera transformacao e os sinais dos tempos.", "fala": "Como nos dias de Noe, Enoque e Elias, o tempo se cumpre e Cristo esta voltando: arrependam-se e facam das palavras sagradas o alicerce da vida."},
            {"cena": 4, "pilar": "Superacao e Continuidade", "duracao_seg": 15, "movimento": "A familia vive em paz e entendimento, a palavra de fe ganha forca e o encerramento convida a acompanhar os proximos capitulos.", "fala": "Quanto mais a Palavra vira habito e pregacao fiel, mais luz ilumina o caminho. Acompanhe os proximos capitulos em primeira mao."},
        ],
    },
    {
        "episodio": 2,
        "titulo": "Pergunta do Publico: Por Que Tanta Confusao em Vez de Entendimento?",
        "origem": "Pergunta do publico sobre brigas banais, escuta mutua e valor das palavras sagradas",
        "cenario_real": "Rua de bairro, comercio e mesa da familia",
        "referencias_biblicas": [
            "Tiago 1:19 (Ouvir com atencao e evitar ira precipitada)",
            "Proverbios 15:1 (Resposta branda desvia o furor)",
            "Salmos 119:105 e Mateus 24 (Luz da Palavra, arrependimento e volta de Cristo)",
        ],
        "escala_valor_palavras_sagradas": {
            "1_a_3_vezes_sem_habito": "Apenas olhar ou abrir de vez em quando sem constancia nao cria raiz profunda nem transforma o rumo do dia a dia.",
            "4_a_5_dias_com_dedicacao": "Quando a pessoa se dedica de verdade quatro, cinco dias ou mais, a vida comeca a mudar, brigas e desconfiancas perdem forca e a fidelidade abre portas.",
            "habito_firme_e_luz": "Quando as palavras sagradas viram habito firme e constante, iluminam como luz, ensinam a ouvir e dao palavra e firmeza para falar da verdade de Deus.",
        },
        "cenas": [
            {"cena": 1, "pilar": "Curiosidade", "duracao_seg": 15, "movimento": "Dois vizinhos comecam uma discussao por um motivo simples, enquanto um morador interveem com calma pedindo para ouvirem um ao outro.", "fala": "Por que tanta discussao por coisas pequenas? Parar para ouvir e buscar a sabedoria das Escrituras muda a conversa."},
            {"cena": 2, "pilar": "Empatia e Nostalgia", "duracao_seg": 20, "movimento": "Em casa, a familia agradece a refeicao e mantem o habito das palavras sagradas, passando o exemplo para as geracoes seguintes.", "fala": "Quando o valor da Biblia deixa de ser visita rara e vira habito firme, a paz entra e a luz ilumina a casa."},
            {"cena": 3, "pilar": "Superacao e Continuidade", "duracao_seg": 20, "movimento": "Cristo reforca o chamado ao arrependimento diante da volta do Senhor e convida a acompanhar o proximo episodio.", "fala": "Cristo esta voltando: arrependa-se, valorize as palavras sagradas e acompanhe o proximo capitulo em primeira mao."},
        ],
    },
]

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("serie_viva_quant_engine.log", encoding="utf-8"),
        logging.StreamHandler(),
    ],
)

_ULTIMO_EMAIL_RECONHECIDO = None


# ==============================================================================
# 2. VALIDACAO DE CADASTRO (NOME, E-MAIL, TELEFONE) + AUTORRECONHECIMENTO
# ==============================================================================

def _normalizar_email(email_bruto):
    limpo = (email_bruto or "").strip().strip('"').strip("'")
    return re.sub(r"\s+", "", limpo).lower()


def _email_formato_valido(email_limpo):
    return bool(re.match(r"^[^@\s]+@[^@\s]+\.[A-Za-z]{2,}$", email_limpo or ""))


def _resolver_email_ativo():
    env_email = _normalizar_email(os.getenv("USUARIO_EMAIL", ""))
    codigo_email = _normalizar_email(EMAIL_USUARIO)
    padrao_email = _normalizar_email(EMAIL_PADRAO_USUARIO)

    if env_email:
        return env_email, "env:USUARIO_EMAIL"
    if codigo_email:
        return codigo_email, "codigo:EMAIL_USUARIO"
    return padrao_email, "padrao:EMAIL_PADRAO_USUARIO"


def _ler_dados_usuario():
    nome = (os.getenv("USUARIO_NOME") or NOME_USUARIO or "").strip()
    email, origem_email = _resolver_email_ativo()
    telefone = (os.getenv("USUARIO_TELEFONE") or TELEFONE_USUARIO or "").strip()
    return nome, email, telefone, origem_email


def validar_cadastro_usuario():
    global _ULTIMO_EMAIL_RECONHECIDO
    nome, email, telefone, origem_email = _ler_dados_usuario()

    partes_nome = [p for p in nome.split() if re.search(r"[A-Za-zÀ-ÿ]", p)]
    nome_ok = len(partes_nome) >= 2
    email_ok = _email_formato_valido(email)
    digitos_fone = re.sub(r"\D", "", telefone)
    telefone_ok = len(digitos_fone) >= 8

    email_trocado = False
    email_anterior = _ULTIMO_EMAIL_RECONHECIDO
    if email_ok:
        if _ULTIMO_EMAIL_RECONHECIDO is not None and _ULTIMO_EMAIL_RECONHECIDO != email:
            email_trocado = True
        _ULTIMO_EMAIL_RECONHECIDO = email

    valido = CHAVE_ROBO_LIGADA and nome_ok and email_ok and telefone_ok
    return valido, {
        "chave_ligada": CHAVE_ROBO_LIGADA,
        "nome": nome,
        "email": email,
        "email_anterior": email_anterior,
        "email_trocado": email_trocado,
        "origem_email": origem_email,
        "telefone": telefone,
        "nome_ok": nome_ok,
        "email_ok": email_ok,
        "telefone_ok": telefone_ok,
    }


def registrar_estado_usuario():
    valido, info = validar_cadastro_usuario()
    status_campos = (
        f"chave={'ON' if info['chave_ligada'] else 'OFF'}, "
        f"nome={'OK' if info['nome_ok'] else 'PENDENTE'}, "
        f"email={'OK' if info['email_ok'] else 'PENDENTE'}, "
        f"telefone={'OK' if info['telefone_ok'] else 'PENDENTE'}"
    )

    if info["email_trocado"]:
        logging.info(
            "AUTORRECONHECIMENTO DE E-MAIL: Alterado de '%s' para '%s' (%s).",
            info["email_anterior"],
            info["email"],
            info["origem_email"],
        )

    if valido:
        logging.info(
            "CHAVE ROBO: LIGADA (True) [%s] | Usuario: %s | E-mail ativo: %s | Telefone: %s",
            status_campos,
            info["nome"],
            info["email"],
            info["telefone"],
        )
    else:
        faltando = []
        if not info["chave_ligada"]:
            faltando.append("chave ROBO_LIGADO desligada")
        if not info["nome_ok"]:
            faltando.append("nome e sobrenome")
        if not info["email_ok"]:
            faltando.append("e-mail valido")
        if not info["telefone_ok"]:
            faltando.append("telefone")
        logging.warning(
            "CHAVE ROBO: DESLIGADA/BLOQUEADA (False) [%s] — Pendente: %s.",
            status_campos,
            ", ".join(faltando) if faltando else "cadastro incompleto",
        )
    return valido, info


# ==============================================================================
# 3. COFRE PROTEGIDO DE CREDENCIAIS E MEMORIA DA SERIE (PYTHON PURO)
# ==============================================================================

def carregar_segredos_cofre():
    _, info_usuario = validar_cadastro_usuario()
    email_ativo = info_usuario["email"] or EMAIL_PADRAO_USUARIO

    cofre_arquivo = {}
    if os.path.exists(ARQUIVO_SEGREDO_LOCAL):
        try:
            with open(ARQUIVO_SEGREDO_LOCAL, "r", encoding="utf-8") as f:
                dados = json.load(f)
                if isinstance(dados, dict):
                    cofre_arquivo = dados
        except Exception as e:
            logging.error("Erro ao ler cofre local (%s): %s", ARQUIVO_SEGREDO_LOCAL, e)

    def obter_chave(nome_chave, padrao=""):
        val_env = os.getenv(nome_chave)
        if val_env is not None and str(val_env).strip() != "":
            return str(val_env).strip()
        val_arq = cofre_arquivo.get(nome_chave, padrao)
        return str(val_arq).strip() if val_arq is not None else ""

    return {
        "OPENAI_API_KEY": obter_chave("OPENAI_API_KEY", CHAVE_OPENAI),
        "FB_ACCESS_TOKEN": obter_chave("FB_ACCESS_TOKEN"),
        "IG_ACCESS_TOKEN": obter_chave("IG_ACCESS_TOKEN"),
        "IG_USER_ID": obter_chave("IG_USER_ID"),
        "SMTP_HOST": obter_chave("SMTP_HOST", "smtp-mail.outlook.com"),
        "SMTP_PORT": obter_chave("SMTP_PORT", "587"),
        "SMTP_USER": obter_chave("SMTP_USER", email_ativo),
        "SMTP_PASSWORD": obter_chave("SMTP_PASSWORD"),
    }


def carregar_memoria_serie():
    padrao = {"episodio_atual": 0, "titulos_usados": [], "historico": []}
    if not os.path.isfile(ARQUIVO_MEMORIA_SERIE):
        return padrao
    try:
        with open(ARQUIVO_MEMORIA_SERIE, "r", encoding="utf-8") as f:
            dados = json.load(f)
            if isinstance(dados, dict):
                dados.setdefault("episodio_atual", 0)
                dados.setdefault("titulos_usados", [])
                dados.setdefault("historico", [])
                return dados
    except Exception:
        logging.warning("Memoria da serie ilegivel; iniciando estrutura limpa.")
    return padrao


def salvar_memoria_serie(memoria):
    try:
        with open(ARQUIVO_MEMORIA_SERIE, "w", encoding="utf-8") as f:
            json.dump(memoria, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logging.error("Erro ao salvar memoria da serie: %s", e)


# ==============================================================================
# 4. MOTOR DE IA UNIFICADO (OPENAI: ROTEIRO EM SERIE + VOZ + CENAS + FFMPEG)
# ==============================================================================

def _post_json_openai(api_key, endpoint, payload, timeout=60):
    url = f"https://api.openai.com/v1/{endpoint}"
    corpo = json.dumps(payload).encode("utf-8")
    req = Request(
        url,
        data=corpo,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _post_bytes_openai(api_key, endpoint, payload, timeout=90):
    url = f"https://api.openai.com/v1/{endpoint}"
    corpo = json.dumps(payload).encode("utf-8")
    req = Request(
        url,
        data=corpo,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urlopen(req, timeout=timeout) as resp:
        return resp.read()


def _escapar_texto_ffmpeg(texto):
    limpo = (texto or "").replace("\\", "\\\\").replace(":", "\\:").replace("'", "\\'")
    limpo = " ".join(limpo.split())
    return limpo[:160]


def _ffmpeg_disponivel():
    return shutil.which("ffmpeg") is not None


def _duracao_audio_segundos(caminho_mp3):
    if not _ffmpeg_disponivel() or not os.path.isfile(caminho_mp3):
        return 18.0
    try:
        proc = subprocess.run(
            ["ffmpeg", "-i", caminho_mp3],
            capture_output=True,
            text=True,
            timeout=30,
        )
        for linha in proc.stderr.splitlines():
            if "Duration:" in linha:
                parte = linha.split("Duration:")[1].split(",")[0].strip()
                h, m, s = parte.split(":")
                total = float(h) * 3600 + float(m) * 60 + float(s)
                if total > 1.0:
                    return total
    except Exception:
        pass
    return 18.0


def gerar_roteiro_serie_ia(api_key, proximo_ep, titulos_anteriores):
    base_ref = EPISODIOS_ORIGEM_BASE[(proximo_ep - 1) % len(EPISODIOS_ORIGEM_BASE)]
    dados = _post_json_openai(
        api_key,
        "chat/completions",
        {
            "model": MODELO_TEXTO,
            "temperature": 0.85,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "Voce cria episodios originais em serie (PT-BR) em formato vertical 9:16 (1080x1920) "
                        "com tom humano, respeitoso, claro e continuidade narrativa entre episodios. "
                        "Respeite rigorosamente as politicas das plataformas, direitos autorais e termos de "
                        "responsabilidade: 100% original (zero copia ou reupload de terceiros), zero promessas "
                        "enganosas e sem depender de engajamento artificial ou impulsionamento. "
                        "Responda SOMENTE em JSON valido com as chaves: "
                        "'episodio', 'titulo', 'narracao', 'legenda_curta', 'cenas'. "
                        f"Onde 'cenas' e uma lista de {QTD_CENAS_SERIE} objetos com 'prompt_visual' e 'legenda_cena'."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"Tema base: {TEMA_SERIE_BASE}\n"
                        f"Referencia estrutural de origem: {base_ref['origem']} | Cenario: {base_ref['cenario_real']}\n"
                        f"Episodio numero: {proximo_ep}\n"
                        f"PROIBIDO repetir titulos anteriores: {titulos_anteriores}\n"
                        "Crie um episodio original e coerente com a serie."
                    ),
                },
            ],
        },
        timeout=50,
    )

    conteudo = dados["choices"][0]["message"]["content"].strip()
    if conteudo.startswith("```"):
        conteudo = conteudo.strip("`").replace("json", "", 1).strip()

    roteiro = json.loads(conteudo)
    if not isinstance(roteiro, dict) or not roteiro.get("narracao"):
        raise ValueError("Roteiro invalido retornado pela OpenAI.")

    titulo = (roteiro.get("titulo") or f"Serie Viva - Ep. {proximo_ep:02d}").strip()
    if titulo.lower() in [t.lower() for t in titulos_anteriores]:
        titulo = f"{titulo} - Ep. {proximo_ep:02d}"

    cenas = roteiro.get("cenas")
    if not isinstance(cenas, list) or len(cenas) == 0:
        cenas = [
            {
                "prompt_visual": (
                    f"Cena {idx + 1} em estilo cinematografico real e humano sobre {titulo}, "
                    f"iluminacao natural, sem texto na imagem e sem marcas de terceiros"
                ),
                "legenda_cena": roteiro.get("legenda_curta", roteiro["narracao"])[:120],
            }
            for idx in range(QTD_CENAS_SERIE)
        ]
    else:
        cenas = cenas[:QTD_CENAS_SERIE]

    roteiro["episodio"] = proximo_ep
    roteiro["titulo"] = titulo
    roteiro["cenas"] = cenas
    roteiro.setdefault("legenda_curta", roteiro["narracao"][:140])
    return roteiro


def gerar_voz_ia(api_key, texto_narracao, caminho_mp3):
    audio_bytes = _post_bytes_openai(
        api_key,
        "audio/speech",
        {
            "model": MODELO_VOZ,
            "voice": VOZ_NARRADOR,
            "input": texto_narracao,
        },
        timeout=60,
    )
    with open(caminho_mp3, "wb") as f:
        f.write(audio_bytes)
    return caminho_mp3


def gerar_imagem_cena_ia(api_key, prompt_visual, caminho_png):
    dados = _post_json_openai(
        api_key,
        "images/generations",
        {
            "model": MODELO_IMAGEM,
            "prompt": prompt_visual,
            "size": "1024x1792",
        },
        timeout=90,
    )
    item = dados["data"][0]
    if item.get("b64_json"):
        with open(caminho_png, "wb") as f:
            f.write(base64.b64decode(item["b64_json"]))
    elif item.get("url"):
        with urlopen(item["url"], timeout=60) as img_resp:
            with open(caminho_png, "wb") as f:
                f.write(img_resp.read())
    else:
        raise RuntimeError("Resposta de imagem sem b64_json ou url.")
    return caminho_png


def _renderizar_clipe_cena(caminho_png, legenda_cena, duracao_seg, indice_cena, caminho_clipe_mp4):
    frames = max(25, int(round(duracao_seg * 25)))
    texto_legenda = _escapar_texto_ffmpeg(legenda_cena)

    if indice_cena % 2 == 0:
        movimento = (
            f"zoompan=z='min(zoom+0.0009,1.14)':"
            f"x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={frames}:s=1080x1920:fps=25"
        )
    else:
        movimento = (
            f"zoompan=z='1.10':"
            f"x='(iw-iw/zoom)*(on/{max(1, frames)})':y='(ih-ih/zoom)*0.45':d={frames}:s=1080x1920:fps=25"
        )

    filtro = (
        f"[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,"
        f"{movimento},"
        f"drawbox=x=0:y=ih-360:w=iw:h=260:color=black@0.58:t=fill,"
        f"drawtext=text='{texto_legenda}':fontcolor=white:fontsize=32:"
        f"x=(w-text_w)/2:y=ih-260:line_spacing=8[vout]"
    )

    comando = [
        "ffmpeg", "-y",
        "-loop", "1", "-t", f"{duracao_seg:.2f}", "-i", caminho_png,
        "-filter_complex", filtro,
        "-map", "[vout]",
        "-an",
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-r", "25",
        caminho_clipe_mp4,
    ]

    proc = subprocess.run(comando, capture_output=True, text=True, timeout=180)
    if proc.returncode != 0:
        raise RuntimeError(f"Falha ao animar cena {indice_cena + 1}: {proc.stderr[-350:]}")
    return caminho_clipe_mp4


def montar_video_multicena(caminhos_png, cenas_info, caminho_voz_mp3, caminho_mp4_final):
    if not _ffmpeg_disponivel():
        logging.warning("FFmpeg nao encontrado; video MP4 nao compilado neste ambiente.")
        return None

    duracao_total = _duracao_audio_segundos(caminho_voz_mp3)
    duracao_por_cena = max(3.0, duracao_total / max(1, len(caminhos_png)))
    pasta_temp = os.path.dirname(caminho_mp4_final)
    clipes_mp4 = []

    for idx, png_path in enumerate(caminhos_png):
        legenda = cenas_info[idx].get("legenda_cena", f"Cena {idx + 1}") if idx < len(caminhos_png) else f"Cena {idx + 1}"
        clipe_path = os.path.join(pasta_temp, f"_cena_{idx + 1}_{int(time.time())}.mp4")
        _renderizar_clipe_cena(png_path, legenda, duracao_por_cena, idx, clipe_path)
        clipes_mp4.append(clipe_path)

    lista_txt = os.path.join(pasta_temp, f"_lista_cenas_{int(time.time())}.txt")
    with open(lista_txt, "w", encoding="utf-8") as f:
        for clipe in clipes_mp4:
            caminho_normalizado = os.path.abspath(clipe).replace("\\", "/")
            f.write(f"file '{caminho_normalizado}'\n")

    video_sem_audio = os.path.join(pasta_temp, f"_video_cenas_{int(time.time())}.mp4")
    proc_concat = subprocess.run(
        ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", lista_txt, "-c:v", "libx264", "-pix_fmt", "yuv420p", video_sem_audio],
        capture_output=True,
        text=True,
        timeout=180,
    )
    if proc_concat.returncode != 0:
        raise RuntimeError(f"Falha ao unir cenas: {proc_concat.stderr[-350:]}")

    tem_trilha = os.path.isfile(ARQUIVO_TRILHA)
    cmd_final = ["ffmpeg", "-y", "-i", video_sem_audio, "-i", caminho_voz_mp3]
    if tem_trilha:
        cmd_final.extend([
            "-i", ARQUIVO_TRILHA,
            "-filter_complex",
            "[1:a]volume=1.0[voz];[2:a]volume=0.14[trilha];[voz][trilha]amix=inputs=2:duration=first:dropout_transition=2[aout]",
            "-map", "0:v", "-map", "[aout]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", caminho_mp4_final,
        ])
    else:
        cmd_final.extend([
            "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", caminho_mp4_final,
        ])

    proc_mix = subprocess.run(cmd_final, capture_output=True, text=True, timeout=180)
    if proc_mix.returncode != 0:
        raise RuntimeError(f"Falha ao mixar audio no video: {proc_mix.stderr[-350:]}")

    if os.path.isfile(caminho_mp4_final) and os.path.getsize(caminho_mp4_final) > 0:
        return caminho_mp4_final
    return None


def executar_producao_serie_ia(cofre):
    api_key = (cofre.get("OPENAI_API_KEY") or "").strip()
    os.makedirs(PASTA_SAIDA_MIDIA, exist_ok=True)
    carimbo = datetime.now().strftime("%Y%m%d_%H%M%S")

    memoria = carregar_memoria_serie()
    proximo_ep = int(memoria.get("episodio_atual", 0)) + 1
    titulos_anteriores = memoria.get("titulos_usados", [])[-25:]

    if not api_key:
        return {
            "status_ia": "AGUARDANDO_OPENAI_API_KEY",
            "episodio": proximo_ep,
            "titulo": f"Serie Viva - Ep. {proximo_ep:02d} (Aguardando Chave IA)",
            "video_mp4": None,
        }

    roteiro = gerar_roteiro_serie_ia(api_key, proximo_ep, titulos_anteriores)
    caminho_voz = os.path.join(PASTA_SAIDA_MIDIA, f"voz_ep{proximo_ep:02d}_{carimbo}.mp3")
    gerar_voz_ia(api_key, roteiro["narracao"], caminho_voz)

    caminhos_png = []
    for idx, cena in enumerate(roteiro["cenas"]):
        png_path = os.path.join(PASTA_SAIDA_MIDIA, f"cena_ep{proximo_ep:02d}_{idx + 1}_{carimbo}.png")
        gerar_imagem_cena_ia(api_key, cena["prompt_visual"], png_path)
        caminhos_png.append(png_path)

    caminho_mp4 = os.path.join(PASTA_SAIDA_MIDIA, f"video_ep{proximo_ep:02d}_{carimbo}.mp4")
    video_final = montar_video_multicena(caminhos_png, roteiro["cenas"], caminho_voz, caminho_mp4)

    memoria["episodio_atual"] = proximo_ep
    memoria.setdefault("titulos_usados", []).append(roteiro["titulo"])
    memoria.setdefault("historico", []).append({
        "episodio": proximo_ep,
        "titulo": roteiro["titulo"],
        "video_mp4": video_final,
        "criado_em": datetime.now().isoformat(timespec="seconds"),
    })
    salvar_memoria_serie(memoria)

    return {
        "status_ia": "EPISODIO_SERIE_GERADO",
        "episodio": proximo_ep,
        "titulo": roteiro["titulo"],
        "video_mp4": video_final,
    }


# ==============================================================================
# 5. AGENTE DIRETOR DE APROVACAO, E-MAIL E CICLO 24/7 (PYTHON PURO)
# ==============================================================================

def agente_diretor_aprovar(pacote_midia, info_usuario):
    video_path = (pacote_midia or {}).get("video_mp4")
    video_valido = bool(video_path and os.path.isfile(video_path) and os.path.getsize(video_path) > 0)

    aprovacao = {
        "aprovado": video_valido,
        "video_valido": video_valido,
        "motivo": (
            "APROVADO_PELO_DIRETOR"
            if video_valido
            else "BLOQUEADO_SEM_VIDEO_MP4_VALIDO"
        ),
        "video_aprovado": video_path if video_valido else None,
        "ritmo_humano_24h": f"{RITMO_VIDEOS_24H_MIN} a {RITMO_VIDEOS_24H_MAX} videos/24h",
        "responsavel": info_usuario.get("nome", ""),
    }

    if video_valido:
        logging.info(
            "[Agente Diretor] APROVADO (video_valido=True) | Arquivo: %s | Ritmo: %s.",
            video_path,
            aprovacao["ritmo_humano_24h"],
        )
    else:
        logging.warning(
            "[Agente Diretor] %s (video_valido=False) | Nenhuma postagem liberada | Ritmo: %s.",
            aprovacao["motivo"],
            aprovacao["ritmo_humano_24h"],
        )
    return aprovacao


def enviar_email_relatorio(assunto, mensagem, cofre, info_usuario):
    destino = _normalizar_email(info_usuario.get("email") or EMAIL_PADRAO_USUARIO)
    if not _email_formato_valido(destino):
        logging.warning("E-mail de destino invalido ('%s').", destino)
        return False

    smtp_host = cofre.get("SMTP_HOST", "smtp-mail.outlook.com")
    smtp_port = int(cofre.get("SMTP_PORT", "587") or "587")
    smtp_user = cofre.get("SMTP_USER", destino)
    smtp_password = cofre.get("SMTP_PASSWORD", "")

    if not smtp_password:
        logging.info(
            "Notificacao preparada para [%s], mas SMTP_PASSWORD nao configurada no cofre. Envio ignorado sem erro.",
            destino,
        )
        return False

    msg = EmailMessage()
    msg["Subject"] = assunto
    msg["From"] = smtp_user
    msg["To"] = destino
    msg.set_content(mensagem)

    try:
        with smtplib.SMTP(smtp_host, smtp_port, timeout=20) as conexao:
            conexao.starttls()
            conexao.login(smtp_user, smtp_password)
            conexao.send_message(msg)
        logging.info("E-mail de relatorio enviado para %s.", destino)
        return True
    except Exception:
        logging.exception("Falha ao enviar e-mail para %s.", destino)
        return False


def _rodar_corrotina_segura(corrotina):
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        res = {}
        err = {}

        def _runner():
            try:
                res["v"] = asyncio.run(corrotina)
            except Exception as exc:
                err["e"] = exc

        t = threading.Thread(target=_runner, daemon=True)
        t.start()
        t.join()
        if "e" in err:
            raise err["e"]
        return res.get("v")

    return asyncio.run(corrotina)


def executar_ciclo():
    valido, info_usuario = registrar_estado_usuario()
    if not valido:
        return None

    cofre = carregar_segredos_cofre()
    logging.info("========== INICIO DO CICLO (%s) ==========", NOME_PROJETO)
    logging.info("Ritmo humano configurado: %s a %s videos/24h (24/7).", RITMO_VIDEOS_24H_MIN, RITMO_VIDEOS_24H_MAX)

    pacote = _rodar_corrotina_segura(asyncio.to_thread(executar_producao_serie_ia, cofre))
    aprovacao = agente_diretor_aprovar(pacote, info_usuario)

    if not aprovacao["aprovado"]:
        logging.info("[Publicador] BLOQUEADO pelo Diretor (%s). Nada postado.", aprovacao["motivo"])
    else:
        logging.info("[Publicador] Video aprovado pelo Diretor pronto para distribuicao.")

    relatorio = {
        "projeto": NOME_PROJETO,
        "versao": VERSAO_SISTEMA,
        "data": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        "usuario": info_usuario["nome"],
        "email": info_usuario["email"],
        "telefone": info_usuario["telefone"],
        "ritmo_24h": aprovacao["ritmo_humano_24h"],
        "producao": pacote,
        "diretor": aprovacao,
    }

    try:
        with open(ARQUIVO_RELATORIO, "w", encoding="utf-8") as f:
            json.dump(relatorio, f, ensure_ascii=False, indent=4)
    except Exception as e:
        logging.error("Erro ao salvar relatorio: %s", e)

    enviar_email_relatorio(
        assunto=f"[{NOME_PROJETO}] Relatorio do Ciclo",
        mensagem=(
            f"Usuario: {info_usuario['nome']}\n"
            f"E-mail: {info_usuario['email']}\n"
            f"Telefone: {info_usuario['telefone']}\n"
            f"Data: {relatorio['data']}\n"
            f"Ritmo: {aprovacao['ritmo_humano_24h']}\n"
            f"Diretor: {aprovacao['motivo']} (video_valido={aprovacao['video_valido']})"
        ),
        cofre=cofre,
        info_usuario=info_usuario,
    )

    logging.info("========== FIM DO CICLO (%s) ==========", NOME_PROJETO)
    return relatorio


def loop_segundo_plano():
    logging.info("Motor 24/7 iniciado (%s).", VERSAO_SISTEMA)
    while True:
        try:
            executar_ciclo()
        except Exception:
            logging.exception("Erro isolado no ciclo em segundo plano.")
        time.sleep(INTERVALO_VARREDURA_SEGUNDOS)


def main():
    logging.info("Inicializando %s — %s", NOME_PROJETO, VERSAO_SISTEMA)
    iniciar_porta_render()
    worker = threading.Thread(target=loop_segundo_plano, name="worker-serie-viva-quant", daemon=True)
    worker.start()
    while True:
        time.sleep(60)


if __name__ == "__main__":
    main()