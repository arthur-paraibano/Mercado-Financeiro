"""
Tradução de strings nativas do Streamlit que não têm localização.

O Streamlit não oferece i18n nativo. Esta solução injeta um pequeno script
JavaScript que substitui strings em inglês por português em tempo real,
observando mutações no DOM.
"""
import streamlit.components.v1 as components

# Mapeamento de tradução: regex (ou string literal) -> substituto
# Use $1, $2 para grupos capturados em regex
TRADUCOES = [
    # Multiselect "+N badges"
    (r"^View (\d+) more$", "Ver mais $1"),
    (r"^View less$", "Ver menos"),
    # Botões padrão
    (r"^Press Enter to apply$", "Pressione Enter para aplicar"),
    (r"^Press Enter to submit form$", "Pressione Enter para enviar"),
    # Selects
    (r"^Choose an option$", "Escolha uma opção"),
    (r"^No options to select\.$", "Sem opções disponíveis."),
    (r"^No results$", "Nenhum resultado"),
    # File uploader
    (r"^Drag and drop file here$", "Arraste e solte o arquivo aqui"),
    (r"^Limit (\d+\w+) per file$", "Limite $1 por arquivo"),
    (r"^Browse files$", "Selecionar arquivos"),
    # Gráficos / dataframes
    (r"^View fullscreen$", "Tela cheia"),
    (r"^Exit fullscreen$", "Sair da tela cheia"),
    (r"^Download as PNG$", "Baixar como PNG"),
    (r"^Download as CSV$", "Baixar como CSV"),
    (r"^Search$", "Buscar"),
    # Status / botões de execução
    (r"^Running\.\.\.$", "Executando..."),
    (r"^Stop$", "Parar"),
    (r"^Rerun$", "Reexecutar"),
    (r"^Deploy$", "Publicar"),
    # Sidebar
    (r"^Close sidebar$", "Fechar menu lateral"),
    (r"^Open sidebar$", "Abrir menu lateral"),
    # Toolbar
    (r"^Settings$", "Configurações"),
    (r"^Print$", "Imprimir"),
    (r"^Record a screencast$", "Gravar tela"),
    (r"^Report a bug$", "Reportar bug"),
    (r"^Get help$", "Ajuda"),
    (r"^About$", "Sobre"),
    (r"^Clear cache$", "Limpar cache"),
    (r"^Developer options$", "Opções de desenvolvedor"),
]


def _gerar_regras_js() -> str:
    """Converte TRADUCOES em array JS."""
    regras = []
    for padrao, repl in TRADUCOES:
        # Escapar barras invertidas e aspas para JS
        padrao_js = padrao.replace("\\", "\\\\").replace("'", "\\'")
        repl_js = repl.replace("'", "\\'")
        regras.append(f"{{re: /{padrao_js}/, sub: '{repl_js}'}}")
    return "[" + ",".join(regras) + "]"


def aplicar_traducoes_streamlit():
    """
    Injeta script JS que observa o DOM e substitui strings em inglês do
    Streamlit por português. Chame uma vez no app.py.
    """
    regras = _gerar_regras_js()
    script = """
    <script>
    (function() {
        const REGRAS = """ + regras + """;
        const doc = window.parent.document;

        function traduzirNo(no) {
            if (!no) return;
            // TextNode direto
            if (no.nodeType === 3) {
                const t = no.nodeValue;
                if (!t || !t.trim()) return;
                for (const r of REGRAS) {
                    if (r.re.test(t.trim())) {
                        no.nodeValue = t.trim().replace(r.re, r.sub);
                        return;
                    }
                }
                return;
            }
            // Elemento: percorre filhos
            if (no.nodeType === 1) {
                no.childNodes.forEach(traduzirNo);
            }
        }

        function traduzirTudo() {
            try { traduzirNo(doc.body); } catch (e) {}
        }

        // Roda imediatamente e a cada mudança no DOM
        traduzirTudo();
        const obs = new MutationObserver(() => {
            window.requestAnimationFrame(traduzirTudo);
        });
        try {
            obs.observe(doc.body, {childList: true, subtree: true, characterData: true});
        } catch (e) {}

        // Fallback de segurança: roda periodicamente caso o observer falhe
        setInterval(traduzirTudo, 1500);
    })();
    </script>
    """
    components.html(script, height=0, width=0)
