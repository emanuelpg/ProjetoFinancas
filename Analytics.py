import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import matplotlib.dates as mdates
from matplotlib.figure import Figure
import numpy as np
import sqlite3
import datetime
import os, sys

from BancoDeDados import DataBase

class Analytics:
    def __init__(self):
        self.db = DataBase()
        self.dir = r"C:\Users\emanu\ProjetoFinanças\Charts"
        if not os.path.exists(self.dir):
            os.makedirs(self.dir)

    def extractMonths(self):
        query = "select distinct strftime('%Y-%m', dia) AS mes " \
        "from gastos " \
        "Order by mes DESC"

        results, _ = self.db.consultaManual(query)

        meses = np.array(results)[:,0]

        return meses

    def gastoPorCategoria(self, curMes=None):
        if curMes is None:
            curMes = datetime.datetime.today().strftime('%Y-%m')
    
        query = "select g.categoria, g.gasto_total from " \
        "(select categoria, strftime('%Y-%m', dia) AS mes, " \
        "SUM(valor) as gasto_total "\
        "FROM gastos "\
        f"where mes = '{curMes}' AND tipo_gasto in ('Gasto Fixo', 'Gasto Não Fixo') "\
        "GROUP BY categoria, mes) as g; "

        result, colunas = self.db.consultaManual(query)
        result = np.array(result)
        if np.ndim(result) == 1:
            result = result.reshape(1, -1)

        categorias = result[:, 0]
        valores = [float(val) for val in result[:, 1]]
        fig_path = os.path.join(self.dir, "categoria.png")

        fig, ax = plt.subplots()

        fig.set_size_inches((5, 3.5))
        ax.set_title("Gastos por Categoria", fontsize=11, fontweight="bold")
        plt.tight_layout()

        barras = ax.barh(categorias, valores)
        max_valor = max(valores) if valores else 100
        ax.set_xlim(0, max_valor * 1.25)  # 20% de margem no topo da barra

        ax.bar_label(
            barras, 
            fmt="R$ %.2f",           # Formata como valor monetário (ex: R$ 254.00)
            label_type="edge",       # "center" coloca no meio da barra; "edge" coloca na ponta
            color="black",            
            fontsize=9, 
            fontweight="bold"
        )

        fig.savefig(fig_path, bbox_inches='tight', dpi=100)

        #plt.show()
        plt.close()

        return result, colunas, fig_path

    def gastoOrcamentario(self, curMes=None):
        if curMes is None:
            curMes = datetime.datetime.today().strftime('%Y-%m')

        """ Orçamento por Tipo """
        query = f"""
            select g.tipo_gasto, g.gasto_total from 
                (select tipo_gasto, strftime('%Y-%m', dia) AS mes, sum(valor) as gasto_total 
                    from gastos 
                    where mes = '{curMes}' AND tipo_gasto in ('Gasto Fixo', 'Gasto Não Fixo', 'Investimento') 
                    group by tipo_gasto, mes) as g
            """

        result_t, colunas_t = self.db.consultaManual(query)
        result_t = np.array(result_t)

        if np.ndim(result_t) == 2:
            tipos = result_t[:, 0]
            valores = [float(val) for val in result_t[:, 1]]
            fig_path_t = os.path.join(self.dir, "orcamento.png")
            
            fig, ax = plt.subplots()
            fig.set_size_inches((5, 3.5))
            ax.pie(valores, labels=tipos, autopct='%1.1f%%')
            ax.set_title(f"Distribuição do Orçamento em {curMes}")
            plt.tight_layout()

            fig.savefig(fig_path_t, bbox_inches='tight', dpi=100)

            plt.close()
        else:
            fig_path_t = None

        """ Orçamento Alimentar """
        query = f"""
            select g.categoria, g.gasto_total from 
                (select categoria, strftime('%Y-%m', dia) AS mes, sum(valor) as gasto_total 
                    from gastos 
                    where mes = '{curMes}' AND categoria  in ('Doce', 'Fruta', 'Comida Pronta', 'Comida para Fazer') 
                    group by categoria, mes) as g
        """

        result_c, colunas_c = self.db.consultaManual(query)
        result_c = np.array(result_c)

        for res in result_c:
            if (res[0] == "Comida Pronta") or (res[0] == "Doce"):
                res = list(res)
                res[0] = "Restaurante/Delivery" 
            else:
                res = list(res)
                res[0] = "Mercado" 

        if np.ndim(result_c) == 2:
            tipos = result_c[:, 0]
            valores = [float(val) for val in result_c[:, 1]]
            fig_path_c = os.path.join(self.dir, "alimentacao.png")
            
            fig, ax = plt.subplots()
            fig.set_size_inches((5, 3.5))
            ax.pie(valores, labels=tipos, autopct='%1.1f%%')
            ax.set_title(f"Alimentação em {curMes}")
            plt.tight_layout()

            fig.savefig(fig_path_c, bbox_inches='tight', dpi=100)

            plt.close()
        else:
            fig_path_c = None
        
        
        return fig_path_t, fig_path_c

    def evolucaoTemporal(self, curMes="Anual"):
        if curMes != "Anual":
            mensal = 0
            query = f"""
                SELECT 
                    dia,
                    
                    -- Balanço Líquido (Ganhos - Gastos)
                    COALESCE(SUM(CASE WHEN tipo_gasto = 'Entrada' THEN valor ELSE 0 END), 0) -
                    COALESCE(SUM(CASE WHEN tipo_gasto IN ('Gasto Fixo', 'Gasto Não Fixo') THEN valor ELSE 0 END), 0) AS saldo,
                    
                    -- Total Gasto
                    COALESCE(SUM(CASE WHEN tipo_gasto IN ('Gasto Fixo', 'Gasto Não Fixo') THEN valor ELSE 0 END), 0) AS gasto,
                    
                    -- Total Ganho / Entrada
                    COALESCE(SUM(CASE WHEN tipo_gasto = 'Entrada' THEN valor ELSE 0 END), 0) AS ganho,
                    
                    -- Total Investido
                    COALESCE(SUM(CASE WHEN tipo_gasto = 'Investimento' THEN valor ELSE 0 END), 0) AS investimento
                FROM gastos
                WHERE strftime('%Y-%m', dia) = '{curMes}'
                group by dia
                order by dia;                
                """
            result, colunas = DataBase.consultaManual(query)
            result = np.array(result)
            title = f"Evolução Diária do Patrimônio em {curMes}" 

        else:
            mensal = 1
            query = f"""
                SELECT 
                    strftime('%Y-%m', dia) as mes,
                    
                    -- Balanço Líquido (Ganhos - Gastos)
                    COALESCE(SUM(CASE WHEN tipo_gasto = 'Entrada' THEN valor ELSE 0 END), 0) -
                    COALESCE(SUM(CASE WHEN tipo_gasto IN ('Gasto Fixo', 'Gasto Não Fixo') THEN valor ELSE 0 END), 0) AS saldo,
                    
                    -- Total Gasto
                    COALESCE(SUM(CASE WHEN tipo_gasto IN ('Gasto Fixo', 'Gasto Não Fixo') THEN valor ELSE 0 END), 0) AS gasto,
                    
                    -- Total Ganho / Entrada
                    COALESCE(SUM(CASE WHEN tipo_gasto = 'Entrada' THEN valor ELSE 0 END), 0) AS ganho,
                    
                    -- Total Investido
                    COALESCE(SUM(CASE WHEN tipo_gasto = 'Investimento' THEN valor ELSE 0 END), 0) AS investimento
                FROM gastos
                group by mes
                order by mes;                
                """
            result, colunas = DataBase.consultaManual(query)
            result = np.array(result)
            title = f"Evolução Mensal do Patrimônio"

        if np.ndim(result) == 2:
            if mensal:
                idx = -12
                datas = [mes.split("-")[1] for mes in result[idx:, 0]]
            else:
                idx = 0
                datas = [dia.split("-")[2] for dia in result[:, 0]]
                

            saldos = [np.round(float(val), 2)+DataBase.consultaSaldo() for val in result[idx:, 1]]
            gastos = [np.round(float(val), 2) for val in result[idx:, 2]]
            ganhos = [np.round(float(val), 2) for val in result[idx:, 3]]

            fig_path = os.path.join(self.dir, "evolucao.png")

            # Criação da figura com proporção adequada
            fig, ax = plt.subplots(figsize=(6, 3.8), facecolor="white")
            ax.set_facecolor("white")

            # Plotagem com paleta refinada e espessura moderna
            ax.plot(datas, saldos, marker="o", markersize=4, linewidth=2.4, color="#2980b9", label="Saldo", zorder=4)
            ax.plot(datas, gastos, marker="o", markersize=4, linewidth=2.0, color="#e74c3c", label="Gasto", alpha=0.9, zorder=3)
            ax.plot(datas, ganhos, marker="o", markersize=4, linewidth=2.0, color="#27ae60", label="Ganho", alpha=0.9, zorder=3)
            if mensal:
                investimentos = [np.round(float(val), 2) for val in result[idx:, 4]]
                ax.plot(datas, investimentos, marker="o", markersize=4, linewidth=1.8, color="#8e44ad", label="Invest.", 
                        alpha=0.85, linestyle="--", zorder=3)

            # Preenchimento suave sob a linha de saldo para destacar a tendência
            ax.fill_between(datas, saldos, color="#2980b9", alpha=0.08, zorder=2)

            # Linha de referência no zero (importante para saldos negativos/positivos)
            ax.axhline(0, color="#bdc3c7", linewidth=0.9, linestyle="--", zorder=1)

            # Limpeza de bordas (spines) e grid horizontal sutil
            for spine in ["top", "right"]:
                ax.spines[spine].set_visible(False)
            for spine in ["bottom", "left"]:
                ax.spines[spine].set_color("#dcdde1")

            ax.grid(axis="y", linestyle=":", alpha=0.5, color="#bdc3c7", zorder=1)

            # Formatação dos Eixos e Título
            ax.set_title(
                f"{title}", fontsize=11, fontweight="bold", color="#2c3e50", pad=12
            )
            ax.tick_params(colors="#7f8c8d", labelsize=8.5)

            # Formata o eixo Y como moeda abreviada (ex: R$ 1.500)
            ax.yaxis.set_major_formatter(
                ticker.FuncFormatter(lambda x, pos: f"R$ {x:,.0f}")
            )

            # Legenda compacta e sem caixa pesada
            ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.15), ncol=4, frameon=False, fontsize=8.5, labelcolor="#2c3e50")

            # Salvar sem margens excessivas
            fig.savefig(fig_path, bbox_inches="tight", dpi=130)
            plt.close(fig)  # Libera memória imediatamente

        else:
            fig_path = None

        return fig_path

    def gastoMedioMensal(self):
        meses, _ = [l[0] for l in self.db.consultaManual(
            "select distinct " \
            "strftime('%Y-%m', dia) AS mes" \
            "FROM gastos"
        )]

        review = []
        cols = ["mes", "entrada", "outcome", "saldo", "variância"]

        for mes in meses:
            income = 0
            outcome = 0

            query = f"select strftime('%Y-%m', dia) AS mes,"\
            "SUM(valor) as gasto_total,"\
            "tipo_gasto"\
            "FROM gastos"\
            "where mes = {mes} "\
            "GROUP BY tipo_gasto, mes"\
            "ORDER BY mes DESC;"

            result, _ = self.db.consultaManual(query)

            for l in result:
                if l[-1] in ("Gasto Fixo", "Gasto Não Fixo"):
                    outcome += l[1]
                if l[-1] == "entrada":
                    income += l[1]

            review.append(np.array([mes, income, outcome, income-outcome]))

        mean = np.mean(np.array(review)[:, -1])
        for l in review:
            review = np.concatenate(l, [l[-1]-mean])

        return review, cols
        

""" Testes manuais """
# test = Analytics()
# print(test.evolucaoTemporal(curMes="2026-09"))
# print("----------------------------------")
# print(test.evolucaoTemporal())

