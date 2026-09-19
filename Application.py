from tkinter import *
import tkinter as tk
from tkinter import messagebox, simpledialog
from tkinter import ttk
from tkcalendar import DateEntry

from datetime import date, datetime

import qrcode
import PIL.Image as pilImg
from PIL import ImageTk
import threading
import numpy as np

from Chat import Chat
from BancoDeDados import DataBase
from Gasto import Gasto
from Camera import Camera
from Analytics import Analytics
import const

""" Constantes """
MAPEAMENTO_CATEGORIAS = {
    "Gasto Fixo": const.CATEGORIAS_FIXOS,
    "Gasto Não Fixo": const.CATEGORIAS_N_FIXOS,
    "Entrada": const.CATEGORIAS_INCOME,
    "Investimento": const.CATEGORIAS_INVEST,
}

""" View Classes """
class MainView(Frame):
    def __init__(self, parent):
        super().__init__(parent, bg="#f4f6f9")
        self.db = DataBase()
        self.analisty = Analytics()

        App.create_label(
            self, text="Página Inicial", font=("Helvetica", 14, "bold"), pady=20
        )

        self.content = Frame(self, bg="white")
        self.content.pack(fill="both", expand=True, padx=10, pady=10)
        self.rowconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)
        self.rowconfigure(2, weight=1)
        self.content.grid_columnconfigure(0, weight=1, uniform="grupo1")
        self.content.grid_columnconfigure(1, weight=1, uniform="grupo1")
        self.content.grid_columnconfigure(2, weight=1, uniform="grupo1")
        self.content.grid_columnconfigure(3, weight=1, uniform="grupo1")

        self.mostraValores()

        # Tabela dos gastos recentes
        Label(self.content, bg="white", text="Últimos Gastos", font=("Helvetica", 12, "bold")).grid(row=1, column=0, columnspan=2, padx=10, pady=15, sticky="nswe")
        Label(self.content, bg="white", text="Orçamento do Mês", font=("Helvetica", 12, "bold")).grid(row=1, column=2, columnspan=2, padx=10, pady=15, sticky="nswe")

        self.frame_tabela = Frame(self.content)
        self.frame_tabela.grid(row=2, column=0, sticky="nsew", columnspan=2, padx=10, pady=15)

        self.colunas = []
        _, self.colunas = DataBase.consultaManual("select nome, valor, categoria, dia from gastos order by id DESC")

        self.tree = App.create_tree_table(self.frame_tabela, self.colunas)
        self.carregar_ultmos_gastos()


        # Gráfico de orçamento do mês
        o_img_path, _  = self.analisty.gastoOrcamentario()

        self.showChart(o_img_path, row=2, col=2, colspan=2)

    def mostraValores(self):
        self.saldoTotal = StringVar()
        self.saldoMensal = StringVar()
        self.gastoMensal = StringVar()
        self.mediaDiaria = StringVar()

        # Saldo da conta
        Label(self.content, bg="#b2dcff", textvariable=self.saldoTotal, font=("Helvetica", 10, "bold")).grid(row=0, column=0, padx=10, pady=15, sticky="nswe")
        # Saldo do Mês
        self.lbl_saldo_mensal = Label(self.content, bg="#b2dcff", textvariable=self.saldoMensal, font=("Helvetica", 10, "bold"))
        self.lbl_saldo_mensal.grid(row=0, column=1, padx=10, pady=15, sticky="nswe")
        # Gastos do Mês
        Label(self.content, bg="#b2dcff", textvariable=self.gastoMensal, font=("Helvetica", 10, "bold")).grid(row=0, column=2, padx=10, pady=15, sticky="nswe")
        # Média diária
        Label(self.content, bg="#b2dcff", textvariable=self.mediaDiaria, font=("Helvetica", 10, "bold")).grid(row=0, column=3, padx=10, pady=15, sticky="nswe")

        self.atualizar_kpis()

    def atualizar_kpis(self):
        """Consulta o banco de dados e atualiza o texto de todos os cards."""
        hoje = datetime.today()
        mes_atual = hoje.strftime("%Y-%m")
        dia_atual = max(hoje.day, 1)  # previne divisão por zero no dia 0

        # Consulta saldo total
        saldo_t = DataBase.consultaSaldo()
        saldo_t_val = saldo_t if saldo_t is not None else 0.0

        # Consulta do mês atual: [0] = saldo do mês, [1] = gastos do mês
        dados_mes = DataBase.consultaSaldo(mes=mes_atual)
        saldo_m = dados_mes[0] if dados_mes and dados_mes[0] is not None else 0.0
        gasto_m = dados_mes[1] if dados_mes and dados_mes[1] is not None else 0.0
        entrada_m = dados_mes[2] if dados_mes and dados_mes[1] is not None else 0.0

        media_d = gasto_m / dia_atual

        # Atualiza as variáveis reativas (o Tkinter atualiza a tela na hora)
        self.saldoTotal.set(f"Saldo Total\nR$ {saldo_t_val:.2f}")
        self.saldoMensal.set(f"Saldo Mês\nR$ {saldo_m:.2f}")
        self.gastoMensal.set(f"Total Gasto\nR$ {gasto_m:.2f}")
        self.mediaDiaria.set(f"Média/Dia\nR$ {media_d:.2f}")

        if saldo_m < 0:
            self.lbl_saldo_mensal.config(
                fg="#c0392b"
            )  # Vermelho para valores negativos
        elif gasto_m > (0.8*entrada_m):
            self.lbl_saldo_mensal.config(
                fg="#c0a52b"
            )  # Amarelo para gasto maior que 80%
        else:
            self.lbl_saldo_mensal.config(
                fg="#2c3e50"
            )  # Cor padrão/neutra


    def carregar_ultmos_gastos(self, dados_fetchall=None):
        dados_fetchall, _ = DataBase.consultaManual("select nome, valor, categoria, dia from gastos where tipo_gasto='Gasto Não Fixo' order by dia DESC, id DESC")
        for item in self.tree.get_children():
            self.tree.delete(item)

        cont = 0
        for linha in dados_fetchall:
            if cont == 10:
                break
            # Formata o valor monetário
            valores = list(linha)
            valores[1] = f"R$ {valores[1]:.2f}"
            self.tree.insert("", "end", values=valores)
            cont+= 1

    def showChart(self, img_path, row=0, col=0, colspan=1):
        # Moldura individual para cada gráfico/texto dentro da grade
        card = Frame(self.content, bg="white", bd=1, relief="solid")
        card.grid(row=row, column=col, columnspan=colspan, sticky="nsew", padx=10, pady=15)
        card.pack_propagate(False)  # Impede que o conteúdo altere o tamanho do card

        if img_path is not None:
            imagem_original = pilImg.open(img_path)
            img_label = Label(card, bg="white")
            img_label.pack(fill="both", expand=True)

            ultimo = {"w": 0, "h": 0}

            def redimensionar(event):
                w = event.width
                h = event.height

                if w > 60 and h > 60:
                    # Evita recálculos desnecessários por pequenas variações
                    if abs(w - ultimo["w"]) > 6 or abs(h - ultimo["h"]) > 6:
                        ultimo["w"] = w
                        ultimo["h"] = h

                        img_copy = imagem_original.copy()
                        img_copy.thumbnail((w - 10, h - 10), pilImg.Resampling.LANCZOS)

                        img_tk = ImageTk.PhotoImage(img_copy, master=card)
                        img_label.config(image=img_tk)
                        img_label.image = img_tk  # Previne Garbage Collector

            # O evento fica no card pai, prevenindo loop infinito do Label
            card.bind("<Configure>", redimensionar)
            return img_label
        else:
            aviso_label = Label(
                card, 
                text="Gráfico ainda não disponível\npara esse mês", 
                bg="white", 
                fg="#7f8c8d",
                justify="center",
                wraplength=180
            )
            aviso_label.pack(fill="both", expand=True)
            return aviso_label

class InserirGastoView(Frame):

    def __init__(self, parent):
        super().__init__(parent, bg="#f4f6f9")
        self.db = DataBase()
        label = Label(
            self, text="Tela: Inserir Novo Gasto", font=("Helvetica", 14, "bold")
        )
        label.pack(pady=20)

        self.imagem_capturada = None
        self.cadastro_manual()
        self.cadastro_upload()
        product_button = Button(self, text="Novo Produto", command=self.cadastro_nome_produto)
        product_button.pack(padx=(0, 0), pady=(0, 0))  

    def cadastro_manual(self):
        
        # Frame de campos de inserção
        form_frame = Frame(self)
        form_frame.pack(pady=10, padx=10)

        # Tipo
        self.prodTipo_var = StringVar()
        App.create_option_field(form_frame, "Tipo", textVar=self.prodTipo_var, valores=const.TIPOS_DE_GASTO, row=0, padx=5, pady=2)
        
        # Nome 
        self.prodName_var = StringVar()
        App.create_entry_field(form_frame, "Nome", textVar=self.prodName_var, row=1, padx=5, pady=2)

        # Data
        self.prodDate_var = StringVar()
        App.create_date_field(form_frame, "Data:", dateVar=self.prodDate_var, row=2, padx=5, pady=2)

        # Categoria
        self.prodCat_var = StringVar()
        self.cat_combo = App.create_option_field(form_frame, "Categoria", textVar=self.prodCat_var, valores=const.CATEGORIAS, row=3, padx=5, pady=2)
        self.prodTipo_var.trace_add("write", self.atualizar_categorias)

        # Valor
        self.prodValue_var = StringVar()
        App.create_entry_field(form_frame, "Valor", textVar=self.prodValue_var, row=4, padx=5, pady=2)

        # Metodo de Pagamento
        self.prodMet_var = StringVar()
        App.create_option_field(form_frame, "Método de Pagamento", textVar=self.prodMet_var, valores=const.METODOS_PAGAMENTO, row=5, padx=5, pady=2)
        

        # self.prodName_entry = Entry(self, textvar=self.prodName_text)
        # self.prodName_entry.pack(fill=BOTH, expand=False, padx=5, pady=5)

        confirm_button = Button(self, text="Cadastrar Gasto", command=self.confirmar_gasto)
        confirm_button.pack(padx=(0, 0), pady=(0, 0))

    def cadastro_upload(self):
        upload_button = Button(self, text="Extrair foto", command=self.abrir_popup_qrcode)
        upload_button.pack(padx=(0, 0), pady=(0, 0))

    def cadastro_nome_produto(self):
        answ = simpledialog.askstring(title="Registrar Produto", prompt="digite a chave e valor do produto separados por virgula (e.g. caixa de chocolate, chocolate)")
        if answ is not None:
            key, val = answ.split(",")
            Gasto.map_key_value(key.strip(), val.strip())

    def confirmar_gasto(self):
        product = Gasto(self.prodTipo_var.get(), self.prodName_var.get(), self.prodValue_var.get(), self.prodCat_var.get(), self.prodDate_var.get(), self.prodMet_var.get())
        params = product._asList()
        if "" not in params:
            if messagebox.askyesno(title="confirm data", message=product.__str__(flag=1)):
                self.cadastrar_gasto(product)
            else:
                print("Cadastro cancelado")
        else:
            messagebox.showwarning(title="Cadastro Incompleto", message="Complete os dados do gasto para cadastrar")

    def cadastrar_gasto(self, product=None):
        if product is None:
            messagebox.showwarning(title="Product Not Found", message="Nenhum produto para cadastrar.")
            return
        params = product._asList()
        if "" not in params:
            if product.flag == 0:
                answer = messagebox.askyesnocancel(title="Product Unknown", message=f"Produto {product.ori_name} não identificado, gostaria de cadastra-lo com novo nome (se não, o nome {product.ori_name} será cadastrado)?")
                if answer == True:
                    novo_nome = simpledialog.askstring(
                                    title="Cadastrar Produto",
                                    prompt=f"Digite o nome padronizado para:\n'{product.ori_name}'"
                                )
                    # Se o usuário digitou e não cancelou:
                    if novo_nome and novo_nome.strip():
                        Gasto.map_key_value(product.name, novo_nome.strip())
                        Gasto.map_key_value(novo_nome.strip(), novo_nome.strip())
                        product.name = novo_nome 
                elif answer == False:
                    product.name = product.ori_name
                    Gasto.map_key_value(product.name, product.name)
                else:
                    messagebox.showwarning(title="Cadastro Cancelado", message=f"Gasto {product.ori_name} não foi cadastrado")
                    return

            self.db.insertGasto(product)
            print("Gastos cadastrados com sucesso!")
            self.db.showGastos()
        else:
            messagebox.showwarning(title="Gasto Incompleto", message="Complete os dados do gasto para cadastrar")

    def abrir_popup_qrcode(self):
        # 1. Obtém a URL e gera a imagem
        url = Camera.upload_url()
        url_img = qrcode.make(url)
        url_img = url_img.resize((220, 220))

        # 2. Cria a janela PopUp (Toplevel)
        popup = Toplevel(self)
        popup.title("Escanear QR Code")
        popup.geometry("300x340")
        popup.resizable(False, False)
        
        # Mantém o foco e bloqueia interação com a janela de trás até fechar
        popup.transient(self.winfo_toplevel())
        popup.grab_set()

        # 3. Conteúdo da Janela
        lbl_instrucao = Label(popup, text="Aponte a câmera do celular:", font=("Helvetica", 10, "bold"))
        lbl_instrucao.pack(pady=(15, 5))

        self.qr_photo = ImageTk.PhotoImage(url_img)
        lbl_qr = Label(popup, image=self.qr_photo)
        lbl_qr.pack(pady=5)

        lbl_status = Label(popup, text="Aguardando foto...", fg="#555")
        lbl_status.pack(pady=5)

        # 4. Escuta o upload em segundo plano para não congelar o Tkinter
        def aguardar_foto():
            imagem = Camera.extract_image()
            
            # Fecha o popup e processa a foto assim que terminar
            self.after(0, popup.destroy)
            self.after(0, lambda: self.processar_imagem_recebida(imagem))

        threading.Thread(target=aguardar_foto, daemon=True).start()

    def atualizar_categorias(self, *args):
        tipo_selecionado = self.prodTipo_var.get()
        
        # Busca a lista correspondente (ou const.CATEGORIAS como fallback)
        novas_opcoes = MAPEAMENTO_CATEGORIAS.get(tipo_selecionado, const.CATEGORIAS)
        
        # Atualiza as opções do Combobox existente
        self.cat_combo["values"] = novas_opcoes
        
        # Limpa ou define o primeiro valor da nova lista
        if novas_opcoes:
            self.prodCat_var.set("")

    def processar_imagem_recebida(self, imagem):
        # class variables
        db = DataBase()
        chat = Chat()

        showGastos_frame = Frame()

        answ = chat.getModelAnswer(imagem)
        message = ""
        if answ is not None:
            linhas = answ.split("\n")
            produtos = []
            for l in linhas:
                prodInfo = l.split("/")
                tipo = "Gasto Não Fixo"
                name = prodInfo[0].strip()
                price = float(prodInfo[1].replace(",", ".").strip())
                data = prodInfo[2].strip()
                categ = prodInfo[3].strip()
                metodo = "Crédito"
                produtos.append(Gasto(tipo, name, price, categ, data, metodo))

            if messagebox.askyesno(title="Produtos Encontrados", message=message):
                message += f"{len(produtos)} produtos encontrados, dia: {data}"
                db.showGastos()
                messagebox.showinfo(title="Cadastro Concluído", message="Nota fiscal cadastrada com sucesso")
            else:
                messagebox.showwarning(title="Cadastro Cancelado", message="Nota fiscal não foi cadastrada")
        else:
            messagebox.showerror(title="Falha no Cadastro", message="Erro no modelo de leitura da NF")

class AnaliseView(Frame):
    analisador = Analytics()

    def __init__(self, parent):
        super().__init__(parent, bg="#f4f6f9")

        self.mapa_subvisoes = {
            "categoria": AnaliseView.SubVisaoCategorias,
            "tipo": AnaliseView.SubVisaoTipoGasto,
            "pagamento": AnaliseView.SubVisaoMetodos,
            "temporal": AnaliseView.SubVisaoEvolucao
        }

        self.frame_menu_cards = Frame(self, bg="#f4f6f9")
        self.frame_menu_cards.pack(fill="both", expand=True)

        self.frame_detalhes = Frame(self, bg="#ffffff") # começa oculto e só aparece quando um card é clicado

        self._criar_cabecalho()
        self._criar_grid_de_cards()

    def _criar_cabecalho(self):
        header = Frame(self.frame_menu_cards, bg="#f4f6f9")
        header.pack(side="top", fill="both", padx=25, pady=(20, 10))

        # Label: Painel de Análises Financeiras
        App.create_label(header, "📊 Painel de Análises Financeiras", font=("Helvetica", 16, "bold"), bg="#f4f6f9", fg="#2c3e50", anchor="w")

        # Label: Selecione um cartão para explorar os detalhes:
        App.create_label(header, text="Selecione um cartão para explorar os detalhes:", font=("Helvetica", 10), bg="#f4f6f9", fg="#7f8c8d", anchor="w")

    def _criar_grid_de_cards(self):
        grid_frame = Frame(self.frame_menu_cards, bg="#f4f6f9")
        grid_frame.pack(padx=20, pady=10, fill="both", expand=True)

        grid_frame.columnconfigure(0, weight=1)
        grid_frame.columnconfigure(1, weight=1)

        cards_info = [
            {
                "chave": "categoria",
                "icone": "🏷️",
                "titulo": "Gastos por Categoria",
                "desc": "Distribuição percentual e ranking\nde despesas (Mercado, Lazer, etc.)",
                "row": 0, "col": 0,
                "cor_hover": "#e8f4f8"
            },
            {
                "chave": "tipo",
                "icone": "⚖️",
                "titulo": "Distribuição Orçamentária",
                "desc": "Balanço do orçamento mensal:\nEssenciais, Estilo de Vida e Renda",
                "row": 0, "col": 1,
                "cor_hover": "#e8f8f0"
            },
            {
                "chave": "temporal",
                "icone": "📈",
                "titulo": "Evolução no Tempo",
                "desc": "Linha do tempo diária/mensal e\ncurva de ritmo de consumo acumulado",
                "row": 1, "col": 0,
                "cor_hover": "#fef9e7"
            },
            {
                "chave": "pagamento",
                "icone": "💳",
                "titulo": "Métodos de Pagamento",
                "desc": "Concentração de compras em PIX,\nCartão de Crédito, Débito e Dinheiro",
                "row": 1, "col": 1,
                "cor_hover": "#fcedf2"
            }
        ]

        for card in cards_info:
            self._criar_card(grid_frame, card)

    def _criar_card(self, parent, info):
        card_btn = Frame(
            parent,
            bg="white",
            bd=1,
            relief="solid",
            cursor="hand2",
            padx=15,
            pady=15
        )
        card_btn.grid(row=info["row"], column=info["col"], padx=12, pady=12, sticky="nsew")

        lbl_icone = App.create_label(card_btn, text=info["icone"], font=("Helvetica", 22), bg="white", anchor="w", pady=(0, 5))
        lbl_titulo = App.create_label(card_btn, text=info["titulo"], font=("Helvetica", 11, "bold"), bg="white", fg="#2c3e50", anchor="w")
        lbl_desc = App.create_label(card_btn, text=info["desc"], font=("Helvetica", 9), bg="white", fg="#7f8c8d", justify="left", anchor="w", pady=(4, 8))
        lbl_acao = App.create_label(card_btn, text="Abrir relatório ➔", font=("Helvetica", 9, "bold"), bg="white", fg="#2980b9", anchor="e", side="bottom")

        # Clicar em qualquer parte do card aciona o método
        elementos = [card_btn, lbl_icone, lbl_titulo, lbl_desc, lbl_acao]
        for elem in elementos:
            elem.bind("<Button-1>", lambda e, chave=info["chave"]: self.abrir_detalhe(chave))
            elem.bind("<Enter>", lambda e, f=card_btn, cor=info["cor_hover"]: self._aplicar_hover(f, cor))
            elem.bind("<Leave>", lambda e, f=card_btn: self._aplicar_hover(f, "white"))

    def _aplicar_hover(self, frame, cor):
        frame.configure(bg=cor)
        for child in frame.winfo_children():
            child.configure(bg=cor)

    def abrir_detalhe(self, chave):
        """Oculta o menu de cartões e renderiza a sub-visão selecionada."""
        self.frame_menu_cards.pack_forget()

        # Limpa detalhes abertos anteriormente
        for widget in self.frame_detalhes.winfo_children():
            widget.destroy()

        self.frame_detalhes.pack(fill="both", expand=True)

        # # Barra superior da tela de detalhe com botão voltar
        # barra_topo = Frame(self.frame_detalhes, bg="#ffffff")
        # barra_topo.pack(fill="x", padx=15, pady=10)

        # INSTANCIA A SUB-VISÃO AQUI:
        ClasseView = self.mapa_subvisoes.get(chave)
        if ClasseView:
            # Cria a instância da sub-visão passando o frame_detalhes como pai
            sub_view_instancia = ClasseView(self.frame_detalhes, self.voltar_ao_menu_cards)
            sub_view_instancia.pack(fill="both", expand=True)
            if hasattr(ClasseView, "update_dados"):
                sub_view_instancia.update_dados()

    def voltar_ao_menu_cards(self):
        """Oculta a tela de detalhe e traz o menu de cartões de volta."""
        self.frame_detalhes.pack_forget()
        self.frame_menu_cards.pack(fill="both", expand=True)

    class SubVisaoBase(Frame):
        """Classe base com a barra superior e botão voltar."""
        def __init__(self, parent, titulo_texto, voltar_callback):
            super().__init__(parent, bg="#ffffff")
            self.voltar_callback = voltar_callback
            self.analisty = AnaliseView.analisador

            # Barra superior com botão voltar
            top_bar = Frame(self, bg="#ffffff")
            top_bar.pack(fill="x", padx=15, pady=10)

            btn_voltar = Button(
                top_bar,
                text="⬅ Voltar aos Cartões",
                font=("Helvetica", 9, "bold"),
                bg="#ecf0f1",
                relief="flat",
                command=self.voltar_callback,
                padx=10,
                pady=4,
                cursor="hand2"
            )
            btn_voltar.pack(side="left")

            titulo = App.create_label(top_bar, text=titulo_texto, font=("Helvetica", 13, "bold"), bg="#ffffff", fg="#2c3e50", side="left", padx=15)

            # Separador visual
            ttk.Separator(self, orient="horizontal").pack(fill="x", padx=15, pady=(0, 10))

        @staticmethod
        def carregar_dados(root, dados_fetchall, colunas, img):
            frame_tabela = Frame(root, bg="white", bd=1, relief="solid")
            frame_tabela.pack(fill="both", expand=True, padx=10, pady=10)
            frame_tabela.pack_propagate(False)

            #root.tree = App.create_tree_table(frame_tabela, colunas)
            root.tree = App.create_table_and_graph(frame_tabela, colunas, img, row=0)
    
            for item in root.tree.get_children():
                root.tree.delete(item)
    
            for linha in dados_fetchall:
                # linha é uma tupla, ex: (1, 'Alimentação', 'Mercado', '2026-09-16', 'PIX', 45.50)
                valores = list(linha)
                
                # Formata o valor monetário se desejar
                if "valor" in colunas:
                    idx = colunas.index("valor")
                    valores[idx] = f"R$ {valores[idx]:.2f}"
                
                root.tree.insert("", "end", values=valores)


    class SubVisaoCategorias(SubVisaoBase):
        def __init__(self, parent, voltar_callback):
            super().__init__(parent, "🏷️ Análise por Categoria", voltar_callback)
        
            App.create_label(self, text=f"Relatório: Gastos por Categoria", font=("Helvetica", 14, "bold"), bg="white", pady=10)

            # Frame de campos de inserção
            form_frame = Frame(self)
            form_frame.pack(pady=10, padx=10)

            self.mes_text = StringVar()
            box = App.create_option_field(form_frame, "Mês", self.mes_text, list(self.analisty.extractMonths()), pady=0, bg="white")
            box.current(0)
            self.mes_text.trace_add("write", self.update_dados)

            self.conteudo = Frame(self, bg="#ffffff")
            self.conteudo.pack(fill="both", expand=True, padx=20, pady=5)

            self.update_dados()

        def update_dados(self, *args):
            for widget in self.conteudo.winfo_children():
                    widget.destroy()

            lbl = App.create_label(self.conteudo, text=f"Tabela / Gráfico de Categorias em {self.mes_text.get()}", bg="white", fg="#7f8c8d", pady=5)

            valores, colunas, chart_path = self.analisty.gastoPorCategoria(curMes=self.mes_text.get())

            self.chart = pilImg.open(chart_path).resize((320, 240), pilImg.Resampling.LANCZOS)
            
            self.carregar_dados(self.conteudo, valores, colunas, self.chart)
        
    class SubVisaoTipoGasto(SubVisaoBase):
        def __init__(self, parent, voltar_callback):
            super().__init__(parent, "⚖️ Distribuição Orçamentária", voltar_callback)

            App.create_label(self, text="Relatório: Distribuição Orçamentária", font=("Helvetica", 14, "bold"), bg="white", pady=20)

            # Frame de campos de inserção
            form_frame = Frame(self)
            form_frame.pack(pady=10, padx=10)

            self.mes_text = StringVar()
            box = App.create_option_field(form_frame, "Mês", self.mes_text, list(self.analisty.extractMonths()), pady=0, bg="white")
            box.current(0)
            self.mes_text.trace_add("write", self.update_dados)

            self.conteudo = Frame(self, bg="#ffffff")
            self.conteudo.pack(fill="both", expand=True, padx=20, pady=5)
            self.grid_columnconfigure(0, weight=1, uniform="grupo1")
            self.grid_columnconfigure(1, weight=1, uniform="grupo1")

            self.update_dados()


        def update_dados(self, *args):
            for widget in self.conteudo.winfo_children():
                    widget.destroy()

            lbl = App.create_label(self.conteudo, text=f"Gráficos Orçamentários em {self.mes_text.get()}", bg="white", fg="#7f8c8d", pady=5)


            o_img_path, a_img_path  = self.analisty.gastoOrcamentario(curMes=self.mes_text.get())

            self.frame_graphs = Frame(self.conteudo, bg="white", bd=1, relief="solid")
            self.frame_graphs.pack(fill="both", expand=True, padx=10, pady=10)
            self.frame_graphs.pack_propagate(False)
            self.frame_graphs.rowconfigure(0, weight=1)
            self.frame_graphs.grid_columnconfigure(0, weight=1)
            self.frame_graphs.grid_columnconfigure(1, weight=1)

            self.orcamento = self.showChart(o_img_path, row=0, col=0)
            self.alimentacao = self.showChart(a_img_path, row=0, col=1)

        def showChart(self, img_path, row, col):
            # Moldura individual para cada gráfico/texto dentro da grade
            card = Frame(self.frame_graphs, bg="white", bd=1, relief="solid")
            card.grid(row=0, column=col, sticky="nsew", padx=8, pady=8)
            card.pack_propagate(False)  # Impede que o conteúdo altere o tamanho do card

            if img_path is not None:
                imagem_original = pilImg.open(img_path)
                img_label = Label(card, bg="white")
                img_label.pack(fill="both", expand=True)

                ultimo = {"w": 0, "h": 0}

                def redimensionar(event):
                    w = event.width
                    h = event.height

                    if w > 60 and h > 60:
                        # Evita recálculos desnecessários por pequenas variações
                        if abs(w - ultimo["w"]) > 6 or abs(h - ultimo["h"]) > 6:
                            ultimo["w"] = w
                            ultimo["h"] = h

                            img_copy = imagem_original.copy()
                            img_copy.thumbnail((w - 10, h - 10), pilImg.Resampling.LANCZOS)

                            img_tk = ImageTk.PhotoImage(img_copy, master=card)
                            img_label.config(image=img_tk)
                            img_label.image = img_tk  # Previne Garbage Collector

                # O evento fica no card pai, prevenindo loop infinito do Label
                card.bind("<Configure>", redimensionar)
                return img_label
            else:
                aviso_label = Label(
                    card, 
                    text="Gráfico ainda não disponível\npara esse mês", 
                    bg="white", 
                    fg="#7f8c8d",
                    justify="center",
                    wraplength=180
                )
                aviso_label.pack(fill="both", expand=True)
                return aviso_label
            

    class SubVisaoEvolucao(SubVisaoBase):
        def __init__(self, parent, voltar_callback):
            super().__init__(parent, "📈 Evolução Temporal e Tendências", voltar_callback)

            #App.create_label(self, text="Evolução Temporal", font=("Helvetica", 14, "bold"), bg="white", pady=15)

            # Frame de campos de inserção
            form_frame = Frame(self)
            form_frame.pack(pady=10, padx=10)

            self.mes_text = StringVar()
            options = list(self.analisty.extractMonths())
            options.insert(0, "Anual")
            box = App.create_option_field(form_frame, "Periodo", self.mes_text, options, pady=0, bg="white")
            box.current(0)
            self.mes_text.trace_add("write", self.update_dados)

            self.conteudo = Frame(self, bg="#ffffff")
            self.conteudo.pack(fill="both", expand=True, padx=20, pady=5)
            self.grid_columnconfigure(0, weight=1, uniform="grupo1")
            self.grid_columnconfigure(1, weight=1, uniform="grupo1")

            self.update_dados()


        def update_dados(self, *args):
            for widget in self.conteudo.winfo_children():
                    widget.destroy()

            lbl = App.create_label(self.conteudo, text=f"Gráficos Orçamentários em {self.mes_text.get()}", bg="white", fg="#7f8c8d", pady=5)


            img_path  = self.analisty.evolucaoTemporal(curMes=self.mes_text.get())

            self.frame_graphs = Frame(self.conteudo, bg="white", bd=1, relief="solid")
            self.frame_graphs.pack(fill="both", expand=True, padx=10, pady=10)
            self.frame_graphs.pack_propagate(False)
            self.frame_graphs.rowconfigure(0, weight=1)
            self.frame_graphs.grid_columnconfigure(0, weight=1)
            #self.frame_graphs.grid_columnconfigure(1, weight=1)

            self.orcamento = self.showChart(img_path, row=0, col=0)

        def showChart(self, img_path, row, col):
            # Moldura individual para cada gráfico/texto dentro da grade
            card = Frame(self.frame_graphs, bg="white", bd=1, relief="solid")
            card.grid(row=0, column=col, sticky="nsew", padx=8, pady=8)
            card.pack_propagate(False)  # Impede que o conteúdo altere o tamanho do card

            if img_path is not None:
                imagem_original = pilImg.open(img_path)
                img_label = Label(card, bg="white")
                img_label.pack(fill="both", expand=True)

                ultimo = {"w": 0, "h": 0}

                def redimensionar(event):
                    w = event.width
                    h = event.height

                    if w > 60 and h > 60:
                        # Evita recálculos desnecessários por pequenas variações
                        if abs(w - ultimo["w"]) > 6 or abs(h - ultimo["h"]) > 6:
                            ultimo["w"] = w
                            ultimo["h"] = h

                            img_copy = imagem_original.copy()
                            img_copy.thumbnail((w - 10, h - 10), pilImg.Resampling.LANCZOS)

                            img_tk = ImageTk.PhotoImage(img_copy, master=card)
                            img_label.config(image=img_tk)
                            img_label.image = img_tk  # Previne Garbage Collector

                # O evento fica no card pai, prevenindo loop infinito do Label
                card.bind("<Configure>", redimensionar)
                return img_label
            else:
                aviso_label = Label(
                    card, 
                    text="Gráfico ainda não disponível\npara esse mês", 
                    bg="white", 
                    fg="#7f8c8d",
                    justify="center",
                    wraplength=180
                )
                aviso_label.pack(fill="both", expand=True)
                return aviso_label

    class SubVisaoMetodos(SubVisaoBase):
        def __init__(self, parent, voltar_callback):
            super().__init__(parent, "💳 Métodos de Pagamento (PIX, Cartão, etc.)", voltar_callback)

            App.create_label(self, text="Relatório: Métodos de Pagamento", font=("Helvetica", 14, "bold"), bg="white", pady=20)

        def carregar_dados(self):
            print("Recarregando métodos de pagamento...")

class HistoricoView(Frame):

    def __init__(self, parent):
        super().__init__(parent)
        label = Label(
            self, text="Tela: Histórico de Gastos", font=("Helvetica", 14, "bold")
        )
        label.pack(pady=20)

        self.db = DataBase()

        self.refresh_button = Button(self, text="Refresh", command=lambda: self.carregar_dados(self.db.getAllGastos()))
        self.refresh_button.pack(side=TOP, padx=(20, 0), pady=(0, 0), anchor='w')

        self.frame_tabela = Frame(self)
        self.frame_tabela.pack(fill="both", expand=True, padx=10, pady=10)

        self.colunas = ("id", "nome", "dia", "valor", "tipo_gasto", "categoria", "metodo_pagamento")

        self.tree = App.create_tree_table(self.frame_tabela, self.colunas)

        self.carregar_dados(self.db.getAllGastos())
    
        
    def carregar_dados(self, dados_fetchall):
        for item in self.tree.get_children():
            self.tree.delete(item)

        for linha in dados_fetchall:
            # linha é uma tupla, ex: (1, 'Alimentação', 'Mercado', '2026-09-16', 'PIX', 45.50)
            
            # Formata o valor monetário se desejar
            valores = list(linha)
            valores[3] = f"R$ {valores[3]:.2f}"

            self.tree.insert("", "end", values=valores)

class SQLView(Frame):

    def __init__(self, parent):
        super().__init__(parent, bg="#f4f6f9")
        label = Label(
            self, text="Tela: Consultas SQL", font=("Helvetica", 14, "bold")
        )
        label.pack(pady=20)

        self.query = App.create_multiline_field(self, "Digite sua consulta aqui")

        confirm_button = Button(self, text="Realizar Consulta", command=self.runQuery)
        confirm_button.pack(padx=(0, 0), pady=(0, 0))


    def runQuery(self):

        cur_query = self.query.get("1.0", "end-1c")
        if ("delete" in str.lower(cur_query)) or ("drop" in str.lower(cur_query)) or ("select" not in str.lower(cur_query)):
            messagebox.showwarning(title="Ação Proibida", message="só são permitidas ações de select")
        else:
            db = DataBase()
            print("Consulta:", cur_query)
            resul_consulta, colunas = db.consultaManual(cur_query)
            print("Colunas:", colunas)
            print("Resultado", resul_consulta)
            self.showResult(resul_consulta, colunas)


    def showResult(self, dados_fetchall, colunas):
        popup = Toplevel(self)
        popup.title("Query Result")
        popup.geometry("600x400")
        popup.resizable(True, True)

        # Mantém o foco e bloqueia interação com a janela de trás até fechar
        popup.transient(self.winfo_toplevel())
        popup.grab_set()

        frame_tabela = Frame(popup)
        frame_tabela.pack(fill="both", expand=True, padx=10, pady=10)

        self.tree = App.create_tree_table(frame_tabela, colunas)

        self.carregar_dados_sql(dados_fetchall, colunas)

    def carregar_dados_sql(self, dados_fetchall, colunas):
        for item in self.tree.get_children():
            self.tree.delete(item)

        for linha in dados_fetchall:
            # linha é uma tupla, ex: (1, 'Alimentação', 'Mercado', '2026-09-16', 'PIX', 45.50)
            valores = list(linha)
            
            # Formata o valor monetário se desejar
            if "valor" in colunas:
                idx = colunas.index("valor")
                valores[idx] = f"R$ {valores[idx]:.2f}"
            
            self.tree.insert("", "end", values=valores)


""" Application Class """
class App(Tk):
    def __init__(self, master=None):
        super().__init__()
        self.title("Finance Manager")
        self.geometry("750x600")
        self.minsize(700, 550)

        self.container = Frame(self, bg="#f4f6f9")
        self.container.pack(side="bottom", fill="both", expand=True)


        checkdb = DataBase()

        if checkdb.first:
            curDia = datetime.today().strftime('%Y-%m-%d')
            promp = "Qual seu saldo total no momento? Se não souber pode ser uma estimativa"
            saldo_inicial = simpledialog.askfloat(title="Sua Primeira Vez Aqui!", prompt=promp, initialvalue=0.)
            if saldo_inicial is not None:
                saldo_inicial = float(str(saldo_inicial).replace(",", "."))
                print(f"INSERT INTO saldo ({str(saldo_inicial).replace(",", ".")}, {curDia})")
                DataBase.atualizaSaldo(saldo_inicial, curDia)
                messagebox.showinfo(title="Saldo cadastrado com sucesso!", message=f"Saldo inicial de {saldo_inicial} cadastrado!")

        self.frames = {}    
        for ViewClass in (InserirGastoView, AnaliseView, HistoricoView, SQLView, MainView):
            frame = ViewClass(self.container)
            self.frames[ViewClass] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)

        self.configNavBar()

    def configNavBar(self):
        self.nav_bar = Frame(self, bg="#2c3e50", height=45, bd=0, highlightthickness=0)
        self.nav_bar.pack(side="top", fill="x", expand=False)
        self.nav_bar.pack_propagate(False)  # <-- Garante que a barra não encolha nem suma!

        self._create_nav_button("📊 Início", MainView)
        self._create_nav_button("➕ Inserir Gasto", InserirGastoView)
        self._create_nav_button("📊 Análise", AnaliseView)
        self._create_nav_button("📋 Histórico", HistoricoView)
        self._create_nav_button("🗄️ SQL / Banco", SQLView)

    def _create_nav_button(self, text, frame_class):
        btn = Button(
            self.nav_bar,
            text=text,
            bg="#34495e",
            fg="white",
            relief="flat",
            padx=15,
            pady=8,
            command=lambda: self.show_frame(frame_class),
        )
        btn.pack(side="left", fill='y', padx=5, pady=5)

    def show_frame(self, frame_class):
        frame = self.frames[frame_class]
        frame.tkraise()

        if hasattr(frame, "atualizar_kpis"):
            frame.atualizar_kpis()
        if hasattr(frame, "carregar_dados"):
            frame.carregar_dados(DataBase.getAllGastos())
        if hasattr(frame, "carregar_ultmos_gastos"):
            frame.carregar_ultmos_gastos()

    @staticmethod
    def create_label(root, text, image=None, **kwargs):
        text_label = Label(root, text=text, image=image, font=kwargs.get("font"), bg=kwargs.get("bg"), fg=kwargs.get("fg"))
        text_label.pack(
            expand=kwargs.get("expand", False),
            fill=kwargs.get("fill"), 
            side=kwargs.get("side", "top"), 
            padx=kwargs.get("padx"), 
            pady=kwargs.get("pady"),
            anchor=kwargs.get("anchor")
            )

        return text_label

    @staticmethod
    def create_entry(root, textVar, **kwargs):
        entry = Entry(root, textvar=textVar, justify=kwargs.get("justify"))
        entry.pack(
            expand=kwargs.get("expand", False),
            fill=kwargs.get("fill"), 
            side=kwargs.get("side", "top"), 
            padx=kwargs.get("padx"), 
            pady=kwargs.get("pady"),
            )
        
        return entry

    @staticmethod
    def create_entry_field(root, fieldName, textVar, row=0, **kwargs):
        field_label = Label(root, text=fieldName)
        field_entry = Entry(root, textvar=textVar)

        field_label.grid(row=row, column=0, sticky='w', padx=kwargs.get("padx"), pady=kwargs.get("pady"))
        field_entry.grid(row=row, column=1, sticky='w', padx=kwargs.get("padx"), pady=kwargs.get("pady"))

    @staticmethod
    def create_option_field(root, fieldName, textVar, valores, row=0, **kwargs):
        field_label = Label(root, text=fieldName, bg=kwargs.get("bg"))
        field_combo = ttk.Combobox(
            root, 
            textvariable=textVar, 
            values=valores,          # Lista de opções finitas, ex: ["PIX", "Cartão de Crédito", "Dinheiro"]
            state="readonly"         # Evita que o usuário digite um valor fora da lista
            )

        field_label.grid(row=row, column=0, sticky='w', padx=kwargs.get("padx"), pady=kwargs.get("pady"))
        field_combo.grid(row=row, column=1, sticky='w', padx=kwargs.get("padx"), pady=kwargs.get("pady"))

        return field_combo

    @staticmethod
    def create_date_field(parent, fieldName, dateVar=None, row=0, **kwargs):

        field_label = Label(parent, text=fieldName)

        # DateEntry já vem com calendário suspenso embutido
        field_date = DateEntry(
            parent,
            textvariable=dateVar,
            date_pattern="yyyy-mm-dd",  # Formato ideal para salvar direto no SQL (YYYY-MM-DD)
            locale="pt_BR",             # Dias e meses em português
            width=12
        )

        field_label.grid(row=row, column=0, sticky='w', padx=kwargs.get("padx", 5), pady=kwargs.get("pady", 5))
        field_date.grid(row=row, column=1, sticky='w', padx=kwargs.get("padx", 5), pady=kwargs.get("pady", 5))

    @staticmethod
    def create_multiline_field(parent, fieldName, row=0, height=3, width=25, **kwargs):
        field_label = Label(parent, text=fieldName)
        field_text = Text(parent, height=height, width=width, wrap="word")
        
        # Vincula o evento de digitação para manter as novas linhas centralizadas
        field_text.bind("<KeyRelease>", lambda event: field_text.tag_add("1.0", "end"))

        field_label.pack(padx=kwargs.get("padx", 5), pady=kwargs.get("pady", 5))
        field_text.pack(padx=kwargs.get("padx", 5), pady=kwargs.get("pady", 5))

        return field_text

    @staticmethod
    def create_tree_table(root, colunas):
        tree = ttk.Treeview(
            root,
            columns=colunas,
            show="headings",        # Oculta a coluna fantasma padrão (#0) do Treeview
            selectmode="extended"   # Permite selecionar linhas
        )

        for col in colunas:
            if col == "id":
                tree.heading("id", text="ID")
                tree.column("id", width=40, anchor="center")
            elif col == "dia":
                tree.heading("dia", text="Data")
                tree.column("dia", width=80, anchor="center")
            elif col == "valor":
                tree.heading("valor", text="Valor (R$)")
                tree.column("valor", width=80, anchor="e")  # Alinhado à direita para moeda
            elif col == "metodo_pagamento":
                tree.heading("metodo_pagamento", text="Método")
                tree.column("metodo_pagamento", width=110, anchor="w")
            else:
                tree.heading(col, text=col)
                tree.column(col, width=100, anchor="w")
            

        scrollbar = ttk.Scrollbar(root, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)

        scrollbarX = ttk.Scrollbar(root, orient="horizontal", command=tree.xview)
        tree.configure(xscrollcommand=scrollbarX.set)

        tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        return tree

    @staticmethod
    def create_table_and_graph(root, colunas, img, row=0, **kwargs):

        root.grid_rowconfigure(row, weight=1)
        root.grid_columnconfigure(0, weight=1, uniform="grupo1")
        root.grid_columnconfigure(1, weight=1, uniform="grupo1")

        frame_tabela = tk.Frame(root, bg="white", bd=1, relief="solid")
        frame_tabela.grid(row=row, column=0, sticky="nsew", padx=10, pady=10)

        tree = App.create_tree_table(frame_tabela, colunas)

        lbl_img = Label(root, bg="white")
        lbl_img.grid(row=row, column=1, sticky="nsew", padx=10, pady=10)

        if isinstance(img, str):
            imagem_original = pilImg.open(img)
        elif isinstance(img, pilImg.Image):
            imagem_original = img
        else:
            imagem_original = None

        if imagem_original:
            ultimo_tamanho = {"w": 0, "h": 0}
            def redimensionar_grafico(event):
                # Obtém a largura e altura disponíveis no momento
                w_disp = event.width
                h_disp = event.height

                if w_disp > 50 and h_disp > 50:
                    n_max = 4
                    if abs(w_disp - ultimo_tamanho["w"]) > n_max or abs(h_disp - ultimo_tamanho["h"]) > n_max:
                        # Mantém a proporção ou estica para ocupar o espaço do frame
                        img_redimensionada = imagem_original.resize((w_disp - n_max, h_disp - n_max), pilImg.Resampling.LANCZOS)
                        img_tk = ImageTk.PhotoImage(img_redimensionada, master=root)
                        
                        lbl_img.config(image=img_tk)
                        lbl_img.image = img_tk  # Previne Garbage Collector
            lbl_img.bind("<Configure>", redimensionar_grafico)



        return tree