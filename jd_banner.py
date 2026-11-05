"""JD Pisces terminal identity for NEXUS Market Intelligence (no dependencies)."""
import sys
import os

RESET = "\033[0m"
CYAN = "\033[96m"
BLUE = "\033[94m"
GOLD = "\033[93m"
WHITE = "\033[97m"
BOLD = "\033[1m"


def jd_banner(stream=None):
    """Print the banner once; does not clear screen or touch trading state."""
    out = stream if stream is not None else sys.stdout
    color = bool(out.isatty()) and not os.environ.get('NO_COLOR')
    def paint(text, code):
        return f"{code}{text}{RESET}" if color else text
    width = 36
    def row(text='', code=CYAN):
        print(paint('║', CYAN) + paint(text.center(width), code) + paint('║', CYAN), file=out)
    print(paint('╔' + '═'*width + '╗', CYAN), file=out)
    row('JD NEXUS MARKET INTELLIGENCE', WHITE+BOLD)
    row('PAPER TRADING • OFFLINE')
    row('COTAÇÕES MANUAIS')
    print(paint('╠' + '═'*width + '╣', CYAN), file=out)
    row('><(((°>       <°)))><', BLUE) if not color else print(
        paint('║', CYAN)+' '*7+paint('><(((°>', BLUE)+' '*7+paint('<°)))><', GOLD)+' '*8+paint('║', CYAN), file=out)
    row('PEIXE AZUL   PEIXE DOURADO', GOLD)
    row('╔══════════╗', GOLD)
    row('║    JD    ║', GOLD+BOLD)
    row('╚══════════╝', GOLD)
    row('♓ PEIXES', CYAN+BOLD)
    row('JADILSON TAVARES', WHITE+BOLD)
    row('STAY LIVE', GOLD+BOLD)
    print(paint('╚' + '═'*width + '╝', CYAN), file=out)


if __name__ == '__main__':
    jd_banner()
