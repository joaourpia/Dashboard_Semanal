import os
from git import Repo
from datetime import datetime
import sys

# --- CONFIGURAÇÕES ---
CAMINHO_PROJETO = r"C:\Projetos_Python\Dashboard_Semanal"
# Nota: O script agora pega TUDO, não precisa especificar o CSV

def atualizar_projeto():
    try:
        print(f"🔄 Acessando repositório em: {CAMINHO_PROJETO}")
        repo = Repo(CAMINHO_PROJETO)
        origin = repo.remote(name='origin')

        # 1. GARANTIA: Baixar atualizações do GitHub antes de qualquer coisa
        print("⬇️  Baixando atualizações remotas (Pull)...")
        try:
            origin.pull()
            print("✅ Sincronização concluída.")
        except Exception as e:
            print(f"⚠️ Aviso no Pull (pode ser ignorado se for o primeiro uso): {e}")

        # 2. Verificar mudanças locais
        if not repo.is_dirty(untracked_files=True):
            print("✅ Nenhuma alteração encontrada para enviar.")
            return

        # 3. Adicionar TODOS os arquivos (app.py, csv, imagens)
        print("📂 Adicionando arquivos modificados...")
        repo.git.add(all=True)

        # 4. Criar o commit
        data_hoje = datetime.now().strftime("%d/%m/%Y %H:%M")
        mensagem = f"Atualização automática - {data_hoje}"
        repo.index.commit(mensagem)
        print(f"📝 Commit criado: {mensagem}")

        # 5. Enviar para o GitHub
        print("🚀 Enviando para o GitHub (Push)...")
        origin.push()
        
        print("\n✅ SUCESSO TOTAL! O projeto foi atualizado.")
        print("⏳ Aguarde o processamento no Streamlit Cloud.")

    except Exception as e:
        print("\n❌ ERRO CRÍTICO:")
        print(e)
        print("\nSUGESTÃO: Se o erro for de 'refs', tente rodar 'git pull origin main' manualmente no CMD.")

if __name__ == "__main__":
    atualizar_projeto()
    input("\nPressione Enter para sair...")