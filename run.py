"""
Ponto de entrada da aplicação Café Aroma.
Execute com: python run.py
"""

from app import criar_app

app = criar_app()

if __name__ == '__main__':
    # debug=True: recarrega automaticamente ao salvar arquivos (modo desenvolvimento)
    app.run(host='0.0.0.0', port=5000, debug=True)
