import customtkinter as ctk
from tkinter import filedialog, messagebox
import os
import shutil
import threading
import time
from mutagen.mp3 import MP3
import pygame
import tkinter as tk
from PIL import Image, ImageTk, ImageDraw

pygame.mixer.init()
sincronizando_barra = False  # Para evitar conflitos durante o clique
posicao_manual = -1          # Armazena a posição ajustada manualmente

# Configuração inicial do CustomTkinter
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("dark-blue")

# Variáveis globais
biblioteca_musicas = {}
musica_atual = None
player_ativo = False
utilizador_atual = None
musicas_recentemente_tocadas = []
base_path = "artistas/"



# Caminho da pasta onde as músicas serão armazenadas
pasta_biblioteca = os.path.join(os.getcwd(), "biblioteca_musicas")
if not os.path.exists(pasta_biblioteca):
    os.makedirs(pasta_biblioteca)

# Funções do gerenciador de música
def carregar_musica():
    global musica_atual
    caminhos_arquivos = filedialog.askopenfilenames(filetypes=[("Arquivos de Áudio", "*.mp3 *.wav")])
    if caminhos_arquivos:
        for caminho in caminhos_arquivos:
            nome_musica = os.path.basename(caminho)
            caminho_destino = os.path.join(pasta_biblioteca, nome_musica)

            if nome_musica not in biblioteca_musicas:
                shutil.copy2(caminho, caminho_destino)
                biblioteca_musicas[nome_musica] = {"caminho": caminho_destino, "like": False}

        musica_atual = caminhos_arquivos[0]
        status_label.configure(text=f"{len(caminhos_arquivos)} músicas carregadas.")
        
        # Atualizar a lista de músicas após carregar
        atualizar_lista_musicas()
        salvar_biblioteca_musicas()

def selecionar_musica(nome):
    global musica_atual
    if nome in biblioteca_musicas:
        musica_atual = biblioteca_musicas[nome]["caminho"]
        status_label.configure(text=f"{nome}")

def tocar_musica():
    global player_ativo
    if musica_atual:
        parar_musica()
        try:
            pygame.mixer.music.load(musica_atual)
            pygame.mixer.music.play()
            player_ativo = True
            status_label.configure(text=f"Tocando: {os.path.basename(musica_atual)}")

            # Adicionar a música à lista de recentemente tocadas
            if musica_atual not in musicas_recentemente_tocadas:
                musicas_recentemente_tocadas.insert(0, musica_atual)
            # Limitar para as últimas 3 músicas
            if len(musicas_recentemente_tocadas) > 3:
                musicas_recentemente_tocadas.pop()

            thread = threading.Thread(target=atualizar_barra_progresso)
            thread.daemon = True
            thread.start()
            atualizar_recents()
        except Exception as e:
            messagebox.showerror("Erro", f"Não foi possível tocar a música: {e}")
    else:
        messagebox.showwarning("Nenhuma música selecionada", "Por favor, selecione uma música para tocar.")

def parar_musica():
    global player_ativo
    if player_ativo:
        pygame.mixer.music.stop()
        player_ativo = False
    status_label.configure(text="Parado")
    barra_progresso.set(0.0)

def atualizar_barra_progresso():
    """Atualiza a barra de progresso enquanto a música toca."""
    global musica_atual, player_ativo, sincronizando_barra, posicao_manual
    if musica_atual:
        try:
            audio = MP3(musica_atual)
            duracao = audio.info.length

            while player_ativo:
                if not sincronizando_barra:
                    # Se uma posição manual foi definida, sincroniza com ela
                    if posicao_manual != -1:
                        posicao_atual = posicao_manual
                        posicao_manual = -1  # Reseta após usar
                    else:
                        posicao_atual = pygame.mixer.music.get_pos() / 1000

                    barra_progresso.set(posicao_atual / duracao)

                time.sleep(0.5)  # Atualização a cada 500ms
        except Exception as e:
            print(f"Erro ao atualizar a barra de progresso: {e}")

def alterar_posicao(event):
    """Ajusta a posição da música e sincroniza a barra de progresso."""
    global musica_atual, sincronizando_barra, posicao_manual
    if musica_atual and player_ativo:
        try:
            sincronizando_barra = True  # Interrompe a atualização contínua

            # Calcula a nova posição com base no clique
            largura_barra = barra_progresso.winfo_width()
            clique_x = event.x
            audio = MP3(musica_atual)
            duracao = audio.info.length
            nova_posicao = (clique_x / largura_barra) * duracao

            # Atualiza a posição no mixer e sincroniza a barra
            pygame.mixer.music.set_pos(nova_posicao)
            barra_progresso.set(nova_posicao / duracao)
            posicao_manual = nova_posicao
        except Exception as e:
            print(f"Erro ao alterar posição: {e}")
        finally:
            sincronizando_barra = False



def atualizar_lista_musicas():
    # Carregar a biblioteca de músicas ao iniciar
    biblioteca_musicas = carregar_biblioteca_musicas()

    for widget in music_grid_frame.winfo_children():
        widget.destroy()

    for nome, dados in biblioteca_musicas.items():
        cor = "red" if dados["like"] else "white"
        musica_button = ctk.CTkButton(music_grid_frame, 
                                      text=nome, 
                                      fg_color=cor, 
                                      text_color="black",
                                      command=lambda nome=nome: selecionar_musica(nome))
        musica_button.pack(padx=10, pady=10, fill="x")

# Funções de autenticação
def login():
    utilizador = utilizador_entry.get().strip()
    senha = senha_entry.get().strip()

    if not utilizador or not senha:
        messagebox.showerror("Erro", "Por favor, preencha todos os campos.")
        return

    caminho_utilizador = os.path.join("dados_utilizador", utilizador)

    if os.path.exists(caminho_utilizador):
        f = open(os.path.join(caminho_utilizador, "dados.txt"), "r")
        dados = f.readlines()
        f.close()
        senha_correta = dados[1].split(": ")[1].strip()


        if senha == senha_correta:
                global utilizador_atual
                utilizador_atual = utilizador
                login_frame.pack_forget()
                app_frame.pack(expand=True, fill="both", padx=20, pady=20)
                return

    messagebox.showerror("Erro", "Utilizador ou senha incorretos.")

def criar_conta():
    novo_utilizador = novo_utilizador_entry.get().strip()
    nova_senha = nova_senha_entry.get().strip()
    confirmar_senha = confirmar_senha_entry.get().strip()

    caminho_utilizador = os.path.join("dados_utilizador", novo_utilizador)

    if not novo_utilizador or not nova_senha or not confirmar_senha:
        messagebox.showerror("Erro", "Por favor, preencha todos os campos.")
        return

    if nova_senha != confirmar_senha:
        messagebox.showerror("Erro", "As senhas não coincidem.")
        return

    if os.path.exists(caminho_utilizador):
        messagebox.showerror("Erro", "Nome de utilizador já está em uso.")
        return

    os.makedirs(caminho_utilizador)
    f = open(os.path.join(caminho_utilizador, "dados.txt"), "w")
    f.write(f"Utilizador: {novo_utilizador}\nSenha: {nova_senha}")
    f.close()


    messagebox.showinfo("Sucesso", "Conta criada com sucesso.")
    criar_conta_frame.pack_forget()
    login_frame.pack(expand=True, fill="both", padx=20, pady=20)

        
def verificar_admin(utilizador, senha):
    """Verifica se o utilizador é um administrador."""
    admin_utilizador = "admin"
    admin_senha = "admin123"
    return utilizador == admin_utilizador and senha == admin_senha

def remover_utilizador():
    """Remove um utilizador selecionado."""
    utilizador_selecionado = utilizador_entry.get().strip()
    if not utilizador_selecionado:
        messagebox.showerror("Erro", "Por favor, selecione um utilizador para remover.")
        return

    caminho_utilizador = os.path.join("dados_utilizador", utilizador_selecionado)
    if os.path.exists(caminho_utilizador):
        shutil.rmtree(caminho_utilizador)
        messagebox.showinfo("Sucesso", f"Utilizador {utilizador_selecionado} removido com sucesso.")
    else:
        messagebox.showerror("Erro", "Utilizador não encontrado.")

def mostrar_tela_admin():
    """Mostra a tela de administração."""
    for widget in conteudo_frame.winfo_children():
        widget.destroy()

    admin_label = ctk.CTkLabel(conteudo_frame, text="Administração", font=("Roboto", 24, "bold"))
    admin_label.pack(pady=20)

    remover_utilizador_label = ctk.CTkLabel(conteudo_frame, text="Remover utilizador", font=("Roboto", 18))
    remover_utilizador_label.pack(pady=10)

    global utilizador_entry
    utilizador_entry = ctk.CTkEntry(conteudo_frame, placeholder_text="Utilizador", width=300, height=33)
    utilizador_entry.pack(pady=10)

    remover_utilizador_button = ctk.CTkButton(conteudo_frame, text="Remover", command=remover_utilizador, fg_color="#FF0000", text_color="white", width=300, height=33, corner_radius=15)
    remover_utilizador_button.pack(pady=10)

def login():
    global utilizador_atual
    utilizador = utilizador_entry.get().strip()
    senha = senha_entry.get().strip()

    if not utilizador or not senha:
        messagebox.showerror("Erro", "Por favor, preencha todos os campos.")
        return

    if verificar_admin(utilizador, senha):
        utilizador_atual = utilizador
        login_frame.pack_forget()
        app_frame.pack(expand=True, fill="both", padx=20, pady=20)
        mostrar_tela_admin()
        return

    caminho_utilizador = os.path.join("dados_utilizador", utilizador)
    if os.path.exists(caminho_utilizador):
        f = open(os.path.join(caminho_utilizador, "dados.txt"), "r")
        dados = f.readlines()
        f.close()
        senha_correta = dados[1].split(": ")[1].strip()

        if senha == senha_correta:
            utilizador_atual = utilizador
            login_frame.pack_forget()
            app_frame.pack(expand=True, fill="both", padx=20, pady=20)
            return

    messagebox.showerror("Erro", "Utilizador ou senha incorretos.")

# Configuração da interface
def mostrar_tela_criar_conta():
    login_frame.pack_forget()
    criar_conta_frame.pack(expand=True, fill="both", padx=20, pady=20)

def mostrar_dados_utilizador():
    """Exibe os dados do utilizador na área do conteúdo quando o botão 'Conta' é clicado, ou mantém o conteúdo atual caso não haja utilizador logado."""
    global utilizador_atual

    if utilizador_atual:
        # Limpar o conteúdo atual do frame
        for widget in conteudo_frame.winfo_children():
            widget.destroy()

        caminho_utilizador = os.path.join("dados_utilizador", utilizador_atual, "dados.txt")

        if os.path.exists(caminho_utilizador):
            f = open(caminho_utilizador, "r")
            try:
                dados = f.read()
            finally:
                f.close()

            # Exibe os dados do utilizador no frame
            dados_label = ctk.CTkLabel(conteudo_frame, text=dados, font=("Roboto", 16))
            dados_label.pack(pady=20, padx=20)
        else:
            messagebox.showwarning("Erro", "Não foi possível encontrar os dados do utilizador.")
    else:
        # Mostra uma mensagem de erro, mas não altera a tela
        messagebox.showerror("Erro", "Nenhum utilizador está logado no momento.")

def restaurar_tela_padrao():
    """Restaura o conteúdo padrão do frame."""
    # Limpar o conteúdo atual do frame
    for widget in conteudo_frame.winfo_children():
        widget.destroy()

def mostrar_biblioteca():
    """Exibe a lista de músicas carregadas na biblioteca."""
    # Limpar o conteúdo atual do frame
    for widget in conteudo_frame.winfo_children():
        widget.destroy()

    # Ordena as músicas
    lista_musicas = sorted(biblioteca_musicas.keys())

    # Exibe as músicas na tela
    for i, nome_musica in enumerate(lista_musicas):
        musica_button = ctk.CTkButton(conteudo_frame, 
                                      text=nome_musica, 
                                      command=lambda nome=nome_musica: selecionar_musica(nome))
        musica_button.grid(row=i+1, column=0, padx=20, pady=5, sticky="w")

def salvar_biblioteca_musicas():
    caminho_arquivo_biblioteca = os.path.join(pasta_biblioteca, 'biblioteca_musicas.txt')
    try:
        f = open(caminho_arquivo_biblioteca, 'w')
        try:
            for nome, dados in biblioteca_musicas.items():
                f.write(f"{nome}|{dados['like']}\n")
        finally:
            f.close()
    except Exception as e:
        print(f"Erro ao salvar a biblioteca de músicas: {e}")


def carregar_biblioteca_musicas():
    caminho_arquivo_biblioteca = os.path.join(pasta_biblioteca, 'biblioteca_musicas.txt')
    try:
        if os.path.exists(caminho_arquivo_biblioteca):
            biblioteca = {}
            f = open(caminho_arquivo_biblioteca, 'r')
            try:
                for linha in f:
                    # Certifique-se de que a linha tenha exatamente dois elementos após a divisão
                    partes = linha.strip().split('|')
                    if len(partes) == 2:
                        nome, like = partes
                        caminho_completo = os.path.join(pasta_biblioteca, nome)
                        biblioteca[nome] = {"caminho": caminho_completo, "like": like == 'True'}
                    else:
                        print(f"Formato inválido na linha: {linha}")
            finally:
                f.close()
            return biblioteca
    except Exception as e:
        print(f"Erro ao carregar a biblioteca de músicas: {e}")
    return {}

def atualizar_recents():
    # Limpar o conteúdo atual de músicas recentes
    for widget in conteudo_frame.winfo_children():
        widget.destroy()

def salvar_musicas_recentemente_tocadas():
    caminho_arquivo_recent = os.path.join(pasta_biblioteca, 'musicas_recentemente_tocadas.txt')
    try:
        f = open(caminho_arquivo_recent, 'w')
        try:
            for musica in musicas_recentemente_tocadas:
                f.write(f"{musica}\n")
        finally:
            f.close()
    except Exception as e:
        print(f"Erro ao salvar músicas recentes: {e}")

def carregar_musicas_recentemente_tocadas():
    caminho_arquivo_recent = os.path.join(pasta_biblioteca, 'musicas_recentemente_tocadas.txt')
    try:
        if os.path.exists(caminho_arquivo_recent):
            f = open(caminho_arquivo_recent, 'r')
            try:
                return [linha.strip() for linha in f]
            finally:
                f.close()
    except Exception as e:
        print(f"Erro ao carregar músicas recentes: {e}")
    return []

def alterar_volume(valor):
    """Ajusta o volume da música com base no valor do slider."""
    pygame.mixer.music.set_volume(float(valor))

musicas_recentemente_tocadas = carregar_musicas_recentemente_tocadas()

for i, musica in enumerate(musicas_recentemente_tocadas):
    musica_button = ctk.CTkButton(conteudo_frame, 
                                  text=musica, 
                                  command=lambda musica=musica: selecionar_musica(musica))
    musica_button.grid(row=i+2, column=0, padx=20, pady=10, sticky="w")

biblioteca_musicas = carregar_biblioteca_musicas()

def carregar_artistas_por_genero():
    artistas_por_genero = {}
    caminho_artistas = "artistas"  # Caminho onde a pasta de artistas está localizada

    for genero in os.listdir(caminho_artistas):
        genero_path = os.path.join(caminho_artistas, genero)
        if os.path.isdir(genero_path):  # Verifica se é uma pasta
            artistas_por_genero[genero] = []
            for arquivo in os.listdir(genero_path)[:5]:  # Limita a 5 artistas
                if arquivo.endswith(".txt"):
                    nome_artista = arquivo.replace(".txt", "")  # Nome do artista
                    artistas_por_genero[genero].append(nome_artista)

    return artistas_por_genero

# Função para mostrar os artistas no frame
def mostrar_artistas(genero_selecionado):
    if not genero_selecionado:
        messagebox.showwarning("Seleção de Gênero", "Por favor, selecione um gênero de música!")
        return

    caminho_arquivo = os.path.join(base_path, "artistas.txt")
    artistas_por_genero = {}

    # Lê o arquivo e organiza os artistas por gênero
    try:
        f = open(caminho_arquivo, "r", encoding="utf-8")
        try:
            categoria_atual = None
            for linha in f:
                linha = linha.strip()
                if linha.startswith("[") and linha.endswith("]"):
                    categoria_atual = linha[1:-1]
                    if categoria_atual not in artistas_por_genero:
                        artistas_por_genero[categoria_atual] = []
                elif linha.startswith("artistas:") and categoria_atual:
                    artistas = linha.split(":")[1].strip().split(", ")
                    artistas_por_genero[categoria_atual].extend(artistas)
        finally:
            f.close()
    except FileNotFoundError:
        messagebox.showerror("Erro", f"Arquivo não encontrado: {caminho_arquivo}")
        return

    # Obter artistas do gênero selecionado
    artistas = artistas_por_genero.get(genero_selecionado, [])

    # Limpar o frame de conteúdo
    for widget in conteudo_frame.winfo_children():
        widget.destroy()

    if artistas:
        row, col = 0, 0
        for artista in artistas:
            imagem_path = os.path.join(base_path, genero_selecionado, f"{artista}.png")

            if os.path.exists(imagem_path):
                try:
                    # Criar imagem circular
                    img = Image.open(imagem_path).resize((100, 100))
                    mask = Image.new("L", (100, 100), 0)
                    draw = ImageDraw.Draw(mask)
                    draw.ellipse((0, 0, 100, 100), fill=255)
                    img = Image.composite(img, Image.new("RGB", (100, 100), (0, 0, 0)), mask)
                    img = ImageTk.PhotoImage(img)

                    # Criar frame para artista
                    artista_frame = tk.Frame(conteudo_frame, bg="#f0f0f0")
                    artista_frame.grid(row=row, column=col, padx=10, pady=10)

                    img_label = tk.Label(artista_frame, image=img, bg="#f0f0f0")
                    img_label.image = img
                    img_label.pack()

                    nome_label = tk.Label(artista_frame, text=artista, font=("Helvetica", 12), bg="#f0f0f0")
                    nome_label.pack()

                    # Vincula a função para exibir detalhes
                    img_label.bind("<Button-1>", lambda e, nome=artista: mostrar_detalhes_artista(nome))
                    nome_label.bind("<Button-1>", lambda e, nome=artista: mostrar_detalhes_artista(nome))

                    col += 1
                    if col > 3:
                        col = 0
                        row += 1

                except Exception as e:
                    print(f"Erro ao carregar imagem para {artista}: {e}")

    else:
        label_nenhum_artista = tk.Label(
            conteudo_frame,
            text="Nenhum artista encontrado",
            font=("Helvetica", 14, "italic"),
            bg="#f0f0f0",
            fg="#888"
        )
        label_nenhum_artista.pack(pady=10, fill="x")

# Função para mostrar o menu de seleção de artistas
def mostrar_menu_artistas():
    # Limpar o conteúdo anterior
    for widget in conteudo_frame.winfo_children():
        widget.destroy()

    # Lista de gêneros de música
    generos = ["rock", "pop", "hiphop", "jazz", "eletronica", "rap"]

    # Criar um botão para cada gênero
    for genero in generos:
        btn_genero = ctk.CTkButton(
            conteudo_frame,
            text=genero.capitalize(),
            command=lambda genero=genero: mostrar_artistas(genero),
            font=("Helvetica", 16, "bold"),
            width=200,  # Tamanho do botão
            height=60,  # Tamanho do botão
            fg_color="#5B299B",  # Cor de fundo
            text_color="white",  # Cor do texto
            corner_radius=10
        )
        btn_genero.pack(padx=20, pady=10, fill="x")

def carregar_artistas_com_detalhes():
    artistas = {}
    base_path = "artistas"  # Pasta base contendo os arquivos
    for genero in os.listdir(base_path):
        genero_path = os.path.join(base_path, genero)
        if os.path.isdir(genero_path):
            for artista_folder in os.listdir(genero_path):
                artista_path = os.path.join(genero_path, artista_folder)
                if os.path.isdir(artista_path):
                    artistas[artista_folder] = {"álbuns": [], "músicas": []}
                    albuns_path = os.path.join(artista_path, "álbuns")
                    musicas_path = os.path.join(artista_path, "músicas")

                    # Carregar álbuns
                    if os.path.exists(albuns_path):
                        artistas[artista_folder]["álbuns"] = os.listdir(albuns_path)

                    # Carregar músicas
                    if os.path.exists(musicas_path):
                        artistas[artista_folder]["músicas"] = os.listdir(musicas_path)
    return artistas

def mostrar_detalhes_artista(artista_selecionado):
    caminho_arquivo = os.path.join(base_path, "artistas.txt")
    detalhes_artista = {}

    # Lê detalhes do artista
    try:
        f = open(caminho_arquivo, "r", encoding="utf-8")
        try:
            linhas = f.readlines()

            for i, linha in enumerate(linhas):
                if linha.strip() == f"[{artista_selecionado}]":
                    for j in range(i + 1, len(linhas)):
                        if linhas[j].startswith("["):  # Encerra quando encontra o próximo bloco
                            break
                        linha_stripped = linhas[j].strip()
                        if ": " in linha_stripped:  # Garantir que há chave: valor
                            chave, valor = linha_stripped.split(": ", 1)
                            detalhes_artista[chave] = valor.split(", ")
                        else:
                            print(f"Linha inválida ignorada: {linha_stripped}")
        finally:
            f.close()
    except FileNotFoundError:
        messagebox.showerror("Erro", f"Arquivo não encontrado: {caminho_arquivo}")
        return

    # Limpar o frame principal
    for widget in conteudo_frame.winfo_children():
        widget.destroy()

    # Configurar fundo preto
    conteudo_frame.configure(fg_color="black")

    # Título do Artista
    artista_label = ctk.CTkLabel(conteudo_frame, text=artista_selecionado, font=("Helvetica", 18, "bold"), fg_color="black", text_color="white")
    artista_label.pack(pady=10)

    # Frame para Álbuns
    albuns_frame = ctk.CTkFrame(conteudo_frame, fg_color="black")
    albuns_frame.pack(fill="x", pady=10)

    # Centralizar os álbuns
    albuns_inner_frame = tk.Frame(albuns_frame, bg="black")
    albuns_inner_frame.pack(side="top", pady=10)

    albuns = detalhes_artista.get("álbuns", [])
    albuns_imagens = detalhes_artista.get("álbuns_imagens", [])

    for i, (album, imagem_path) in enumerate(zip(albuns, albuns_imagens)):
        if os.path.exists(imagem_path):
            img = Image.open(imagem_path).resize((100, 100))
            img = ImageTk.PhotoImage(img)

            # Frame para cada álbum
            album_frame = tk.Frame(albuns_inner_frame, bg="black")
            album_frame.pack(side="left", padx=20)  # Espaçamento entre os álbuns

            img_label = tk.Label(album_frame, image=img, bg="black")
            img_label.image = img  # Referência para a imagem
            img_label.pack()

            album_label = tk.Label(album_frame, text=album, font=("Helvetica", 12), bg="black", fg="white")
            album_label.pack()

    # Frame para Músicas
    musicas_frame = ctk.CTkFrame(conteudo_frame, fg_color="black")
    musicas_frame.pack(fill="x", pady=20)

    musicas = detalhes_artista.get("músicas", [])
    if musicas:
        musicas_label = ctk.CTkLabel(musicas_frame, text="Músicas", font=("Helvetica", 16, "bold"), fg_color="black", text_color="white")
        musicas_label.pack(pady=10)

        for musica in musicas:
            musica_label = tk.Label(musicas_frame, text=musica, font=("Helvetica", 12), bg="black", fg="white")
            musica_label.pack(pady=5)
    else:
        no_music_label = tk.Label(musicas_frame, text="Nenhuma música disponível.", font=("Helvetica", 12), bg="black", fg="white")
        no_music_label.pack(pady=5)
        

app = ctk.CTk()
app.title("MusicWave")
app.geometry("1024x640")
app.grid_rowconfigure(0, weight=1)
app.grid_columnconfigure(1, weight=1)

# Tela de login
login_frame = ctk.CTkFrame(app, corner_radius=10)
login_frame.pack(expand=True, fill="both", padx=20, pady=20)

login_label = ctk.CTkLabel(login_frame, text="Login", font=("Roboto", 24, "bold"))
login_label.pack(pady=20)

utilizador_entry = ctk.CTkEntry(login_frame, placeholder_text="utilizador", width=522, height=33)
utilizador_entry.pack(pady=10, padx=20)

senha_entry = ctk.CTkEntry(login_frame, placeholder_text="Senha", show="*", width=522, height=33)
senha_entry.pack(pady=10, padx=20)

login_button = ctk.CTkButton(login_frame, text="Entrar", command=login, fg_color="#5B299B", text_color="white", width=522, height=33, corner_radius=15)
login_button.pack(pady=10)

criar_conta_button = ctk.CTkButton(login_frame, text="Criar Conta", command=mostrar_tela_criar_conta, fg_color="#5B299B", text_color="white", width=522, height=33, corner_radius=15)
criar_conta_button.pack(pady=10)

entrar_sem_login_label = ctk.CTkLabel(
    login_frame, 
    text="Entrar como convidado", 
    text_color="lightcoral",  # Texto em vermelho claro
    cursor="hand2",  # Cursor de mão para indicar que é clicável
    font=("Roboto", 16)  # Fonte opcional para ajustar o estilo
)
entrar_sem_login_label.pack(pady=10)
entrar_sem_login_label.bind("<Button-1>", lambda e: [login_frame.pack_forget(), app_frame.pack(expand=True, fill="both", padx=20, pady=20)])

# Tela de criação de conta
criar_conta_frame = ctk.CTkFrame(app, corner_radius=10)

criar_conta_label = ctk.CTkLabel(criar_conta_frame, text="Criar Conta", font=("Roboto", 24, "bold"))
criar_conta_label.pack(pady=20)

novo_utilizador_entry = ctk.CTkEntry(criar_conta_frame, placeholder_text="Novo Utilizador", width=522, height=33)
novo_utilizador_entry.pack(pady=10, padx=20)


nova_senha_entry = ctk.CTkEntry(criar_conta_frame, placeholder_text="Senha", show="*", width=522, height=33)
nova_senha_entry.pack(pady=10, padx=20)


confirmar_senha_entry = ctk.CTkEntry(criar_conta_frame, placeholder_text="Confirmar Senha", show="*", width=522, height=33)
confirmar_senha_entry.pack(pady=10, padx=20)

salvar_conta_button = ctk.CTkButton(criar_conta_frame, text="Criar Conta", command=criar_conta, fg_color="#5B299B", text_color="white", width=522, height=43, corner_radius=15)
salvar_conta_button.pack(pady=20)

btn_voltar_login = ctk.CTkButton(criar_conta_frame, fg_color="#5B299B", text_color="white", width=522, height=41, corner_radius=15, text="Voltar", command=lambda: [criar_conta_frame.pack_forget(), login_frame.pack(expand=True, fill="both", padx=20, pady=20)])
btn_voltar_login.pack(pady=10)

# Tela principal
app_frame = ctk.CTkFrame(app)

# Cabeçalho da tela principal
app_label = ctk.CTkLabel(app_frame, text="MusicWave", font=("Roboto", 24, "bold"))
app_label.grid(row=0, column=0, padx=20, pady=10, sticky="w")

btn_conta = ctk.CTkButton(app_frame, text="Conta", width=80, corner_radius=10, fg_color="#5B299B", text_color="white", command=mostrar_dados_utilizador)
btn_conta.grid(row=0, column=1, padx=20, pady=10, sticky="e")

# Menu lateral 
menu_frame = ctk.CTkFrame(app_frame, width=200, corner_radius=10)
menu_frame.grid(row=1, column=0, sticky="nsw", padx=10, pady=10)

menu_label = ctk.CTkLabel(menu_frame, text="Música", font=("Roboto", 20, "bold"))
menu_label.pack(pady=20)

search_entry = ctk.CTkEntry(menu_frame, placeholder_text="Pesquisar...")
search_entry.pack(pady=10, padx=20, fill="x")

btn_home = ctk.CTkButton(menu_frame, text="Home", width=180, corner_radius=5, fg_color="purple")
btn_home.pack(pady=5)

btn_playlists = ctk.CTkButton(menu_frame, text="Playlists", width=180, corner_radius=5)
btn_playlists.pack(pady=5)

btn_albums = ctk.CTkButton(menu_frame, text="Álbuns", width=180, corner_radius=5)
btn_albums.pack(pady=5)

btn_artists = ctk.CTkButton(menu_frame, text="Artistas", width=180, corner_radius=5, command=mostrar_menu_artistas)
btn_artists.pack(pady=5)

btn_carregar_musica = ctk.CTkButton(menu_frame, text="Carregar Música", width=180, corner_radius=5, command=carregar_musica)
btn_carregar_musica.pack(pady=5)

btn_biblioteca = ctk.CTkButton(menu_frame, text="Biblioteca", width=180, corner_radius=5, command=mostrar_biblioteca)
btn_biblioteca.pack(pady=5)

# Conteúdo principal da tela de música
conteudo_frame = ctk.CTkFrame(app_frame, corner_radius=10)
conteudo_frame.grid(row=1, column=1, sticky="nsew", padx=10, pady=10)

conteudo_label = ctk.CTkLabel(conteudo_frame, text="Bem-vindo", font=("Roboto", 26, "bold"))
conteudo_label.grid(row=0, column=0, padx=20, pady=10, sticky="w")

btn_conta = ctk.CTkButton(app_frame, text="Conta", width=80, corner_radius=10, fg_color="#5B299B", text_color="white", command=mostrar_dados_utilizador)
btn_conta.grid(row=0, column=1, padx=20, pady=10, sticky="e")

recent_label = ctk.CTkLabel(conteudo_frame, text="Ouvido recentemente", font=("Roboto", 18))
recent_label.grid(row=1, column=0, padx=20, pady=10, sticky="w")

# Placeholder de músicas recentes
for i in range(3):
    placeholder = ctk.CTkFrame(conteudo_frame, width=150, height=150, fg_color="gray")
    placeholder.grid(row=2, column=i, padx=10, pady=10)

# Grid para exibir músicas
music_grid_frame = ctk.CTkScrollableFrame(conteudo_frame, width=600, height=300)
music_grid_frame.grid(row=3, column=0, columnspan=3, sticky="nsew", padx=20, pady=10)

# Controles de reprodução
controles_frame = ctk.CTkFrame(app_frame, height=80, corner_radius=10)
controles_frame.grid(row=2, column=0, columnspan=2, sticky="ew", padx=10, pady=10)

barra_progresso = ctk.CTkProgressBar(controles_frame, height=10)
barra_progresso.set(0.0)
barra_progresso.pack(fill="x", padx=20, pady=10)
barra_progresso.bind("<Button-1>", alterar_posicao)  # Vincula o clique na barra

status_label = ctk.CTkLabel(controles_frame, text="Bem-vindo ao Gestor de Música", font=("Roboto", 14))
status_label.pack(side="left", padx=20)

btn_prev = ctk.CTkButton(controles_frame, text="\u23ee\ufe0f", width=50)
btn_prev.pack(side="left", padx=5)

btn_play = ctk.CTkButton(controles_frame, text="\u25b6\ufe0f", width=50, command=tocar_musica)
btn_play.pack(side="left", padx=5)

btn_next = ctk.CTkButton(controles_frame, text="\u23ed\ufe0f", width=50)
btn_next.pack(side="left", padx=5)

btn_stop = ctk.CTkButton(controles_frame, text="\u23f9\ufe0f", width=50, command=parar_musica)
btn_stop.pack(side="left", padx=5)

volume_slider = ctk.CTkSlider(controles_frame, from_=0, to=1, number_of_steps=100, command=alterar_volume)
volume_slider.set(0.5)  # Valor inicial do volume
volume_slider.pack(side="right", padx=20)


# Função para sair
def logout():
    global utilizador_atual
    utilizador_atual = None
    app_frame.pack_forget()
    login_frame.pack(expand=True, fill="both", padx=20, pady=20)

# Configuração do grid
app_frame.grid_rowconfigure(1, weight=1)
app_frame.grid_columnconfigure(1, weight=1)

musicas_recentemente_tocadas = carregar_musicas_recentemente_tocadas()
biblioteca_musicas = carregar_biblioteca_musicas()

# Inicializar o app
app.mainloop()
